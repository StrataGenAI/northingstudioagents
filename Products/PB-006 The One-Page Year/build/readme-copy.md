# README copy ledger — PB-006 The One-Page Year

Every sentence in `dist/README.txt`, and where it comes from. Added in round 2,
answering the round-1 MINOR "`README.txt` copy passes through no gate".

**Why this is a separate file from `new-copy.md`.** `spec_coverage.py` treats
every `-` bullet in the file passed to `--ledger` as a justification that makes a
sentence in the PDF acceptable. If the README's sentences lived in `new-copy.md`,
they would widen that allow-list — "Undated. Use it in any year, starting any
day." would silently justify itself if it ever appeared in a *page*. The PDF
ledger therefore stays exactly as narrow as it was, and the README is documented
here instead.

`banned_terms.py` **does** cover `README.txt` (`qa/terms-all.json`, PASS), so the
file is screened for banned names and unsafe claims. What it was missing, and
what this file supplies, is a check that its sentences are authorised at all.

---

## Spec-ordered

The spec's Deliverables table requires `README.txt` to carry a "licence line,
'works with GoodNotes, Notability, Samsung Notes', support email, rating
request". All four are present:

- The LICENCE section — the spec's "licence line". The OFL facts (commercial use,
  embedding permitted, files never sold on their own) come from `brand-kit.md`
  §Typography, which records the licence verification.
- "Works with GoodNotes, Notability and Samsung Notes." — spec, verbatim
  requirement. **UNVERIFIED: none of the three has been opened on a real device.**
- "Email hello@northingstudio.example and tell us what happened…" — the spec's
  "support email". The address is an **[Assumption]**; no support address exists
  anywhere in `Product Plans/`.
- The IF IT HELPED rating request — the spec's "rating request".

## Derived from the spec's other sections

- The WHAT'S INSIDE file list, with page counts and sheet sizes — the spec's
  Deliverables table. The counts and trim sizes are the gate's measured figures
  (`qa/verify-*.json`), not estimates.
- "The Letter edition is laid out separately for the shorter, wider sheet. It is
  not a scaled copy of the A4, so nothing shifts in the margins when you print
  it." — the spec's Deliverables note, "laid out separately, **not** a scaled A4".
- "The Tablet file is a flat page — there are no tabs to tap, because a two-page
  file does not need them." — the spec's hyperlink map, which says exactly that.
- "This page is free and complete as it is. There is no locked version of it." —
  the spec's page-2 honest-limit line, restated for the README.
- "A structured self-reflection tool. Not therapy, diagnosis or financial
  advice." — the spec's mandatory footer note, verbatim.
- "One page you'll actually look at." — the spec's page-1 italic accent line.

## Builder-written, with reasons

- "Page 1 is the plan: one sentence, three goals, why those three, the first step
  for each, and the one habit you keep on a bad week." / "Page 2 is how to use
  it, and what comes next." — a two-line contents summary. It makes no new claim:
  it names the spec's own five blocks and the spec's own page-2 purpose.
- The PRINTING section ("Print at 100%… 'Actual size', not 'Fit to page'…
  Portrait. Single-sided, so you can pin page 1 up.") — a printable is unusable
  without print-dialog instructions, and "pin it up" is the spec's stated purpose
  for page 1 ("so it can be pinned up").
- "Both are ink-light: they print in pure black and white with no loss, and they
  use very little ink." — **measured, not asserted**: ink 1.70–2.26% against the
  spec's ≤8% ceiling, and the greyscale renders were opened this round. "No loss"
  refers to the greyscale render; a mono laser print is still a human check.
- "The writing lines are 7.5 mm apart, which suits a normal pen." — 7.5 mm is the
  spec's Page setup figure and measures 7.42 mm rendered. **"Suits a normal pen"
  is UNVERIFIED** — nobody has written on it. It is the one sentence in this file
  making a claim about paper that only a person with a pen can settle.
- "Import the Tablet PDF and write on it with a stylus as you would on paper." —
  usage instruction for the tablet edition. Unverified alongside the app claim.
- "Undated. Use it in any year, starting any day." — **builder-written claim.**
  True of the file: no year is printed anywhere, and `v1.0 · 2026-09` is the
  document version, not the buyer's year. But round 1 found there is nowhere on
  page 1 to *write* the year, so two completed copies cannot be told apart. That
  gap is **DEFERRED** to the owner — a year field is new copy and new writing
  space, both of which the spec fixes exactly. See `BUILD-LOG.md` round 2.
- "We answer every message." — a service promise, not a product fact. **Flagged
  for the owner:** it is only honest if the owner intends to keep it.
- "This file is for your own personal use. Print as many copies as you like for
  yourself. Please don't resell it, redistribute it, or include it in another
  product." — the personal-use licence grant the spec's "licence line" requires.
- The CHANGELOG line — required by the builder's own Phase 5, not by the spec.

No statistic, research claim, testimonial, sales number, competitor wording or
proof number appears in `README.txt`.
