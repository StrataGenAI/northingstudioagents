# Critique — PB-006 The One-Page Year, round 1

**Verdict:** FIX · **Blockers:** 0 · **Major:** 6 · **Minor:** 8 · **Ideas:** 3

Critic: Product Critique Agent · Date: 2026-09-12 · Spec: `Product Plans/specs/PB-006 The One-Page Year.md` (v1) · Brand kit: `Product Plans/brand-kit.md` (v1)

Every gate below was re-run by me, from the spec, against the files currently in
`dist/`. I opened **all twelve** rendered pages — A4, Letter and Tablet, pages 1
and 2, colour and greyscale — with Read before writing a word about how anything
looks. Every market claim cites `Research Reports/` or `research/`; where I have
no evidence I say "my judgement, not evidence".

---

## Gates I ran

| Gate | Command | Result | Key numbers |
|---|---|---|---|
| Print, A4 | `verify_pdf.py …_A4.pdf --size a4 --expect-pages 2 --sparse-pages 1` | **PASS** 0 fails, 0 warnings | 2 pp · 210.000×297.000 mm · ink 1.45 / 1.91% (limit 8%) · type 8.0–30.0 pt · 6 faces embedded, no Type3 |
| Print, Letter | `verify_pdf.py …_Letter.pdf --size letter …` | **PASS** 0 fails, 0 warnings | 2 pp · 215.900×279.400 mm · ink 1.49 / 1.97% · type 8.0–30.0 pt |
| Print, Tablet | `verify_pdf.py …_Tablet.pdf --size tablet …` | **PASS** 0 fails, 0 warnings | 2 pp · 428.625×571.500 mm (1620×2160 px) · ink 1.53 / 2.02% · type 16.3–61.2 pt |
| Spec coverage | `spec_coverage.py "<spec>" …_A4.pdf --ledger build/new-copy.md` | **PASS** | 19 required strings checked · **0 missing** · **0 unjustified new** · ledger 14 entries |
| Banned terms | `banned_terms.py …_A4.pdf --require-disclaimer reflection` | **PASS** | 0 banned · 0 claims · 0 hype · reflection disclaimer **present** |
| Render | `render_pages.py` ×3 editions `--grey` | 12 images | `qa/critic-pages/` |

JSON written by me: `qa/critic-a4.json`, `qa/critic-letter.json`,
`qa/critic-tablet.json`, `qa/critic-coverage.json`, `qa/critic-terms.json`.

**Gates I ran that the builder did not, and their results:**

- **Text-layer integrity.** I extracted the full text of all three PDFs with
  `pypdf`. Every string comes out in document order, no glyph shattering, no
  `A  s t r uc t ur e d` damage. The pipeline-level `opacity` fix holds: **I
  measured no remaining text-layer damage in any edition.**
- **Determinism.** I ran `verify_pdf.py` on the A4 file three times; identical
  output each time (ink 1.45 / 1.91). This matters for M4 below.
- **Per-column whitespace.** The gate's `max_gap_pct` measures full-width empty
  bands only. I measured each column separately. See M1 — this is the single
  most important number in the review.
- **Rendered colour sampling.** I sampled glyph-core RGB from the renders to
  check the brand kit's contrast rules against what actually prints. See M5.

---

## Findings

### [MAJOR] p.2 — the cross-sell column, the page's whole commercial job, is 37.5% empty paper

- **Dimension:** 2 Design craft · 7 Marketability
- **Evidence:** measured from `qa/critic-pages/…-p02.png` by column, not by sheet:

  | Edition | Largest empty band, **right column only** | As % of sheet | What the gate reports for the whole sheet |
  |---|---|---|---|
  | A4 | **111.4 mm** (120.7 → 231.9 mm down) | **37.5%** | `max_gap_pct` **3.4** |
  | Letter | **95.2 mm** (119.5 → 214.5 mm) | **34.1%** | `max_gap_pct` **3.4** |
  | Tablet | **194.7 mm** (244.9 → 439.2 mm) | **34.1%** | `max_gap_pct` **13.1** |

  The cross-sell text ends at 119 mm down the sheet. Nothing follows it for
  111 mm except the compass device parked at the foot. `qa/critic-a4.json` →
  page 2 `max_gap_pct` 3.4, `fill_pct` 92.0 — both structurally blind here,
  because the left column staggers content across every horizontal band, so no
  *full-width* row of the sheet is ever empty.
- **Why it matters:** `BUILD-LOG.md` §2 identifies exactly this failure mode on
  the left column — "five lines of text marooned in ~60 mm of white" — calls it
  "the clearest case in the build of a gate being necessary and not sufficient",
  and then fixes the left column only. The same defect, **three times larger**,
  survives in the right column. This is a free lead magnet whose stated job is
  "the click to PB-002" (spec, "What it is"); the column carrying that click is
  the emptiest region of the product.
- **Fix:** the cross-sell column must occupy its own height with material that
  earns the click. What that material is, is the owner's call — the research
  records competitors using a free-vs-paid ✅/❌ comparison (`research/audits/gumroad-organizeddashboard-knhhvu.md`)
  and a "what this free version doesn't do" block. Do not fill it with more device art.
- **Verdict:** **CONFIRMED (measured)**

### [MAJOR] p.2 — the left column restates page 1's intro at five times the length, and is given the larger share of the sheet

- **Dimension:** 3 Copywriting · 4 Instructional quality · 2 Design craft
- **Evidence:** page 1 intro, verbatim from the extracted text layer:
  > "Fill this in once. Put it where you'll see it. Come back to it on the first Sunday of every month."

  Page 2, steps 2–4, verbatim:
  > "2 Answer the five blocks in one sitting. Don't polish — first answers are usually the honest ones."
  > "3 Put it somewhere you pass every day."
  > "4 On the first Sunday of each month, read it and change anything that's no longer true."

  Three of the five steps restate the one-line intro the buyer read on page 1.
  Step 1 — "Print it, or open it in your tablet notes app." — instructs an action
  the reader has necessarily already taken to be reading it. The column is given
  `1.08fr` of `1.08fr 0.92fr` on A4 and `1.15fr` of `1.15fr 0.85fr` on Letter and
  Tablet (`build/product.css` lines 89, 187–188) — i.e. the restatement gets the
  wider column and the cross-sell gets the narrower one.
- **Why it matters:** this is the first moment reading it as a buyer where I felt
  talked down to. Page 1 already told me what to do, in one calm line that is
  better written than the five steps that repeat it. The product's second and
  final page spends its larger half telling me again.
- **Fix:** page 2 must stop repeating page 1. The space allocation must follow the
  page's purpose — the spec's own words for page 2 are "Remove friction, **then
  point up the ladder**". **Note:** both strings are spec-verbatim and
  `spec_coverage.py` passes, so this cannot be fixed by the builder alone; it needs
  a spec amendment from the owner.
- **Verdict:** **CONFIRMED** for the duplication (strings quoted) · **PLAUSIBLE** for the space-allocation judgement

### [MAJOR] p.2 — the only conversion asset in the product is styled as its weakest element

- **Dimension:** 7 Marketability · 8 Accessibility · 2 Design craft
- **Evidence:** the link line is `quietcompass.example/compass-system` set at
  **8.5 pt IBM Plex Mono** in primary `#3E6B89`, with
  `.linkline a { text-decoration: none; }` (`build/product.css` lines 147–153).
  Measured contrast on paper: **5.40:1**. It is smaller than the body prompts
  (10.5 pt), smaller than the steps (11 pt), and carries no underline, no border,
  no call to action, no price, no page count and no format. It is visually
  indistinguishable from the `quietcompass.example / v1.0 · 2026-09` running
  footer, which is also mono in primary.
  Against the brand kit: primary on paper is "for headings and large text
  (≥18 pt) and UI labels only — **not for 9–11 pt body**", and 8.5 pt mono is
  specified for "spec strips". The URL is functional text, not a spec strip.
  On the **Tablet** edition this string is the single tappable object in the
  entire file (`qa/critic-tablet.json` → page 2, 1 external link).
- **Why it matters:** the spec says this product "exists to earn the email
  address, the Gumroad rating and the click to PB-002". The click target is the
  most typographically recessive thing on the sheet. On paper a buyer must read
  and retype it at 8.5 pt.
- **Fix:** the link must read as the page's call to action and must survive being
  copied off paper by hand. What it should say alongside the URL is the owner's
  call — the research records no evidence on cross-sell copy *inside* a delivered
  file (all recorded cross-sell evidence is about listing pages and images).
- **Verdict:** **CONFIRMED (measured)**

### [MAJOR] process — `BUILD-LOG.md` documents a different build than the one in `dist/`

- **Dimension:** 1 Print & production (evidence integrity)
- **Evidence:**

  | Claim in `BUILD-LOG.md` §1/§5 | What I measured |
  |---|---|
  | A4 `55,230` bytes | **55,243** (+13) |
  | Letter `54,289` bytes | **54,302** (+13) |
  | Tablet `58,717` bytes | **58,731** (+14) |
  | A4 page 1 ink `1.47%` | **1.45%**, identical on three consecutive runs |
  | Letter page 1 ink `1.51%` | **1.49%** |
  | Tablet page 1 ink `1.54%` | **1.53%** |

  File mtimes: the three PDFs were written at **16:10:30–16:10:43**;
  `BUILD-LOG.md` was written at **15:57:05** — the log predates the artefacts it
  describes by thirteen minutes. `verify_pdf.py` is deterministic (three
  identical runs), so these are not rasterisation noise.
- **Why it matters:** control 2 of `product-build-loop` is "Every claim is a
  measurement… both paste the actual output". The pasted output belongs to a
  build that is no longer in `dist/`. Nothing I measured is *worse* than the log
  claims — every gate still passes — but the log cannot be used as evidence for
  anything, which is the one job it has.
- **Fix:** the gate output in the log must come from the files actually shipped;
  re-run and re-paste after the last rebuild, not before it.
- **Verdict:** **CONFIRMED (measured)**

### [MAJOR] p.1 — `BUILD-LOG.md` claims the disclaimer was set to full-strength ink; it was not

- **Dimension:** 1 Print & production · 8 Accessibility (claim accuracy)
- **Evidence:** `BUILD-LOG.md` §3: *"Fixed by setting the disclaimer to
  full-strength ink in `product.css`, which also raises the contrast of the
  smallest text on the sheet."* `build/product.css` line 164 is:
  `.disclaimer { opacity: 1; margin: 4mm 0 3mm; }` — it overrides `opacity`, and
  **never overrides the colour**. The shared stylesheet
  (`Products/_assets/product-base.css` line 304) sets
  `.disclaimer { font-size: 9pt; color: color-mix(in srgb, var(--ink) 80%, var(--paper)); }`.
  I sampled the glyph cores of the rendered A4 page 1:

  | Element | Rendered core RGB |
  |---|---|
  | H1 title 30 pt | `#1F2A36` (full ink) |
  | body prompt 10.5 pt | `#1F2A36` (full ink) |
  | **disclaimer 9 pt** | **`#4C535C`** |

  Predicted for `color-mix(ink 80%, paper)`: `#4B535C`. The disclaimer is at 80%
  ink, exactly as the base stylesheet specifies — not "full-strength". The
  `opacity: 1` is now a no-op, because the shared stylesheet no longer uses
  opacity at all.
- **Why it matters:** this is **not** an accessibility failure — I measured
  `#4C535C` on `#FBF8F3` at **7.37:1**, comfortably past AA. It is a false claim
  in the build record about the smallest and most legally protective text in the
  product, and it will mislead the next person who reads the log.
- **Fix:** either set the colour and re-measure, or correct the log to say what
  was actually changed (the opacity, which was the real text-layer fix). Do not
  leave a dead `opacity: 1` next to a comment describing a change that is not there.
- **Verdict:** **CONFIRMED (measured)**

### [MAJOR] package — no listing images exist, so the product cannot be listed

- **Dimension:** 7 Marketability
- **Evidence:** `dist/` contains three PDFs, `README.txt` and `licences/` —
  no images. The spec's Assets section orders: *"Listing images: flat A4 page
  stack (2 pages, slight tilt, soft shadow) + one tablet frame + one
  pinned-to-wall flat-lay."* The brand kit states *"Every product ships all 10
  slots."* The plan specifies a full 10-slot set for PB-006 by name
  (`Product Plans/2026-09-12 Product Plan.md`, PB-006 brief).
  Against the market: every one of Ideas To Thrive's seven free kits ships
  **exactly 2 images**, Easlo's free Habit Tracker 2, JNKxStudio's free ADHD
  Starter Kit 2 (`research/sellers/gumroad-S3-ideastothrive.md`;
  `research/audits/gumroad-easlo-DEnNV.md`; `research/sellers/gumroad-03-jnkxstudio.md`).
  Zero is below even the thin market norm.
- **Why it matters:** the report's stated cheapest durable advantage is the
  complete image tour (*"Image sets are thin even on expensive products… A
  complete 8–10 image tour is an easy edge"*). A free product with no images
  cannot be published at all.
- **Fix:** owner scope call, then build the set. **In fairness to the builder:**
  the spec's Deliverables table lists only the three PDFs and `README.txt`, and
  the spec's own Build plan budgets 6.0 h of page work with no image time. The
  builder built the contract as written. The contract is incomplete.
- **Verdict:** **CONFIRMED (absence)**

---

### [MINOR] p.1 + p.2 — the same brand mark is drawn at two different stroke weights

- **Dimension:** 2 Design craft · 9 Compliance (brand kit conformance)
- **Evidence:** the compass SVG is identical in both places — `viewBox="0 0 120 120"`,
  `stroke-width="1.4"` — but is scaled to two sizes:
  `.device--mark { width: 26mm }` on page 1 and `.more .device--mark { width: 46mm }`
  on page 2 (`build/product.css` lines 36, 157). Effective stroke:

  | Instance | Width | Effective stroke |
  |---|---|---|
  | p.1 title block | 26 mm | **0.86 pt** |
  | p.2 column foot | 46 mm | **1.52 pt** |

  Brand kit, "Line weights": *"diagram strokes `1.25 pt`"*. Neither instance
  matches, and they differ from each other by 1.77×.
- **Why it matters:** the mark is the brand signature and it appears twice in a
  two-page file at visibly different weights. A stroke set in user units scales
  with the box; it has to be corrected per size.
- **Fix:** both instances must render at the brand kit's 1.25 pt.
- **Verdict:** **CONFIRMED (measured from SVG + CSS)**

### [MINOR] p.2 — the decorative repeat of the mark is larger than the signature itself, and exists to fill a hole

- **Dimension:** 2 Design craft
- **Evidence:** 46 mm on page 2 against 26 mm on page 1 — the repeat is **1.77×**
  the signature. `build/product.css` line 155 states the reason outright:
  *"The device anchors the foot of the column, so both columns finish on the same
  baseline instead of the short one stopping half-way."* Brand kit: *"One icon per
  product family, never more than one icon per listing image."*
- **Why it matters:** the hierarchy is inverted — the ornament outranks the mark —
  and the CSS comment concedes the ornament is there for the layout's convenience,
  not the reader's. It is also the visible symptom of M1.
- **Fix:** the column must be filled by something the buyer wants; the device must
  not be sized to plug a gap.
- **Verdict:** **CONFIRMED (measured + quoted)**

### [MINOR] build — `letter.html` documents a column ratio the stylesheet does not use

- **Dimension:** 1 Print & production (evidence integrity)
- **Evidence:** `build/letter.html` line 14: *"page 2 re-flows its columns to
  **1.28fr / 0.72fr**, so the steps column uses the extra width"*.
  `build/product.css` line 187: `body.size-letter .p2grid { grid-template-columns: 1.15fr 0.85fr; gap: 10mm; }`.
- **Why it matters:** small, but it is the third documentation claim in this build
  that does not match the code (see M4, M5). The Letter re-layout **is** genuine —
  I confirmed it independently: different column ratio, the intro set on one line
  instead of two, different wrap points, `fill_pct` 91.3 vs 92.0. The comment
  describing it is simply wrong.
- **Fix:** correct the comment.
- **Verdict:** **CONFIRMED (quoted both)**

### [MINOR] p.2 — the title leaves an orphan in all three editions

- **Dimension:** 2 Design craft
- **Evidence:** "Five minutes now, five minutes a / **month**" — "month" sits
  alone on the second line at 30 pt Fraunces in A4, Letter **and** Tablet. I
  opened all three renders. Caused by `.p2title { max-width: 150mm; }`
  (`build/product.css` line 92).
- **Why it matters:** a single orphaned word under a 30 pt display line is the
  most visible typesetting fault on the page, and it is the page's headline.
- **Fix:** the title must break at a considered point, or not break.
- **Verdict:** **CONFIRMED (all three renders opened)**

### [MINOR] p.1 — section rules are indistinguishable from writing lines

- **Dimension:** 2 Design craft · 4 Instructional quality
- **Evidence:** `.block__name` closes with
  `border-bottom: var(--hairline) solid var(--stone)` (`build/product.css` line 65);
  `.lines > i` uses `border-bottom: var(--hairline) solid var(--stone)`
  (`product-base.css` line 151). Identical weight, identical colour.
  I counted the full-width rules on rendered A4 page 1: **17 rules**, at gaps of
  18.03 / 7.42 / 10.61 / 18.24 / 7.42 / 7.42 / 10.82 / 18.03 / 7.42 / 7.21 /
  11.03 / 17.82 / 7.42 / 18.24 / 18.03 / 7.42 mm. The 7.4 mm gaps are writing
  lines; the rest are structure — and nothing distinguishes them visually.
  Brand kit separates the two: *"hairline rules `0.5 pt` stone; **section rules
  `1 pt` primary**"*.
- **Why it matters:** the rule under "2 THREE GOALS" reads as a line to write on.
  On a sheet whose entire function is knowing where to write, the structural rules
  and the writing rules must not look the same.
- **Fix:** section rules to the brand kit's 1 pt primary, so the writing lines are
  the only stone hairlines on the page.
- **Verdict:** **CONFIRMED (measured + quoted)**

### [MINOR] p.1 — the A4 intro wraps to two lines for no reason

- **Dimension:** 2 Design craft
- **Evidence:** `.intro { max-width: 118mm; }` (`build/product.css` line 32) makes
  A4 set *"Fill this in once. Put it where you'll see it. Come back to it on the
  first Sunday / of every month."* over two lines. Letter and Tablet override to
  `max-width: none` (lines 175–176) and set the same sentence on **one** line.
  I opened all three: the compass device clears the intro vertically in every
  edition, so the 118 mm cap buys nothing.
- **Why it matters:** the flagship paper size gets the worse setting of the
  product's first sentence, and a ragged hole to its right.
- **Fix:** let A4's intro take the measure the other two editions already take.
- **Verdict:** **CONFIRMED (measured + all three renders opened)**

### [MINOR] package — `README.txt` copy passes through no gate

- **Dimension:** 1 Print & production (evidence integrity) · 9 Compliance
- **Evidence:** `spec_coverage.py` takes a single PDF; I ran it on the A4 file,
  as the builder did. `README.txt` is never covered. It contains builder-written
  sentences that appear in no ledger — e.g. *"Undated. Use it in any year,
  starting any day."*, *"The writing lines are 7.5 mm apart, which suits a normal
  pen."*, *"Both are ink-light: they print in pure black and white with no loss."*
  `build/new-copy.md` scopes itself to *"Every string in the built PDF"*.
  (`banned_terms.py` **does** cover it — `qa/terms-all.json` includes README and
  passes — so this is a coverage gap, not a compliance one.)
- **Why it matters:** `README.txt` is the file that makes the three tablet-app
  claims and the ink claim. Those are the product's riskiest unverified
  assertions and nothing checks them against the spec.
- **Fix:** the README's sentences need the same ledger discipline as the PDF's.
- **Verdict:** **CONFIRMED**

### [MINOR] p.1 — the product claims to be undated and reusable, then gives nowhere to write the year

- **Dimension:** 4 Instructional quality · 6 Productivity value
- **Evidence:** `README.txt`: *"Undated. Use it in any year, starting any day."*
  Page 1 has no year field — I checked the full extracted text layer and opened
  all six page-1 renders. The footer carries only `v1.0 · 2026-09`, which is the
  document version, not the buyer's year.
- **Why it matters:** the product is explicitly sold as reusable across years and
  is designed to be pinned up. Two completed copies are indistinguishable, and
  the sheet cannot say which year it is the plan for. The undated claim is
  builder-written (see the README finding above), so the gap is self-inflicted.
- **Fix:** a place to write the year, without breaking the five-block rhythm.
- **Verdict:** **CONFIRMED (absence)**

---

### [IDEA] the page never states its time cost, where the market always does

Page 2's title says "Five minutes now, five minutes a month" — which is the right
promise, on the wrong page, since page 1 is the sheet that gets pinned up.
The research records that competitors describe free kits by **component count and
time cost, never by page count**: *"Takes about 5 minutes"* (Keystone Habit
Finder), *"About 20 minutes to set up, then 30 seconds a day"* (Rest-of-Year
Comeback Plan) — `research/raw/gumroad/ideastothrive/habit-finder.json`,
`…/rgirz.json`. Owner's call; beyond the spec.

### [IDEA] email capture is a listing job, not a page job — recorded so it is not re-litigated

The spec opens: *"It exists to earn the email address…"*, and the product contains
no capture mechanism. **This is correct.** The plan puts capture at the platform:
*"Free product → Gumroad email capture → a five-email welcome sequence"*
(`Product Plans/2026-09-12 Product Plan.md`), and the research confirms the
mechanism is the $0 checkout itself — *"the free duplicate captures their email
(Gumroad checkout requires one)"* (`research/audits/gumroad-chrisnotion-iummy.md`).
I raise no finding against the product. It belongs on the listing.

### [IDEA] the honest-limit line is the strongest copy in the product and is buried

*"This free page is the whole page — there's no locked version of it."* This
matches the pattern the research singles out as borrowable — Organized
dashboard's *"⚠️ What This Free Version Doesn't Do"*
(`research/audits/gumroad-organizeddashboard-knhhvu.md`). It currently sits below
the link, in the emptiest part of the sheet. Owner's call whether it earns a
stronger position or a listing slot.

---

## Dimension scores

| # | Dimension | Score | Why |
|---|---|---|---|
| 1 | Print & production | **5** | Trim exact on all three editions (210.000×297.000, 215.900×279.400, 428.625×571.500 mm); 6 static faces embedded, no Type3; ink 1.45–2.02% against an 8% limit; text layer extracts clean and in order in all three; 0.21 MB against Gumroad's 250 MB cap; `licences/` shipped with a manifest. Docked nothing here — M4/M5 are log-accuracy defects, scored under evidence integrity, not print. |
| 2 | Design craft | **2** | Page 1 is a genuine 4 — clean grid, three content type sizes, one accent. Page 2 drags the score down: 111.4 mm (37.5%) of dead paper in the cross-sell column, a 46 mm ornament sized to plug it, a 30 pt orphan ("month"), and section rules indistinguishable from writing lines. Half the product is page 2. |
| 3 | Copywriting | **4** | The voice is right and verbatim to spec: "Three things, not ten. Number them in the order you'd protect them if the year got hard." · "A plan you've edited is a plan you're using." · "This free page is the whole page — there's no locked version of it." Docked one for the page-1/page-2 redundancy (three of five steps restate the intro) and a cross-sell that names no price, format or size. |
| 4 | Instructional quality | **3** | A stranger can complete page 1 alone; every prompt is answerable in one line and no term is used before it is defined. But there is no worked example anywhere — and the research names exactly that as a competitor weakness twice over ("no example of a completed page", `research/audits/gumroad-ideastothrive-habit-finder.md`; "no example of a filled month", `research/audits/gumroad-heyismail-HabitTracker.md`). No year field. Page 2 calls them "the five blocks"; page 1 never uses the word. |
| 5 | Uniqueness | **4** | The research set records **no** single-sheet "year on one page" printable at all. The nearest competitor is Ideas To Thrive's free *Rest-of-Year Comeback Plan* — "One-page goal rebuild + 7-day visual tracker", 104 downloads, 0 ratings, listing scored 3.9, described by the research as corporate-clean (`research/sellers/gumroad-S3-ideastothrive.md`). This is typographically far ahead of it. Docked one because the five blocks themselves are a conventional goal-sheet structure; the craft is the differentiator, not the content. |
| 6 | Productivity value | **3** | It does change a decision: ranking three goals by "the order you'd protect them if the year got hard" and naming a floor habit are real forcing functions, and the monthly return is specified. But nothing closes the loop — no re-audit artefact, nothing to compare against next month, no year field. The closest competitor pairs its one-pager with a 7-day tracker for exactly this reason (`research/raw/gumroad/ideastothrive/rgirz.json`). |
| 7 | Marketability | **2** | Zero listing images against a 10-slot brand standard, a spec that names three mockups, and a market norm of 2–3 even on free products. The click target is the most recessive text on the sheet. The URL is a placeholder domain. The craft would photograph beautifully — none of it has been photographed. |
| 8 | Accessibility | **4** | Measured on paper: body/prompts `#1F2A36` **13.74:1**; disclaimer `#4C535C` **7.37:1**; all primary text (kickers, block names, footer, line numerals, link) **5.40:1** — every text colour passes AA. Accent never carries meaning and survives greyscale: I measured the brass rule at grey 205 against the stone rules at 233 in `…-p02-grey.png`, so it stays distinguishable. Text layer intact for screen readers in all three editions. Writing lines measured at 7.42 mm against a 7.5 mm spec — within one raster pixel. Docked one: the 8.5 pt / 8 pt mono sits at the very floor, and that floor is where the URL lives. |
| 9 | Compliance & IP | **5** | `banned_terms.py` PASS on the A4 PDF and, per the builder's `terms-all.json`, across all three PDFs plus README. No "Wheel of Life", GTD, PARA, 12 Week Year, WOOP, Atomic Habits or "Life Compass" — notable given the research set contains a competitor "WOOP Activation Kit" we correctly avoid. The mandatory reflection disclaimer is present and correct on page 1 of every edition. Three OFL licences shipped with `FONT-LICENCES.md`. All art original; the compass is deliberately not the ikigai Venn. |

---

## Is this better than the competitor free products in the research report?

**On craft, yes — decisively. On everything that turns craft into ratings, not yet.**

The evidence for "yes": the report's own judgement of the closest competitor set
is that Ideas To Thrive's seven free kits *"look like web forms: plain, identical,
no designed printable. **The same tools, beautifully typeset (and in
tablet-planner form), would outclass them**"*
(`research/sellers/gumroad-S3-ideastothrive.md`). This product is precisely that
brief executed — and it is executed well. At 1.45–2.02% ink it is far under the
8% that Ideas To Thrive markets as a *paid* feature on its $29 Discipline System
(`research/raw/gumroad/ideastothrive/discipline-system.json`), and it ships a
genuine Letter re-layout rather than a scaled A4, which that same competitor also
sells as a paid differentiator. No free product in the research set does either.

The evidence against complacency, which I think matters more:

1. **Being prettier is not what earns ratings.** Ideas To Thrive's free kits took
   **1,145 downloads and earned 0–2 ratings each**
   (`research/sellers/gumroad-S3-ideastothrive.md`). Chris's freebies earn
   ratings at 1.7–2.7% of sales because the download steps *ask*: *"Before you
   click on the template link make sure to give this product a rating"*
   (`research/audits/gumroad-chrisnotion-ylqkn.md`). Our rating request exists and
   is well written — but it is the second-to-last section of a `.txt` file.
2. **Free downloads do not demonstrably drive Discover ranking; ratings do.** The
   research's discovery was run on `sort=most_reviewed`, and states that free
   tiers drive ranking *because ratings accumulate* — not because downloads do.
3. **It cannot be listed.** Zero images against a market norm of 2–3 on free
   products and a 10-slot house standard.
4. **No competitor comparison exists for this exact shape.** The research set
   records no single-sheet year planner, so there is no benchmark for whether two
   pages is the right size for a free lead magnet — and **no free product in the
   entire set has a page count recorded anywhere**. If anyone argues "2 pages is
   too thin" or "about right", that is judgement, not evidence.

My judgement, not evidence: page 1 is good enough that I would print it and pin it
up. Page 2 is the reason I would not click through — it repeats what I just read,
then offers the upgrade in the smallest type on the sheet, surrounded by 111 mm of
nothing. For a lead magnet, page 2 is the product.

---

## What I could not verify here

- **Whether the `.claude` pipeline fixes are correctly applied elsewhere.** I
  verified only that this product's text layer is clean.
- **Whether `Products/_assets/product-base.css` is unmodified**, as `BUILD-LOG.md`
  §1 claims. This is not a git repository, so there is no history to diff against.
- **The `banned.json` rule change** described in `BUILD-LOG.md` §4. It is
  pipeline-wide and I did not audit it; I confirmed only that the current
  `banned_terms.py` passes this product and correctly reports the reflection
  disclaimer present.
- **Anything about real buyers.** The research set contains **no review text at
  all** — Gumroad exposes only star breakdowns — so there is zero evidence about
  what buyers say about free products.

## What still needs a human with a printer and a tablet

Nothing in this section has been tested. I make no claim about any of it.

- **One A4 and one Letter sheet off a real printer.** The writing rules are
  `0.5 pt` stone — I measured them at **1.28:1** against the paper ground. That is
  correct for a pen guide and wrong for a cheap inkjet or a draft-mode laser,
  which is exactly what drops hairlines. This is the highest-risk unverified item.
- **Writing on it with a real pen.** 7.5 mm pitch is correct in the file (I
  measured 7.42 mm rendered). Whether it suits normal handwriting, and whether the
  `1.` `2.` `3.` numerals — absolutely positioned at `left: 0` — crowd the start of
  the line, only a person with a pen can say.
- **Pure greyscale on a mono laser.** The brass N marker survives in my raster
  (grey 205 vs 233) but a raster is not a print.
- **GoodNotes, Notability and Samsung Notes on real devices.** `README.txt` claims
  all three. **None has been opened.** Also unverified: whether a
  428.6 × 571.5 mm page imports sanely, and whether the single outbound link is
  tappable in each app.
- **Whether anyone will type a URL off a printed page at 8.5 pt.**

## Questions only the owner can answer

1. **Confirm or replace the brand name.** "Quiet Compass" is a logged
   `[Assumption]` in `brand-kit.md`, still unconfirmed. It is literal text in the
   page-1 kicker, both running footers, the footer domain, `README.txt` and all
   three file names. Not a builder failure — but it blocks the listing, and the
   brand kit is explicit that its own conflict screen *"is a search screen only,
   NOT a legal clearance"*.
2. **Provide the real PB-002 listing URL.** `quietcompass.example/compass-system`
   is a placeholder printed on page 2 of all three editions. Blocks the listing.
3. **Provide the real support email.** `hello@quietcompass.example` is a
   placeholder in `README.txt`. Blocks the listing.
4. **Confirm the pipeline-wide `banned.json` rule change** described in
   `BUILD-LOG.md` §4. It affects every product, not just this one.
5. **Free-tier structure (plan Q3).** Separate free listing or a $0 tier inside
   PB-002's listing. The research explicitly leaves this open — report
   "Open questions" #3 — and records both patterns working. Nothing in these
   files depends on the answer; the listing does.
6. **Are listing images in scope for this product?** The spec's Deliverables table
   says no; its Assets section and the brand kit say yes. See the MAJOR above.
7. **Does page 2's copy get to change?** Two of my three most important findings
   are against spec-verbatim copy that `spec_coverage.py` passes. Without a spec
   amendment the builder cannot fix them.
