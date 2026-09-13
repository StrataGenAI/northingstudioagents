#!/usr/bin/env python3
"""Download the brand's OFL fonts as STATIC instances, with licences and a manifest.

Why static: Chrome renders *variable* fonts into Type3 outlines when it prints to
PDF. Type3 text cannot be selected, searched or reliably reproduced by a print
shop. verify_pdf.py fails any build that contains one.

Why this particular fetch: the Google Fonts CSS API serves a different file per
user agent. A modern browser gets a variable woff2 (and, per weight, tiny
unicode-range subsets); an ancient IE agent gets EOT, which Chrome cannot use.
The Chrome-30 agent below gets the **full static face as WOFF** — one file per
weight and style, which is exactly what a print build needs.

The manifest records the resolved URL, SHA-256, byte count, date and PostScript
name for every file. It is the evidence behind the licence claim — never state
that a font is licensed from memory; read it from here. The PostScript name is
what a PDF embeds, so verify_pdf.py --fonts uses it to tell the brand's own face
from a substitute.

Usage:
  fetch_fonts.py --dir brands/quiet-compass/fonts                  # fetch missing, record names
  fetch_fonts.py --dir ... --check                                 # verify files against the manifest
  fetch_fonts.py --dir ... --force                                 # re-download everything
  fetch_fonts.py --dir ... --install-system                        # install the faces for fontconfig
  fetch_fonts.py --dir ... --check --check-system                  # ...and verify fontconfig sees them
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

# Old enough to be served complete static WOFF, new enough to be served WOFF at all.
FETCH_UA = ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36")
CSS_API = "https://fonts.googleapis.com/css2?family="
REPO = "https://raw.githubusercontent.com/google/fonts/main/ofl"
EXT = ".woff"
SYSTEM_DIR = os.path.expanduser("~/.local/share/fonts/northing")

# local file stem -> (css2 query, css family name, weight, style)
FACES = {
    "Fraunces-Regular":     ("Fraunces:opsz,wght@72,400",         "Fraunces", 400, "normal"),
    "Fraunces-SemiBold":    ("Fraunces:opsz,wght@72,600",         "Fraunces", 600, "normal"),
    "Fraunces-Display":     ("Fraunces:opsz,wght@144,600",        "Fraunces Display", 600, "normal"),
    "Fraunces-Italic":      ("Fraunces:ital,opsz,wght@1,72,400",  "Fraunces", 400, "italic"),
    "SourceSans3-Regular":  ("Source+Sans+3:wght@400",            "Source Sans 3", 400, "normal"),
    "SourceSans3-SemiBold": ("Source+Sans+3:wght@600",            "Source Sans 3", 600, "normal"),
    "SourceSans3-Italic":   ("Source+Sans+3:ital,wght@1,400",     "Source Sans 3", 400, "italic"),
    "IBMPlexMono-Regular":  ("IBM+Plex+Mono:wght@400",            "IBM Plex Mono", 400, "normal"),
    "IBMPlexMono-SemiBold": ("IBM+Plex+Mono:wght@600",            "IBM Plex Mono", 600, "normal"),
}
LICENCES = {"OFL-Fraunces.txt": f"{REPO}/fraunces/OFL.txt",
            "OFL-SourceSans3.txt": f"{REPO}/sourcesans3/OFL.txt",
            "OFL-IBMPlexMono.txt": f"{REPO}/ibmplexmono/OFL.txt"}
FONT_MAGIC = (b"wOFF", b"wOF2", b"\x00\x01\x00\x00", b"true", b"OTTO")


def curl(url, ua=None, binary=True):
    """Python's urllib may have no CA bundle; curl does."""
    cmd = ["curl", "-sSL", "--fail", "--max-time", "60"]
    if ua:
        cmd += ["-H", f"User-Agent: {ua}"]
    cmd.append(url)
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode()[:200].strip() or f"curl exit {p.returncode}")
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def resolve(query):
    """Ask the CSS API for one face and return the font URL it offers."""
    css = curl(CSS_API + query, ua=FETCH_UA, binary=False)
    urls = re.findall(r"src:\s*url\((https://[^)]+)\)", css)
    if not urls:
        raise RuntimeError("no src url in the CSS response")
    return urls[0]


def postscript_name(data):
    """The PostScript name (name ID 6) of a WOFF, TTF or OTF font file."""
    tables = {}
    if data[:4] == b"wOFF":
        for i in range(struct.unpack_from(">H", data, 12)[0]):
            tag, off, comp, orig, _ = struct.unpack_from(">4sIIII", data, 44 + 20 * i)
            tables[tag] = (off, comp, orig)
        if b"name" not in tables:
            raise ValueError("no name table")
        off, comp, orig = tables[b"name"]
        name = zlib.decompress(data[off:off + comp]) if comp < orig else data[off:off + comp]
    elif data[:4] in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
        for i in range(struct.unpack_from(">H", data, 4)[0]):
            tag, _, off, length = struct.unpack_from(">4sIII", data, 12 + 16 * i)
            tables[tag] = (off, length)
        if b"name" not in tables:
            raise ValueError("no name table")
        off, length = tables[b"name"]
        name = data[off:off + length]
    else:
        raise ValueError(f"cannot read names from a {data[:4]!r} file (WOFF2 needs brotli)")
    _, count, strings = struct.unpack_from(">HHH", name, 0)
    found = {}
    for i in range(count):
        pid, _, _, nid, length, off = struct.unpack_from(">HHHHHH", name, 6 + 12 * i)
        if nid == 6:
            raw = name[strings + off: strings + off + length]
            found[pid] = raw.decode("utf-16-be") if pid in (0, 3) else raw.decode("latin-1")
    for pid in (3, 1, 0):
        if found.get(pid, "").strip():
            return found[pid].strip()
    raise ValueError("font has no PostScript name (name ID 6)")


def fonts_css(manifest, path):
    """Generate the @font-face sheet the products link to."""
    out = ["/* Generated by fetch_fonts.py - do not edit by hand.",
           " * Static instances only: variable fonts become Type3 in Chrome's PDF output.",
           " */", ""]
    for stem, rec in sorted(manifest["fonts"].items()):
        out += ["@font-face {",
                f"  font-family: \"{rec['css_family']}\";",
                f"  font-style: {rec['style']};",
                f"  font-weight: {rec['weight']};",
                f"  src: url(\"{stem}{EXT}\") format(\"woff\");",
                "  font-display: block;",
                "}", ""]
    open(path, "w").write("\n".join(out))


def licence_sheet(manifest, path):
    fams = sorted({r["css_family"].replace(" Display", "") for r in manifest["fonts"].values()})
    sheet = ["# Font licences", "",
             "Every font in this product is licensed under the **SIL Open Font License 1.1**,",
             "which permits commercial use and embedding in PDFs. The font files are never",
             "sold or redistributed on their own. The full licence text sits beside this file.", ""]
    for f in fams:
        dates = [r["date"] for r in manifest["fonts"].values() if r["css_family"].startswith(f)]
        sheet.append(f"- **{f}** - OFL 1.1 - fetched {min(dates)} from Google Fonts")
    sheet += ["", "SHA-256 of every file: `manifest.json`."]
    open(path, "w").write("\n".join(sheet) + "\n")


def fc_tool(name):
    """System fontconfig first: the browser links the system library, not Homebrew's."""
    for cand in (f"/usr/bin/{name}", shutil.which(name)):
        if cand and os.path.exists(cand):
            return cand
    return None


def install_system(font_dir, manifest):
    """Copy the faces where fontconfig looks, refreshing only what changed."""
    fails = []
    os.makedirs(SYSTEM_DIR, exist_ok=True)
    changed = 0
    for stem in FACES:
        src = os.path.join(font_dir, stem + EXT)
        dst = os.path.join(SYSTEM_DIR, stem + EXT)
        if not os.path.exists(src):
            fails.append(f"{stem}{EXT}: not in {font_dir}")
            continue
        if not os.path.exists(dst) or open(dst, "rb").read() != open(src, "rb").read():
            shutil.copyfile(src, dst)
            changed += 1
    fc_cache = fc_tool("fc-cache")
    if not fc_cache:
        fails.append("fc-cache not found (apt package fontconfig)")
    elif changed:
        subprocess.run([fc_cache, "-f", SYSTEM_DIR], capture_output=True)
    print(f"  system fonts: {changed} face(s) updated in {SYSTEM_DIR}")
    return fails


def check_system():
    fails = []
    fc_list = fc_tool("fc-list")
    if not fc_list:
        return ["fc-list not found (apt package fontconfig)"]
    listed = subprocess.run([fc_list, "--format", "%{file}\n"], capture_output=True,
                            text=True).stdout.splitlines()
    for stem in FACES:
        if os.path.join(SYSTEM_DIR, stem + EXT) not in listed:
            fails.append(f"{stem}{EXT}: fontconfig does not list it - run --install-system")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="brands/quiet-compass/fonts")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--install-system", action="store_true",
                    help=f"copy the faces into {SYSTEM_DIR} and refresh fontconfig")
    ap.add_argument("--check-system", action="store_true",
                    help="with --check: also verify fontconfig lists every face")
    a = ap.parse_args()

    os.makedirs(a.dir, exist_ok=True)
    mpath = os.path.join(a.dir, "manifest.json")
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    manifest.setdefault("fonts", {})
    manifest.setdefault("licences", {})

    fails, got = [], []

    if a.install_system:
        fails += install_system(a.dir, manifest)
    elif a.check:
        for stem in FACES:
            rec = manifest["fonts"].get(stem)
            dest = os.path.join(a.dir, stem + EXT)
            if not rec:
                fails.append(f"{stem}: missing from the manifest")
            elif not os.path.exists(dest):
                fails.append(f"{stem}{EXT}: file missing")
            else:
                data = open(dest, "rb").read()
                if hashlib.sha256(data).hexdigest() != rec["sha256"]:
                    fails.append(f"{stem}{EXT}: sha256 changed - licence evidence broken")
                elif not rec.get("postscript_name"):
                    fails.append(f"{stem}: no PostScript name recorded - run without --check")
                elif postscript_name(data) != rec["postscript_name"]:
                    fails.append(f"{stem}: recorded PostScript name does not match the file")
        for name in LICENCES:
            if not os.path.exists(os.path.join(a.dir, name)):
                fails.append(f"{name}: licence text missing")
        if not os.path.exists(os.path.join(a.dir, "fonts.css")):
            fails.append("fonts.css: missing - products have nothing to link")
        if a.check_system:
            fails += check_system()
    else:
        for stem, (query, family, weight, style) in FACES.items():
            dest = os.path.join(a.dir, stem + EXT)
            if os.path.exists(dest) and stem in manifest["fonts"] and not a.force:
                rec = manifest["fonts"][stem]
                if not rec.get("postscript_name"):
                    try:
                        rec["postscript_name"] = postscript_name(open(dest, "rb").read())
                        print(f"  named {stem}{EXT} -> {rec['postscript_name']}")
                    except ValueError as e:
                        fails.append(f"{stem}: {e}")
                else:
                    print(f"  have  {stem}{EXT}")
                continue
            try:
                url = resolve(query)
                data = curl(url)
                if not data.startswith(FONT_MAGIC):
                    raise RuntimeError(f"not a font file (starts {data[:4]!r})")
                ps_name = postscript_name(data)
            except Exception as e:                      # noqa: BLE001
                fails.append(f"{stem}: {e}")
                continue
            open(dest, "wb").write(data)
            manifest["fonts"][stem] = {
                "css_family": family, "weight": weight, "style": style,
                "query": query, "url": url, "container": data[:4].decode("latin1"),
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                "date": datetime.date.today().isoformat(),
                "licence": "SIL Open Font License 1.1",
                "postscript_name": ps_name,
            }
            got.append(stem)
            print(f"  got   {stem}{EXT}  ({len(data):,} bytes, {ps_name})")

        for name, url in LICENCES.items():
            dest = os.path.join(a.dir, name)
            if os.path.exists(dest) and name in manifest["licences"] and not a.force:
                continue
            if os.path.exists(dest) and not a.force:
                # Already on disk from an earlier run: record it rather than
                # re-downloading, so the manifest is complete either way.
                data = open(dest, "rb").read()
                manifest["licences"][name] = {
                    "url": url, "sha256": hashlib.sha256(data).hexdigest(),
                    "date": datetime.date.fromtimestamp(os.path.getmtime(dest)).isoformat()}
                print(f"  kept  {name}")
                continue
            try:
                data = curl(url)
            except Exception as e:                      # noqa: BLE001
                fails.append(f"{name}: {e}")
                continue
            open(dest, "wb").write(data)
            manifest["licences"][name] = {
                "url": url, "sha256": hashlib.sha256(data).hexdigest(),
                "date": datetime.date.today().isoformat()}
            print(f"  got   {name}")

        if manifest["fonts"]:
            json.dump(manifest, open(mpath, "w"), indent=2, sort_keys=True)
            fonts_css(manifest, os.path.join(a.dir, "fonts.css"))
            licence_sheet(manifest, os.path.join(a.dir, "FONT-LICENCES.md"))

    if fails:
        print("\nFAIL", file=sys.stderr)
        for f in fails:
            print("  " + f, file=sys.stderr)
        return 1
    print(f"\nOK - {len(manifest['fonts'])} faces, {len(manifest['licences'])} licences in {a.dir}"
          + (f"; {len(got)} newly fetched" if got else "")
          + ("; fontconfig lists every face" if a.check_system else ""))
    if got:
        print("     fonts.css and FONT-LICENCES.md regenerated.")
        print("     Now prove it: render a page and check verify_pdf.py --fonts reports no substitute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
