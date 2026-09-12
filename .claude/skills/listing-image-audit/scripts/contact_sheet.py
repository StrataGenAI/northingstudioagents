#!/usr/bin/env python3
"""Tile many images into ONE labelled PNG so a whole listing (or a search grid of competitor
thumbnails) can be viewed with a single Read. Uses headless Google Chrome.

Usage:
  contact_sheet.py DIR_OR_IMAGES... --out sheet.png [--cols 4] [--cell 360]
  contact_sheet.py a/01.jpg b/01.jpg c/01.jpg --out thumbs.png --cell 220 --cols 5   # search-grid test

--cell is the width of each tile in px (220 is roughly what a buyer sees in a search grid).
"""
import argparse
import glob
import html
import os
import pathlib
import subprocess
import sys
import tempfile

EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    sys.exit("No Chrome/Chromium/Edge/Brave found in /Applications")


def uri(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


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
        cells.append(f'<figure><div class="im"><img src="{html.escape(uri(f))}"></div>'
                     f'<figcaption>{label}</figcaption></figure>')
    doc = f"""<html><head><style>
      body{{margin:0;padding:{gap}px;background:#fff;font:12px -apple-system,Helvetica,sans-serif;color:#333}}
      .g{{display:grid;grid-template-columns:repeat({cols},{a.cell}px);gap:{gap}px}}
      figure{{margin:0}} .im{{width:{a.cell}px;height:{a.cell}px;background:#f2f2f2;display:flex;align-items:center;justify-content:center;overflow:hidden}}
      img{{max-width:100%;max-height:100%;object-fit:contain}}
      figcaption{{height:{label_h}px;line-height:{label_h}px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
    </style></head><body><div class="g">{''.join(cells)}</div></body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as t:
        t.write(doc)
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                    "--allow-file-access-from-files", f"--window-size={width},{height}",
                    "--virtual-time-budget=5000", f"--screenshot={out}", uri(t.name)],
                   capture_output=True)
    os.unlink(t.name)
    if not os.path.exists(out):
        sys.exit("Chrome did not write the screenshot")
    print(f"{out}  ({len(files)} images, {cols}x{rows}, {width}x{height}px)")


if __name__ == "__main__":
    main()
