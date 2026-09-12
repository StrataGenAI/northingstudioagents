# New copy ledger — PB-006 The One-Page Year

Every string in the built PDF that `spec_coverage.py` reports as not found in
`Product Plans/specs/PB-006 The One-Page Year.md`, with the reason it is there.

**Scope: the PDF only.** `README.txt` has its own ledger in
`build/readme-copy.md`, deliberately kept out of this file. `spec_coverage.py`
treats every `-` bullet here as a justification that makes a sentence in the PDF
acceptable, so folding the README's sentences in would widen the allow-list that
protects the pages — "Undated. Use it in any year, starting any day." would
silently justify itself if it ever appeared on a page. This file stays as narrow
as the pages require: **14 entries.**

**There is exactly one piece of genuinely new copy in this product: the URL on
page 2.** Everything else below is spec copy that the PDF text extractor returns
as one run because the strings sit on adjacent lines or in the same text block —
a kicker joined to the title under it, a block name joined to its prompt, the two
halves of the running footer joined across the width of the rule. The gate cannot
tell a concatenation from an invention, so each one is listed here and each half
can be checked against the spec.

No statistic, research claim, testimonial, sales number or competitor wording
appears anywhere in this product.

---

## 1. Genuinely new copy

- northingstudio.example/compass-system — **[Assumption]** the plain link line the spec's page 2 orders ("Then a plain link line ... → PB-002 listing URL"). The spec gives no URL, and no real one exists anywhere in `Product Plans/`, so this placeholder is built from the domain in the spec's own "Page setup" footer line (`northingstudio.example`) plus the confirmed PB-002 product name, "The Compass System". **It must be replaced with the real PB-002 listing URL before the product is listed.** It is deliberately a plain, readable, non-tracking address, as the spec's QA checklist requires ("not a tracking-heavy URL").

## 2. Spec copy the extractor returned joined together

Re-verified in round 2 against the rebuilt PDFs, because the page-2 restructure
changed where things sit. The extractor's behaviour is unchanged: it joins across
single line breaks and only ends a run at a sentence terminator, so every entry
below is still load-bearing. The one difference is on page 2's title, which now
carries a placed line break and extracts as "Five minutes now," / "five minutes a
month" — two lines, joined back into the same run, and matched by the gate as one
string.

Page 1:

- NORTHING STUDIO · ONE PAGE The One-Page Year One page you'll actually look at. — the page 1 kicker, title and italic accent line, all three set verbatim from the spec, extracted as one run because they are stacked in the title block.
- 1 THE SENTENCE If this year went well, what would be true by the end of it? — the spec's "**Block 1 — The sentence.**" name joined to its prompt. The prompt's second sentence, "Write one sentence.", is present and sits below the 30-character threshold the gate reports on.
- 2 THREE GOALS Three things, not ten. — the spec's "**Block 2 — Three goals.**" name joined to the opening sentence of its prompt.
- 3 WHY THESE For each goal, finish this line: This matters because… 4 THE FIRST STEP The smallest next step for each goal — something you could do in under an hour. — blocks 3 and 4, each name joined to its prompt, and the two blocks joined to each other because block 3's prompt ends in an ellipsis rather than a full stop. Every word is the spec's.
- 5 THE FLOOR One habit you'll keep even on your worst week. — the spec's "**Block 5 — The floor.**" name joined to the opening sentence of its prompt.
- NORTHING STUDIO northingstudio.example / v1.0 · 2026-09 1. — the running footer. The spec's "Page setup" section orders it: "footer left: `NORTHING STUDIO` wordmark; footer right: `northingstudio.example / v1.0 · 2026-09`". The two halves sit at opposite ends of one rule, so they extract as a single line; the trailing "1." is the first of the nine line numerals, which the extractor emits after the footer.

Page 2:

- HOW TO USE Five minutes now, five minutes a month 1 Print it, or open it in your tablet notes app. — the page 2 kicker, title and first step, all verbatim, extracted as one run because nothing before step 1's full stop ends a sentence.
- 2 Answer the five blocks in one sitting. — step 2's number joined to the first sentence of the spec's step 2. The rest of that step, "Don't polish — first answers are usually the honest ones.", is present and matched by the gate.
- 3 Put it somewhere you pass every day. — step 3's number joined to the spec's step 3.
- 4 On the first Sunday of each month, read it and change anything that's no longer true. — step 4's number joined to the spec's step 4.
- IF YOU WANT MORE This page is the shortest version of a longer method. — the cross-sell kicker joined to the first sentence of the spec's cross-sell paragraph.
- northingstudio.example/compass-system This free page is the whole page — there's no locked version of it. — the placeholder URL above joined to the spec's honest-limit line, which follows it in the cross-sell band.
- NORTHING STUDIO northingstudio.example / v1.0 · 2026-09 — the page 2 running footer, same as page 1.

## 3. Numbering added to the writing lines

The spec gives block 2 the fields `1.` `2.` `3.`. The same three numerals are set
on the writing lines of blocks 3 and 4 as well, because both prompts are written
per goal — "For each goal, finish this line" and "The smallest next step for each
goal" — so the buyer's three goals line up goal-for-goal down the sheet. These
are the spec's own numerals, they add no words, and each is below the length the
gate reports on. Recorded here so the decision is visible rather than silent.
