#!/usr/bin/env python3
"""Render a listing-image artboard (HTML) to an exact-size PNG or JPEG.

Listing images are the shop. A buyer decides in the search grid, at about 220 px
wide, before reading a word of the description — so these are rendered at full
size from real brand CSS and real product pages, never mocked up by hand.

    render_artboard.py build/01-hero.html -o images/01-hero.png --size 2000x2000
    render_artboard.py build/02-thumb.html -o images/02-thumb.jpg --size 2000x2000 --jpg

Chrome writes the screenshot at exactly --window-size when the device scale
factor is 1, and the result is verified afterwards: a listing image that is one
pixel off the platform's expected ratio gets cropped by the platform, not by us.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def chrome():
    for c in CHROMES:
        if os.path.exists(c):
            return c
    found = shutil.which("google-chrome") or shutil.which("chromium")
    if found:
        return found
    sys.exit("No Chrome/Chromium found - install Google Chrome.")


def complete(path):
    """A finished PNG ends with the IEND chunk; a JPEG with FFD9."""
    try:
        size = os.path.getsize(path)
        if size < 100:
            return False
        with open(path, "rb") as fh:
            fh.seek(max(0, size - 12))
            tail = fh.read()
        return b"IEND" in tail or tail.endswith(b"\xff\xd9")
    except OSError:
        return False


def shoot(html, out, w, h, budget):
    exe = chrome()
    if os.path.exists(out):
        os.remove(out)
    with tempfile.TemporaryDirectory() as profile:
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-sandbox",
               "--hide-scrollbars", "--allow-file-access-from-files",
               "--force-device-scale-factor=1",
               f"--virtual-time-budget={budget}",
               f"--window-size={w},{h}",
               f"--user-data-dir={profile}",
               f"--screenshot={out}",
               "file://" + os.path.abspath(html)]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Same lesson as the PDF builder: Chrome often writes the file and then
        # fails to exit, and a stalled write looks like a finished one by size
        # alone. Wait for the file to settle AND to end with its terminator.
        deadline = time.time() + max(300.0, budget / 1000.0 + 60)
        size, stable = -1, 0
        while time.time() < deadline:
            if p.poll() is not None:
                break
            if os.path.exists(out):
                s = os.path.getsize(out)
                stable = stable + 1 if (s == size and s > 0) else 0
                size = s
                if stable >= 3 and complete(out):
                    break
            time.sleep(0.5)
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        err = (p.stderr.read() or b"").decode("utf-8", "replace") if p.stderr else ""
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        sys.exit(f"Chrome produced no image.\n{err[-1200:]}")


def dimensions(path):
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                       capture_output=True, text=True)
    w = h = 0
    for line in r.stdout.splitlines():
        if "pixelWidth:" in line:
            w = int(line.split(":")[1])
        if "pixelHeight:" in line:
            h = int(line.split(":")[1])
    return w, h


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
    shoot(a.html, png, w, h, a.budget)

    got_w, got_h = dimensions(png)
    if (got_w, got_h) != (w, h):
        sys.exit(f"FAIL: rendered {got_w}x{got_h}, asked for {w}x{h}. "
                 f"The platform will crop this, not us.")

    out = a.out
    if a.jpg:
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions",
                        str(a.quality), png, "--out", out],
                       check=True, capture_output=True)
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
