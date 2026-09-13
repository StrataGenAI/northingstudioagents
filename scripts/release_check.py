#!/usr/bin/env python3
"""Release gate: the defects that shipped past the critic in v1, checked by script.

v1 shipped:
- a live "quietcompass.example" link in a customer file
- upsells to "The Balance Audit" and "The Compass System", neither of which exists
- a file named PB-001_Focus_Audit_Workbook.pdf

The critic reads pages; this script reads everything else, and it does not get
tired. Run it after the critic's last round and BEFORE pdf-protect (default mode),
again once the listing and pins exist (--listing), and on SIGNOFF.md (--signoff).
Exit code 1 on any failure. Nothing in here is a warning that can be waved through.

  release_check.py "Products/PB-022 The 10-Minute Life Audit"
  release_check.py "Products/PB-022 The 10-Minute Life Audit" --listing
  release_check.py "Products/PB-022 The 10-Minute Life Audit" --signoff --require-drive-links

Default-mode checks (per edition wherever that applies):
  urls          every URL, bare domain and email in the PDFs, README and licences
                resolves. Reserved .example/.test/.invalid domains fail outright;
                etsy.com verifies only through the Etsy API (ETSY_API_KEY).
  placeholders  no <OWNER ...>, [Assumption], TODO or {template} left in a customer file
  licence       dist/licences/LICENCE.txt exists (make_licence.py) and README points to it
  catalogue     every sibling product named and every shop URL is live in catalogue.md
  formats       all three editions ship; every format a cover or README claims ships
                as a file of that size; every page count claimed matches the edition
  sku           no PB-/BN- IDs in customer filenames, PDF metadata or customer text
  crossrefs     every "page N" in each edition is declared in the spec's
                Cross-references table and lands on the declared heading
                (table: Reference text | Target page | Target heading | Editions)
  stamps        version and date stamps agree across A4, Letter, Tablet and README
  tablet        a real screen edition: tablet page size, not A4 proportions, no print
                boxes, no print margins, and a working link wherever it says "page N"
  interaction   the spec declares fillable | annotate-only; README agrees; the PDFs
                carry form fields exactly when fillable
  rasters       every edition has a full, current page render in qa/pages/<edition>/
  critic        the latest critique round has no open BLOCKER/MAJOR (or each one is
                OWNER-ACCEPTED in BUILD-LOG.md), rendered every edition itself, and
                lists every page PNG under "## Pages opened"
  voice-sync    voice.md and banned.json agree
"""
import argparse
import datetime
import glob
import json
import os
import re
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lib import inventory, raster, shop  # noqa: E402
from lib.shop import norm  # noqa: E402

PT_PER_MM = 72.0 / 25.4
SIZES = {"A4": (210.0, 297.0), "Letter": (215.9, 279.4), "A5": (148.0, 210.0),
         "Tablet": (1620 / 96 * 25.4, 2160 / 96 * 25.4)}
MAIN_EDITIONS = ("A4", "Letter", "Tablet")
A4_ASPECT = 297.0 / 210.0
DEFAULT_TABLET_MARGIN_PCT = 8.0

TLDS = ("com|net|org|io|co|app|dev|shop|store|studio|me|info|biz|uk|us|ca|au|de|fr|eu|nz|ie|"
        "ai|xyz|link|page|site|online|gg|example|test|invalid|localhost")
RESERVED_SUFFIXES = (".example", ".test", ".invalid", ".localhost")
RESERVED_HOSTS = {"example.com", "example.net", "example.org", "localhost"}
# A plain tool agent, not a browser one: some sites (adobe.com) stall browser-looking
# agents from datacenter IPs but answer an honest link checker at once.
UA = {"User-Agent": "NorthingStudio-release-check/1.0 (link check)"}

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.I)
BARE_RE = re.compile(r"(?<![@\w./-])((?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:" + TLDS
                     + r"))(?![\w-])(/[^\s<>\"')\]]*)?", re.I)
SKU_RE = re.compile(r"(?<![A-Za-z])(?:PB|BN)-?\d{2,3}(?!\d)", re.I)
PLACEHOLDERS = [
    (re.compile(r"<[A-Z][A-Z0-9 ,.'’/-]{3,}[^<>]*>"), "an unfilled <PLACEHOLDER>"),
    (re.compile(r"\[(?:OWNER|TODO|TBD|PLACEHOLDER|INSERT|FILL)[^\]]*\]", re.I), "an unfilled [placeholder]"),
    (re.compile(r"\[Assumption\]", re.I), "an [Assumption] marker"),
    (re.compile(r"\bTODO\b|\bTBD\b|\bXXX\b|lorem ipsum", re.I), "a TODO/TBD marker"),
    (re.compile(r"\{[a-z_]{3,}\}"), "an unrendered {template} field"),
]
FORMAT_CLAIMS = {
    "A4": re.compile(r"\bA4\b"),
    "Letter": re.compile(r"\bUS Letter\b|\bLetter\b|8\.5\s*[x×]\s*11"),
    "A5": re.compile(r"\bA5\b"),
    "Tablet": re.compile(r"\btablet\b|\biPad\b|\bGoodNotes\b|\bNotability\b", re.I),
}
PAGES_CLAIM = re.compile(r"\b(\d{1,3})[\s-]*pages?\b", re.I)
PAGE_REF = re.compile(r"\b(?:pages?|p\.)\s*(\d{1,3}(?:\s*(?:,|and|&|or|to|-)\s*\d{1,3})*)(?!\d)", re.I)
STAMP_RE = re.compile(r"\b(?:v|version\s+)(\d+\.\d+)\b(?:\s*[·•|-]?\s*(\d{4}-\d{2})(?:-\d{2})?)?", re.I)


# ------------------------------------------------------------------ report
class Report:
    def __init__(self):
        self.checks = {}

    def _add(self, check, ok, msg):
        c = self.checks.setdefault(check, {"status": "PASS", "details": []})
        if not ok:
            c["status"] = "FAIL"
        c["details"].append(("ok    " if ok else "FAIL  ") + msg)

    def ok(self, check, msg):
        self._add(check, True, msg)

    def fail(self, check, msg):
        self._add(check, False, msg)

    @property
    def fails(self):
        return [f"{name}: {d[6:]}" for name, c in self.checks.items()
                for d in c["details"] if d.startswith("FAIL")]


# ------------------------------------------------------------------ product
def open_pdf(path):
    from pypdf import PdfReader
    r = PdfReader(path)
    if r.is_encrypted:
        r.decrypt("")
    return r


def classify(w_mm, h_mm):
    for name, (w, h) in SIZES.items():
        if abs(w - w_mm) <= 1.0 and abs(h - h_mm) <= 1.0:
            return name
    return None


def read(path):
    return open(path, encoding="utf-8", errors="replace").read()


def section(text, title):
    m = re.search(r"^##\s+%s\b.*?$(.*?)(?=^##\s|\Z)" % re.escape(title), text, re.M | re.S)
    return m.group(1) if m else None


class Product:
    def __init__(self, path, spec_path=None):
        self.dir = os.path.abspath(path)
        if not os.path.isdir(self.dir):
            sys.exit(f"no such product folder: {path}")
        self.pb_id = shop.product_id(self.dir)
        self.spec_path = os.path.abspath(spec_path) if spec_path else shop.find_spec(self.pb_id)
        self.spec = read(self.spec_path)
        _, self.name = shop.spec_identity(self.spec_path)
        self.dist = os.path.join(self.dir, "dist")
        self.pdfs = {}
        for f in sorted(glob.glob(os.path.join(glob.escape(self.dist), "*.pdf"))):
            r = open_pdf(f)
            mb = r.pages[0].mediabox
            w, h = float(mb.width) / PT_PER_MM, float(mb.height) / PT_PER_MM
            m = re.search(r"_(A4|Letter|Tablet|A5)\.pdf$", f)
            self.pdfs[os.path.basename(f)] = {
                "path": f, "edition": m.group(1) if m else None, "reader": r,
                "texts": [p.extract_text() or "" for p in r.pages], "size_mm": (w, h),
                "format": classify(w, h), "pages": len(r.pages)}

    def edition(self, name):
        for rec in self.pdfs.values():
            if rec["edition"] == name:
                return rec
        return None

    @property
    def readme(self):
        path = os.path.join(self.dist, "README.txt")
        return read(path) if os.path.exists(path) else None

    def licence_files(self):
        return sorted(glob.glob(os.path.join(glob.escape(self.dist), "licences", "*.txt"))
                      + glob.glob(os.path.join(glob.escape(self.dist), "licences", "*.md")))

    def corpus(self):
        """Every customer-facing text: (label, text)."""
        out = []
        for base, rec in self.pdfs.items():
            label = rec["edition"] or base
            out += [(f"{label} p{i}", t) for i, t in enumerate(rec["texts"], 1)]
        if self.readme is not None:
            out.append(("README.txt", self.readme))
        out += [(f"licences/{os.path.basename(p)}", read(p)) for p in self.licence_files()]
        return out

    def interaction(self):
        m = re.search(r"^\s*(?:[-*]\s*)?\**Interaction:?\**:?\s*`?(fillable|annotate-only)`?", self.spec,
                      re.M | re.I)
        return m.group(1).lower() if m else None


# ------------------------------------------------------------------ urls
_url_cache = {}


def host_of(url):
    return (urlparse(url if "://" in url else "https://" + url).hostname or "").lower()


def reserved(host):
    return host in RESERVED_HOSTS or host.endswith(RESERVED_SUFFIXES)


def check_url(url):
    if url in _url_cache:
        return _url_cache[url]
    host = host_of(url)
    if reserved(host):
        result = (False, "a reserved example domain - a placeholder, not a real address")
    elif re.search(r"(^|\.)etsy\.(com|me)$", host):
        result = check_etsy(url)
    else:
        result = fetch(url if "://" in url else "https://" + url)
    _url_cache[url] = result
    return result


def fetch(url):
    import requests
    last = "no response"
    for attempt in range(3):
        try:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=15, headers=UA)
            except requests.RequestException:
                resp = None                 # some servers stall on HEAD but answer GET
            if resp is None or resp.status_code in (400, 403, 405) or resp.status_code >= 500:
                resp = requests.get(url, allow_redirects=True, timeout=25, headers=UA, stream=True)
                resp.close()
            if resp.status_code < 400:
                return True, f"HTTP {resp.status_code}"
            last = f"HTTP {resp.status_code}"
            if resp.status_code in (404, 410):
                break
        except requests.RequestException as e:
            last = f"{type(e).__name__}: {str(e)[:140]}"
        if attempt < 2:
            time.sleep(2 ** attempt)
    return False, last


def check_etsy(url):
    key = os.environ.get("ETSY_API_KEY")
    if not key:
        return False, ("etsy.com blocks this server, so the link cannot be verified by fetching it; "
                       "set ETSY_API_KEY to verify it through the Etsy API (MULTI_AGENT_PLAN.md, M4)")
    m = re.search(r"/listing/(\d+)", url)
    if not m:
        return False, "only Etsy listing URLs (/listing/<id>) can be verified"
    import requests
    try:
        resp = requests.get(f"https://openapi.etsy.com/v3/application/listings/{m.group(1)}",
                            headers={"x-api-key": key}, timeout=20)
    except requests.RequestException as e:
        return False, f"Etsy API unreachable: {e}"
    if resp.status_code == 200 and resp.json().get("state") == "active":
        return True, "active Etsy listing (API)"
    return False, f"Etsy API: HTTP {resp.status_code}, state {resp.json().get('state') if resp.ok else '?'}"


def check_email(domain):
    domain = domain.lower()
    if reserved(domain):
        return False, "a reserved example domain - a placeholder, not a real address"
    try:
        socket.getaddrinfo(domain, None)
        return True, "domain resolves"
    except socket.gaierror as e:
        return False, f"domain does not resolve ({e})"


def extract_links(texts):
    """[(label, kind, value)] for URLs, bare domains and emails found in texts."""
    out = []
    for label, text in texts:
        rest = text
        for m in URL_RE.finditer(text):
            out.append((label, "url", m.group(0).rstrip(".,;:")))
        rest = URL_RE.sub(" ", rest)
        for m in EMAIL_RE.finditer(rest):
            out.append((label, "email", m.group(0)))
        rest = EMAIL_RE.sub(" ", rest)
        for m in BARE_RE.finditer(rest):
            out.append((label, "domain", m.group(0).rstrip(".,;:")))
    return out


def annotation_uris(product):
    out = []
    for base, rec in product.pdfs.items():
        for i, page in enumerate(rec["reader"].pages, 1):
            for a in page.get("/Annots") or []:
                try:
                    act = a.get_object().get("/A")
                    uri = act.get_object().get("/URI") if act else None
                except Exception:                           # noqa: BLE001
                    uri = None
                if uri:
                    out.append((f"{rec['edition'] or base} p{i} (link)", "url", str(uri)))
    return out


def run_link_checks(rep, links):
    seen = set()
    if not links:
        rep.ok("urls", "no URLs, domains or emails in customer text")
    for label, kind, value in links:
        if (kind, value) in seen:
            continue
        seen.add((kind, value))
        if kind == "email":
            ok, why = check_email(value.split("@", 1)[1])
        else:
            ok, why = check_url(value)
        (rep.ok if ok else rep.fail)("urls", f"{label}: {value} - {why}")


def normal_url(url):
    u = url.lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def run_catalogue_checks(rep, product, texts, links):
    rows = shop.load_catalogue()
    facts = shop.shop_facts()
    live_names = {norm(r.get("name", "")) for r in rows if r.get("name")}
    live_urls = [normal_url(r["url"]) for r in rows if r.get("url")]
    storefronts = {normal_url(facts[k]) for k in ("gumroad", "etsy_shop") if facts.get(k)}
    own = norm(product.name)
    named = False
    for name, pid in sorted(shop.known_products().items()):
        n = norm(name)
        if pid == product.pb_id or n == own:
            continue
        hits = [label for label, text in texts if n in norm(text)]
        if not hits:
            continue
        named = True
        if n in live_names:
            rep.ok("catalogue", f"names “{name}”, which is live ({', '.join(hits[:3])})")
        else:
            rep.fail("catalogue", f"{', '.join(hits[:4])}: names “{name}” ({pid}), which is not live "
                                  f"in catalogue.md - a customer cannot buy it")
    for label, kind, value in links:
        if kind == "email":
            continue
        host = host_of(value)
        if not (host.endswith("gumroad.com") or re.search(r"(^|\.)etsy\.(com|me)$", host)
                or "northingstudio" in host):
            continue
        u = normal_url(value)
        if u in storefronts:
            rep.ok("catalogue", f"{label}: {value} is the shop storefront")
        elif any(u == live or u.startswith(live + "/") for live in live_urls):
            rep.ok("catalogue", f"{label}: {value} is a live catalogue URL")
        else:
            rep.fail("catalogue", f"{label}: links to {value}, which is not a live URL in catalogue.md")
    if not named and not rep.checks.get("catalogue"):
        rep.ok("catalogue", "no sibling products or shop URLs referenced")


def run_placeholder_checks(rep, texts):
    found = False
    for label, text in texts:
        for rx, what in PLACEHOLDERS:
            for m in rx.finditer(text):
                found = True
                rep.fail("placeholders", f"{label}: {what} - “{m.group(0)[:80]}”")
    if not found:
        rep.ok("placeholders", "no placeholders in customer text")


def run_sku_text_checks(rep, texts):
    found = False
    for label, text in texts:
        for m in SKU_RE.finditer(text):
            found = True
            rep.fail("sku", f"{label}: internal ID “{m.group(0)}” in customer text")
    return found


def sku_filename_checks(rep, folders):
    found = False
    for folder in folders:
        for base, _, files in os.walk(folder):
            for name in files:
                if SKU_RE.search(name):
                    found = True
                    rep.fail("sku", f"customer filename carries an internal ID: "
                                    f"{os.path.relpath(os.path.join(base, name), ROOT)}")
    return found


# ------------------------------------------------------------------ default-mode checks
def check_licence(rep, product):
    path = os.path.join(product.dist, "licences", "LICENCE.txt")
    if not os.path.exists(path):
        rep.fail("licence", "dist/licences/LICENCE.txt is missing - run scripts/make_licence.py --tier personal")
    else:
        rep.ok("licence", "dist/licences/LICENCE.txt exists")
    if product.readme is None:
        rep.fail("licence", "dist/README.txt is missing")
    elif "LICENCE.txt" not in product.readme:
        rep.fail("licence", "README.txt does not point the buyer to licences/LICENCE.txt")


def check_formats(rep, product):
    shipped = {}
    for base, rec in product.pdfs.items():
        if rec["format"]:
            shipped.setdefault(rec["format"], []).append(base)
        else:
            rep.fail("formats", f"{base}: page size {rec['size_mm'][0]:.1f}x{rec['size_mm'][1]:.1f} mm "
                                f"is not a known format")
    for e in MAIN_EDITIONS:
        rec = product.edition(e)
        if not rec:
            rep.fail("formats", f"no {e} edition in dist/ (expected *_{e}.pdf)")
        elif rec["format"] != e:
            rep.fail("formats", f"the {e} file is {rec['format'] or 'an unknown size'}, not {e}")
        else:
            rep.ok("formats", f"{e} edition ships ({rec['pages']} pages)")
    extra_counts = {rec["pages"] for rec in product.pdfs.values() if rec["edition"] is None}

    sources = [(f"{rec['edition'] or base} cover", rec["texts"][0] if rec["texts"] else "", rec)
               for base, rec in product.pdfs.items()]
    if product.readme is not None:
        sources.append(("README.txt", product.readme, None))
    for label, text, rec in sources:
        for fmt, rx in FORMAT_CLAIMS.items():
            if rx.search(text):
                if fmt in shipped:
                    rep.ok("formats", f"{label} claims {fmt}; shipped as {', '.join(shipped[fmt])}")
                else:
                    rep.fail("formats", f"{label} claims {fmt}, but no {fmt}-sized file is in the package")
        for m in PAGES_CLAIM.finditer(text):
            n = int(m.group(1))
            if rec is not None:
                targets = [(rec["edition"] or os.path.basename(rec["path"]), rec["pages"])]
            else:
                targets = [(e, product.edition(e)["pages"]) for e in MAIN_EDITIONS if product.edition(e)]
            if n in extra_counts:
                continue
            for ed, pages in targets:
                if n == pages:
                    rep.ok("formats", f"{label} claims {n} pages; {ed} has {pages}")
                else:
                    rep.fail("formats", f"{label} claims “{m.group(0)}”; the {ed} edition has {pages} pages")


def check_sku(rep, product, texts):
    folders = [product.dist] + [p for p in (os.path.join(product.dir, "dist-practitioner"),) if os.path.isdir(p)]
    found = sku_filename_checks(rep, folders)
    for base, rec in product.pdfs.items():
        md = rec["reader"].metadata or {}
        for key in ("/Title", "/Subject", "/Keywords", "/Author"):
            if md.get(key) and SKU_RE.search(str(md[key])):
                found = True
                rep.fail("sku", f"{base}: PDF {key[1:]} metadata carries an internal ID - “{md[key]}”")
    found = run_sku_text_checks(rep, texts) or found
    if not found:
        rep.ok("sku", "no internal IDs in filenames, metadata or customer text")


def crossref_rows(sec):
    rows = []
    lines = [l.strip() for l in sec.splitlines() if l.strip().startswith("|")]
    for line in lines[1:]:
        if re.fullmatch(r"\|[\s:|-]+\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        rows.append({"ref": cells[0].strip("`\"“”* "),
                     "targets": [int(n) for n in re.findall(r"\d{1,3}", cells[1])],
                     "headings": [h.strip("`\"“”* ") for h in cells[2].split(";")],
                     "editions": ([e.strip() for e in cells[3].split(",") if e.strip()]
                                  if len(cells) > 3 and cells[3].strip().lower() not in ("", "all")
                                  else list(MAIN_EDITIONS))})
    return rows


def check_crossrefs(rep, product):
    sec = section(product.spec, "Cross-references")
    if sec is None:
        rep.fail("crossrefs", "the spec has no '## Cross-references' section - it is required "
                              "(write 'None.' under it if the product has no page references)")
        return
    rows = crossref_rows(sec)
    for e in MAIN_EDITIONS:
        rec = product.edition(e)
        if not rec:
            continue
        texts = [norm(t) for t in rec["texts"]]
        rows_e = [r for r in rows if e in r["editions"]]   # tablet-only navigation stays tablet-only
        mentions = 0
        for pno, t in enumerate(texts, 1):
            for m in PAGE_REF.finditer(t):
                for n in (int(x) for x in re.findall(r"\d{1,3}", m.group(1))):
                    mentions += 1
                    if not any(norm(r["ref"]) in t and n in r["targets"] for r in rows_e):
                        rep.fail("crossrefs", f"{e} p{pno}: says “{m.group(0)}”, but the spec's "
                                              f"Cross-references table declares no reference to page {n} there")
        for r in rows_e:
            found = [i for i, t in enumerate(texts, 1) if norm(r["ref"]) in t]
            if not found:
                rep.fail("crossrefs", f"{e}: the declared reference “{r['ref']}” is on no page")
                continue
            for k, n in enumerate(r["targets"]):
                heading = r["headings"][min(k, len(r["headings"]) - 1)]
                if not 1 <= n <= len(texts):
                    rep.fail("crossrefs", f"{e}: “{r['ref']}” points to page {n}; the edition has {len(texts)} pages")
                elif norm(heading) not in texts[n - 1]:
                    rep.fail("crossrefs", f"{e}: “{r['ref']}” (p{found[0]}) points to page {n}, but page {n} "
                                          f"does not carry “{heading}” - the layout moved")
                else:
                    rep.ok("crossrefs", f"{e}: “{r['ref']}” -> p{n} “{heading}”")
        if not rows_e and not mentions:
            rep.ok("crossrefs", f"{e}: no page references, none declared")


def check_stamps(rep, product):
    sources = []
    for e in MAIN_EDITIONS:
        rec = product.edition(e)
        if rec:
            sources.append((e, "\n".join(rec["texts"])))
    if product.readme is not None:
        sources.append(("README.txt", product.readme))
    found = {}
    for label, text in sources:
        versions, dates = set(), set()
        for m in STAMP_RE.finditer(text):
            versions.add(m.group(1))
            if m.group(2):
                dates.add(m.group(2))
        found[label] = (versions, dates)
    all_versions = set().union(*(v for v, _ in found.values())) if found else set()
    all_dates = set().union(*(d for _, d in found.values())) if found else set()
    for label, (versions, dates) in found.items():
        if not versions:
            rep.fail("stamps", f"{label} carries no version stamp; others carry {', '.join(sorted(all_versions)) or 'none'}")
        if all_dates and not dates:
            rep.fail("stamps", f"{label} carries no date stamp; others carry {', '.join(sorted(all_dates))}")
    if len(all_versions) > 1:
        rep.fail("stamps", "version stamps disagree: " + "; ".join(
            f"{label} {', '.join(sorted(v)) or '-'}" for label, (v, _) in found.items()))
    if len(all_dates) > 1:
        rep.fail("stamps", "date stamps disagree: " + "; ".join(
            f"{label} {', '.join(sorted(d)) or '-'}" for label, (_, d) in found.items()))
    if "stamps" not in rep.checks:
        rep.ok("stamps", f"v{', '.join(sorted(all_versions))} {', '.join(sorted(all_dates))} on every edition and README")


def link_targets(reader, page):
    """1-based page numbers this page's internal links land on."""
    from pypdf.generic import ArrayObject
    out = []
    try:
        named = reader.named_destinations
    except Exception:                                       # noqa: BLE001
        named = {}
    for annot in page.get("/Annots") or []:
        a = annot.get_object()
        if a.get("/Subtype") != "/Link":
            continue
        dest = None
        act = a.get("/A")
        if act is not None:
            act = act.get_object()
            if act.get("/S") == "/GoTo":
                dest = act.get("/D")
        if dest is None and "/Dest" in a:
            dest = a["/Dest"]
        if dest is None:
            continue
        dest = dest.get_object() if hasattr(dest, "get_object") else dest
        if isinstance(dest, ArrayObject) and dest:
            ref = dest[0]
            for i, p in enumerate(reader.pages, 1):
                if p.indirect_reference is not None and getattr(ref, "idnum", None) == p.indirect_reference.idnum:
                    out.append(i)
                    break
        else:
            d = named.get(str(dest)) or named.get("/" + str(dest).lstrip("/"))
            if d is not None:
                try:
                    out.append(reader.get_destination_page_number(d) + 1)
                except Exception:                           # noqa: BLE001
                    pass
    return out


def side_margins(pdf_path, page_no, h_mm):
    px = max(320, min(1400, int(round(h_mm * 320 / 297.0))))
    w, h, rows = raster.page_rgb(pdf_path, page_no, px)
    lum = [[0.299 * r + 0.587 * g + 0.114 * b for (r, g, b) in row] for row in rows]
    flat = sorted(v for row in lum for v in row)
    paper = max(flat[int(len(flat) * 0.97)], 1.0)
    counts = [0] * w
    for row in lum:
        for x, v in enumerate(row):
            if (paper - v) / paper > 0.02:
                counts[x] += 1
    cols = [x for x in range(w) if counts[x] > h * 0.004]
    if not cols:
        return None
    return 100.0 * cols[0] / w, 100.0 * (w - 1 - cols[-1]) / w


def check_tablet(rep, product):
    rec = product.edition("Tablet")
    if not rec:
        rep.fail("tablet", "no Tablet edition to check")
        return
    a4 = product.edition("A4")
    m = re.search(r"Tablet margin max:?\**:?\s*(\d+(?:\.\d+)?)\s*%", product.spec, re.I)
    limit = float(m.group(1)) if m else DEFAULT_TABLET_MARGIN_PCT
    want = SIZES["Tablet"]
    r = rec["reader"]
    for i, page in enumerate(r.pages, 1):
        mb = page.mediabox
        w, h = float(mb.width) / PT_PER_MM, float(mb.height) / PT_PER_MM
        if abs(w - want[0]) > 0.1 or abs(h - want[1]) > 0.1:
            rep.fail("tablet", f"p{i}: {w:.1f}x{h:.1f} mm is not the tablet page ({want[0]:.1f}x{want[1]:.1f} mm)")
        if abs(h / w - A4_ASPECT) <= 0.02:
            rep.fail("tablet", f"p{i}: A4 proportions (1:{h / w:.3f}) - an A4 re-export, not a screen edition")
        if a4 and abs(w - a4["size_mm"][0]) <= 1 and abs(h - a4["size_mm"][1]) <= 1:
            rep.fail("tablet", f"p{i}: dimensionally identical to the A4 edition")
        for box_name in ("cropbox", "trimbox", "bleedbox"):
            box = getattr(page, box_name)
            if any(abs(float(x) - float(y)) > 0.05 for x, y in zip(box, mb)):
                rep.fail("tablet", f"p{i}: {box_name} differs from the media box - print trim/bleed boxes "
                                   f"do not belong in a screen edition")
        margins = side_margins(rec["path"], i, h)
        if margins:
            left, right = margins
            if max(left, right) > limit:
                rep.fail("tablet", f"p{i}: side margins {left:.1f}% / {right:.1f}% of the page width - print "
                                   f"margins, over the {limit:g}% screen limit")
            else:
                rep.ok("tablet", f"p{i}: side margins {left:.1f}% / {right:.1f}% (limit {limit:g}%)")
        targets = link_targets(r, page)
        text = norm(rec["texts"][i - 1])
        for mm in PAGE_REF.finditer(text):
            for n in (int(x) for x in re.findall(r"\d{1,3}", mm.group(1))):
                if n == i:
                    continue
                if n in targets:
                    rep.ok("tablet", f"p{i}: “{mm.group(0)}” has a working link to page {n}")
                else:
                    rep.fail("tablet", f"p{i}: says “{mm.group(0)}” but no link on the page lands on page {n}")
    if "tablet" not in rep.checks:
        rep.ok("tablet", f"{rec['pages']} tablet pages checked")


def check_interaction(rep, product):
    declared = product.interaction()
    if not declared:
        rep.fail("interaction", "the spec does not declare '**Interaction:** fillable | annotate-only' "
                                "- it is a required field")
        return
    rep.ok("interaction", f"spec declares {declared}")
    readme = product.readme or ""
    if declared == "fillable":
        if not re.search(r"\bfillable\b", readme, re.I):
            rep.fail("interaction", "README.txt does not say the product is fillable")
    else:
        if not re.search(r"\bannotate[- ]only\b", readme, re.I):
            rep.fail("interaction", "README.txt does not say the product is annotate-only")
        for m in re.finditer(r"\bfillable\b", readme, re.I):
            if not re.search(r"\b(not|no|isn't|n't|never)\b", readme[max(0, m.start() - 30):m.start()], re.I):
                rep.fail("interaction", "README.txt calls an annotate-only product fillable")
    for base, rec in product.pdfs.items():
        try:
            fields = rec["reader"].get_fields() or {}
        except Exception:                                   # noqa: BLE001
            fields = {}
        if declared == "annotate-only" and fields:
            rep.fail("interaction", f"{base}: {len(fields)} form field(s) in an annotate-only product")
        if declared == "fillable" and rec["edition"] == "Tablet" and not fields:
            rep.fail("interaction", f"{base}: declared fillable but the tablet edition has no form fields")


def load_manifest(folder, stem):
    path = os.path.join(folder, f"{stem}.manifest.json")
    return json.load(open(path)) if os.path.exists(path) else None


def manifest_problems(man, rec, sha):
    problems = []
    if man.get("partial"):
        problems.append("the render is partial (--pages)")
    if man.get("pdf_pages") != rec["pages"] or len(man.get("images", [])) != rec["pages"]:
        problems.append(f"{len(man.get('images', []))} PNG(s) for {rec['pages']} pages")
    if sha and man.get("pdf_sha256") != sha:
        problems.append("the PNGs were rendered from a different PDF than the one in dist/")
    return problems


def check_rasters(rep, product):
    for e in MAIN_EDITIONS:
        rec = product.edition(e)
        if not rec:
            continue
        stem = os.path.splitext(os.path.basename(rec["path"]))[0]
        folder = os.path.join(product.dir, "qa", "pages", e.lower())
        man = load_manifest(folder, stem)
        sha = None if rec["reader"].is_encrypted else inventory.sha256(rec["path"])
        if not man:
            rep.fail("rasters", f"{e}: no page render in qa/pages/{e.lower()}/ - run render_pages.py")
            continue
        problems = manifest_problems(man, rec, sha)
        for p in problems:
            rep.fail("rasters", f"{e}: {p}")
        if not problems:
            rep.ok("rasters", f"{e}: {rec['pages']} page PNGs match the shipped PDF")


def check_critic(rep, product):
    rounds = sorted(glob.glob(os.path.join(glob.escape(product.dir), "critique", "round-*.md")),
                    key=lambda p: int(re.search(r"round-(\d+)", p).group(1)))
    if not rounds:
        rep.fail("critic", "no critique/round-N.md - the critic has not reviewed this build")
        return
    latest = rounds[-1]
    name = os.path.basename(latest)
    text = read(latest)
    m = re.search(r"\*\*Verdict:\*\*\s*\**\s*(SHIP|FIX|REBUILD)\**.*?\*\*Blockers:\*\*\s*(\d+).*?"
                  r"\*\*Major:\*\*\s*(\d+)", text[:3000], re.S)
    if not m:
        rep.fail("critic", f"{name} has no '**Verdict:** … · **Blockers:** n · **Major:** n' header")
    else:
        verdict, blockers, majors = m.group(1), int(m.group(2)), int(m.group(3))
        if blockers + majors == 0:
            rep.ok("critic", f"{name}: verdict {verdict}, no open BLOCKER or MAJOR")
        else:
            log_path = os.path.join(product.dir, "BUILD-LOG.md")
            log = read(log_path) if os.path.exists(log_path) else ""
            accepted = [norm(x) for x in re.findall(r"^\s*[-*]?\s*OWNER-ACCEPTED:\s*(.+?)\s*$", log, re.M)]
            open_findings = re.findall(r"^###\s*\[(BLOCKER|MAJOR)\]\s*(.+?)\s*$", text, re.M)
            unaccepted = [f"[{sev}] {title}" for sev, title in open_findings
                          if not any(acc and acc in norm(title) for acc in accepted)]
            if unaccepted or len(accepted) < blockers + majors:
                rep.fail("critic", f"{name}: {blockers} BLOCKER / {majors} MAJOR still open and not "
                                   f"OWNER-ACCEPTED in BUILD-LOG.md" +
                                   (": " + "; ".join(unaccepted[:6]) if unaccepted else ""))
            else:
                rep.ok("critic", f"{name}: {blockers + majors} open finding(s), each OWNER-ACCEPTED")
    opened_sec = section(text, "Pages opened")
    if opened_sec is None:
        rep.fail("critic", f"{name} has no '## Pages opened' table - no proof the critic looked at every page")
        opened = set()
    else:
        opened = set(re.findall(r"[\w.+-]+\.png", opened_sec))
    for e in MAIN_EDITIONS:
        rec = product.edition(e)
        if not rec:
            continue
        stem = os.path.splitext(os.path.basename(rec["path"]))[0]
        folder = os.path.join(product.dir, "qa", "critic-pages", e.lower())
        man = load_manifest(folder, stem)
        if not man:
            rep.fail("critic", f"{e}: the critic did not render this edition (qa/critic-pages/{e.lower()}/)")
            continue
        sha = None if rec["reader"].is_encrypted else inventory.sha256(rec["path"])
        for p in manifest_problems(man, rec, sha):
            rep.fail("critic", f"{e}: {p}")
        missing = [img["png"] for img in man.get("images", []) if img["png"] not in opened]
        if missing:
            rep.fail("critic", f"{e}: {len(missing)} page PNG(s) not listed under Pages opened - "
                               f"{', '.join(missing[:5])}")
        elif opened_sec is not None:
            rep.ok("critic", f"{e}: every page PNG is listed as opened")


def check_voice_sync(rep):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_voice_sync.py")],
                       capture_output=True, text=True)
    for line in (r.stdout + r.stderr).strip().splitlines():
        (rep.ok if r.returncode == 0 else rep.fail)("voice-sync", line)


# ------------------------------------------------------------------ listing mode
def listing_texts(listing):
    etsy, gum = listing.get("etsy", {}), listing.get("gumroad", {})
    out = [("listing etsy.title", etsy.get("title", "")),
           ("listing etsy.tags", " | ".join(etsy.get("tags", []))),
           ("listing etsy.description", etsy.get("description", "")),
           ("listing gumroad.name", gum.get("name", "")),
           ("listing gumroad.summary", gum.get("summary", "")),
           ("listing gumroad.description", gum.get("description", ""))]
    for i, tier in enumerate(gum.get("tiers", []) or [], 1):
        out.append((f"listing gumroad.tiers[{i}]", json.dumps(tier, ensure_ascii=False)))
    return [(label, text) for label, text in out if text]


def check_listing_mode(rep, product):
    ldir = os.path.join(product.dir, "Listing")
    lpath = os.path.join(ldir, "listing.json")
    if not os.path.exists(lpath):
        rep.fail("listing", "Listing/listing.json is missing")
        return
    listing = json.load(open(lpath, encoding="utf-8"))
    texts = listing_texts(listing)

    pins_path = os.path.join(product.dir, "Pinterest", "pins.json")
    pins = json.load(open(pins_path, encoding="utf-8")).get("pins", []) if os.path.exists(pins_path) else None
    if pins is None:
        rep.fail("pins", "Pinterest/pins.json is missing - Pinterest is a required output")
        pins = []
    for i, pin in enumerate(pins, 1):
        texts.append((f"pin {i} title", pin.get("title", "")))
        texts.append((f"pin {i} description", pin.get("description", "")))
        texts.append((f"pin {i} alt", pin.get("alt", "")))

    links = extract_links(texts)
    own_live = [r for r in shop.load_catalogue() if r.get("id") == product.pb_id]
    for i, pin in enumerate(pins, 1):
        dest = (pin.get("destination") or "").strip()
        if dest == "pending-own-listing":
            if own_live:
                rep.fail("pins", f"pin {i}: destination is still pending, but the listing is live at {own_live[0]['url']}")
            else:
                rep.ok("pins", f"pin {i}: destination pending until this listing is live - set it and re-run")
        elif dest:
            links.append((f"pin {i} destination", "url", dest))
        else:
            rep.fail("pins", f"pin {i}: no destination")

    run_link_checks(rep, links)
    run_placeholder_checks(rep, texts)
    run_catalogue_checks(rep, product, texts, links)

    claims = listing.get("claims", {})
    for fmt in claims.get("formats", []):
        rec = product.edition(fmt) if fmt in MAIN_EDITIONS else None
        sized = [b for b, r in product.pdfs.items() if r["format"] == fmt]
        if not sized:
            rep.fail("formats", f"listing claims {fmt}; no {fmt}-sized file is in the package")
        elif claims.get("pages") and rec and rec["pages"] != claims["pages"]:
            rep.fail("formats", f"listing claims {claims['pages']} pages; the {fmt} edition has {rec['pages']}")
        else:
            rep.ok("formats", f"listing claims {fmt}; shipped as {', '.join(sized)}")
    for label, text in texts:
        for fmt, rx in FORMAT_CLAIMS.items():
            if rx.search(text) and not any(r["format"] == fmt for r in product.pdfs.values()):
                rep.fail("formats", f"{label} mentions {fmt}, but no {fmt}-sized file is in the package")

    declared = product.interaction()
    if not declared:
        rep.fail("interaction", "the spec does not declare Interaction")
    elif claims.get("interaction") != declared:
        rep.fail("interaction", f"listing claims.interaction is {claims.get('interaction')!r}; the spec declares {declared}")
    elif not any(re.search(r"\bfillable\b" if declared == "fillable" else r"\bannotate[- ]only\b", t, re.I)
                 for label, t in texts if "description" in label):
        rep.fail("interaction", f"no listing description tells the buyer the product is {declared}")
    else:
        rep.ok("interaction", f"listing declares {declared}, matching the spec")

    folders = [os.path.join(ldir, "images"), os.path.join(product.dir, "Pinterest")]
    found = sku_filename_checks(rep, [f for f in folders if os.path.isdir(f)])
    found = run_sku_text_checks(rep, texts) or found
    if not found:
        rep.ok("sku", "no internal IDs in listing or pin filenames or copy")

    brief = os.path.join(ldir, "slot-brief.md")
    approval = os.path.join(ldir, "slot-brief.APPROVED")
    if not os.path.exists(brief):
        rep.fail("slot-brief", "Listing/slot-brief.md is missing")
    elif not os.path.exists(approval):
        rep.fail("slot-brief", "the owner has not approved the slot brief (Listing/slot-brief.APPROVED)")
    else:
        m = re.search(r"sha256:\s*([0-9a-f]{64})", read(approval))
        if not m or m.group(1) != inventory.sha256(brief):
            rep.fail("slot-brief", "slot-brief.md changed after the owner approved it")
        else:
            rep.ok("slot-brief", "approved brief unchanged")

    images = [f for f in sorted(glob.glob(os.path.join(glob.escape(ldir), "images", "*")))
              if re.match(r"\d{2}-", os.path.basename(f)) and not re.search(r"-220\.\w+$", f)]
    if not 8 <= len(images) <= 10:
        rep.fail("listing", f"{len(images)} listing images; 8 to 10 are required")
    else:
        rep.ok("listing", f"{len(images)} listing images")


# ------------------------------------------------------------------ signoff mode
REQUIRED_OWNER_CHECKS = [("print it on paper", r"\bprint"), ("write on it with a pen", r"\b(write|pen)\b"),
                         ("test the tablet PDF in GoodNotes", r"goodnotes"),
                         ("test the tablet PDF in Notability", r"notability")]


def check_signoff(rep, product, require_drive_links):
    path = os.path.join(product.dir, "SIGNOFF.md")
    if not os.path.exists(path):
        rep.fail("signoff", "SIGNOFF.md is missing")
        return
    text = read(path)
    sec = section(text, "Owner checks")
    if sec is None:
        rep.fail("signoff", "SIGNOFF.md has no '## Owner checks' section")
    else:
        boxes = re.findall(r"^\s*[-*]\s*\[([ xX])\]\s*(.+?)\s*$", sec, re.M)
        for label, pat in REQUIRED_OWNER_CHECKS:
            hits = [b for b in boxes if re.search(pat, b[1], re.I)]
            if not hits:
                rep.fail("signoff", f"Owner checks does not list: {label}")
        ticked = [b[1] for b in boxes if b[0] in "xX"]
        for t in ticked:
            rep.fail("signoff", f"an owner check is ticked in SIGNOFF.md - no agent may tick these: “{t}”")
        if boxes and not ticked:
            rep.ok("signoff", f"{len(boxes)} owner check(s) listed, none ticked")
    if require_drive_links:
        headings = re.findall(r"^##\s+(.+?)\s*$", text, re.M)
        drive = section(text, "Drive links")
        if not headings or not headings[-1].lower().startswith("drive links"):
            rep.fail("signoff", "SIGNOFF.md does not end with a '## Drive links' section")
        elif not drive or "https://drive.google.com/" not in drive:
            rep.fail("signoff", "the Drive links section has no drive.google.com links")
        else:
            rep.ok("signoff", f"ends with {drive.count('https://drive.google.com/')} Drive link(s)")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("product", help='product folder, e.g. "Products/PB-022 The 10-Minute Life Audit"')
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--listing", action="store_true", help="check the listing copy, images and pins")
    mode.add_argument("--signoff", action="store_true", help="check SIGNOFF.md")
    ap.add_argument("--require-drive-links", action="store_true",
                    help="with --signoff: SIGNOFF.md must end with the Drive links")
    ap.add_argument("--spec", help="build spec to check against (default: Product Plans/specs/<PB-ID> *.md)")
    ap.add_argument("--json", help="default: qa/release-check[-listing|-signoff].json in the product")
    ap.add_argument("--verbose", action="store_true", help="also print passing details")
    a = ap.parse_args()

    product = Product(a.product, a.spec)
    rep = Report()
    mode_name = "listing" if a.listing else "signoff" if a.signoff else "release"

    if a.signoff:
        check_signoff(rep, product, a.require_drive_links)
    elif a.listing:
        check_listing_mode(rep, product)
    else:
        texts = product.corpus()
        links = extract_links(texts) + annotation_uris(product)
        run_link_checks(rep, links)
        run_placeholder_checks(rep, texts)
        check_licence(rep, product)
        run_catalogue_checks(rep, product, texts, links)
        check_formats(rep, product)
        check_sku(rep, product, texts)
        check_crossrefs(rep, product)
        check_stamps(rep, product)
        check_tablet(rep, product)
        check_interaction(rep, product)
        check_rasters(rep, product)
        check_critic(rep, product)
        check_voice_sync(rep)

    passed = not rep.fails
    report = {"product": os.path.relpath(product.dir, ROOT), "pb_id": product.pb_id, "name": product.name,
              "mode": mode_name, "checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "pass": passed, "checks": rep.checks, "fails": rep.fails}
    if mode_name == "release":
        report["dist_inventory"] = inventory.inventory(product.dist)
    suffix = "" if mode_name == "release" else f"-{mode_name}"
    out = a.json or os.path.join(product.dir, "qa", f"release-check{suffix}.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(report, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"{product.pb_id} {product.name} - release check ({mode_name})")
    for name, c in rep.checks.items():
        print(f"  {c['status']:<4}  {name}")
        for d in c["details"]:
            if d.startswith("FAIL") or a.verbose:
                print(f"          {d}")
    print(f"\n  wrote {os.path.relpath(out, ROOT)}")
    print("\nPASS - release gate met." if passed else f"\nFAIL - {len(rep.fails)} problem(s). Nothing uploads until this passes.")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
