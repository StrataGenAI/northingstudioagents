#!/usr/bin/env python3
"""Render a product's licence from the shop's templates in brands/licences/.

  make_licence.py "Products/PB-022 The 10-Minute Life Audit" --tier personal
      -> dist/licences/LICENCE.txt        run before release_check.py
  make_licence.py "Products/PB-022 The 10-Minute Life Audit" --tier practitioner
      -> dist-practitioner/               run after pdf-protect: a copy of the protected
                                          dist/ with the practitioner LICENCE.txt in it

Where the facts come from:
- the product name: the spec's title
- the licensor and support contact: brands/SHOP.md
- the version and date: the stamp in dist/README.txt, unless --version and --date are given

A missing fact fails the run. A licence is never rendered with a blank or a guess
in it. The practitioner tier is priced separately: the price lives in
brands/SHOP.md and on the listing, never in the licence file.
"""
import argparse
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lib import shop  # noqa: E402

DISCLAIMERS = {   # fixed wording, brands/quiet-compass/voice.md §5
    "reflection": "A structured self-reflection tool. Not therapy, diagnosis or financial advice.",
    "money": "Educational only — not financial advice.",
}
STAMP = re.compile(r"\b(?:v|version\s+)(\d+\.\d+)\b(?:\s*[·•|-]?\s*(\d{4}-\d{2}(?:-\d{2})?))?", re.I)


def render(tier, facts):
    template = open(os.path.join(ROOT, "brands", "licences", f"{tier}.md"), encoding="utf-8").read()
    text = re.sub(r"<!--.*?-->\s*", "", template, flags=re.S)
    for key, value in facts.items():
        text = text.replace("{" + key + "}", value)
    left = sorted(set(re.findall(r"\{[a-z_]+\}", text)))
    if left:
        sys.exit(f"FAIL: the {tier} template still has unfilled fields: {', '.join(left)}")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("product")
    ap.add_argument("--tier", choices=["personal", "practitioner"], required=True)
    ap.add_argument("--version", help="e.g. v1.0 (default: read from dist/README.txt)")
    ap.add_argument("--date", help="e.g. 2026-09 (default: read from dist/README.txt)")
    ap.add_argument("--disclaimer", choices=sorted(DISCLAIMERS), default="reflection")
    a = ap.parse_args()

    product = os.path.abspath(a.product)
    pb_id = shop.product_id(product)
    _, name = shop.spec_identity(shop.find_spec(pb_id))
    dist = os.path.join(product, "dist")
    if not os.path.isdir(dist):
        sys.exit(f"FAIL: {dist} does not exist - build the product first")

    version, date = a.version, a.date
    readme = os.path.join(dist, "README.txt")
    if (not version or not date) and os.path.exists(readme):
        for m in STAMP.finditer(open(readme, encoding="utf-8").read()):
            version = version or f"v{m.group(1)}"
            date = date or m.group(2)
    facts = shop.shop_facts()
    missing = [k for k, v in (("licensor", facts.get("licensor")),
                              ("support_contact", facts.get("support_contact")),
                              ("version", version), ("date", date)) if not v]
    if missing:
        sys.exit(f"FAIL: cannot render the licence - not decided: {', '.join(missing)}. "
                 f"Set licensor/support_contact in brands/SHOP.md; version/date come from the "
                 f"README stamp or --version/--date.")
    values = {"product_name": name, "licensor": facts["licensor"], "version": version, "date": date,
              "support": facts["support_contact"], "disclaimer": DISCLAIMERS[a.disclaimer]}
    text = render(a.tier, values)

    if a.tier == "personal":
        out_dir = os.path.join(dist, "licences")
    else:
        from pypdf import PdfReader
        pdfs = [f for f in os.listdir(dist) if f.lower().endswith(".pdf")]
        unprotected = [f for f in pdfs if not PdfReader(os.path.join(dist, f)).is_encrypted]
        spec_text = open(shop.find_spec(pb_id), encoding="utf-8").read()
        if (shop.spec_field(spec_text, "Protection") or "").lower().startswith("none"):
            unprotected = []            # the spec ships this product unprotected on purpose
        if not pdfs or unprotected:
            sys.exit("FAIL: the practitioner package is copied from the PROTECTED build - run pdf-protect "
                     f"first (unprotected: {', '.join(unprotected) or 'no PDFs at all'})")
        target = os.path.join(product, "dist-practitioner")
        if os.path.isdir(target):
            shutil.rmtree(target)
        shutil.copytree(dist, target)
        out_dir = os.path.join(target, "licences")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "LICENCE.txt")
    open(out, "w", encoding="utf-8").write(text)
    print(f"{os.path.relpath(out, ROOT)}  ({a.tier}, {name}, {version}, {date})")
    print("  Draft licence text - have it reviewed before selling under it (MULTI_AGENT_PLAN.md, M3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
