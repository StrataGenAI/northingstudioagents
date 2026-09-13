#!/usr/bin/env python3
"""Render a listing-image artboard (HTML) to an exact-size PNG or JPEG.

Listing images are the shop. A buyer decides in the search grid, at about 220 px
wide, before reading a word of the description — so these are rendered at full
size from real brand CSS and real product pages, never mocked up by hand.

    render_artboard.py build/01-hero.html -o images/01-hero.png --size 2000x2000
    render_artboard.py build/02-thumb.html -o images/02-thumb.jpg --size 2000x2000 --jpg
    render_artboard.py pins/build/pin-1.html -o pins/pin-1.png --size 1000x1500

Chrome writes the screenshot at exactly --window-size when the device scale
factor is 1, and the result is verified afterwards: a listing image that is one
pixel off the platform's expected ratio gets cropped by the platform, not by us.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "scripts"))
from lib import chromium, raster  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--size", default="2000x2000", help="WxH in pixels")
    ap.add_argument("--jpg", action="store_true", help="convert to JPEG after rendering")
    ap.add_argument("--quality", type=int, default=90, help="JPEG quality (default 90)")
    ap.add_argument("--max-mb", type=float, default=20.0,
                    help="warn above this file size; CHECK the platform's current limit")
    ap.add_argument("--budget", type=int, default=15000)
    a = ap.parse_args()

    try:
        w, h = (int(x) for x in a.size.lower().split("x"))
    except ValueError:
        sys.exit("--size must look like 2000x2000")
    if not os.path.exists(a.html):
        sys.exit(f"no such file: {a.html}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    png = a.out if not a.jpg else os.path.splitext(a.out)[0] + ".render.png"
    chromium.screenshot(a.html, png, w, h, a.budget)

    got_w, got_h = raster.image_size(png)
    if (got_w, got_h) != (w, h):
        sys.exit(f"FAIL: rendered {got_w}x{got_h}, asked for {w}x{h}. "
                 f"The platform will crop this, not us.")

    out = a.out
    if a.jpg:
        raster.to_jpeg(png, out, quality=a.quality)
        os.remove(png)

    mb = os.path.getsize(out) / 1e6
    print(f"{out}")
    print(f"  size   {got_w} x {got_h} px  (exact)")
    print(f"  bytes  {os.path.getsize(out):,}  ({mb:.2f} MB)")
    if mb > a.max_mb:
        print(f"  WARN   over {a.max_mb} MB - re-render as --jpg, or lower --quality")
    print("\n  Now LOOK at it, and look at it shrunk to 220px: that is the size the")
    print("  buyer actually decides at.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
