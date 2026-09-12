#!/usr/bin/env python3
"""Render a product HTML file to a print-exact PDF with headless Chrome.

Chrome's own A4 is 209.9 mm wide, not 210 — so after rendering, every page box is
normalised to the exact trim size. Content is laid out in millimetres, so the
correction is under 0.12 mm and never moves type off the grid.

Usage:
  build_pdf.py build/focus-audit.html -o dist/QuietCompass_Focus-Audit_A4.pdf --size a4
  build_pdf.py build/focus-audit.html -o dist/..._Tablet.pdf --size tablet

Sizes:   a4 (210x297mm) · letter (215.9x279.4mm) · tablet (1620x2160px @ 96dpi)
         or --size 210x297mm / --size 1620x2160px

The HTML must set its own `@page { size: ...; margin: 0 }` to match --size; this
script verifies that it did and fails loudly if the two disagree.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PT_PER_MM = 72.0 / 25.4
SIZES = {                      # name -> (width_mm, height_mm)
    "a4": (210.0, 297.0),
    "letter": (215.9, 279.4),
    "a5": (148.0, 210.0),
    "tablet": (1620 / 96 * 25.4, 2160 / 96 * 25.4),   # 428.625 x 571.5 mm
}
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
    sys.exit("No Chrome/Chromium found — install Google Chrome.")


def parse_size(s):
    if s in SIZES:
        return SIZES[s]
    m = re.fullmatch(r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)(mm|px|in)", s.strip())
    if not m:
        sys.exit(f"--size must be one of {', '.join(SIZES)} or WxH with mm/px/in, got {s!r}")
    w, h, unit = float(m.group(1)), float(m.group(2)), m.group(3)
    f = {"mm": 1.0, "px": 25.4 / 96, "in": 25.4}[unit]
    return w * f, h * f


def complete(path):
    """Has Chrome finished writing this PDF?

    Byte count alone cannot tell a finished write from a stalled one, and on a
    loaded machine writes stall for seconds at a time. A finished PDF ends with
    %%EOF, so ask the file itself. Shipping a half-written render is worse than
    waiting: it produces a valid-looking file that every later gate measures.
    """
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            fh.seek(max(0, size - 64))
            return b"%%EOF" in fh.read()
    except OSError:
        return False


def render(html, out, budget):
    """Print the page with Chrome.

    Chrome in --headless=new regularly writes the PDF and then never exits, so
    waiting on the process is not an option: wait for the file to appear and stop
    growing, then stop Chrome ourselves. (--run-all-compositor-stages-before-draw
    makes the hang far worse and buys nothing for a static page, so it is gone.)
    """
    exe = chrome()
    if os.path.exists(out):
        os.remove(out)
    with tempfile.TemporaryDirectory() as profile:
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-sandbox",
               "--no-pdf-header-footer", "--hide-scrollbars",
               "--allow-file-access-from-files",
               f"--virtual-time-budget={budget}",
               f"--user-data-dir={profile}",
               f"--print-to-pdf={out}",
               "file://" + os.path.abspath(html)]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Generous on purpose: a render that takes five seconds on an idle machine
        # has taken two and a half minutes on a loaded one. The completeness test
        # below is what normally ends the wait; this only stops us hanging forever.
        deadline = time.time() + max(600.0, budget / 1000.0 + 60)
        size, stable = -1, 0
        while time.time() < deadline:
            if p.poll() is not None:
                break
            if os.path.exists(out):
                s = os.path.getsize(out)
                stable = stable + 1 if (s == size and s > 0) else 0
                size = s
                if stable >= 3 and complete(out):    # settled AND ends with %%EOF
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
        sys.exit(f"Chrome produced no PDF.\n{err[-1500:]}")


def normalise(path, w_mm, h_mm, tol_mm=0.02):
    """Set every page box to the exact trim size. Returns (before_mm, fixed_pages)."""
    from pypdf import PdfReader, PdfWriter
    want_w, want_h = w_mm * PT_PER_MM, h_mm * PT_PER_MM
    r = PdfReader(path)
    before = (float(r.pages[0].mediabox.width) / PT_PER_MM,
              float(r.pages[0].mediabox.height) / PT_PER_MM)
    fixed = 0
    w = PdfWriter(clone_from=path)
    for page in w.pages:
        mb = page.mediabox
        if (abs(float(mb.width) - want_w) > tol_mm * PT_PER_MM
                or abs(float(mb.height) - want_h) > tol_mm * PT_PER_MM):
            fixed += 1
        # Anchor at the top-left corner, which is where Chrome lays content out.
        top = float(mb.top)
        mb.lower_left = (float(mb.left), top - want_h)
        mb.upper_right = (float(mb.left) + want_w, top)
        page.cropbox = mb
        page.trimbox = mb
    if fixed:
        w.write(path)
    return before, fixed


def declared_page_sizes(html_path):
    """Every `@page { size: ... }` in the HTML and the CSS it links.

    The shared stylesheet declares a named page per sheet (a4sheet, lettersheet,
    tabletsheet...), so there are always several. The build is happy if any one of
    them matches the size being asked for.
    """
    text = open(html_path, encoding="utf-8", errors="replace").read()
    here = os.path.dirname(os.path.abspath(html_path))
    for href in re.findall(r'<link[^>]+href="([^"]+\.css)"', text):
        p = os.path.join(here, href)
        if os.path.exists(p):
            text += open(p, encoding="utf-8", errors="replace").read()
    out = []
    for m in re.finditer(r"@page[^{]*\{[^}]*?size:\s*([^;}]+)", text, re.I | re.S):
        spec = m.group(1).strip().rstrip(";")
        pair = re.findall(r"(\d+(?:\.\d+)?)(mm|in|px|pt)", spec)
        if len(pair) == 2:
            f = {"mm": 1.0, "in": 25.4, "px": 25.4 / 96, "pt": 25.4 / 72}
            out.append((float(pair[0][0]) * f[pair[0][1]], float(pair[1][0]) * f[pair[1][1]]))
        elif spec.split()[0].lower() in SIZES:
            out.append(SIZES[spec.split()[0].lower()])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--size", default="a4")
    ap.add_argument("--budget", type=int, default=15000,
                    help="virtual time budget in ms; raise it for heavy pages")
    ap.add_argument("--allow-size-mismatch", action="store_true")
    a = ap.parse_args()

    w_mm, h_mm = parse_size(a.size)
    if not os.path.exists(a.html):
        sys.exit(f"no such file: {a.html}")

    declared = declared_page_sizes(a.html)
    if declared and not any(abs(d[0] - w_mm) <= 0.5 and abs(d[1] - h_mm) <= 0.5 for d in declared):
        shown = ", ".join(f"{d[0]:.1f}x{d[1]:.1f}" for d in declared)
        msg = (f"no @page rule matches --size {a.size} ({w_mm:.1f}x{h_mm:.1f}mm); "
               f"the stylesheet declares {shown}mm. Check the sheet class on <body>.")
        if not a.allow_size_mismatch:
            sys.exit("FAIL: " + msg)
        print("warning: " + msg)
    if not declared:
        print("warning: no `@page { size: ... }` found; Chrome will guess the sheet size.")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    render(a.html, a.out, a.budget)
    before, fixed = normalise(a.out, w_mm, h_mm)

    from pypdf import PdfReader
    r = PdfReader(a.out)
    mb = r.pages[0].mediabox
    print(f"{a.out}")
    print(f"  pages   {len(r.pages)}")
    print(f"  size    {float(mb.width) / PT_PER_MM:.3f} x {float(mb.height) / PT_PER_MM:.3f} mm"
          f"  (Chrome gave {before[0]:.3f} x {before[1]:.3f}; {fixed} page box(es) corrected)")
    print(f"  bytes   {os.path.getsize(a.out):,}")
    print("\nNext: verify_pdf.py checks fonts, ink, type size and page fill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
