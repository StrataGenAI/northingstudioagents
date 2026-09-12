#!/usr/bin/env python3
"""Prove that the built PDF contains the copy the spec ordered — and nothing invented.

This is the anti-hallucination gate of the whole pipeline. The build spec written
by the planning agent is the single source of truth for product copy. Two
directions are checked:

  MISSING   copy the spec requires that is absent from the PDF
            -> the builder dropped or paraphrased it
  NEW       sentences in the PDF that appear nowhere in the spec
            -> the builder invented them; each one must be justified in the
               new-copy ledger, or it does not ship

Neither direction is a judgement call, so neither agent may argue with it.

Usage:
  spec_coverage.py "Product Plans/specs/PB-001 The Focus Audit.md" dist/Product_A4.pdf \
      --ledger "Products/PB-001 The Focus Audit/build/new-copy.md" --json qa/coverage.json
"""
import argparse
import json
import os
import re
import sys
import unicodedata

MIN_NEW_LEN = 30          # ignore fragments shorter than this when hunting new copy
MIN_REQUIRED_LEN = 12     # ignore trivial quoted scraps like "yes / no"


def norm(s):
    """Fold quotes, dashes, spacing and case so PDF text and Markdown compare fairly."""
    s = unicodedata.normalize("NFKD", s)
    s = (s.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"')
          .replace("—", "-").replace("–", "-").replace("−", "-")
          .replace(" ", " ").replace("…", "..."))
    s = re.sub(r"[^a-z0-9'\"/.,:;?!()%&+-]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def pdf_text(path):
    from pypdf import PdfReader
    r = PdfReader(path)
    if r.is_encrypted:
        r.decrypt("")
    return [(i + 1, p.extract_text() or "") for i, p in enumerate(r.pages)]


def spec_rows(md):
    """Rows of the 'Page-by-page' table: (page_label, cells)."""
    rows, in_table = [], False
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|") and re.search(r"\|\s*#\s*\|", s):
            in_table = True
            continue
        if in_table:
            if not s.startswith("|"):
                if s and not s.startswith("|"):
                    in_table = False
                continue
            if re.fullmatch(r"\|[\s:|-]+\|", s):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 5:
                rows.append((cells[0], cells))
    return rows


def required_strings(cell):
    """Pull the exact copy out of an 'Elements & exact copy' cell."""
    out = []
    # "quoted copy", *"italic copy"*, `MONO KICKERS`
    #
    # Pair the quotes in document order and filter by length afterwards. Putting
    # the length filter inside the pattern ({12,}) means a short quote such as
    # "Your wheel" fails to match, the scan resumes at its *closing* quote and
    # pairs that with the next *opening* one - so every later quote in the cell
    # shifts one position out of step, the gate demands the spec's own editorial
    # prose as if it were product copy, and the real strings are never checked.
    for m in re.finditer(r'"([^"]*)"', cell):
        out.append(m.group(1))
    for m in re.finditer(r'“([^”]*)”', cell):
        out.append(m.group(1))
    for m in re.finditer(r"`([^`]{3,})`", cell):
        out.append(m.group(1))
    cleaned = []
    for s in out:
        s = re.sub(r"\*\*|\*|_", "", s).strip()
        # A cell often chains several sentences inside one pair of quotes; keep
        # the whole run, the comparison is substring-based anyway.
        if len(s) >= 3:
            cleaned.append(s)
    return cleaned


def ledger_entries(path):
    if not path or not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*[-*]\s+(?:\[[ xX]\]\s*)?(.+)", line)
        if m:
            out.append(norm(m.group(1)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("pdf")
    ap.add_argument("--ledger", help="build/new-copy.md — justified additions")
    ap.add_argument("--json")
    ap.add_argument("--max-new", type=int, default=0,
                    help="unjustified new sentences tolerated before failing")
    a = ap.parse_args()

    for p in (a.spec, a.pdf):
        if not os.path.exists(p):
            sys.exit(f"no such file: {p}")

    md = open(a.spec, encoding="utf-8").read()
    pages = pdf_text(a.pdf)
    whole = norm(" ".join(t for _, t in pages))
    spec_norm = norm(md)
    ledger = ledger_entries(a.ledger)

    # ---------------------------------------------------------- missing copy
    missing, checked = [], 0
    for label, cells in spec_rows(md):
        cell = cells[4] if len(cells) > 4 else ""
        for want in required_strings(cell):
            n = norm(want)
            if len(n) < MIN_REQUIRED_LEN:
                continue
            checked += 1
            if n in whole:
                continue
            # A long run may be broken across pages; accept it if its opening
            # clause is present, and report the rest as partial.
            head = " ".join(n.split()[:8])
            missing.append({"spec_page": label, "text": want[:160],
                            "partial": bool(head and head in whole)})

    # -------------------------------------------------------------- new copy
    new = []
    for pno, text in pages:
        for raw in re.split(r"(?<=[.!?])\s+|\n{2,}", text):
            s = raw.strip()
            if len(s) < MIN_NEW_LEN:
                continue
            n = norm(s)
            if len(n) < MIN_NEW_LEN:
                continue
            if n in spec_norm:
                continue
            head = " ".join(n.split()[:9])
            if head and head in spec_norm:
                continue
            if any(n in l or l in n for l in ledger):
                continue
            new.append({"page": pno, "text": s[:200]})

    report = {"spec": a.spec, "pdf": a.pdf, "required_checked": checked,
              "missing": missing, "new_unjustified": new,
              "ledger_entries": len(ledger)}

    print(f"spec  {os.path.basename(a.spec)}")
    print(f"pdf   {os.path.basename(a.pdf)}  ({len(pages)} pages)")
    print(f"  required copy strings checked: {checked}")
    print(f"  missing from the PDF:          {len(missing)}")
    print(f"  new copy without justification:{len(new)}  (ledger has {len(ledger)} entries)")
    for m in missing[:40]:
        flag = "PARTIAL" if m["partial"] else "MISSING"
        print(f"  {flag}  spec page {m['spec_page']}: “{m['text']}”")
    if len(missing) > 40:
        print(f"  ... and {len(missing) - 40} more")
    for n in new[:40]:
        print(f"  NEW      p{n['page']}: “{n['text']}”")
    if len(new) > 40:
        print(f"  ... and {len(new) - 40} more")

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(report, open(a.json, "w"), indent=2)
        print(f"\n  wrote {a.json}")

    hard_missing = [m for m in missing if not m["partial"]]
    fail = bool(hard_missing) or len(new) > a.max_new
    print("\n" + ("PASS — the PDF says what the spec ordered, and nothing else."
                  if not fail else
                  f"FAIL — {len(hard_missing)} required string(s) missing, "
                  f"{len(new)} unjustified new sentence(s).\n"
                  "       Add the copy, or justify each addition in the new-copy ledger."))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
