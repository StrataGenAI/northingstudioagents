#!/usr/bin/env python3
"""Fail if a line's voice.md and the release gate's banned.json have drifted apart.

voice.md is the locked ground truth a human reads; banned.json is what
banned_terms.py enforces. A word banned in one and missing from the other is a
rule nobody is actually checking, so every backticked bullet under voice.md's
"Banned words" heading must exist as a `term` in banned.json.

Usage:
  check_voice_sync.py                                   # every brands/*/voice.md
  check_voice_sync.py brands/quiet-compass/voice.md
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RULES = os.path.join(ROOT, ".claude", "skills", "product-qa", "assets", "banned.json")


def banned_words(voice_path):
    text = open(voice_path, encoding="utf-8").read()
    m = re.search(r"^##\s+\d*\.?\s*Banned words\s*$(.*?)(?=^##\s)", text, re.M | re.S)
    if not m:
        sys.exit(f"FAIL: {voice_path} has no '## Banned words' section")
    return re.findall(r"^\s*-\s+`([^`]+)`", m.group(1), re.M)


def main():
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "brands", "*", "voice.md")))
    if not paths:
        sys.exit("FAIL: no brands/*/voice.md found")
    rules = json.load(open(RULES))
    terms = {e.get("term", "").lower() for group in ("banned_terms", "unsafe_claims", "voice", "hype")
             for e in rules.get(group, [])}
    fails = 0
    for path in paths:
        words = banned_words(path)
        missing = [w for w in words if w.lower() not in terms]
        rel = os.path.relpath(path, ROOT)
        if not words:
            print(f"FAIL  {rel}: the Banned words section lists nothing")
            fails += 1
        for w in missing:
            print(f"FAIL  {rel}: `{w}` is banned in voice.md but has no rule in banned.json")
            fails += 1
        if words and not missing:
            print(f"PASS  {rel}: all {len(words)} banned words are enforced by banned.json")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
