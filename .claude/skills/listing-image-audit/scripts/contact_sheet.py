#!/usr/bin/env python3
"""Tile many images into ONE labelled PNG so a whole listing (or a search grid of competitor
thumbnails) can be viewed with a single Read. Uses headless Chrome (scripts/lib/chromium.py).

Usage:
  contact_sheet.py DIR_OR_IMAGES... --out sheet.png [--cols 4] [--cell 360]
  contact_sheet.py a/01.jpg b/01.jpg c/01.jpg --out thumbs.png --cell 220 --cols 5   # search-grid test

--cell is the width of each tile in px (220 is roughly what a buyer sees in a search grid).
"""
import argparse
import glob
import html
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "scripts"))
from lib import chromium  # noqa: E402

EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def collect(inputs):
    files = []
    for p in inputs:
        if os.path.isdir(p):
            files += sorted(f for f in glob.glob(os.path.join(p, "*"))
                            if f.lower().endswith(EXTS) and not os.path.basename(f).startswith("_"))
        elif p.lower().endswith(EXTS) and os.path.exists(p):
            files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--cell", type=int, default=360)
    a = ap.parse_args()
    files = collect(a.inputs)
    if not files:
        sys.exit("No images found")
    cols = min(a.cols, len(files))
    rows = -(-len(files) // cols)
    gap, label_h = 12, 22
    width = cols * a.cell + (cols + 1) * gap
    height = rows * (a.cell + label_h + gap) + gap
    cells = []
    for f in files:
        parent = os.path.basename(os.path.dirname(os.path.abspath(f)))
        label = html.escape(f"{parent}/{os.path.basename(f)}")
        cells.append(f'<figure><div class="im"><img src="{html.escape(chromium.uri(f))}"></div>'
                     f'<figcaption>{label}</figcaption></figure>')
    doc = f"""<html><head><style>
      body{{margin:0;padding:{gap}px;background:#fff;font:12px "DejaVu Sans",Helvetica,sans-serif;color:#333}}
      .g{{display:grid;grid-template-columns:repeat({cols},{a.cell}px);gap:{gap}px}}
      figure{{margin:0}} .im{{width:{a.cell}px;height:{a.cell}px;background:#f2f2f2;display:flex;align-items:center;justify-content:center;overflow:hidden}}
      img{{max-width:100%;max-height:100%;object-fit:contain}}
      figcaption{{height:{label_h}px;line-height:{label_h}px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
    </style></head><body><div class="g">{''.join(cells)}</div></body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as t:
        t.write(doc)
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        chromium.screenshot(t.name, out, width, height, budget=5000)
    finally:
        os.unlink(t.name)
    print(f"{out}  ({len(files)} images, {cols}x{rows}, {width}x{height}px)")


if __name__ == "__main__":
    main()
