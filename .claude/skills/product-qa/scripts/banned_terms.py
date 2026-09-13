#!/usr/bin/env python3
"""Scan a product (PDF, HTML or Markdown) for trademarked names, unsafe claims, voice
violations and hype.

The ban list is evidence-backed, not a guess: WHEEL OF LIFE is a live US
registration covering our exact goods, and the method names below belong to other
people's books and systems. The claims list keeps us out of medical, therapeutic
and financial-advice territory, which is both a legal and a brand rule. The voice
list is the measurable part of the line's locked voice.md (brands/<line>/voice.md).

Edit assets/banned.json to change the lists — never hard-code a new rule here.
'banned_terms', 'unsafe_claims' and 'voice' block a release; 'hype' warns.

Usage:
  banned_terms.py dist/Product_A4.pdf
  banned_terms.py build/*.html build/new-copy.md --require-disclaimer reflection
  banned_terms.py dist/Product_A4.pdf --json qa/terms.json
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "..", "assets", "banned.json")
GROUPS = (("banned_terms", "banned", "BANNED  "), ("unsafe_claims", "claims", "CLAIM   "),
          ("voice", "voice", "VOICE   "), ("hype", "hype", "HYPE    "))
BLOCKING = ("banned", "claims", "voice")


def load_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        r = PdfReader(path)
        if r.is_encrypted:
            r.decrypt("")
        return [(i + 1, p.extract_text() or "") for i, p in enumerate(r.pages)]
    text = open(path, encoding="utf-8", errors="replace").read()
    if ext in (".html", ".htm"):
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
    elif ext == ".md":
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    return [(0, text)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--rules", default=RULES)
    ap.add_argument("--require-disclaimer", choices=["reflection", "money", "none"],
                    default="none")
    ap.add_argument("--json")
    a = ap.parse_args()

    rules = json.load(open(a.rules))
    findings = {"banned": [], "claims": [], "voice": [], "hype": [], "disclaimer": None}

    all_text = []
    for path in a.files:
        if not os.path.exists(path):
            sys.exit(f"no such file: {path}")
        for pno, text in load_text(path):
            all_text.append(text)
            flat = re.sub(r"\s+", " ", text)
            for group, key, _ in GROUPS:
                for entry in rules.get(group, []):
                    pat = entry["pattern"] if entry.get("regex") else re.escape(entry["term"])
                    near = [w.lower() for w in entry.get("allow_if_near", [])]
                    for m in re.finditer(pat, flat, re.I):
                        s = max(0, m.start() - 50)
                        # A disclaimer says the clinical words on purpose ("not a
                        # diagnosis, not therapy"). Skip a match that sits next to
                        # one of its permitted neighbours, in either direction.
                        if near:
                            window = flat[max(0, m.start() - 70):m.end() + 30].lower()
                            # Whole words only. Substring matching would let
                            # "another" satisfy "not" and quietly exempt a real
                            # advice or clinical claim.
                            if any(re.search(r"\b%s\b" % re.escape(w), window) for w in near):
                                continue
                        findings[key].append({
                            "file": os.path.basename(path), "page": pno,
                            "term": entry.get("term", entry.get("pattern")),
                            "why": entry["why"],
                            "context": flat[s:m.end() + 50].strip()})

    joined = re.sub(r"\s+", " ", " ".join(all_text)).lower()
    if a.require_disclaimer != "none":
        need = rules["disclaimers"][a.require_disclaimer]
        hit = any(re.search(p, joined, re.I) for p in need["patterns"])
        findings["disclaimer"] = {"kind": a.require_disclaimer, "present": hit,
                                  "expected": need["example"]}

    for _, key, label in GROUPS:
        for f in findings[key]:
            where = f"{f['file']}" + (f" p{f['page']}" if f["page"] else "")
            print(f"{label}{where}: “{f['term']}” — {f['why']}")
            print(f"          ...{f['context']}...")
    d = findings["disclaimer"]
    if d and not d["present"]:
        print(f"MISSING  the {d['kind']} disclaimer. Expected something like:\n"
              f"          “{d['expected']}”")

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(findings, open(a.json, "w"), indent=2)
        print(f"\n  wrote {a.json}")

    hard = sum(len(findings[k]) for k in BLOCKING) + (1 if d and not d["present"] else 0)
    soft = len(findings["hype"])
    if hard:
        print(f"\nFAIL — {hard} blocking issue(s), {soft} tone warning(s).")
        return 1
    print(f"\nPASS — no banned names, no unsafe claims, no voice violations"
          + (f"; {soft} tone warning(s) to consider." if soft else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
