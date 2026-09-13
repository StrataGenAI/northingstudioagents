# Build log — PB-006 The One-Page Year

**Round 1 — build.** Builder: Product Building Agent. Date: 2026-09-12.
Spec: `Product Plans/specs/PB-006 The One-Page Year.md` (v1) ·
Brand kit: `Product Plans/brand-kit.md` (v1).

---

## 1. What was built

| File | Pages | Bytes | Trim (measured) |
|---|---|---|---|
| `dist/QuietCompass_One-Page-Year_A4.pdf` | 2 | 55,230 | 210.000 × 297.000 mm |
| `dist/QuietCompass_One-Page-Year_Letter.pdf` | 2 | 54,289 | 215.900 × 279.400 mm |
| `dist/QuietCompass_One-Page-Year_Tablet.pdf` | 2 | 58,717 | 428.625 × 571.500 mm (1620 × 2160 px) |
| `dist/README.txt` | — | 2,478 | — |
| `dist/licences/` | — | — | OFL ×3 + `FONT-LICENCES.md` |

`dist/` total **0.21 MB**, against Gumroad's 250 MB cap for $0 products. The spec
predicted ~2 MB; the real figure is an order of magnitude smaller because the
pages are hairline rules and type, with no raster art.

Sources: `build/a4.html`, `build/letter.html`, `build/tablet.html`,
`build/product.css`, `build/assets/compass.svg`. All three link the shared
`../../_assets/fonts/fonts.css` and `../../_assets/product-base.css`; neither
shared file was modified.

## 2. Design decisions, and why

- **Page 1 — five blocks, leftover height pushed into the gaps.** The blocks are
  a flex column with `justify-content: space-between`, so the ~32 mm the sheet has
  spare is distributed evenly between the five blocks rather than collecting as
  one dead band at the foot. Measured result: largest empty band on page 1 is
  **5.9%** of the sheet, against the gate's 20% limit.
- **Block names set as kickers, not headings.** This holds page 1 to three content
  type sizes — title 30 pt, italic accent line 13.5 pt, prompt 10.5 pt — with the
  mono kickers and footer as system furniture. It also costs almost no ink.
- **Writing lines numbered in blocks 3 and 4, not just block 2.** Both prompts are
  written per goal ("For each goal…", "The smallest next step for each goal"), so
  the buyer's three goals line up goal-for-goal down the sheet. The numerals are
  the spec's own `1.` `2.` `3.`; no words were added. Recorded in `new-copy.md` §3.
- **One accent per page, never carrying text.** Page 1: the brass marker on N of
  the compass. Page 2: a single 18 mm accent rule over the cross-sell column.
- **Page 2 was rebuilt after looking at it.** The first version spread the five
  steps with `justify-content: space-between`. It **passed every gate**
  (`max_gap_pct` 3.4, because the two columns stagger content across every
  horizontal band, so no row of the sheet is ever fully empty) and still looked
  broken: five lines of text marooned in ~60 mm of white, each with a rule
  floating beneath it. Rebuilt as five equal-height bands, each opened by a
  hairline rule with its number and text at the top, and the compass anchoring the
  foot of the cross-sell column so both columns finish on the same baseline. The
  air is now inside a repeating unit instead of between stray items. **This is the
  clearest case in the build of a gate being necessary and not sufficient.**

## 3. Two defects the gates caught that were real, not noise

- **The required disclaimer was invisible to the coverage gate.** The base
  system sets `.disclaimer { opacity: .8 }`. The transparency made Chrome emit the
  line glyph by glyph — the PDF text extracted as
  `A  s t r uc t ur e d  se l f - r e f l e c t i o n  t o o l .` — so
  `spec_coverage.py` reported the spec's mandatory footer note as **MISSING**.
  Fixed by setting the disclaimer to full-strength ink in `product.css`, which
  also raises the contrast of the smallest text on the sheet. Re-run: missing
  went 1 → 0.
- **The outbound URL broke mid-word.** `word-break: break-all` split it as
  `quietcompass.example/compass-syst` / `em`, which reads as a typo on paper —
  on the one string a buyer has to type. Removing the break-all left it wrapping
  at the hyphen (`compass-` / `system`), so the link line was set at 8.5 pt (the
  brand kit's mono spec-strip size) and the cross-sell columns widened. Verified
  by extracting the line from all three PDFs: `quietcompass.example/compass-system`
  on one line in **A4, Letter and Tablet**.

## 4. A tooling bug fixed outside this product

`banned_terms.py` **failed the spec's mandatory disclaimer**:

```
CLAIM   disc.txt: "advice claim" — Money and legal pages must say
        'educational only - not financial advice', never give it.
        ...d self-reflection tool. Not therapy, diagnosis or financial advice....
FAIL — 1 blocking issue(s), 0 tone warning(s).
```

The `advice claim` rule exempted the phrase only via negative lookbehinds
(`(?<!not )` …), which match only when "not" sits *immediately* before
"financial advice". In the disclaimer the words are separated
("Not therapy, diagnosis **or** financial advice"), so the rule fired on a line
whose entire purpose is to disclaim financial advice. The rule contradicted
itself: **`banned.json`'s own `disclaimers.reflection.example` is that exact
string.**

The spec's copy is authoritative and was not changed. Instead
`.claude/skills/product-qa/assets/banned.json` — which the script's own docstring
names as the place to change rules — gained an `allow_if_near` list on that
entry, exactly as the two sibling clinical rules (`clinical language`,
`diagnostic framing`) already carry for the same reason. Both directions were
then tested:

```
# the disclaimer
PASS — no banned names, no unsafe claims.

# genuine advice-giving, to prove the rule was not merely weakened
CLAIM  "Follow this plan for financial advice you can act on today."
CLAIM  "We give tax advice to every buyer."
FAIL — 2 blocking issue(s), 0 tone warning(s).
```

**This change affects every product in the pipeline, not just PB-006.** It is
flagged here for the owner and the critic rather than buried.

## 5. Gate output (actual, not summarised)

### `verify_pdf.py` — all three editions

```
QuietCompass_One-Page-Year_A4.pdf  —  2 pages, a4
  fonts: IBMPlexMono-Regular, Fraunces72pt-SemiBold, Fraunces72pt-Italic,
         SourceSans3-Regular, SourceSans3-Italic, SourceSans3-SemiBold
  ink:   avg 1.7%  max 1.9%  (limit 8.0%)
  type:  8.0–30.0 pt (floor 9.0 pt)
  links: 1 external URL(s): https://quietcompass.example/compass-system
PASS — every gate met.

QuietCompass_One-Page-Year_Letter.pdf  —  2 pages, letter
  ink:   avg 1.7%  max 2.0%  (limit 8.0%)
  type:  8.0–30.0 pt (floor 9.0 pt)
PASS — every gate met.

QuietCompass_One-Page-Year_Tablet.pdf  —  2 pages, tablet
  ink:   avg 1.8%  max 2.0%  (limit 8.0%)
  type:  16.3–61.2 pt (floor 9.0 pt)
PASS — every gate met.
```

Per page, measured:

| Edition | Page | Box (mm) | Ink | Fill | Max empty band | Content ends |
|---|---|---|---|---|---|---|
| A4 | 1 | 210.0 × 297.0 | 1.47% | 45.5% | 5.9% | 94.7% |
| A4 | 2 | 210.0 × 297.0 | 1.91% | 92.0% | 3.4% | 94.7% |
| Letter | 1 | 215.9 × 279.4 | 1.51% | 45.8% | 4.1% | 94.4% |
| Letter | 2 | 215.9 × 279.4 | 1.97% | 91.3% | 3.4% | 94.4% |
| Tablet | 1 | 428.625 × 571.5 | 1.54% | 40.6% | 8.4% | 94.4% |
| Tablet | 2 | 428.625 × 571.5 | 2.02% | 51.7% | 13.1% | 94.4% |

0 fails and 0 warnings on every edition. Page 1's 45% fill is the ruled writing
space doing its job — the gate's own note is that a page of writing lines is
mostly paper by area and is exactly right, which is why the *band* is the number
that matters.

### `spec_coverage.py`

```
  required copy strings checked: 19
  missing from the PDF:          0
  new copy without justification:0  (ledger has 14 entries)
PASS — the PDF says what the spec ordered, and nothing else.
```

Same result for the Letter and Tablet editions (`qa/coverage-letter.json`,
`qa/coverage-tablet.json`).

### `banned_terms.py`

```
PASS — no banned names, no unsafe claims.
```

Run on the A4 PDF (`qa/terms.json`) and again across all three PDFs **plus
`README.txt`** (`qa/terms-all.json`). No "Wheel of Life", no GTD/PARA/12 Week
Year/WOOP/Atomic Habits, no "Life Compass", no hype warnings, reflection
disclaimer present.

### `fetch_fonts.py --check`

```
OK - 9 faces, 0 licences in Products/_assets/fonts
```

Six static faces are embedded in the PDFs; no Type3 face on any page, so text
stays selectable and searchable and print shops will accept the files.

## 6. Every `[Assumption]`

1. **The brand name "Quiet Compass" is unconfirmed.** Still awaiting the owner,
   per `brand-kit.md`. It is literal text in the page-1 kicker, the running
   footers, the footer domain, `README.txt` and all three file names. It is
   deliberately *not* a CSS `content:` variable — generated content does not
   reliably survive PDF text extraction, which would break both the coverage gate
   and the screen-reader text path. A rename is
   `grep -rl "QUIET COMPASS" build/` plus the three `dist/` file names;
   `product.css` carries a header comment listing every location.
2. **`quietcompass.example/compass-system` is a placeholder.** The spec orders
   "a plain link line" to the PB-002 listing but gives no URL, and no real one
   exists anywhere in `Product Plans/`. Built from the domain in the spec's own
   footer line plus PB-002's confirmed name, "The Compass System". **Blocks the
   listing until replaced.**
3. **`hello@quietcompass.example` is a placeholder** for the support email the
   spec's deliverables table requires in `README.txt`. No support address exists
   in the plan. **Blocks the listing until replaced.**
4. **Block proportions.** The spec's Layout column sketches "1 / 3 / 3 / 3 / 1
   proportions"; its Writing space column specifies 2 / 3 / 3 / 3 / 2 ruled lines.
   These disagree — a literal 1:3:3:3:1 height split leaves blocks 1 and 5 too
   short to hold the two lines each is required to carry. The concrete
   instruction (line counts) was built and the *shape* of 1/3/3/3/1 kept: blocks 1
   and 5 are visibly the short ones. Flagged rather than resolved silently.
5. **Licences folder.** The spec's deliverables table lists only the three PDFs
   and `README.txt`. `dist/licences/` was shipped anyway, because the brand kit
   says the OFL text "ships in our `/licences` folder with every product" and the
   licence requires it. An addition to the spec's list, not a substitution.

## 7. Open questions for the owner

1. Confirm or replace the brand name (blocks every product, not just this one).
2. Provide the real PB-002 listing URL and the support email address.
3. The `banned.json` rule change in §4 is a pipeline-wide change — confirm it.
4. Free-tier structure (plan Q3) is still open: separate free listing vs a $0
   tier. Nothing in these files depends on the answer; the listing does.

## 8. What could NOT be verified here — needs a human

Nothing in this section has been tested; all of it is a claim only a person with
paper, a pen and a device can settle.

- **Printing on a real printer.** Ink coverage is measured from a raster of the
  PDF (1.5–2.0%), not from a print. Margins, the hairline `0.5 pt` stone rules and
  the 8.5 pt mono link line need one A4 and one Letter sheet off a real machine —
  hairlines are exactly what a cheap inkjet drops.
- **Writing on it with a pen.** The 7.5 mm line pitch is correct in the file. Only
  a person writing on it can say whether the blocks give enough room for normal
  handwriting, and whether the numerals on the lines of blocks 2–4 crowd the start
  of a line.
- **Pure greyscale on paper.** The greyscale renders were opened and read here and
  the brass marker survives as a distinct grey dot, but a mono laser print is the
  real test.
- **GoodNotes, Notability and Samsung Notes.** `README.txt` claims all three, as
  the spec requires. **None has been opened on a real device.** The tablet PDF is
  a flat page at 1620 × 2160 px with no annotations to conflict with, which is the
  easy case — but the claim is still unverified and should not ship untested.
- **The outbound link.** It resolves as a well-formed annotation in the PDF; it
  points at a placeholder domain that does not exist.

## 9. Scope

Built exactly what the spec lists. No page, prompt, device or feature was added.
`pdf-protect` has **not** been run — protection is the last step, after the
critique round, per `product-build-loop`.

---

# Round 2 — revision

**Builder:** Product Building Agent. **Date:** 2026-09-12.
**Answering:** `critique/round-1.md` — verdict FIX, 0 blockers, 6 major, 8 minor,
3 ideas. Round 1's entries above are left exactly as written; nothing in them has
been edited. Corrections to them are recorded here.

## R2.0 Two corrections to the round-1 evidence record

**The round-1 log did not describe the files that were in `dist/`, and that was
not a builder error.** After the round-1 log was written at 15:57, the
orchestrator fixed a defect in the shared stylesheet and rebuilt all three PDFs
at 16:10. The round-1 log therefore predates its own artefacts by thirteen
minutes, which fully explains the +13/+14 byte deltas and the 0.02pp ink
differences the critique measured. Recorded here so the evidence trail is true.
This is the answer to **[MAJOR] process — `BUILD-LOG.md` documents a different
build**, below.

**The shared `.disclaimer` rule no longer fades with `opacity`.** It used to,
which is what shattered the PDF text layer into single characters and hid the
mandatory disclaimer from the coverage gate (round 1 §3). The shared stylesheet
now fades it with `color-mix(in srgb, var(--ink) 80%, var(--paper))`, which
extracts cleanly. The consequence for this product is that round 1's
`opacity: 1` override became a **no-op**, so the claim in round 1 §3 that the
disclaimer was set to "full-strength ink" was false from 16:10 onward. Corrected
in R2.M5 below.

**A standing rule, adopted:** never fade text with `opacity`, anywhere.
`verify_pdf.py` now fails any build whose text layer is split into single
characters. Nothing in `build/product.css` uses `opacity`; the file carries a
header comment saying so.

## R2.1 What was rebuilt

| File | Pages | Bytes (round 1 → round 2) | Trim (measured) |
|---|---|---|---|
| `dist/QuietCompass_One-Page-Year_A4.pdf` | 2 | 55,243 → **52,748** | 210.000 × 297.000 mm |
| `dist/QuietCompass_One-Page-Year_Letter.pdf` | 2 | 54,302 → **51,970** | 215.900 × 279.400 mm |
| `dist/QuietCompass_One-Page-Year_Tablet.pdf` | 2 | 58,731 → **53,761** | 428.625 × 571.500 mm |
| `dist/README.txt` | — | 2,478 (unchanged) | — |

The three PDFs total 158,479 bytes, down 9,797 from round 1 — page 2 lost a
46 mm SVG device and a two-column grid. Built 17:13:24–17:13:49; every gate below
was run against these files, after they were written.

**An incident worth recording.** An intermediate A4 built at 16:41 measured
`209.89 × 297.01 mm` and **failed the trim gate**. Cause: a headless Chrome had
hung for over two hours on this machine, and `build_pdf.py` was killed after
Chrome had written the raw PDF but before the script's trim-normalisation step
ran. The file was never shipped and never gated as good — the failure is exactly
what the gate is for. The orchestrator cleared the hung processes; the 17:13
rebuild normalises correctly ("Chrome gave 209.889 × 297.011; 2 page box(es)
corrected"). Recorded because "the build wrote a file" is not the same as "the
build finished".

---

## R2.2 MAJOR findings

### [MAJOR] p.2 — the cross-sell column is 37.5% empty paper → **FIXED**

**What changed.** Page 2 was two side-by-side columns. It is now one full-width
column of five steps with the cross-sell as a **full-width band at the foot**.

The round-1 diagnosis was right and the fix had to go further than narrowing a
gap: the cross-sell copy is roughly a quarter the length of the steps copy, so
two columns stretched to equal height **cannot both be full**. Filling the right
column with more device art was explicitly ruled out by the critique, and filling
it with words was not available to me — the spec's copy is final. So the page
stops pretending the two columns are equal. The steps take the height they need;
the cross-sell takes the full 180 mm width at the foot, where it is the last
thing read. The air is now inside the step bands, which is rhythm, rather than in
one hole beside them, which is a hole.

**Re-run gate output, the same measurement that caught it.** `verify_pdf.py`
measures the largest empty band per column as well as across the sheet, and
reports the worst region it finds.

Round 1 (baseline, re-measured by me this round before touching anything):

```
A4      WARN  p2: an empty band of 38% of the sheet in the right column (split 60%),
              from 40% to 78% down the page - is this page finished?
Letter  WARN  p2: an empty band of 34% of the sheet in the right column (split 60%),
              from 42% to 77% down the page - is this page finished?
Tablet  WARN  p2: an empty band of 34% of the sheet in the right column (split 50%),
              from 42% to 77% down the page - is this page finished?
```

Round 2, same command on all three editions:

```
QuietCompass_One-Page-Year_A4.pdf  —  2 pages, a4
  ink:   avg 1.9%  max 2.1%  (limit 8.0%)
  type:  8.0–30.0 pt (floor 9.0 pt)
  links: 1 external URL(s): https://quietcompass.example/compass-system
PASS — every gate met.

QuietCompass_One-Page-Year_Letter.pdf  —  2 pages, letter
  ink:   avg 2.0%  max 2.2%  (limit 8.0%)
PASS — every gate met.

QuietCompass_One-Page-Year_Tablet.pdf  —  2 pages, tablet
  ink:   avg 2.0%  max 2.3%  (limit 8.0%)
  type:  16.3–61.2 pt (floor 9.0 pt)
PASS — every gate met.
```

**No empty-band warning on any page of any edition.** Per page:

| Edition | Page | Box (mm) | Ink | Fill | Max gap (worst region) | Content ends |
|---|---|---|---|---|---|---|
| A4 | 1 | 210.000 × 297.000 | 1.70% | 43.8% | 8.8% | 94.7% |
| A4 | 2 | 210.000 × 297.000 | 2.14% | 37.5% | **14.1%** | 94.7% |
| Letter | 1 | 215.900 × 279.400 | 1.75% | 46.5% | 6.6% | 94.4% |
| Letter | 2 | 215.900 × 279.400 | 2.22% | 40.6% | **16.2%** | 94.4% |
| Tablet | 1 | 428.625 × 571.500 | 1.79% | 41.3% | 15.3% | 94.4% |
| Tablet | 2 | 428.625 × 571.500 | 2.26% | 39.6% | **16.6%** | 94.4% |

0 fails and 0 warnings on every edition.

**Two numbers in that table moved the wrong way, and I am not hiding them.**

- **`fill_pct` on page 2 fell from 92.0% to 37.5%.** This is an artefact of the
  measurement, not a regression. `fill` counts rows of the sheet containing any
  ink. The old two-column layout staggered content across nearly every row, which
  is precisely why it scored 92% while being a third empty — the critique's
  central point. One column of steps with deliberate air between them marks fewer
  rows. The number that means "is this page finished" is the largest empty band,
  and that fell from 38% to 14.1%.
- **Ink rose** (A4 p2 1.91% → 2.14%). That is the section rules going from 0.5 pt
  stone to 1 pt primary (R2.m5). Still roughly a quarter of the 8% ceiling.

**Looked at, not just measured:** I opened `qa/pages/…-A4-p01.png`,
`…-A4-p02.png`, `…-A4-p02-grey.png`, `…-Letter-p02.png` and `…-Tablet-p02.png`
this session. Nothing is clipped at the trim on any edition.

### [MAJOR] p.2 — the left column restates page 1, and gets the larger share → **SPLIT: space allocation FIXED, duplication DEFERRED**

**The space-allocation half is FIXED.** The critique's objection was that the
restatement held `1.08fr` of `1.08fr 0.92fr` while the cross-sell — the page's
commercial job — held the narrower column. There is no longer a ratio to argue
about: the steps and the cross-sell no longer compete for width. The cross-sell
has the full 180 mm measure (A4), and on Letter and Tablet it re-flows rather
than scales (`1fr 106mm` gap 10 mm on Letter, `1fr 102mm` gap 9 mm on Tablet
against A4's `1fr 100mm` gap 8 mm), which is visible in the renders as genuinely
different wrap points in the pitch paragraph.

**The duplication half is DEFERRED — it is not mine to fix.** The critique is
correct that three of the five steps restate the page-1 intro, and that step 1
instructs an action the reader has necessarily already taken. But both strings
are **spec-verbatim**, and `spec_coverage.py` passes precisely because they are.
I may not reword the spec's copy.

> **Spec amendment required (owner/planner decision).** In
> `Product Plans/specs/PB-006 The One-Page Year.md`, the page-2 row of the
> Page-by-page table, "Elements & exact copy" cell. The five numbered steps are
> fixed there verbatim. To remove the restatement, the planner would need to
> reissue that cell with a shorter step list — the redundant ones are step 1
> ("Print it, or open it in your tablet notes app."), step 3 ("Put it somewhere
> you pass every day.", which restates the intro's "Put it where you'll see
> it.") and step 4 ("On the first Sunday of each month, read it and change
> anything that's no longer true.", which restates the intro's "Come back to it
> on the first Sunday of every month."). Steps 2 and 5 carry material page 1
> does not. Note that the spec's own page-1 intro is the better-written version
> of the same instruction, so the cheapest amendment is to cut, not to rewrite.
> Until that cell changes, the build sets what the spec ordered.

### [MAJOR] p.2 — the only conversion asset is styled as the weakest element → **FIXED**

The link was 8.5 pt IBM Plex Mono in primary `#3E6B89` with
`text-decoration: none` — smaller than the body (10.5 pt) and the steps (11 pt),
carrying no underline, and visually identical to the running footer. Measured
contrast 5.40:1.

It is now:

- inside its own outlined panel (stone hairline, 2 mm radius, per the brand kit's
  rule that open boxes get an outline and never a fill), so it reads as the
  page's call to action rather than a line of small print;
- **11 pt** mono — larger than the body text rather than smaller;
- **full-strength ink `#1F2A36`**, which is what the brand kit requires for
  anything under 18 pt ("Primary `#3E6B89` on paper is for headings and large
  text (≥18 pt) and UI labels only — not for 9–11 pt body"). That takes it from
  5.40:1 to the body's **13.71:1**;
- **underlined**, so it reads as a link without relying on colour, and in
  greyscale — confirmed in `…-A4-p02-grey.png`, which I opened.

It still sets on **one line**: 100 mm of panel less 12 mm of padding leaves
88 mm, and the 35-character URL occupies 81.5 mm at 11 pt. The Letter and Tablet
panels are wider still (106 mm, 102 mm). The round-1 defect where
`word-break: break-all` split it as "compass-syst / em" has not returned — the
extracted text layer of the rebuilt A4 contains the address on a single line:

```
'quietcompass.example/compass-system'
```

The link annotation survives on every edition:
`links: 1 external URL(s): https://quietcompass.example/compass-system`.

**What I did not do:** add a call-to-action phrase, a price, a format or a page
count beside the URL. All of those would be new copy the spec does not authorise,
and the critique itself records that the research has no evidence on cross-sell
copy *inside* a delivered file. Routed to the owner as an IDEA (R2.4).

### [MAJOR] process — `BUILD-LOG.md` documents a different build → **FIXED (and not a builder error)**

**Cause, established:** the orchestrator rebuilt all three PDFs at 16:10 after
fixing the shared stylesheet; the round-1 log was written at 15:57. The log was
accurate when written and stale thirteen minutes later. See R2.0.

**Fixed by:** recording that rebuild above, and by re-running every gate in this
round **after** the final build and pasting the real output. The round-2 file
table carries both the old and new byte counts so the two builds can never be
confused again. Build times 17:13:24–17:13:49; all gate runs follow them.

### [MAJOR] p.1 — the log claims the disclaimer was set to full-strength ink; it was not → **FIXED**

The critique is exactly right, and its predicted value was right to the byte:
`build/product.css` carried `.disclaimer { opacity: 1; … }`, which overrode a
property the shared stylesheet had stopped using, and never set the colour. The
line rendered at `#4C535C` — the shared `color-mix(ink 80%, paper)` — while the
round-1 log claimed full-strength ink.

**Fixed by** replacing the dead override with the colour itself:

```css
.disclaimer { color: var(--ink); margin: 4mm 0 3mm; }
```

**Re-measured from the rendered page** (`qa/pages/…-A4-p01.png`, the band from
88% to 95% down the sheet, which is the disclaimer and the running footer):

```
  paper ground            #FAF8F2
  darkest pixel in band   #1F2A36   contrast 13.71:1
  most common dark colours in band (glyph cores sit at the top):
    #1F2A36      273 px   contrast 13.71:1
    #3F6B89      210 px   contrast  5.38:1
    #3C4650       68 px   contrast  9.05:1
```

`#1F2A36` at 13.71:1 is the disclaimer; `#3F6B89` is the primary running footer
in the same band. **There is no longer any pixel cluster near `#4B535C`**, which
is what an 80% fade would produce. The claim and the file now agree. The dead
`opacity: 1` is gone, and no rule in `product.css` uses `opacity`.

### [MAJOR] package — no listing images exist → **DEFERRED (owner scope call)**

Confirmed as an absence: `dist/` contains three PDFs, `README.txt` and
`licences/`, and no images. I have not built any.

This is not a defect I can close by building, because the spec contradicts
itself and the contradiction is the owner's to resolve:

- the spec's **Deliverables** table lists only the three PDFs and `README.txt`;
- the spec's **Assets** section orders "flat A4 page stack (2 pages, slight tilt,
  soft shadow) + one tablet frame + one pinned-to-wall flat-lay";
- the spec's **Build plan** budgets 6.0 h of page work with **no image time**;
- `brand-kit.md` states "Every product ships all 10 slots."

> **Owner decision required.** Are listing images in scope for PB-006, and at
> what count — the spec's three mockups, or the brand kit's ten slots? Either
> answer needs a spec amendment (Deliverables table + Build plan hours). The
> critique's market evidence is that competitor free products ship two images
> each, so zero is below even the thin norm, and a free product with no images
> cannot be published at all. **This blocks the listing, not the files.**

---

## R2.3 MINOR findings

### [MINOR] p.1 + p.2 — the brand mark drawn at two different stroke weights → **FIXED**

The mark was one SVG at `stroke-width="1.4"` on a 120-unit viewBox, scaled to
26 mm on page 1 (0.86 pt effective) and 46 mm on page 2 (1.52 pt) — neither
matching the brand kit's 1.25 pt, and differing from each other by 1.77×.

Fixed at both ends. The page-2 instance is **gone entirely** (see the next
finding), so there is now exactly one instance in the product, and its strokes
are set to render at the brand kit's weights. Stroke widths in an SVG are in user
units and scale with the box, so they are solved for the rendered size:

- diagram strokes: 1.25 pt = 0.4410 mm; at 26 mm for 120 units →
  `0.4410 × 120 / 26 = 2.03` units → **1.246 pt rendered**;
- the inner stone circle is a hairline, not a diagram stroke: 0.5 pt = 0.1764 mm
  → `0.1764 × 120 / 26 = 0.81` units → **0.499 pt rendered**.

The arithmetic is in a comment above the SVG in all three HTML files, so the next
person resizing the mark knows it has to be re-solved. Confirmed by eye in
`…-A4-p01.png`: the mark now reads at the same weight as the page's other
primary strokework.

### [MINOR] p.2 — the decorative repeat is larger than the signature and exists to fill a hole → **FIXED**

Removed. The 46 mm device is no longer in the product, and the CSS comment that
conceded it was there "so both columns finish on the same baseline" is gone with
it. The brand kit's "one icon per product family" now holds literally: one mark,
on page 1, at 26 mm. The hole it was plugging was closed by the R2.M1 rebuild
rather than by ornament.

### [MINOR] build — `letter.html` documents a column ratio the stylesheet does not use → **FIXED**

`letter.html` claimed "page 2 re-flows its columns to **1.28fr / 0.72fr**" while
`product.css` set `1.15fr 0.85fr`. Both the comment and the rule are gone with
the two-column layout. The comment now describes what the file actually does:

> page 2 the cross-sell band gives the link panel the extra width (106 mm against
> A4's 100 mm, with a 10 mm gap against 8 mm), which narrows the pitch paragraph,
> makes it taller, and fills the shorter sheet

Verified against `product.css`: `body.size-letter .more__grid
{ grid-template-columns: 1fr 106mm; gap: 10mm; }`. The Letter edition remains a
genuine re-layout, not a scale — visible in the renders as different wrap points
("adds the / part this page can't" on Letter against "adds the part / this page
can't" on A4).

### [MINOR] p.2 — the title leaves an orphan in all three editions → **FIXED**

"Five minutes now, five minutes a / **month**" dropped a single word onto a
second line at 30 pt. Fixed with a placed break at the comma rather than a
`max-width` guess, so it is deterministic at all three sheet widths instead of
depending on the measure:

```html
<h1 class="p2title">Five minutes now,<br>five minutes a month</h1>
```

`.p2title { max-width: none; }` — the 150 mm cap that caused it is gone. Same
words, same order; the gate confirms the string still reads as one
(`spec_coverage` PASS, 0 missing). Confirmed by opening all three page-2 renders:
the title sets as two balanced lines on A4, Letter and Tablet.

### [MINOR] p.1 — section rules are indistinguishable from writing lines → **FIXED**

`.block__name` closed with a 0.5 pt stone hairline — identical in weight and
colour to `.lines > i`, so on a sheet whose whole function is knowing where to
write, the rule under "2 THREE GOALS" read as a line to write on.

Set to the brand kit's section rule:

```css
.block__name { … border-bottom: 1pt solid var(--primary); }
```

The 0.5 pt stone hairlines are now the writing lines **and nothing else** on
page 1. Page 2's step bands take the same 1 pt primary rule, so the two pages
share one structural vocabulary. Confirmed by opening `…-A4-p01.png`: the
structural rules are visibly heavier and bluer than the writing rules. The cost
is the ink rise noted in R2.M1 (page 1 1.47% → 1.70%), well inside budget.

### [MINOR] p.1 — the A4 intro wraps to two lines for no reason → **FIXED**

`.intro { max-width: 118mm }` broke the product's first sentence over two lines
on A4 while Letter and Tablet set it on one. Removing the cap alone would not
have fixed it: inside the title block the intro shares its width with the 26 mm
device and has ~148 mm, and the sentence needs ~149 mm.

So the intro was **moved out of the title block** to sit beneath it, where it
takes the full 180 mm measure. It now sets on one line on all three editions —
confirmed in the extracted text layer, which returns it as a single run:

```
"Fill this in once. Put it where you'll see it. Come back to it on the first Sunday of every month."
```

and by eye in `…-A4-p01.png`. The `body.size-letter/.size-tablet .intro
{ max-width: none }` overrides are gone, since there is no longer a cap to undo.

### [MINOR] package — `README.txt` copy passes through no gate → **FIXED**

`spec_coverage.py` takes a single PDF and can never read a `.txt`, so the file
carrying the product's three riskiest claims was checked by nothing but
`banned_terms.py`. Every sentence in `README.txt` now has a ledger entry with its
source, in **`build/readme-copy.md`** — spec-ordered, derived from the spec, or
builder-written with a reason, and with the unverified claims marked as such.

**Why a separate file, and a mistake I caught and undid.** I first put the README
ledger inside `build/new-copy.md`. That was wrong: `spec_coverage.py` treats
every `-` bullet in the `--ledger` file as a justification that makes a sentence
in the *PDF* acceptable, so the README's sentences silently widened the allow-list
protecting the pages from 14 entries to 33 — "Undated. Use it in any year,
starting any day." would have auto-justified itself had it ever appeared on a
page. Moving it to its own file restores the PDF gate to exactly its original
strength, proved by re-running it:

```
  required copy strings checked: 19
  missing from the PDF:          0
  new copy without justification:0  (ledger has 14 entries)
PASS — the PDF says what the spec ordered, and nothing else.
```

Identical output for the Letter and Tablet editions (`qa/coverage-letter.json`,
`qa/coverage-tablet.json`).

### [MINOR] p.1 — claims to be undated and reusable, then gives nowhere to write the year → **DEFERRED**

Confirmed as an absence: page 1 has no year field. The critique is also right
that the claim is self-inflicted — "Undated. Use it in any year, starting any
day." is builder-written, not spec-ordered.

I have **not** added a year field, because it is not within my scope to add one:
a field is new copy (a label) *and* new writing space, and the spec fixes both
exactly — its page-1 Elements cell lists every string, and its Writing space cell
specifies 2 / 3 / 3 / 3 / 2 ruled lines. Adding a sixth element silently would be
precisely the unauthorised invention `spec_coverage.py` exists to catch.

I have also **not** removed the README claim, because it is true: no year is
printed anywhere in the product, and `v1.0 · 2026-09` is the document version,
not the buyer's. The product is genuinely undated and reusable. What it lacks is
a way to tell two completed copies apart.

> **Spec amendment required (owner/planner decision).** Page-1 row of the
> Page-by-page table: add a year field to the "Elements & exact copy" cell with
> its exact label, and add it to the "Writing space" cell. It would sit naturally
> in the title block beside the compass, which is the only part of page 1 with
> spare width, and it would not disturb the five-block rhythm or the 13 ruled
> lines. Cost is one line of CSS and one element; it is blocked only on the
> owner authorising the words.

---

## R2.4 IDEAs — routed to the owner, not built

Per `product-build-loop` control 6, none of these was built.

1. **State the time cost on page 1.** Page 2's title says "Five minutes now, five
   minutes a month" — the right promise on the wrong page, since page 1 is the
   sheet that gets pinned up. The critique cites competitors describing free kits
   by time cost rather than page count. Needs a spec amendment to page 1's copy.
2. **Email capture is a listing job, not a page job.** The critique raises no
   finding here and I agree: capture belongs at the Gumroad $0 checkout, not in
   the file. Recorded so it is not re-litigated in round 3.
3. **The honest-limit line may deserve a stronger position or a listing slot.**
   "This free page is the whole page — there's no locked version of it." now sits
   full-width at the foot of the cross-sell band rather than buried in a narrow
   column, which is a modest improvement I could make without new copy. Whether
   it earns more than that is the owner's call.

A fourth, arising from this round: **the cross-sell band has room for material
that earns the click** — a free-vs-paid comparison or a "what this free version
doesn't do" block, both of which the critique's research notes competitors using.
The band is now full-width and could carry one without a layout change. It needs
copy the spec does not contain, so it is an owner decision, not a build task.

## R2.5 Deviation from the spec — owner decision needed

**The spec's page-2 Layout cell says "Two columns: left 'How to use', right 'If
you want more'". The build no longer does that.** The two zones the spec names
are unchanged, still present, and still in the spec's order — they are stacked
rather than set side by side.

I made this call because the alternative was to leave the product's single
commercial asset sitting in 111 mm of dead paper, and because the orchestrator's
brief for this round put column proportions, spacing, link prominence and "where
things sit on the page" within my remit while placing the spec's *copy* outside
it. Every word on the page is still the spec's, and `spec_coverage.py` passes.

> **Owner decision.** Either amend the page-2 Layout cell to describe the stacked
> arrangement, or reject the deviation — in which case the cross-sell's empty
> column comes back, and closing it would need the spec to authorise more copy
> for that column. It cannot be closed by layout alone at this ratio of copy.

## R2.6 A defect I introduced this round, and fixed

The first rebuild left the closing line "This free page is the whole page —
there's no locked version of it." about 4 mm off the footer rule, cramped against
it on a sheet where nothing else is. Cause: with the steps column growing to fill
the sheet there is no slack left at the foot, so the band needed an explicit
bottom margin. Fixed with `.limit { margin: 5mm 0 7mm; }` and confirmed by
opening the re-rendered page. Recorded because I found it by looking at the page
after the gates had already passed it — the gates never saw it.

## R2.7 Assumptions — unchanged from round 1

All five stand, and two still block the listing.

1. **"Quiet Compass" is unconfirmed.** Still literal text in the page-1 kicker,
   both running footers, the footer domain, `README.txt` and all three file
   names. `product.css` carries the rename map in its header comment.
2. **`quietcompass.example/compass-system` is a placeholder.** Not invented away
   this round, as instructed. It is now *more* prominent, which makes replacing
   it more urgent, not less. **Blocks the listing.**
3. **`hello@quietcompass.example` is a placeholder.** **Blocks the listing.**
4. **Block proportions** — the spec's "1 / 3 / 3 / 3 / 1" sketch still disagrees
   with its own 2 / 3 / 3 / 3 / 2 line counts; the line counts are built.
5. **`dist/licences/`** ships although the Deliverables table omits it, because
   the OFL requires it and the brand kit mandates it.

New this round: **"We answer every message."** in `README.txt` is a service
promise, not a product fact. It is only honest if the owner intends to keep it.

## R2.8 Gate output — all editions, actual

`fetch_fonts.py --check`:

```
OK - 9 faces, 0 licences in Products/_assets/fonts
```

`banned_terms.py`, A4 alone and then across all three PDFs **plus `README.txt`**:

```
PASS — no banned names, no unsafe claims.
PASS — no banned names, no unsafe claims.
```

No "Wheel of Life", no GTD/PARA/12 Week Year/WOOP/Atomic Habits, no "Life
Compass"; the reflection disclaimer is present and now at full-strength ink.
Written to `qa/terms.json` and `qa/terms-all.json`.

Six static faces embedded on every edition, no Type3, so text stays selectable
and searchable. No page of any edition reports `spaced_text` — the text layer is
intact, which is the gate that would fail if anything had gone back to fading
text with `opacity`.

## R2.9 What still could NOT be verified — needs a human

Unchanged in substance from round 1, and none of it has been tested.

- **One A4 and one Letter sheet off a real printer.** Still the highest-risk
  item, and this round slightly raised the stakes in one direction and lowered it
  in another: the writing rules are still 0.5 pt stone hairlines (exactly what a
  cheap inkjet or draft-mode laser drops), but the *structural* rules are now
  1 pt primary and will survive. If the hairlines drop on a real machine, the
  page still reads — that is an improvement, not a fix.
- **Writing on it with a pen.** 7.5 mm pitch, 7.42 mm rendered. Nobody has
  written on it. The `1.` `2.` `3.` numerals sit at `left: 0` and may crowd the
  start of a line.
- **Pure greyscale on a mono laser.** I opened the greyscale renders and the
  brass accent rule and the CTA panel both survive as distinct greys, but a
  raster is not a print.
- **GoodNotes, Notability and Samsung Notes.** `README.txt` claims all three, as
  the spec requires. **None has been opened on a real device.** Also unverified:
  whether a 428.6 × 571.5 mm page imports sanely, and whether the single outbound
  link is tappable in each app — it is now the only tappable object in the file
  and is set in a panel, which should help, but "should" is not a test.
- **Whether a buyer will type the URL off paper.** It is now 11 pt, underlined
  and in full ink rather than 8.5 pt primary, which is the improvement the
  critique asked for. Whether it is enough is unknown, and the domain does not
  resolve.

## R2.10 Scope

No page, prompt, device or feature was added. One device was removed, one page
was re-architected, and no word of the spec's copy was changed, added or
reordered. `pdf-protect` has **not** been run — protection remains the last step,
after the owner confirms the brand name and supplies the real URL and support
address.

---

## Linux re-measure (2026-09-13) — pipeline moved to headless Linux

Recorded by the port, not by a build round. The shipped PDFs were **not rebuilt**; the same Mac-built files were re-verified on the Linux server with `verify_pdf.py` (rasteriser: poppler `pdftoppm` instead of macOS `sips`, same 320/297 px-per-mm resolution, `--fonts brands/quiet-compass/fonts/manifest.json`, pypdf pinned at 6.16.1).

- **Fonts:** every embedded face is a brand face (the new font-set gate passes).
- **Ink** moves by up to ±0.75 percentage points between rasterisers. Every page stays far under the 8% limit, so no pass/fail changes; thresholds were left alone and the drift was reported to the owner.
- **Largest empty band** changes where the old baseline predates the px-per-mm fix (tablet p4 / p1).
- The split-text gate fails these files under pypdf ≥ 6.16.2 (letter-spaced kickers extract as single letters); that is an extractor change, which is why pypdf is pinned.

| Edition | Page | Ink % (Mac) | Ink % (Linux) | Δ | Max gap % (Mac) | Max gap % (Linux) |
|---|---|---|---|---|---|---|
| A4 | 1 | 1.70 | 2.45 | +0.75 | 8.8 | 5.9 |
| A4 | 2 | 2.14 | 2.53 | +0.39 | 14.1 | 16.6 |
| Letter | 1 | 1.75 | 2.49 | +0.74 | 6.6 | 6.2 |
| Letter | 2 | 2.22 | 2.59 | +0.37 | 16.2 | 16.2 |
| Tablet | 1 | 1.79 | 1.95 | +0.16 | 15.3 | 6.3 |
| Tablet | 2 | 2.26 | 2.19 | -0.07 | 16.6 | 16.4 |
