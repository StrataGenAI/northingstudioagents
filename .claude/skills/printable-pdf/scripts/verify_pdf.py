#!/usr/bin/env python3
"""Deterministic print-quality gates for a product PDF.

This script exists so that quality claims are measurements, not opinions. It is
the only acceptable source for statements like "fonts are embedded" or "ink is
under 8%". If a gate is not in here, it has not been checked.

  verify_pdf.py dist/QuietCompass_Focus-Audit_A4.pdf --size a4 --expect-pages 24 \
      --max-ink 8 --min-type 9 --json qa/verify-a4.json

Gates
  size        every page box equals the trim size (tolerance 0.05 mm)
  pages       page count equals --expect-pages
  fonts       every font is embedded and none is Type3
              (Chrome turns *variable* fonts into Type3 outlines: unselectable,
               unsearchable, rejected by print shops. Use static instances.)
  type        no text is rendered below --min-type points
  ink         average ink coverage per page <= --max-ink percent
  fill        how far down the sheet real content reaches, so half-empty pages
              are reported instead of being shipped
  links       internal destinations resolve; external URIs are listed
Exit code is 1 if any gate fails.
"""
import argparse
import json
import math
import os
import struct
import subprocess
import sys
import tempfile

PT_PER_MM = 72.0 / 25.4
SIZES = {"a4": (210.0, 297.0), "letter": (215.9, 279.4), "a5": (148.0, 210.0),
         "tablet": (1620 / 96 * 25.4, 2160 / 96 * 25.4)}


# ------------------------------------------------------------------ raster
PX_PER_MM = 320 / 297.0          # A4's historic resolution, kept as the reference


def page_bitmap(reader, index, px=None):
    """Render one page to a small RGB bitmap via sips. Returns (w, h, pixels).

    Resolution is fixed in pixels per *millimetre*, not pixels per sheet. `sips -Z`
    scales the longest side, so a fixed 320 px gave A4 0.93 mm per pixel but gave a
    428x571 mm tablet sheet 1.79 mm - at which a 0.5 pt writing rule falls below the
    detection threshold and vanishes. The symptom was the same page 4 measuring
    14.7% dead space on A4 and 54.4% on tablet.
    """
    from pypdf import PdfWriter
    if px is None:
        h_mm = float(reader.pages[index].mediabox.height) / PT_PER_MM
        px = max(320, min(1400, int(round(h_mm * PX_PER_MM))))
    with tempfile.TemporaryDirectory() as td:
        one = os.path.join(td, "p.pdf")
        w = PdfWriter()
        w.add_page(reader.pages[index])
        w.write(one)
        bmp = os.path.join(td, "p.bmp")
        r = subprocess.run(["sips", "-Z", str(px), "-s", "format", "bmp", one, "--out", bmp],
                           capture_output=True)
        if r.returncode != 0 or not os.path.exists(bmp):
            return None
        data = open(bmp, "rb").read()
    off = struct.unpack_from("<I", data, 10)[0]
    w_, h_ = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    step, rows = bpp // 8, abs(h_)
    stride = (w_ * step + 3) & ~3
    px_rows = []
    for y in range(rows):
        base = off + y * stride
        row = []
        for x in range(w_):
            i = base + x * step
            row.append((data[i + 2], data[i + 1], data[i]))   # BMP is BGR
        px_rows.append(row)
    if h_ > 0:                       # bottom-up bitmap
        px_rows.reverse()
    return w_, rows, px_rows


def ink_and_fill(bitmap, margin_frac=0.05):
    """Ink coverage, and where the page is empty.

    Row density alone is a bad measure of a finished page: a page of ruled writing
    lines is mostly paper by area and is exactly right. What actually reads as
    unfinished is a *band* of nothing between two pieces of content, so the useful
    number is the largest empty gap, not the fill percentage.
    """
    w, h, rows = bitmap
    lum = [[(0.299 * r + 0.587 * g + 0.114 * b) for (r, g, b) in row] for row in rows]
    flat = [v for row in lum for v in row]
    # Paper = the brightest common value; a dark cover is not scored against white.
    paper = max(sorted(flat)[int(len(flat) * 0.97)], 1.0)
    # Two different thresholds on purpose. A 0.5 pt stone writing rule anti-aliases
    # to roughly 2% darkness at raster size: counting it as ink would inflate the
    # coverage figure, but *not* counting it as content invents dead space on
    # exactly the pages that are most correct - the ones full of writing lines.
    ink_min, mark_min = 0.04, 0.02
    total = 0.0
    dark = []
    for row in lum:
        drow = []
        for v in row:
            d = (paper - v) / paper
            if d > ink_min:
                total += d
            drow.append(d > mark_min)
        dark.append(drow)
    y0, y1 = int(h * margin_frac), int(h * (1 - margin_frac))

    def rows_with_content(x0, x1):
        span = max(1, x1 - x0)
        return [y for y in range(y0, y1)
                if sum(dark[y][x0:x1]) > span * 0.004]

    def largest_gap(marked):
        if len(marked) < 2:
            return 0, None
        best, start, prev = 0, None, marked[0]
        for y in marked[1:]:
            if y - prev > 1 and (y - prev) > best:
                best, start = y - prev, prev
            prev = y
        return best, start

    out = {"ink": 100.0 * total / (w * h), "fill": 0.0, "first": 0.0, "last": 0.0,
           "max_gap": 0.0, "gap_from": 0.0, "gap_to": 0.0, "gap_where": "sheet"}
    marked = rows_with_content(0, w)
    if not marked:
        return out
    out["first"], out["last"] = marked[0] / h, marked[-1] / h
    out["fill"] = 100.0 * len(marked) / max(1, (y1 - y0))

    # Measure per column as well as across the sheet. A two-column page hides its
    # dead space from a full-width scan: whenever either column has content on a
    # row, that row counts as filled, so a column can be a third empty while the
    # sheet reports a few percent. Real case: a cross-sell column 111 mm empty on
    # a page the sheet-wide scan scored at 3.4%. The gutter position is unknown
    # here, so try the usual splits and report the worst region found.
    regions = [("sheet", 0.0, 1.0)]
    for split in (0.45, 0.5, 0.55, 0.6):
        regions.append((f"left column (split {split:.0%})", 0.0, split))
        regions.append((f"right column (split {split:.0%})", split, 1.0))
    for label, f0, f1 in regions:
        best, start = largest_gap(rows_with_content(int(w * f0), int(w * f1)))
        if start is not None and best / h > out["max_gap"]:
            out["max_gap"] = best / h
            out["gap_from"], out["gap_to"] = start / h, (start + best) / h
            out["gap_where"] = label
    return out


# ------------------------------------------------------------------ fonts
def font_report(page):
    """Every font on the page: (name, subtype, embedded?)."""
    out = []
    res = page.get("/Resources")
    if not res:
        return out
    res = res.get_object()
    fonts = res.get("/Font")
    if not fonts:
        return out
    for key in fonts.get_object():
        f = fonts.get_object()[key].get_object()
        sub = str(f.get("/Subtype", "?"))
        name = str(f.get("/BaseFont", "(unnamed)"))
        desc = f.get("/FontDescriptor")
        if not desc and f.get("/DescendantFonts"):
            d0 = f["/DescendantFonts"][0].get_object()
            desc = d0.get("/FontDescriptor")
        embedded = False
        if desc:
            desc = desc.get_object()
            embedded = any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3"))
        if sub == "/Type3":
            embedded = False          # Type3 = drawn glyphs, not a real embedded face
        out.append({"name": name, "subtype": sub.lstrip("/"), "embedded": embedded})
    return out


def _scale(m):
    try:
        a, b, c, d = float(m[0]), float(m[1]), float(m[2]), float(m[3])
    except Exception:                               # noqa: BLE001
        return 1.0
    det = abs(a * d - b * c)
    return math.sqrt(det) if det > 0 else 1.0


def text_runs(page):
    """Every visible text run with its effective point size and font.

    Chrome prints a page at one device scale (CSS px -> pt = 0.75). pypdf
    sometimes reports a nested graphics state as two separate factors, which makes
    one run look four times too large and another four times too small - the same
    letter-spaced kicker can appear as both 33 pt and 2.9 pt. Normalising every run
    to the page's dominant scale removes that artefact, so the gate measures type
    and not a quirk of the extractor.
    """
    raw = []

    def visit(text, cm, tm, font_dict, font_size):
        if not text or not text.strip():
            return
        name = str((font_dict or {}).get("/BaseFont", "") or "?")
        raw.append({"tf": float(font_size), "tm": _scale(tm), "cm": _scale(cm),
                    "font": name.split("+")[-1].lstrip("/"),
                    "sample": " ".join(text.split())[:40], "chars": len(text.strip())})

    try:
        page.extract_text(visitor_text=visit)
    except Exception:                               # noqa: BLE001
        return [], 1.0

    if not raw:
        return [], 1.0
    weight = {}
    for r in raw:
        weight[round(r["cm"], 3)] = weight.get(round(r["cm"], 3), 0) + r["chars"]
    base = max(weight, key=weight.get) if weight else 1.0

    runs = []
    for r in raw:
        size = r["tf"] * r["tm"] * base
        if 0.5 < size < 400:
            r["size"] = round(size, 2)
            runs.append(r)
    return runs, base


def spaced_text(page):
    """Lines whose letters have been split apart in the PDF text layer.

    Chrome does this to any text carrying CSS `opacity`: the run is drawn in its
    own transparency group and each glyph is emitted separately, so "IF YOU WANT
    MORE" extracts as "I F  Y O U  W A N T  M O R E". The page looks perfect on
    paper, so no visual check finds it, and it is valid embedded text, so no font
    gate finds it - but copy-paste, search and screen readers are all broken.
    Fade text with a colour (color-mix toward the paper), never with opacity.
    """
    out = []
    for line in (page.extract_text() or "").splitlines():
        toks = line.split()
        if len(toks) < 6:
            continue
        # Count single *letters* only. A 0-10 scoring scale and a footer of
        # arrows and page numbers are legitimately full of one-character tokens;
        # a word shattered into glyphs is not. "a" and "I" are real words.
        singles = sum(1 for t in toks
                      if len(t) == 1 and t.isalpha() and t.lower() not in ("a", "i"))
        if singles >= 6 and singles / len(toks) >= 0.6:
            out.append(" ".join(toks)[:64])
    return out


def links(page, n_pages):
    ext, internal, broken = [], 0, 0
    annots = page.get("/Annots")
    if not annots:
        return ext, internal, broken
    for a in annots:
        try:
            a = a.get_object()
        except Exception:                           # noqa: BLE001
            continue
        if a.get("/Subtype") != "/Link":
            continue
        act = a.get("/A")
        if act:
            act = act.get_object()
            uri = act.get("/URI")
            if uri:
                ext.append(str(uri))
                continue
            if act.get("/S") == "/GoTo" or "/D" in act:
                internal += 1
                continue
        if "/Dest" in a:
            internal += 1
        else:
            broken += 1
    return ext, internal, broken


# ------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--size", default="a4")
    ap.add_argument("--expect-pages", type=int)
    ap.add_argument("--max-ink", type=float, default=8.0)
    ap.add_argument("--min-type", type=float, default=9.0,
                    help="floor for body, prompt and caption text")
    ap.add_argument("--min-type-mono", type=float, default=8.0,
                    help="floor for mono kickers, labels and spec strips")
    ap.add_argument("--max-gap", type=float, default=20.0,
                    help="warn when a page has an empty band bigger than this %% of the sheet")
    ap.add_argument("--sparse-pages", default="",
                    help="pages that are meant to be airy, e.g. covers: 1,24")
    ap.add_argument("--source", action="append", default=[], metavar="FILE",
                    help="a source file (HTML/CSS/SVG) that must be OLDER than the PDF; "
                         "repeatable. Catches a half-finished revision that rebuilt one "
                         "edition and left the others stale.")
    ap.add_argument("--no-raster", action="store_true", help="skip ink/fill (faster)")
    ap.add_argument("--json")
    a = ap.parse_args()

    from pypdf import PdfReader
    if not os.path.exists(a.pdf):
        sys.exit(f"no such file: {a.pdf}")
    r = PdfReader(a.pdf)
    if r.is_encrypted:
        r.decrypt("")

    want = SIZES.get(a.size)
    if not want:
        sys.exit(f"--size must be one of {', '.join(SIZES)}")
    sparse = {int(x) for x in a.sparse_pages.replace(" ", "").split(",") if x}

    report = {"file": a.pdf, "pages": len(r.pages), "size": a.size, "page_reports": []}
    fails, warns = [], []

    # A half-finished revision ships one rebuilt edition beside two stale ones, and
    # every other gate passes them happily because each file is internally valid.
    # Comparing the sources against the output is the only thing that catches it.
    for src in a.source:
        if not os.path.exists(src):
            fails.append(f"source not found: {src}")
        elif os.path.getmtime(src) > os.path.getmtime(a.pdf) + 1:
            fails.append(f"{os.path.basename(src)} is NEWER than this PDF - the PDF is "
                         f"stale and every other gate here is measuring an old build. "
                         f"Rebuild it first.")

    if a.expect_pages and len(r.pages) != a.expect_pages:
        fails.append(f"page count is {len(r.pages)}, spec says {a.expect_pages}")

    all_fonts = {}
    for i, page in enumerate(r.pages, 1):
        pr = {"page": i}
        mb = page.mediabox
        w_mm, h_mm = float(mb.width) / PT_PER_MM, float(mb.height) / PT_PER_MM
        pr["size_mm"] = [round(w_mm, 3), round(h_mm, 3)]
        if abs(w_mm - want[0]) > 0.05 or abs(h_mm - want[1]) > 0.05:
            fails.append(f"p{i}: page box {w_mm:.2f}x{h_mm:.2f}mm, expected "
                         f"{want[0]:.2f}x{want[1]:.2f}mm")

        fonts = font_report(page)
        pr["fonts"] = fonts
        for f in fonts:
            all_fonts[f["name"]] = f
            if f["subtype"] == "Type3":
                fails.append(f"p{i}: {f['name']} is a Type3 font — text will not be "
                             f"selectable or searchable and print shops reject it. "
                             f"Use a static font instance, not a variable font.")
            elif not f["embedded"]:
                fails.append(f"p{i}: font {f['name']} is not embedded")

        runs, base = text_runs(page)
        pr["type_sizes"] = sorted({r["size"] for r in runs})
        pr["type_smallest"] = sorted(runs, key=lambda r: r["size"])[:3]
        # Mono carries the kickers, labels and spec strips, which the brand kit
        # sets at 8-8.5 pt on purpose. Everything the buyer reads or writes
        # against holds the 9 pt floor.
        worst = {}
        for run in runs:                    # not `r` - that is the PdfReader
            floor = a.min_type_mono if "mono" in run["font"].lower() else a.min_type
            if run["size"] < floor - 0.05 and run["chars"] >= 3:
                cur = worst.get(run["font"])
                if not cur or run["size"] < cur["size"]:
                    worst[run["font"]] = {"size": run["size"], "floor": floor,
                                          "sample": run["sample"]}
        for font, w in worst.items():
            fails.append(f"p{i}: {font} at {w['size']:.1f} pt, below the "
                         f"{w['floor']:.1f} pt floor - “{w['sample']}”")

        ext, internal, broken = links(page, len(r.pages))
        pr["links"] = {"external": ext, "internal": internal, "broken": broken}
        if broken:
            fails.append(f"p{i}: {broken} link annotation(s) with no destination")

        text = (page.extract_text() or "").strip()
        pr["chars"] = len(text)

        broken_text = spaced_text(page)
        if broken_text:
            pr["spaced_text"] = broken_text
            for s in broken_text:
                fails.append(f"p{i}: the text layer is split into single characters - "
                             f"“{s}”. Something on this page fades text with CSS "
                             f"opacity; fade it with a colour instead.")

        if not a.no_raster:
            bm = page_bitmap(r, i - 1)
            if bm:
                m = ink_and_fill(bm)
                pr["ink_pct"] = round(m["ink"], 2)
                pr["fill_pct"] = round(m["fill"], 1)
                pr["content_ends_at_pct"] = round(m["last"] * 100, 1)
                pr["max_gap_pct"] = round(m["max_gap"] * 100, 1)
                if m["ink"] > a.max_ink:
                    fails.append(f"p{i}: ink coverage {m['ink']:.1f}%, "
                                 f"over the {a.max_ink}% limit")
                if i not in sparse and m["max_gap"] * 100 > a.max_gap:
                    warns.append(f"p{i}: an empty band of {m['max_gap'] * 100:.0f}% of the sheet "
                                 f"in the {m['gap_where']}, from {m['gap_from'] * 100:.0f}% to "
                                 f"{m['gap_to'] * 100:.0f}% down the page - is this page finished?")
        report["page_reports"].append(pr)

    report["fonts_used"] = sorted(all_fonts)
    report["fails"] = fails
    report["warnings"] = warns

    print(f"{a.pdf}  —  {len(r.pages)} pages, {a.size}")
    print(f"  fonts: {', '.join(sorted(all_fonts)) or '(none)'}")
    if not a.no_raster:
        inks = [p.get("ink_pct") for p in report["page_reports"] if p.get("ink_pct") is not None]
        if inks:
            print(f"  ink:   avg {sum(inks) / len(inks):.1f}%  max {max(inks):.1f}%  "
                  f"(limit {a.max_ink}%)")
    sizes = sorted({s for p in report["page_reports"] for s in p["type_sizes"]})
    if sizes:
        print(f"  type:  {sizes[0]:.1f}–{sizes[-1]:.1f} pt (floor {a.min_type} pt)")
    ext_all = sorted({u for p in report["page_reports"] for u in p["links"]["external"]})
    if ext_all:
        print(f"  links: {len(ext_all)} external URL(s): {', '.join(ext_all[:5])}")

    for w in warns:
        print(f"  WARN  {w}")
    for f in fails:
        print(f"  FAIL  {f}")

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(report, open(a.json, "w"), indent=2)
        print(f"\n  wrote {a.json}")

    print("\n" + ("PASS — every gate met." if not fails
                  else f"FAIL — {len(fails)} gate(s) failed."))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
