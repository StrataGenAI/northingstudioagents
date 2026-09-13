#!/usr/bin/env python3
"""Rasterise PDF pages to PNG so an agent can actually look at them.

No claim about how a page looks may be made without opening the PNG this
produces, so the render is a required build output, not a convenience. It fails,
never skips, if poppler's pdftoppm is missing, and a full render that does not end
with one PNG per PDF page exits 1.

Every run writes `<stem>.manifest.json` beside the PNGs: the PDF's sha256 and page
count, and every image written with its own sha256. Gates use it to prove the PNGs
an agent opened belong to the PDF being shipped.

Usage:
  render_pages.py dist/Product_A4.pdf --out qa/pages/a4                  # every page
  render_pages.py dist/Product_A4.pdf --out qa/pages/a4 --grey           # + greyscale copies
  render_pages.py dist/Product_A4.pdf --out qa/r2-check --pages 1,5,14-17
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "scripts"))
from lib import raster  # noqa: E402


def parse_pages(spec, n):
    if not spec:
        return list(range(1, n + 1))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    bad = [p for p in out if p < 1 or p > n]
    if bad:
        sys.exit(f"PDF has {n} pages; asked for {bad}")
    return out


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", default="", help="subset, e.g. 1,5,14-17 (default: every page)")
    ap.add_argument("--width", type=int, default=1400, help="longest side in px")
    ap.add_argument("--grey", action="store_true",
                    help="also write a greyscale copy, for the print-in-mono gate")
    a = ap.parse_args()

    raster.pdftoppm()                     # hard fail before any work if it is missing
    from pypdf import PdfReader
    if not os.path.exists(a.pdf):
        sys.exit(f"no such file: {a.pdf}")
    r = PdfReader(a.pdf)
    if r.is_encrypted:
        r.decrypt("")
    n_pages = len(r.pages)
    pages = parse_pages(a.pages, n_pages)
    partial = bool(a.pages)
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.pdf))[0]

    if not partial:
        # A full render replaces the set: PNGs left over from a longer earlier
        # build would otherwise sit beside the new ones and be judged as current.
        for old in glob.glob(os.path.join(glob.escape(a.out), f"{glob.escape(stem)}-p*.png")):
            os.remove(old)

    images = []
    for n in pages:
        png = raster.page_png(a.pdf, n, os.path.join(a.out, f"{stem}-p{n:02d}.png"), a.width)
        rec = {"page": n, "png": os.path.basename(png), "sha256": sha256(png)}
        if a.grey:
            g = raster.page_png(a.pdf, n, os.path.join(a.out, f"{stem}-p{n:02d}-grey.png"),
                                a.width, grey=True)
            rec["grey_png"], rec["grey_sha256"] = os.path.basename(g), sha256(g)
        images.append(rec)
        print(png)

    colour = [p for p in glob.glob(os.path.join(glob.escape(a.out), f"{glob.escape(stem)}-p*.png"))
              if not p.endswith("-grey.png")]
    manifest = {
        "pdf": a.pdf, "pdf_sha256": sha256(a.pdf), "pdf_pages": n_pages,
        "pages_rendered": len(images), "partial": partial,
        "width_px": a.width, "grey": a.grey, "tool": raster.tool_version(),
        "rendered_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "images": images,
    }
    mpath = os.path.join(a.out, f"{stem}.manifest.json")
    json.dump(manifest, open(mpath, "w"), indent=2)

    if not partial and len(colour) != n_pages:
        print(f"\nFAIL: {len(colour)} page PNG(s) in {a.out} for a {n_pages}-page PDF.",
              file=sys.stderr)
        return 1
    print(f"\n{len(images)} page(s) rasterised into {a.out} (manifest: {os.path.basename(mpath)})"
          " - open them with Read before judging the design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
