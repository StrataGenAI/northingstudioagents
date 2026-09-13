"""Rasterise PDF pages (poppler's pdftoppm) and handle raster images (Pillow).

No page may be judged - by an agent or by a gate - without a raster of it, so
nothing in here degrades quietly: a missing tool is a hard failure, never a
skipped check.
"""
import os
import shutil
import subprocess
import sys
import tempfile


def pdftoppm():
    path = shutil.which("pdftoppm")
    if not path:
        sys.exit("FAIL: pdftoppm not found (apt package poppler-utils). Run scripts/setup.sh. "
                 "Without it no page can be rasterised, so nothing about how a page looks "
                 "can be checked.")
    return path


def tool_version():
    r = subprocess.run([pdftoppm(), "-v"], capture_output=True, text=True)
    return (r.stderr or r.stdout).splitlines()[0].strip()


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"FAIL: {os.path.basename(cmd[0])} exited {r.returncode}: "
                 f"{r.stderr.decode('utf-8', 'replace')[-800:]}")


def page_png(pdf, page, out_png, long_side=None, grey=False):
    """Write page `page` (1-based) of `pdf` to `out_png`, scaled so its longest side
    is `long_side` px. Returns the path written."""
    root = out_png[:-4] if out_png.lower().endswith(".png") else out_png
    cmd = [pdftoppm(), "-f", str(page), "-l", str(page), "-singlefile", "-png"]
    if grey:
        cmd.append("-gray")
    if long_side:
        cmd += ["-scale-to", str(int(long_side))]
    _run(cmd + [pdf, root])
    path = root + ".png"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        sys.exit(f"FAIL: pdftoppm wrote nothing for page {page} of {pdf}")
    return path


def page_rgb(pdf, page, long_side):
    """Page `page` (1-based) as (width, height, rows of (r, g, b)), longest side
    `long_side` px. These are the pixels the ink and fill gates measure."""
    with tempfile.TemporaryDirectory() as td:
        root = os.path.join(td, "p")
        _run([pdftoppm(), "-f", str(page), "-l", str(page), "-singlefile",
              "-scale-to", str(int(long_side)), pdf, root])
        with open(root + ".ppm", "rb") as fh:
            data = fh.read()
    return parse_ppm(data)


def parse_ppm(data):
    """Binary PPM (P6, maxval 255) -> (width, height, rows of (r, g, b))."""
    fields, i = [], 0
    while len(fields) < 4:
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b"#":
            while data[i:i + 1] not in (b"\n", b""):
                i += 1
            continue
        j = i
        while j < len(data) and not data[j:j + 1].isspace():
            j += 1
        fields.append(data[i:j])
        i = j
    i += 1                                   # exactly one whitespace byte before the raster
    if fields[0] != b"P6" or int(fields[3]) != 255:
        raise ValueError(f"unsupported PPM ({fields[0]!r}, maxval {fields[3]!r})")
    w, h = int(fields[1]), int(fields[2])
    if len(data) - i < w * h * 3:
        raise ValueError("truncated PPM raster")
    rows = []
    for y in range(h):
        row = data[i + y * w * 3: i + (y + 1) * w * 3]
        rows.append([(row[x], row[x + 1], row[x + 2]) for x in range(0, w * 3, 3)])
    return w, h, rows


# ------------------------------------------------------------------ Pillow
def _image():
    try:
        from PIL import Image
    except ImportError:
        sys.exit("FAIL: Pillow is not installed for this Python. Run scripts/setup.sh and "
                 "call scripts with .venv/bin/python.")
    return Image


def image_size(path):
    with _image().open(path) as im:
        return im.size


def to_jpeg(src, dst, quality=90, max_side=None):
    """Convert (and optionally shrink, keeping the aspect ratio) an image to JPEG."""
    with _image().open(src) as im:
        if max_side:
            im.thumbnail((max_side, max_side))
        im.convert("RGB").save(dst, "JPEG", quality=quality, optimize=True)
    return dst


def small_rgb(path, max_side=96):
    """The image shrunk to `max_side` px on its longest side, as a flat list of (r, g, b)."""
    with _image().open(path) as im:
        im.thumbnail((max_side, max_side))
        data = im.convert("RGB").tobytes()
    return [(data[i], data[i + 1], data[i + 2]) for i in range(0, len(data), 3)]
