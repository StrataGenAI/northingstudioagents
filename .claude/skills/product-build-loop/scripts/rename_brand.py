#!/usr/bin/env python3
"""Rename the brand across the whole project: plan, specs, brand kit, builds, files.

The brand name is not one constant. Measured on this project it was 135
occurrences across 25 files, plus 6 shipped filenames — planning documents and
build sources alike. Renaming by hand is how a catalogue ends up half-renamed,
so this does it in one auditable pass and logs every change.

It replaces four forms, because the name appears in four shapes:

    "Quiet Compass"   prose, titles, listing copy
    "QUIET COMPASS"   mono kickers and running heads
    "QuietCompass"    file names
    "quietcompass"    handles, domains, e-mail

Dry run by default. Nothing is written without --apply.

    rename_brand.py --from "Quiet Compass" --to "Oldrmonk"
    rename_brand.py --from "Quiet Compass" --to "Oldrmonk" --apply

IMPORTANT: renaming a PDF's *file* does not change the brand printed inside it.
Every edition must be rebuilt afterwards; the script prints the commands. The
`--source` gate in verify_pdf.py will fail any PDF left stale.
"""
import argparse
import datetime
import os
import sys

# Where the brand name legitimately lives. dist/ PDFs are binary and get rebuilt,
# never edited; fonts and licences are third-party and must not be touched.
ROOTS = ["Product Plans", "Products"]
TEXT_EXT = {".md", ".html", ".htm", ".css", ".svg", ".txt", ".py"}

# NEVER rewrite the audit trail. `qa/*.json` are gate measurements of one specific
# build; `BUILD-LOG.md` and `critique/` are the record of what was built and what
# was found, and the loop protocol forbids rewriting earlier entries. A log
# carrying the new name beside numbers measured from files called the old one is
# a false record - exactly what the rest of this pipeline exists to prevent.
# Those files describe history; history keeps the name it had. `_smoke` is a
# regression fixture, not a product.
SKIP_DIRS = {"_assets/fonts", "dist/licences", "/qa", "/critique", "_smoke",
             ".git", "node_modules", "__pycache__"}
SKIP_FILES = {"BUILD-LOG.md", "SIGNOFF.md"}


def variants(name, handle=None):
    """The four shapes a brand name takes, longest first so they match cleanly."""
    plain = " ".join(name.split())
    joined = handle or plain.replace(" ", "")
    return [
        (plain, None),                       # Quiet Compass
        (plain.upper(), "upper"),            # QUIET COMPASS
        (joined, "joined"),                  # QuietCompass
        (joined.lower(), "lower"),           # quietcompass
    ]


def mapping(old, new, old_handle, new_handle):
    """old string -> new string, ordered so longer forms are replaced first."""
    o = variants(old, old_handle)
    n = variants(new, new_handle)
    pairs = []
    for (o_s, kind), (n_s, _) in zip(o, n):
        if o_s and o_s != n_s:
            pairs.append((o_s, n_s, kind or "plain"))
    # Longest first: "QUIET COMPASS" must not be half-eaten by "QuietCompass".
    return sorted(pairs, key=lambda p: -len(p[0]))


def walk(roots):
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            rel = dirpath.replace(os.sep, "/")
            if any(skip in rel for skip in SKIP_DIRS):
                dirnames[:] = []
                continue
            for fn in filenames:
                if fn in SKIP_FILES:
                    continue
                if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                    yield os.path.join(dirpath, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="old", required=True, help='e.g. "Quiet Compass"')
    ap.add_argument("--to", dest="new", required=True, help='e.g. "Oldrmonk"')
    ap.add_argument("--old-handle", help="file-name form of the old name (default: no spaces)")
    ap.add_argument("--handle", help="file-name form of the new name (default: no spaces)")
    ap.add_argument("--apply", action="store_true", help="write the changes")
    ap.add_argument("--root", action="append", default=[], help="override the scan roots")
    a = ap.parse_args()

    roots = a.root or ROOTS
    pairs = mapping(a.old, a.new, a.old_handle, a.handle)
    if not pairs:
        sys.exit("old and new names are the same")

    print(f"{'APPLYING' if a.apply else 'DRY RUN'} — replacing:")
    for o, n, kind in pairs:
        print(f"    {kind:7s} {o!r} -> {n!r}")
    print()

    log, total, touched = [], 0, 0
    for path in walk(roots):
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        new_text, counts = text, {}
        for o, n, kind in pairs:
            c = new_text.count(o)
            if c:
                counts[o] = c
                new_text = new_text.replace(o, n)
        if not counts:
            continue
        touched += 1
        n_here = sum(counts.values())
        total += n_here
        print(f"  {n_here:4d}  {path}")
        for o, c in counts.items():
            log.append(f"{path}\t{o}\t{c}")
        if a.apply:
            open(path, "w", encoding="utf-8").write(new_text)

    # Files whose *names* carry the brand (the shipped PDFs, mainly).
    renames = []
    old_joined = (a.old_handle or a.old.replace(" ", ""))
    new_joined = (a.handle or a.new.replace(" ", ""))
    for root in roots:
        for dirpath, _dirnames, filenames in os.walk(root):
            rel = dirpath.replace(os.sep, "/")
            if any(skip in rel for skip in SKIP_DIRS):
                continue          # qa renders and critique artefacts belong to the old build
            for fn in filenames:
                if old_joined in fn:
                    renames.append((os.path.join(dirpath, fn),
                                    os.path.join(dirpath, fn.replace(old_joined, new_joined))))

    if renames:
        print(f"\n  {len(renames)} file name(s) to rename:")
        for src, dst in renames:
            print(f"    {os.path.basename(src)}  ->  {os.path.basename(dst)}")
            if a.apply:
                os.rename(src, dst)

    print(f"\n{total} occurrence(s) in {touched} file(s); {len(renames)} file(s) renamed.")

    # Some documents carry live copy AND a historical record in the same file.
    # brand-kit.md holds the palette and voice (live, must be renamed) beside the
    # conflict-screen table and changelog (history, must NOT be). A blanket
    # replace turns that table into fabricated evidence: it ends up attributing a
    # screen run against the OLD name to the NEW one. These cannot simply be
    # excluded - that would leave their live half stale - so they are flagged for
    # a human to read afterwards.
    mixed = ("brand-kit.md", "new-copy.md", "page-ledger.md", "README.txt")
    flagged = sorted({line.split("\t")[0] for line in log
                      if os.path.basename(line.split("\t")[0]) in mixed})
    if flagged:
        print("\nREAD THESE BY HAND — they mix live copy with a historical record,")
        print("and the replace above may have rewritten history into a false claim:")
        for f in flagged:
            print(f"    {f}")

    if a.apply:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        logfile = f"rename-{stamp}.log"
        with open(logfile, "w", encoding="utf-8") as fh:
            fh.write(f"# {a.old} -> {a.new}  ({stamp})\n")
            fh.write("\n".join(log) + "\n")
            for src, dst in renames:
                fh.write(f"RENAME\t{src}\t{dst}\n")
        print(f"wrote {logfile}")
        print("\nNOW REBUILD EVERY EDITION. Renaming a PDF does not change the brand")
        print("printed inside it, and the file you just renamed still says the old name:")
        for dirpath, _d, filenames in os.walk("Products"):
            for fn in sorted(filenames):
                if fn in ("a4.html", "letter.html", "tablet.html"):
                    size = {"a4.html": "a4", "letter.html": "letter", "tablet.html": "tablet"}[fn]
                    print(f"    build_pdf.py \"{os.path.join(dirpath, fn)}\" "
                          f"-o \"<dist>/..._{size.capitalize()}.pdf\" --size {size}")
        print("\nThen re-run verify_pdf.py with --source for each edition; it fails any")
        print("PDF older than its sources, which is exactly what a half-done rename leaves.")
    else:
        print("\nNothing written. Re-run with --apply once the name is settled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
