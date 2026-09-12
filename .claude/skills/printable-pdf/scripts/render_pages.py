#!/usr/bin/env python3
"""Rasterise PDF pages to PNG so an agent can actually look at them.

No claim about how a page looks may be made without opening the PNG this
produces. macOS `sips` renders only the first page of a PDF, so each page is
split into a one-page file first.

Usage:
  render_pages.py dist/Product_A4.pdf --out qa/pages            # every page
  render_pages.py dist/Product_A4.pdf --out qa/pages --pages 1,5,14-17
  render_pages.py dist/Product_A4.pdf --out qa/pages --width 1000 --grey
"""
import argparse
import os
import subprocess
import sys
import tempfile


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", default="")
    ap.add_argument("--width", type=int, default=1400, help="longest side in px")
    ap.add_argument("--grey", action="store_true",
                    help="also write a greyscale copy, for the print-in-mono gate")
    a = ap.parse_args()

    from pypdf import PdfReader, PdfWriter
    r = PdfReader(a.pdf)
    pages = parse_pages(a.pages, len(r.pages))
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.pdf))[0]

    written = []
    with tempfile.TemporaryDirectory() as td:
        for n in pages:
            one = os.path.join(td, f"p{n}.pdf")
            w = PdfWriter()
            w.add_page(r.pages[n - 1])
            w.write(one)
            png = os.path.join(a.out, f"{stem}-p{n:02d}.png")
            subprocess.run(["sips", "-s", "format", "png", "-Z", str(a.width), one, "--out", png],
                           check=True, capture_output=True)
            written.append(png)
            if a.grey:
                g = os.path.join(a.out, f"{stem}-p{n:02d}-grey.png")
                subprocess.run(["sips", "-s", "format", "png", "-Z", str(a.width),
                                "-m", "/System/Library/ColorSync/Profiles/Generic Gray Profile.icc",
                                one, "--out", g], check=True, capture_output=True)
                written.append(g)

    for p in written:
        print(p)
    print(f"\n{len(written)} image(s) in {a.out} — open them with Read before judging the design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
