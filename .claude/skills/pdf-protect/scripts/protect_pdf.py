#!/usr/bin/env python3
"""Lock a finished product PDF: no copying, no editing, printing still allowed.

Be honest about what this is. PDF permissions are enforced by the *reader*, not
by cryptography the buyer cannot bypass — the file opens without a password, so
anyone with the right tool can strip the flags. This raises the effort of casual
copy-paste theft and states our intent; it is not DRM and must never be sold as
"uncopyable". What it genuinely does:

  - blocks text/image copy-paste in every mainstream reader
  - blocks editing, page extraction and reassembly
  - keeps printing at full resolution (buyers bought a printable)
  - keeps annotation on for tablet editions, so GoodNotes/Notability still work
  - keeps the accessibility text path open, so screen readers work
    (--deny-accessibility turns that off; think hard before using it)

Usage:
  protect_pdf.py dist/Product_A4.pdf --edition print  --title "The Focus Audit" \
      --author "Quiet Compass" --owner-pass "$QC_OWNER_PASS"
  protect_pdf.py dist/Product_Tablet.pdf --edition tablet ...
  protect_pdf.py dist/Product_A4.pdf --verify-only
"""
import argparse
import datetime
import os
import secrets
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.constants import UserAccessPermissions as P

EDITIONS = {
    # printable: print freely, annotate on paper, copy nothing
    "print": P.PRINT | P.PRINT_TO_REPRESENTATION | P.EXTRACT_TEXT_AND_GRAPHICS,
    # tablet: same, plus annotation and form filling so notes apps work
    "tablet": (P.PRINT | P.PRINT_TO_REPRESENTATION | P.EXTRACT_TEXT_AND_GRAPHICS
               | P.ADD_OR_MODIFY | P.FILL_FORM_FIELDS),
}


def describe(flags):
    on = [n for n in ("PRINT", "PRINT_TO_REPRESENTATION", "MODIFY", "EXTRACT",
                      "EXTRACT_TEXT_AND_GRAPHICS", "ADD_OR_MODIFY",
                      "FILL_FORM_FIELDS", "ASSEMBLE_DOC")
          if getattr(P, n) & flags]
    return ", ".join(on) or "(nothing)"


def verify(path, owner_pass=None):
    r = PdfReader(path)
    print(f"{path}")
    print(f"  encrypted:  {r.is_encrypted}")
    if r.is_encrypted:
        if r.decrypt("") == 0 and owner_pass:
            r.decrypt(owner_pass)
        enc = getattr(r, "_encryption", None)
        if enc is not None:
            print(f"  permissions: {int(enc.P) & 0xFFF} -> {describe(int(enc.P))}")
    print(f"  pages:      {len(r.pages)}")
    md = r.metadata or {}
    for k in ("/Title", "/Author", "/Subject", "/Keywords"):
        if md.get(k):
            print(f"  {k[1:]:<11} {md[k]}")
    txt = r.pages[0].extract_text() or ""
    print(f"  page 1 text extractable with our key: {bool(txt.strip())}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--edition", choices=sorted(EDITIONS), default="print")
    ap.add_argument("--out", help="default: overwrite in place")
    ap.add_argument("--title")
    ap.add_argument("--author", default="Quiet Compass")
    ap.add_argument("--subject")
    ap.add_argument("--keywords")
    ap.add_argument("--owner-pass", default=os.environ.get("QC_OWNER_PASS"),
                    help="owner password; a random one is generated and printed if omitted")
    ap.add_argument("--deny-accessibility", action="store_true",
                    help="also block the screen-reader text path (not recommended)")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.pdf):
        sys.exit(f"no such file: {a.pdf}")
    if a.verify_only:
        return verify(a.pdf, a.owner_pass)

    src = PdfReader(a.pdf)
    if src.is_encrypted:
        sys.exit("already encrypted — protect the unprotected build, not this file.")
    n_before = len(src.pages)

    flags = EDITIONS[a.edition]
    if a.deny_accessibility:
        flags &= ~P.EXTRACT_TEXT_AND_GRAPHICS

    owner = a.owner_pass or secrets.token_urlsafe(18)
    generated = not a.owner_pass

    w = PdfWriter(clone_from=a.pdf)
    meta = {"/Producer": "Quiet Compass build pipeline",
            "/Creator": "Quiet Compass",
            "/ModDate": datetime.datetime.now().strftime("D:%Y%m%d%H%M%S")}
    if a.title:
        meta["/Title"] = a.title
    if a.author:
        meta["/Author"] = a.author
    if a.subject:
        meta["/Subject"] = a.subject
    if a.keywords:
        meta["/Keywords"] = a.keywords
    w.add_metadata(meta)

    # Empty user password: the file opens for everyone, the flags still apply.
    w.encrypt(user_password="", owner_password=owner,
              permissions_flag=flags, algorithm="AES-256")

    out = a.out or a.pdf
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    w.write(out)

    chk = PdfReader(out)
    ok_enc = chk.is_encrypted and chk.decrypt("") != 0
    ok_pages = len(chk.pages) == n_before
    print(f"{out}")
    print(f"  edition:     {a.edition}")
    print(f"  allowed:     {describe(flags)}")
    print(f"  denied:      copy/extract, editing, page assembly"
          + ("" if a.edition == "tablet" else ", annotation"))
    print(f"  opens without a password: {ok_enc}")
    print(f"  pages preserved: {ok_pages} ({len(chk.pages)})")
    if generated:
        print(f"\n  owner password (store it, you need it to edit this file later):\n    {owner}")
        print("  Tip: set QC_OWNER_PASS once and reuse it across the catalogue.")
    print("\n  Reminder: permissions are reader-enforced, not DRM. Never claim in "
          "listing copy that the file cannot be copied.")
    return 0 if (ok_enc and ok_pages) else 1


if __name__ == "__main__":
    sys.exit(main())
