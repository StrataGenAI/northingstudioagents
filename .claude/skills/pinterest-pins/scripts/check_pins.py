#!/usr/bin/env python3
"""Validate a product's five Pinterest pins before they upload.

  check_pins.py "Products/PB-022 The 10-Minute Life Audit"

Pinterest/pins.json:
{"pins": [{"image": "images/pin-1.png",
           "source_pdf": "NorthingStudio_10-Minute-Life-Audit_A4.pdf", "source_page": 3,
           "source_png": "qa/pages/a4/NorthingStudio_10-Minute-Life-Audit_A4-p03.png",
           "title": "...", "description": "...", "alt": "...",
           "destination": "https://... | pending-own-listing"}]}

Fails on:
- anything other than exactly 5 pins
- an image that is not exactly 1000x1500
- a pin not built from a real shipped page: the PDF is in dist/, the page exists,
  and source_png is that page's render and exists
- title, description or alt text empty or over Pinterest's limits
  (100 / 500 / 500 characters, checked 2026-09-13)
- a destination that is neither an https URL nor "pending-own-listing"
- an internal PB-/BN- ID in an image filename
- any blocking banned_terms.py finding in the pin copy: trademarks, unsafe claims, voice

Warns on:
- two pins built from the same page
- duplicate titles

Writes Pinterest/qa/pins-check.json, which upload_to_drive.py --stage listing requires.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lib import raster  # noqa: E402

PIN_COUNT = 5
PIN_SIZE = (1000, 1500)
LIMITS = {"title": 100, "description": 500, "alt": 500}
SKU_RE = re.compile(r"(?<![A-Za-z])(?:PB|BN)-?\d{2,3}(?!\d)", re.I)
BANNED = os.path.join(ROOT, ".claude", "skills", "product-qa", "scripts", "banned_terms.py")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pdir = os.path.abspath(sys.argv[1])
    pins_dir = os.path.join(pdir, "Pinterest")
    path = os.path.join(pins_dir, "pins.json")
    fails, warns = [], []
    if not os.path.exists(path):
        sys.exit("FAIL: Pinterest/pins.json is missing")
    pins = json.load(open(path, encoding="utf-8")).get("pins", [])
    if len(pins) != PIN_COUNT:
        fails.append(f"{len(pins)} pins; exactly {PIN_COUNT} are required")

    from pypdf import PdfReader
    page_counts = {}
    seen_pages, seen_titles = {}, {}
    copy_lines = []
    for i, pin in enumerate(pins, 1):
        img = os.path.join(pins_dir, pin.get("image", ""))
        if not pin.get("image") or not os.path.exists(img):
            fails.append(f"pin {i}: image {pin.get('image')!r} does not exist")
        else:
            size = raster.image_size(img)
            if tuple(size) != PIN_SIZE:
                fails.append(f"pin {i}: {os.path.basename(img)} is {size[0]}x{size[1]}, not {PIN_SIZE[0]}x{PIN_SIZE[1]}")
            if SKU_RE.search(os.path.basename(img)):
                fails.append(f"pin {i}: image filename carries an internal ID - {os.path.basename(img)}")

        src = pin.get("source_pdf", "")
        pdf = os.path.join(pdir, "dist", src)
        page = pin.get("source_page")
        if not src or not os.path.exists(pdf):
            fails.append(f"pin {i}: source_pdf {src!r} is not a shipped file in dist/")
        else:
            if src not in page_counts:
                r = PdfReader(pdf)
                if r.is_encrypted:
                    r.decrypt("")
                page_counts[src] = len(r.pages)
            if not isinstance(page, int) or not 1 <= page <= page_counts[src]:
                fails.append(f"pin {i}: source_page {page!r} does not exist in {src}")
            else:
                want = f"{os.path.splitext(src)[0]}-p{page:02d}.png"
                png = pin.get("source_png", "")
                if os.path.basename(png) != want:
                    fails.append(f"pin {i}: source_png {png!r} is not the render of {src} page {page} ({want})")
                elif not os.path.exists(os.path.join(pdir, png)):
                    fails.append(f"pin {i}: {png} does not exist - render the page first")
                key = (src, page)
                if key in seen_pages:
                    warns.append(f"pin {i}: built from the same page as pin {seen_pages[key]}")
                seen_pages.setdefault(key, i)

        for field, limit in LIMITS.items():
            text = (pin.get(field) or "").strip()
            if not text:
                fails.append(f"pin {i}: {field} is empty")
            elif len(text) > limit:
                fails.append(f"pin {i}: {field} is {len(text)} characters; Pinterest allows {limit}")
            copy_lines.append(text)
        title = (pin.get("title") or "").strip().lower()
        if title in seen_titles:
            warns.append(f"pin {i}: same title as pin {seen_titles[title]}")
        seen_titles.setdefault(title, i)

        dest = (pin.get("destination") or "").strip()
        if dest != "pending-own-listing" and not re.match(r"https://\S+$", dest):
            fails.append(f"pin {i}: destination {dest!r} is neither an https URL nor pending-own-listing")

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
        tmp.write("\n\n".join(copy_lines))
    r = subprocess.run([sys.executable, BANNED, tmp.name], capture_output=True, text=True)
    os.unlink(tmp.name)
    if r.returncode != 0:
        fails.append("pin copy fails banned_terms.py:\n" + r.stdout.strip())

    out = os.path.join(pins_dir, "qa", "pins-check.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"pass": not fails, "fails": fails, "warnings": warns, "pins": len(pins)}, open(out, "w"), indent=2)
    for w in warns:
        print(f"  WARN  {w}")
    for f in fails:
        print(f"  FAIL  {f}")
    print(f"\n{'PASS' if not fails else 'FAIL'} - {len(pins)} pin(s), {len(fails)} blocking, {len(warns)} warning(s).")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
