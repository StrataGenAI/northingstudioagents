#!/usr/bin/env python3
"""Validate a listing before it goes live — limits, required sections, and claims.

The listing is where a product is most tempting to exaggerate: one more page in
the count, a format we did not actually ship, a proof number nobody earned. So
the claims in `listing.json` are checked against the REAL deliverables in dist/,
and the platform limits are counted rather than estimated.

    check_listing.py "Products/PB-006 The One-Page Year/Listing/listing.json" \
        --dist "Products/PB-006 The One-Page Year/dist" --json qa/listing.json

Exit code 1 if anything fails.
"""
import argparse
import glob
import json
import os
import re
import sys

ETSY_TITLE_MAX = 140
ETSY_TAGS = 13
ETSY_TAG_MAX = 20

# The 9-part description structure the research found converts. Each entry is a
# label plus the patterns that count as evidence the section exists.
REQUIRED_SECTIONS = [
    ("what it is",      [r"what (it|this) is", r"^#+ .*what", r"one[- ]line"]),
    ("who it's for",    [r"who (it'?s|this is) for", r"who it is for", r"not for"]),
    ("what's inside",   [r"what'?s (inside|included)", r"what you get", r"includes?:"]),
    ("how it works",    [r"how (it|this) works", r"three steps", r"how to use"]),
    ("formats",         [r"format", r"a4", r"letter", r"pdf"]),
    ("compatibility",   [r"compatib", r"goodnotes", r"notability", r"works with"]),
    ("faq",             [r"\bfaq\b", r"questions"]),
    ("refunds/policy",  [r"refund", r"guarantee", r"digital (download|product).*no"]),
    ("next step",       [r"next step", r"bundle", r"if you want more"]),
]

# Claims nobody has earned yet. The brand rule is no proof numbers until real.
PROOF_CLAIM = re.compile(
    r"\b\d{2,}[\d,]*\s*(\+\s*)?(sales|sold|customers|buyers|downloads|reviews|ratings|"
    r"happy|students)\b|\bbest[- ]?sell(er|ing)\b|\b#1\b|\btop[- ]rated\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def load_banned():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", "product-qa", "assets", "banned.json")
    try:
        return json.load(open(p))["banned_terms"]
    except Exception:                                   # noqa: BLE001
        return []


def pdf_facts(dist):
    """What we ACTUALLY shipped: page counts and trim sizes per file."""
    from pypdf import PdfReader
    PT = 72 / 25.4
    out = {}
    for f in sorted(glob.glob(os.path.join(dist, "*.pdf"))):
        try:
            r = PdfReader(f)
            if r.is_encrypted:
                r.decrypt("")
            mb = r.pages[0].mediabox
            w, h = round(float(mb.width) / PT), round(float(mb.height) / PT)
            out[os.path.basename(f)] = {"pages": len(r.pages), "mm": (w, h)}
        except Exception as e:                          # noqa: BLE001
            out[os.path.basename(f)] = {"error": str(e)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("listing")
    ap.add_argument("--dist", help="the product's dist/ folder, to check claims against")
    ap.add_argument("--json")
    a = ap.parse_args()

    L = json.load(open(a.listing, encoding="utf-8"))
    fails, warns = [], []
    etsy = L.get("etsy", {})
    gum = L.get("gumroad", {})

    # ------------------------------------------------------------ Etsy
    title = (etsy.get("title") or "").strip()
    if not title:
        fails.append("etsy.title is empty")
    else:
        if len(title) > ETSY_TITLE_MAX:
            fails.append(f"etsy.title is {len(title)} chars, limit {ETSY_TITLE_MAX}")
        if EMOJI.search(title):
            fails.append("etsy.title contains an emoji - Etsy titles should not")
        if title.isupper():
            fails.append("etsy.title is all caps")
        head = title.split("|")[0].split("-")[0].strip()
        if len(head) > 60:
            warns.append(f"etsy.title's first phrase is {len(head)} chars; the search "
                         f"grid truncates around 50-60 - front-load the keyword")

    tags = etsy.get("tags") or []
    if len(tags) != ETSY_TAGS:
        fails.append(f"etsy.tags has {len(tags)} tags, Etsy allows exactly {ETSY_TAGS}")
    seen = set()
    for t in tags:
        if len(t) > ETSY_TAG_MAX:
            fails.append(f"tag {t!r} is {len(t)} chars, limit {ETSY_TAG_MAX}")
        if t.lower() in seen:
            fails.append(f"duplicate tag {t!r}")
        seen.add(t.lower())

    # ------------------------------------------------------- banned names
    blob = " ".join([title, " ".join(tags), etsy.get("description", ""),
                     gum.get("name", ""), gum.get("summary", ""),
                     gum.get("description", "")])
    for entry in load_banned():
        pat = entry["pattern"] if entry.get("regex") else re.escape(entry["term"])
        m = re.search(pat, blob, re.I)
        if m:
            fails.append(f"banned term {entry.get('term')!r} in the listing copy - {entry['why']}")

    # -------------------------------------------------------- proof claims
    for m in PROOF_CLAIM.finditer(blob):
        fails.append(f"unearned proof claim: {m.group(0)!r}. No sales or rating numbers "
                     f"until they are real.")

    # ------------------------------------------------------ description
    desc = (gum.get("description") or "") + "\n" + (etsy.get("description") or "")
    low = desc.lower()
    for label, pats in REQUIRED_SECTIONS:
        if not any(re.search(p, low, re.M) for p in pats):
            warns.append(f"description has no recognisable '{label}' section")
    if not (L.get("disclaimer") or "").strip():
        fails.append("no disclaimer recorded")
    elif (L["disclaimer"].lower() not in low):
        warns.append("the disclaimer is not present in the description text")

    # ------------------------------------------------- claims vs reality
    claims = L.get("claims", {})
    if claims.get("interaction") not in ("fillable", "annotate-only"):
        fails.append("claims.interaction must be 'fillable' or 'annotate-only' - every listing "
                     "tells the buyer which it is")
    if a.dist and os.path.isdir(a.dist):
        facts = pdf_facts(a.dist)
        shipped_sizes = {v["mm"] for v in facts.values() if "mm" in v}
        want = {"A4": (210, 297), "Letter": (216, 279),
                "A5": (148, 210), "Tablet": (429, 572)}
        by_format = {}
        for label, fact in facts.items():
            for fmt, mm in want.items():
                if fact.get("mm") == mm:
                    by_format.setdefault(fmt, []).append((label, fact["pages"]))
        if claims.get("pages") and not claims.get("formats"):
            fails.append("claims.pages is set but claims.formats is empty - page counts are "
                         "checked per format")
        for fmt in claims.get("formats", []):
            if fmt not in want:
                # An unknown format must never pass quietly: silence would let
                # "A5 included" ship when no A5 file exists.
                warns.append(f"listing claims a {fmt!r} edition this gate cannot verify - "
                             f"confirm by hand that the file exists")
            elif fmt not in by_format:
                fails.append(f"listing claims a {fmt} edition; no shipped PDF is that size "
                             f"(found {sorted(shipped_sizes)})")
            elif claims.get("pages") and not any(p == claims["pages"] for _, p in by_format[fmt]):
                # Per format, not once per product: a 24-page A4 beside a 22-page
                # Letter passes a "24 is somewhere in the package" check.
                fails.append(f"listing claims {claims['pages']} pages; the {fmt} edition has "
                             + ", ".join(f"{p} ({label})" for label, p in by_format[fmt]))
        for label, fact in facts.items():
            print(f"  shipped: {label}  {fact}")
    elif a.dist:
        fails.append(f"--dist {a.dist} is not a folder")

    # ------------------------------------------------------------ price
    if "price_usd" not in L:
        fails.append("no price_usd recorded")

    for w in warns:
        print(f"  WARN  {w}")
    for f in fails:
        print(f"  FAIL  {f}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump({"fails": fails, "warnings": warns}, open(a.json, "w"), indent=2)

    print(f"\n{'PASS' if not fails else 'FAIL'} — {len(fails)} blocking, {len(warns)} warning(s).")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
