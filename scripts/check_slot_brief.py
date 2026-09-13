#!/usr/bin/env python3
"""Validate a listing's slot brief before any listing image is made.

The brief is the owner's review point. It says what each listing image shows and
exactly which real page it is built from. Images are rendered only after the owner
approves the brief: Listing/slot-brief.APPROVED records the sha256 of the approved
file, and release_check.py --listing fails if the brief changes afterwards.

  check_slot_brief.py "Products/PB-022 The 10-Minute Life Audit"
  check_slot_brief.py "Products/PB-022 ..." --approve
      Only after the owner has said yes in the session: records the approval.

Format of Listing/slot-brief.md, one table row per slot:

| # | Role | Artboard | Source PDF | Page | Source PNG | Overlay text |

  slot 1   HERO. The overlay states every format shipped, the page count and, if
           the spec says undated, "undated".
  slot 2   an interior DECISION page
  slot 3   the CHARTER / OUTPUT page
  4-10     the rest of the tour

A slot that cannot be filled writes "N/A - <reason>" in Role. At least 8 slots
must be filled and at most 10.

Rules for each filled slot:
- Source PDF is a file in dist/.
- Page exists in that file.
- Source PNG is that page's render: <pdf stem>-pNN.png, and it exists.
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lib import inventory, shop  # noqa: E402
from lib.shop import norm  # noqa: E402

ARTBOARDS = {"2000x2000", "2560x1440", "2000x2500"}
ROLE_RULES = {1: (r"\bhero\b", "HERO"), 2: (r"\bdecision\b", "an interior DECISION page"),
              3: (r"\bcharter\b|\boutput\b", "the CHARTER / OUTPUT page")}


def parse(path):
    header, rows = None, []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            low = [c.lower() for c in cells]
            if "role" in low and "source pdf" in low:
                header = low
            continue
        if re.fullmatch(r"\|[\s:|-]+\|", s):
            continue
        rows.append(dict(zip(header, cells)))
    return header, rows


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    approve = "--approve" in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    pdir = os.path.abspath(args[0])
    brief = os.path.join(pdir, "Listing", "slot-brief.md")
    if not os.path.exists(brief):
        sys.exit("FAIL: Listing/slot-brief.md is missing")
    spec = open(shop.find_spec(shop.product_id(pdir)), encoding="utf-8").read()
    dist = os.path.join(pdir, "dist")
    from pypdf import PdfReader
    pdfs = {}
    for f in sorted(os.listdir(dist)) if os.path.isdir(dist) else []:
        if f.lower().endswith(".pdf"):
            r = PdfReader(os.path.join(dist, f))
            if r.is_encrypted:
                r.decrypt("")
            pdfs[f] = len(r.pages)

    fails, oks = [], []
    header, rows = parse(brief)
    if header is None:
        sys.exit("FAIL: slot-brief.md has no table with Role and Source PDF columns")
    filled = [r for r in rows if not r.get("role", "").upper().startswith("N/A")]
    for r in rows:
        if r.get("role", "").upper().startswith("N/A") and not re.search(r"N/A\s*[-—–:]\s*\S", r["role"], re.I):
            fails.append(f"slot {r.get('#')}: N/A without a reason")
    if not 8 <= len(filled) <= 10:
        fails.append(f"{len(filled)} filled slots; a listing needs 8 to 10")

    editions = {m.group(1): (f, n) for f, n in pdfs.items() for m in [re.search(r"_(A4|Letter|Tablet)\.pdf$", f)] if m}
    for r in rows:
        try:
            slot = int(re.sub(r"\D", "", r.get("#", "")) or 0)
        except ValueError:
            slot = 0
        role = r.get("role", "")
        if slot in ROLE_RULES and not role.upper().startswith("N/A") and not re.search(ROLE_RULES[slot][0], role, re.I):
            fails.append(f"slot {slot}: must be {ROLE_RULES[slot][1]} (Role says “{role}”)")
        if role.upper().startswith("N/A"):
            if slot == 1:
                fails.append("slot 1 (HERO) cannot be N/A")
            continue
        size = re.sub(r"\s", "", r.get("artboard", "")).lower().replace("×", "x")
        if not any(a in size for a in ARTBOARDS):
            fails.append(f"slot {slot}: artboard “{r.get('artboard')}” is not one of {', '.join(sorted(ARTBOARDS))}")
        src = r.get("source pdf", "").strip("` ")
        if src not in pdfs:
            fails.append(f"slot {slot}: source PDF “{src}” is not in dist/")
            continue
        try:
            page = int(re.sub(r"\D", "", r.get("page", "")))
        except ValueError:
            fails.append(f"slot {slot}: no page number")
            continue
        if not 1 <= page <= pdfs[src]:
            fails.append(f"slot {slot}: page {page} does not exist in {src} ({pdfs[src]} pages)")
        png = r.get("source png", "").strip("` ")
        want = f"{os.path.splitext(src)[0]}-p{page:02d}.png"
        if os.path.basename(png) != want:
            fails.append(f"slot {slot}: source PNG “{png}” is not the render of {src} page {page} ({want})")
        elif not os.path.exists(os.path.join(pdir, png)):
            fails.append(f"slot {slot}: {png} does not exist - render the page first")
        else:
            oks.append(f"slot {slot}: {role} <- {src} p{page}")
        if slot == 1:
            overlay = r.get("overlay text", "")
            for ed in editions:
                if not re.search(re.escape(ed), overlay, re.I):
                    fails.append(f"slot 1: the hero overlay does not state the {ed} format")
            a4 = editions.get("A4")
            if a4 and not re.search(rf"\b{a4[1]}\b", overlay):
                fails.append(f"slot 1: the hero overlay does not state the page count ({a4[1]})")
            if "undated" in norm(spec) and "undated" not in norm(overlay):
                fails.append("slot 1: the spec says undated; the hero overlay does not")

    out = os.path.join(pdir, "Listing", "qa", "slot-brief-check.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"pass": not fails, "fails": fails, "ok": oks}, open(out, "w"), indent=2)
    for o in oks:
        print(f"  ok    {o}")
    for f in fails:
        print(f"  FAIL  {f}")
    if fails:
        print(f"\nFAIL - {len(fails)} problem(s) in the slot brief.")
        return 1
    if approve:
        stamp = os.path.join(pdir, "Listing", "slot-brief.APPROVED")
        open(stamp, "w").write(f"approved by the owner in the session\n"
                               f"at: {datetime.datetime.now().isoformat(timespec='seconds')}\n"
                               f"sha256: {inventory.sha256(brief)}\n")
        print(f"\nPASS - approval recorded in {os.path.relpath(stamp, ROOT)}")
    else:
        print("\nPASS - the brief is valid. Upload it (--stage brief) and wait for the owner's approval.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
