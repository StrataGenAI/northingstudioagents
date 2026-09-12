#!/usr/bin/env python3
"""Markdown -> styled, print-ready PDF (A4) using headless Google Chrome.

Usage:
  md_to_pdf.py REPORT.md [-o REPORT.pdf] [--title T] [--subtitle S] [--author A] [--date D]
               [--no-cover] [--no-toc] [--css extra.css] [--max-image 1400] [--keep-html]

Markdown conventions it understands (see SKILL.md):
  <!-- pagebreak -->            force a new page
  > [!IDEA] / [!INSIGHT] / [!OPPORTUNITY] / [!WARNING] / [!NOTE] / [!TIP]   coloured callout boxes
  a paragraph of only images   laid out as an image gallery grid
  `#A3B18A`                     inline code that is a hex colour gets a colour swatch
Relative image paths are resolved from the markdown file's folder (paths with spaces are fine);
large local images are downscaled into a cache (macOS `sips`) so the PDF stays a sensible size.
"""
import argparse
import datetime
import hashlib
import html as htmllib
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

try:
    import markdown
except ImportError:
    sys.exit("Missing dependency: run `pip3 install markdown`")

HERE = os.path.dirname(os.path.abspath(__file__))
CSS_FILE = os.path.join(HERE, "..", "assets", "report.css")
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]
CALLOUTS = r"\[!(IDEA|INSIGHT|WARNING|NOTE|TIP|OPPORTUNITY)\]\s*"


def chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    sys.exit("No Chrome/Chromium/Edge/Brave found in /Applications")


def uri(path):
    return pathlib.Path(path).as_uri()


def image_size(path):
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path], capture_output=True, text=True)
    nums = re.findall(r"pixel(?:Width|Height):\s*(\d+)", r.stdout)
    return tuple(int(n) for n in nums) if len(nums) == 2 else (0, 0)


def local_image(src, base_dir, cache_dir, max_px):
    if re.match(r"^(https?:|data:|file:)", src):
        return src
    path = os.path.normpath(os.path.join(base_dir, unquote(htmllib.unescape(src))))
    if not os.path.exists(path):
        print(f"  warning: image not found: {src}", file=sys.stderr)
        return src
    if max_px and path.lower().endswith((".jpg", ".jpeg", ".png")) and max(image_size(path)) > max_px:
        os.makedirs(cache_dir, exist_ok=True)
        key = hashlib.md5(f"{path}{os.path.getmtime(path)}{max_px}".encode()).hexdigest()[:12]
        small = os.path.join(cache_dir, f"{key}.jpg")
        if not os.path.exists(small):
            subprocess.run(["sips", "-Z", str(max_px), "-s", "format", "jpeg", "-s", "formatOptions", "82",
                            path, "--out", small], capture_output=True)
        if os.path.exists(small):
            path = small
    return uri(path)


def callout(m):
    kind = m.group(1).lower()
    return f'<blockquote class="callout {kind}"><p><strong class="callout-label">{kind.upper()}</strong> '


LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s")
QUOTE = re.compile(r"^((?:>\s?)*)")


def normalize_lists(text):
    """Make GitHub-style lists render in Python-Markdown: a blank line before every list
    (also inside > quotes/callouts) and 1-3 space nested items re-indented to 4 spaces."""
    out, in_code = [], False
    for line in text.split("\n"):
        if line.lstrip("> ").startswith("```"):
            in_code = not in_code
        if not in_code:
            quote = QUOTE.match(line).group(1)
            body = line[len(quote):]
            m = LIST_ITEM.match(body)
            if m and 0 < len(m.group(1)) < 4:
                body = "    " + body.lstrip()
                m = LIST_ITEM.match(body)
            if m and not m.group(1) and out:
                prev = out[-1]
                prev_body = prev[len(QUOTE.match(prev).group(1)):]
                if prev_body.strip() and not LIST_ITEM.match(prev_body) and not prev_body.startswith((" ", "\t")):
                    out.append(quote.rstrip())
            line = quote + body
        out.append(line)
    return "\n".join(out)


def postprocess(body, base_dir, cache_dir, max_px):
    body = re.sub(r'<img([^>]*?)src="([^"]+)"',
                  lambda m: f'<img{m.group(1)}src="{htmllib.escape(local_image(m.group(2), base_dir, cache_dir, max_px))}"',
                  body)

    def gallery(m):
        inner = m.group(1)
        if len(re.findall(r"<img", inner)) > 1 and not re.sub(r"<img[^>]*>|<br\s*/?>|\s", "", inner):
            return f'<div class="gallery">{inner}</div>'
        return m.group(0)
    body = re.sub(r"<p>((?:\s*<img[^>]*>\s*(?:<br\s*/?>)?)+)</p>", gallery, body)

    def figure(m):
        img = m.group(1)
        alt = re.search(r'alt="([^"]*)"', img)
        cap = f"<figcaption>{alt.group(1)}</figcaption>" if alt and alt.group(1) else ""
        return f"<figure>{img}{cap}</figure>"
    body = re.sub(r"<p>\s*(<img[^>]*>)\s*</p>", figure, body)

    body = re.sub(r"<!--\s*pagebreak\s*-->", '<div class="page-break"></div>', body)
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    body = re.sub(r"<code>(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})</code>",
                  r'<span class="swatch" style="background:\1"></span><code>\1</code>', body)
    # consecutive "> [!X]" blocks get merged into one blockquote by Markdown; split them back apart
    body = re.sub(r"</p>\s*<p>" + CALLOUTS, lambda m: "</p></blockquote>" + callout(m), body, flags=re.I)
    body = re.sub(r"<blockquote>\s*<p>" + CALLOUTS, callout, body, flags=re.I)
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown_file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--title"); ap.add_argument("--subtitle"); ap.add_argument("--author")
    ap.add_argument("--date", default=datetime.date.today().strftime("%d %B %Y"))
    ap.add_argument("--no-cover", action="store_true"); ap.add_argument("--no-toc", action="store_true")
    ap.add_argument("--css"); ap.add_argument("--max-image", type=int, default=1400)
    ap.add_argument("--keep-html", action="store_true")
    a = ap.parse_args()

    src = os.path.abspath(a.markdown_file)
    base_dir = os.path.dirname(src)
    out = os.path.abspath(a.output or os.path.splitext(src)[0] + ".pdf")
    text = open(src, encoding="utf-8").read()

    title = a.title
    m = re.match(r"\s*#\s+(.+)\n", text)
    if m and not a.no_cover:
        title = title or m.group(1).strip()
        text = text[m.end():]  # the cover shows the title instead
    title = title or os.path.splitext(os.path.basename(src))[0]

    md = markdown.Markdown(extensions=["extra", "sane_lists", "smarty", "toc"],
                           extension_configs={"toc": {"toc_depth": "1-3", "permalink": False}})
    body = md.convert(normalize_lists(text))
    cache_dir = os.path.join(tempfile.gettempdir(), "md_to_pdf-cache")  # keeps report folders clean
    body = postprocess(body, base_dir, cache_dir, a.max_image)

    css = open(CSS_FILE, encoding="utf-8").read()
    if a.css:
        css += "\n" + open(a.css, encoding="utf-8").read()
    esc = htmllib.escape
    cover = "" if a.no_cover else f"""
<section class="cover"><div class="cover-band"></div><div class="cover-inner">
  <div class="cover-kicker">Research report</div>
  <h1 class="cover-title">{esc(title)}</h1>
  {f'<p class="cover-sub">{esc(a.subtitle)}</p>' if a.subtitle else ''}
  <p class="cover-meta">{esc(a.author) + ' &middot; ' if a.author else ''}{esc(a.date)}</p>
</div></section>"""
    toc = "" if a.no_toc or not md.toc_tokens else f'<section class="toc"><h2>Contents</h2>{md.toc}</section>'
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>{esc(title)}</title>
<style>{css}</style></head><body>{cover}{toc}<main>{body}</main></body></html>"""

    html_path = os.path.splitext(out)[0] + ".print.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--run-all-compositor-stages-before-draw",
                    "--virtual-time-budget=20000", f"--print-to-pdf={out}", uri(html_path)],
                   capture_output=True)
    if not a.keep_html:
        os.remove(html_path)
    if not os.path.exists(out):
        sys.exit("Chrome did not produce a PDF")
    pages = "?"
    try:
        import pypdf
        pages = len(pypdf.PdfReader(out).pages)
    except Exception:
        pass
    print(f"PDF written: {out}  ({pages} pages, {os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
