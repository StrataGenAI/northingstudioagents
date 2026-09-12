# Critique — PB-022 The 10-Minute Life Audit, round 1

**Verdict:** FIX · **Blockers:** 0 · **Major:** 3 · **Minor:** 6 · **Ideas:** 2

Reviewed by the Product Critique Agent, 2026-09-12. Every gate below was re-run
by me; I did not read a number out of `BUILD-LOG.md` and repeat it. All 24 page
images (A4, Letter, Tablet × 4 pages × colour and greyscale) were rendered into
`qa/critic-pages-*/` by me and opened with Read before any sentence of this
document was written.

---

## Gates I ran

| Gate | Command | Result | Key numbers |
|---|---|---|---|
| Print, A4 | `verify_pdf.py … _A4.pdf --size a4 --expect-pages 4 --sparse-pages 1` | **PASS** | 4 pp, 210.0×297.0 mm, ink avg 2.5% / max 4.2% (limit 8%), type 8.0–34.0 pt, 6 embedded subsets, 0 fails, 0 warnings |
| Print, Letter | `verify_pdf.py … _Letter.pdf --size letter …` | **PASS** | 4 pp, 215.9×279.4 mm, ink avg 2.5% / max 4.1%, type 8.0–32.0 pt |
| Print, Tablet | `verify_pdf.py … _Tablet.pdf --size tablet …` | **PASS** | 4 pp, 428.6×571.5 mm (1620×2160 px), ink avg 2.5% / max 4.2%, type 16.1–65.3 pt, 6 internal links, 0 broken |
| Spec coverage | `spec_coverage.py "…PB-022….md" … --ledger build/new-copy.md` | **PASS** | 35 required strings checked, **0 missing**, 0 unjustified new copy (ledger has 19 entries) |
| Banned terms, A4 | `banned_terms.py … --require-disclaimer reflection` | **PASS** | 0 banned names, 0 unsafe claims, 1 tone warning; reflection disclaimer detected |
| Banned terms, Letter | as above | **PASS** | identical |
| Banned terms, Tablet | as above | **PASS** | identical |
| Render | `render_pages.py … --out qa/critic-pages-{A4,Letter,Tablet} --grey` | 24 images | all opened |

JSON written to `qa/critic-a4.json`, `qa/critic-letter.json`,
`qa/critic-tablet.json`, `qa/critic-coverage.json`, `qa/critic-terms.json`,
`qa/critic-terms-Letter.json`, `qa/critic-terms-Tablet.json`.

### Where my run disagrees with `BUILD-LOG.md`

1. **`spec_coverage.py` now passes clean.** BUILD-LOG §4.3 records
   `FAIL — 2 required string(s) missing` and spends ~40 lines explaining a
   quote-pairing artefact. My run reports **0 missing**. The gate was fixed at
   the pipeline level after that log was written; the log is stale, not wrong.
   No action for the builder beyond noting it in the next log entry.
2. **BUILD-LOG §8 misstates a shipped measurement.** It asks a human to "write
   on the 'why' lines and the page-4 ruled lines with a real pen — **7.5 mm**
   and 9 mm respectively." The shipped `build/product.css` sets the page-2 "why"
   band to **6.6 mm** on A4 and **6.0 mm** on Letter and tablet. See
   [MAJOR] p.2 below. This is the one disagreement with a consequence.

---

## Findings

### [MAJOR] p.4 — the right-hand stone panel is 80% empty; it does not read as finished
- **Dimension:** 2 Design craft · 7 Marketability
- **Evidence:** measured off `qa/critic-pages-A4/…-p04.png` (990×1400 px,
  4.714 px/mm) by decoding the PNG and scanning the panel column: the stone
  panel runs **y 16.3 → 274.7 mm, 258.4 mm tall, 64.1 mm wide**. Inside it,
  **205.6 mm of 258.4 mm carries no ink at all — 80%** — including a single
  unbroken void of **173.3 mm** between the end of the sell paragraph (72.8 mm)
  and the top of the "This free audit is complete as it is…" line (246.1 mm).
  The same shape appears in Letter (`…Letter-p04.png`) and Tablet
  (`…Tablet-p04.png`): two text blocks pinned to the top and bottom of a long
  empty tinted box. Source: `make_pages.py:276-281` puts a bare
  `<div class="fill"></div>` between them, and `product.css:110` lets it absorb
  every spare millimetre.
- **Why it matters:** this is the page that has to convert a free download into
  a PB-003 sale, and it is the last thing the buyer sees. A 17 cm empty grey
  rectangle reads as a layout that was never finished — the exact impression a
  free product must not leave, because it is the only evidence the buyer has
  about what the paid one will look like. It is also the single most visible
  defect in the product when the four pages are seen together.
- **Fix:** the panel must read as a composed block at its full height — whether
  by giving the panel only the height its content needs and letting the page
  breathe around it, or by earning the height with content the spec already
  allows. It must not be a tall box with a hole in the middle.
- **Verdict:** CONFIRMED (measured)

### [MAJOR] p.3 — the wheel is numbered on one spoke out of eight
- **Dimension:** 4 Instructional quality · 5 Uniqueness
- **Evidence:** `build/assets/wheel.svg` carries exactly five scale numbers —
  `<text x="86.59" y="71.96">2</text>` … `<text x="104.96" y="27.62">10</text>`
  — all five placed on the bisector between the HEALTH (N) and WORK (NE)
  spokes, confirmed visually in `qa/critic-pages-A4/…-p03.png` and its
  greyscale twin. The other **seven** spokes carry no numeric reference of any
  kind. The rings themselves are there and correct (5 circles at r = 12/24/36/
  48/60 units = scores 2/4/6/8/10), and ticks at 1/3/5/7/9 exist on all eight
  spokes (48 `<line>` elements = 8 spokes + 8×5 ticks, counted in the SVG), but
  the ticks are 2.6 mm long in stone hairline.
- **Why it matters:** the page's whole instruction is "Mark each score on its
  spoke". To place PEOPLE at 7, the buyer must carry a ring position from the
  top-right of the diagram around to the lower-right by eye, across a 120 mm
  circle, counting faint ticks with no number anywhere near them. The one task
  this page exists to support is harder than it needs to be. This matters twice
  over because the spec calls this the master asset — "built once here and
  reused (scaled) in PB-003 and PB-002" — so the defect propagates into a paid
  product where the same wheel is re-scored twelve times.
- **Fix:** every spoke must be markable without transferring a position from
  another part of the diagram. What that requires is the builder's call; the
  spec fixes the rings ("concentric rings at 2/4/6/8/10 in hairline stone") but
  says nothing about where the numbers go, so the numbering is free to change.
- **Verdict:** CONFIRMED (geometry measured); the impact on a real pen-and-paper
  user is PLAUSIBLE until a human marks one up.

### [MAJOR] p.2 — the eight "why" writing bands are below the brand kit's 7.5 mm floor
- **Dimension:** 8 Accessibility · 3 Copywriting (prompts a tired person can answer)
- **Evidence:** `build/product.css:74` — `.arow-why .rule { flex: 1 1 auto;
  height: 6.6mm; … }`, and `:147` / `:168` reduce it further:
  `body.size-letter .arow-why .rule { height: 6mm; }` and
  `body.size-tablet .arow-why .rule { height: 6mm; }`. `brand-kit.md`
  §"Visual system" states: "**Writing space:** ruled lines at **7.5 mm**
  (print) with a 0.5 pt stone rule." So all eight lines on the product's main
  input page are **12% under the house floor on A4 and 20% under on Letter and
  tablet**. Corroborated in the PDF: A4 page 2's rules sit on a 27.5 mm row
  pitch (measured from the page content stream: 123.8, 151.3, 178.8, 206.4,
  233.9, 261.4 mm), Letter's on 25.4 mm. `BUILD-LOG.md` §8 tells the human
  print-tester these lines are "7.5 mm".
- **Why it matters:** page 2 is where the buyer actually writes, eight times,
  and the builder's own human-check list names "large handwriting" as the test
  case. The deviation is undocumented — BUILD-LOG §7 records the page-4 9 mm
  rules and four other deviations as `[Assumption]`s, but not this one, so
  nobody downstream knows the house floor was crossed.
- **Fix:** either meet the 7.5 mm floor on all three editions, or record the
  deviation as an explicit `[Assumption]` with the reason and correct the
  figure in the human-check list. Silently shipping 6.0 mm while the log says
  7.5 mm is the part that must not stand.
- **Verdict:** CONFIRMED (measured)

### [MINOR] p.3 — the rings read at ~8% contrast in pure greyscale
- **Dimension:** 1 Print & production · 8 Accessibility
- **Evidence:** decoded `qa/critic-pages-A4/…-p03-grey.png` and sampled a
  vertical line 18 mm right of the wheel centre (chosen to miss the N spoke).
  Paper = **246**. The ring crossings read **221, 225, 226, 227** — a delta of
  **19–25 of 255, under 10%**. The spokes and the NE diagonal on the same line
  read **83**, a delta of **163**. The wheel's outer diameter measures
  **120.5 mm** against the spec's 120 mm, so the geometry is right.
- **Why it matters:** `brand-kit.md` makes greyscale legibility "a QA gate, not
  a preference", and `README.txt` promises "Every page prints legibly in pure
  black and white". The spec's own QA line — "the spokes stay distinguishable
  without colour" — is comfortably **met** (163 vs 20). The risk is the
  opposite one: the rings the buyer must find may be too faint on a real laser
  printer. Note that stone `#E4DCD0` hairlines on paper `#FBF8F3` is exactly
  what the brand kit prescribes, so this is a brand-level question, not a
  builder error — which is why it is MINOR and not MAJOR.
- **Fix:** none required of the builder this round. Route to the owner with the
  physical print check below; if a laser proof drops the rings, the brand kit's
  hairline value needs revisiting for every product, not just this one.
- **Verdict:** CONFIRMED (measured); the printed outcome is unverifiable here.

### [MINOR] p.1 — an 88 mm compass device the spec never ordered fills a 54%-full page
- **Dimension:** 2 Design craft · 4 Instructional quality
- **Evidence:** `qa/critic-a4.json` → page 1 `fill_pct` **54.2**, `max_gap_pct`
  **15.0** — the emptiest page in the product (pages 2/3/4 are 70.1, 62.2,
  95.1). `product.css:92` sizes the device at
  `.page--cover .device--cover { width: 88mm; height: 88mm; }` and
  `make_pages.py:192-194` drops it into a flex `.fill`. The spec's Assets list
  orders one compass: "**Small** compass device for the **footer**" — which is
  separately present and correct at 5 mm (`product.css:32`). The spec's page-1
  layout column reads "Title block; three short paragraphs; a stone box at the
  base" and orders no diagram.
- **Why it matters:** two different circles in a four-page product whose third
  page is titled "Your wheel". A first-time reader meets a large ringed circle
  with a brass dot on page 1, then a different large ringed circle on page 3,
  with nothing explaining that the first is a brand mark and the second is the
  exercise. The device is also doing the job of occupying 40% of the sheet
  rather than earning its place.
- **Fix:** either the page-1 device is justified in `build/new-copy.md` as a
  deliberate cover element at a size that does not compete with page 3, or the
  page is composed to stand without it.
- **Verdict:** CONFIRMED (measured); the reader-confusion claim is PLAUSIBLE —
  my judgement, not evidence.

### [MINOR] dist — the licence file points at a manifest that is not in the download
- **Dimension:** 9 Compliance & IP
- **Evidence:** `dist/licences/FONT-LICENCES.md` ends: "SHA-256 of every file:
  `manifest.json`." `find` over the whole product returns no `manifest*`; the
  only such file is `Products/_assets/fonts/manifest.json`, which is a build
  asset and does not ship. The shipped `dist/licences/` contains exactly
  `FONT-LICENCES.md` and three OFL texts.
- **Why it matters:** the licence record is the one document in the package a
  lawyer or a reseller-checker would read, and it cites evidence the reader
  cannot open. Small, but it is the kind of loose end that undermines the
  "everything is licensed and recorded" claim.
- **Fix:** ship the manifest, or stop citing it.
- **Verdict:** CONFIRMED

### [MINOR] p.1 — the spec strip omits the tablet edition the package contains
- **Dimension:** 7 Marketability
- **Evidence:** the page-1 strip reads `4 PAGES · 8 AREAS · 10 MINUTES ·
  A4 + LETTER · UNDATED` (extracted from all three PDFs). `README.txt` lists
  `QuietCompass_10-Minute-Life-Audit_Tablet.pdf 4 pages, 1620 x 2160 px`, and
  the tablet edition carries 6 working internal links. `brand-kit.md`'s
  exemplar strip is `24 PAGES · 7 DAYS · A4 + LETTER · **PRINT + TABLET** ·
  UNDATED`; the Product Plan's own slot-3 strip for PB-022 is
  `4 PAGES · 8 AREAS · 10 MINUTES · FREE`.
- **Why it matters:** the strip undersells the package on the page the buyer
  keeps, and it is the one line in the product that states what they got.
  Nothing here is dishonest — it is an omission, not a claim.
- **Fix:** the strip should describe what actually ships.
- **Verdict:** CONFIRMED

### [MINOR] p.4 — ~96 mm of the left column is blank band between fields
- **Dimension:** 2 Design craft
- **Evidence:** page-4 rule positions from the A4 content stream (mm from
  page top): 81.7/90.7, 125.1/134.1, 168.3/177.3, 211.7/220.7, 254.8/263.8.
  The pairs are a correct 9 mm apart, but the gap from each field's last rule
  to the next field's first rule is **34.4 mm**, of which roughly 24 mm is
  blank after allowing for the label — **four times, ≈96 mm of a ~210 mm
  column**. Letter and Tablet show the same pattern (Letter: 90.8→120.6,
  129.6→159.5, …). `product.css:111` — `justify-content: space-between` —
  distributes the leftover height into the gaps rather than into the lines.
- **Why it matters:** it is why page 4 reads airy-verging-on-unfinished even
  before the panel is considered. **But** the spec caps this page at "5 fields,
  1–2 lines each", and the builder is already at the top of that range, so the
  column mathematically cannot fill 210 mm within the spec. This is a spec
  tension, not a builder failure — recorded so the owner can decide.
- **Fix:** owner decision (see Q below). No silent change.
- **Verdict:** CONFIRMED (measured)

### [MINOR] p.4 — a prose sentence set as an all-caps mono field label
- **Dimension:** 3 Copywriting
- **Evidence:** the last field renders as
  `RE-SCORE IN 30 DAYS. DATE TO RE-SCORE:` — a two-sentence instruction set in
  letter-spaced uppercase IBM Plex Mono, identical in treatment to the
  four genuine labels above it (`WHEN, EXACTLY:`). The spec's string is
  sentence case: "Re-score in 30 days. Date to re-score:".
- **Why it matters:** `brand-kit.md` reserves mono for "anything that is a
  number, a code or a label"; an instruction with a full stop in the middle of
  it is none of those, and uppercasing it makes the calmest voice in the kit
  read as a shout at the foot of the page.
- **Fix:** the instruction and the label need to stop being the same object.
  The builder writes the treatment; the spec's words do not change.
- **Verdict:** PLAUSIBLE (judgement from reading the page)

### [IDEA] no worked example anywhere in the product
The spec orders none, so this is not a defect. But `product-qa` dimension 4
asks for "a worked example where the task is ambiguous", and "join the marks,
shade it in if you like" is the most ambiguous instruction in the file. The
Product Plan already budgets a hand-marked demo wheel as **listing slot 5**;
a small one inside the product would answer the question at the moment it is
asked. Owner's call, not a silent change.

### [IDEA] the "unlock" tone warning is the spec's own wording
`banned_terms.py` flags p4 on all three editions: *"This free audit is complete
as it is — the paid one goes deeper, it doesn't unlock this."* The builder
correctly refused to rewrite spec copy to silence a gate. The sentence is doing
honest work — it is the anti-hype line — and I would keep it. Recorded so the
warning is not mistaken for an unaddressed defect. This is the builder's Q6.

---

## Dimension scores

| # | Dimension | Score | Why |
|---|---|---|---|
| 1 | Print & production | **4** | All three editions pass every gate on my run: exact trim (210.0×297.0 / 215.9×279.4 / 428.6×571.5 mm), six embedded static subsets and no Type3, ink avg 2.5% / max 4.2% against an 8% limit, 0 fails and 0 warnings. Held off 5 by the ~8% greyscale ring contrast and the missing licence manifest. |
| 2 | Design craft | **3** | Pages 2 and 3 are genuinely well-composed — the zebra rows, the 5.2 mm score rings and the centred 120 mm wheel all hold their grid. Page 4's panel is 80% empty (173.3 mm void) and page 1 is 54.2% filled around an unordered 88 mm device. |
| 3 | Copywriting | **4** | Verbatim spec throughout — 35/35 required strings present, 0 unjustified new sentences, and the voice is the kit's: "Don't average your whole life into a 7." Docked for `RE-SCORE IN 30 DAYS. DATE TO RE-SCORE:` as an all-caps mono label. |
| 4 | Instructional quality | **3** | The arc genuinely chains: eight scores → the wheel → lowest/highest/surprising → one move → "When, exactly:" → a re-score date. Docked because the wheel numbers only one spoke of eight, and no worked example exists for "join the marks". |
| 5 | Uniqueness | **4** | The research report records that the self-audit category leader — Daniel Marthi's free Notion product, 2,278 mostly-free claims — **"never shows a wheel" on its listing** (report §Headline findings 5, and §"The Wheel of Life listing never shows a wheel… Notion-only, dark-mode"). A printable, pen-markable 120 mm wheel on warm paper is the thing the closest competitor does not have. |
| 6 | Productivity value | **4** | It changes a decision rather than only feeling nice: it ends on one named area, one move, a time, a success test and a 30-day re-score date. The 10-minute claim is honest for 4 pages. No restart path, but at four pages that is out of scope. |
| 7 | Marketability | **3** | Page 3 will photograph well and is the obvious hero. Held down by things that block the listing rather than the file: no outbound PB-003 link (the funnel's entire purpose), a placeholder support contact in `README.txt`, an under-stated spec strip, and page 4 — the cross-sell page — being the weakest-looking. |
| 8 | Accessibility | **3** | Ink `#1F2A36` on paper `#FBF8F3` throughout for small text; the brass marker is always paired with a label ("○ LOWEST AREA:") so nothing depends on colour; spokes hold at delta 163 in greyscale. Docked for 6.0–6.6 mm writing bands against a 7.5 mm house floor, and delta-20 rings. |
| 9 | Compliance & IP | **4** | The trademark rule holds — see below. Both disclaimers present (p.1 stone box, p.4 footer, plus README), the Money row carries its † "not financial advice" footnote, three OFL fonts with a licence record. Docked only for the manifest the licence file cites but does not ship. |

**Mean 3.6.**

### The trademark rule — checked four ways, clean

`WHEEL OF LIFE®` (Reg. 3918518, Success Motivation International, Inc.) appears
**nowhere**:

1. `grep -ril "wheel of life"` and `grep -riEl "wheel[ _-]?of[ _-]?life"` across
   the entire product folder — **no matches** (exit 1).
2. `find -iname "*wheel*of*life*"` — **no files**. Shipped names are
   `QuietCompass_10-Minute-Life-Audit_{A4,Letter,Tablet}.pdf`.
3. Extracted text layer of all three PDFs, every page, regex
   `wheel\s*of\s*life` case-insensitive — **clean** on all three.
4. PDF `/Title` metadata on all three: "The 10-Minute Life Audit — Quiet
   Compass — A4/LETTER/TABLET" — **clean**. (Metadata is a real hiding place
   and the gates do not read it.)

`README.txt` is clean. The device is our own eight-spoke drawing, generated by
`build/wheel.py`, and is not the four-circle ikigai Venn. The product's own
language is "the eight-area wheel" / "Your wheel". `banned_terms.py` passes on
all three editions with the mandatory reflection disclaimer detected.

### Page 4's stone panel — the direct answer

**No, it does not read as finished.** 80% of it is empty and 173.3 mm of that is
one continuous void. See the MAJOR above.

### The eight-area wheel — the direct answers

- **Markable at print size?** Geometrically yes: 120.5 mm measured across
  (spec: 120 mm), rings 12 mm apart, so one score point = 6 mm of spoke. That
  is comfortably pen-sized. The obstacle is not the size, it is the numbering.
- **Rings at 2/4/6/8/10 findable?** Present and correctly placed (5 circles at
  r = 12/24/36/48/60), plus ticks at 1/3/5/7/9 on all eight spokes (48 `<line>`
  elements counted). Findable on seven of eight spokes only by transferring a
  position by eye — see the MAJOR.
- **Reads in pure greyscale?** Yes, with a caveat. Spokes delta 163, rings delta
  19–25. The spec's requirement (spokes distinguishable from rings without
  colour) is met with room to spare; the rings' own faintness is the MINOR.
- **All eight labels complete and unclipped?** **Yes — the SVG sizing bug is
  genuinely fixed in the shipped file.** `wheel.svg` carries all eight as real
  `<text>` at `font-size="3.35"` units, and the text layer extracted from the
  shipped PDFs contains `HEALTH WORK MONEY PEOPLE HOME GROWTH PLAY DIRECTION`
  in full — I probed `DIRECTION`, `GROWTH`, `MONEY` and `PLAY` explicitly and
  all four are complete, on A4, Letter and Tablet. Confirmed visually on all
  six page-3 renders. No sign of `RECTION`, `ROWTH`, `MON` or `LAY`.

### The text-layer damage — measured, not assumed

I did not re-derive the `opacity` cause. I measured the result: a regex for
letter-spaced corruption runs (`(?:\b[A-Z]\s){4,}[A-Z]\b`) over the full
extracted text of all three editions returns **zero matches**, and
`IF YOU WANT MORE` extracts as one clean run on A4, Letter and Tablet. The
local fix in `product.css:124` holds. **No remaining damage.**

---

## What I could not verify here

- **Anything involving paper.** Whether the 6.0–6.6 mm "why" bands and the 9 mm
  page-4 rules take real handwriting; whether the 5.2 mm score rings can be
  circled with a real pen without swallowing the neighbour; whether a 100% /
  "Actual size" print lands on the measured trim.
- **Whether the delta-20 rings survive a laser printer.** Dot gain could rescue
  them or crush them. This is the single most valuable physical check in the
  product, because page 3 is the hero and PB-003 inherits the asset.
- **The brass marker and the brass rule on a real colour printer.**
- **Tablet behaviour.** I confirmed the 6 internal link annotations exist and
  resolve (p1→p2; p2→p1,p3; p3→p2,p4; p4→p3, 0 broken). I cannot confirm how
  GoodNotes, Notability or Samsung Notes honour them, whether the page flattens
  on import, or whether text stays selectable.
- **Real buyers.** Nothing here is a claim about what a buyer will do.

---

## Questions only the owner can answer

1. **Confirm the brand name "Quiet Compass."** `[Assumption]` throughout,
   including in the three shipped file names. Known and logged — not a builder
   failure.
2. **The PB-003 listing URL.** The spec orders "one outbound link on p.4 to the
   PB-003 listing"; the cross-sell copy is fully present but the link is not,
   because the URL does not exist yet. The builder correctly refused to invent
   one or ship a dead anchor. **This spec promise is unmet until the owner
   supplies the URL**, and it is the funnel's whole purpose.
3. **The support contact.** `dist/README.txt` ships
   `<SUPPORT CONTACT - owner to insert before the listing goes live>`. Known
   and logged. **The package cannot go live with this string in it** — it is
   the one thing standing between "FIX" and a releasable file.
4. **Page 4's blank bands.** The spec caps the page at "5 fields, 1–2 lines
   each", which cannot fill the column. Either the spec grows the field
   allowance or the page accepts the air. Not the builder's to decide.
5. **The shared `product-base.css` opacity defect.** The builder fixed it
   locally and did not touch the shared asset. Still open for every future
   product.
6. **The "unlock" tone warning** is the spec's own verbatim sentence — keep
   (my recommendation) or have the planner revise the spec.
7. **Free-listing structure** (plan §"Open questions" Q3) — still open per the
   spec's own header.

---

## Is it better than the competitor free products?

**Yes, on the axis the research says is open — and the evidence is cited, not
remembered.**

The research report's headline finding 5 records that the self-audit category
leader, Daniel Marthi's free Notion "Wheel of Life" with 2,278 mostly-free
claims, **"never shows a wheel" on its listing** [Observed], and §05 adds that
it is "Notion-only, dark-mode", with "stale '3.0' and undated sale banners" and
a hero with no text. The report names the free competitor set for PB-003 as
"Daniel Marthi: free Notion, no wheel shown · Easlo Wheel (free)". The
positioning map puts "warm, light, editorial × guided method" as the only open
quadrant.

This product puts a real, 120 mm, pen-markable eight-area wheel on warm paper,
in print **and** tablet form, with eight defined areas, a disclaimer, a money
footnote, and an honest "this free audit is complete as it is" upgrade line. On
what the buyer actually receives, it beats that set — it is the artefact the
category leader's listing does not even picture.

Two honest qualifications. First, the comparison is drawn from listing-level
observations in the report; I have not opened the competitors' actual files, and
neither did the report in every case. Second, the free competitors are Notion
templates — a different medium, so "better" here means better for someone who
wants paper or a stylus, which is exactly the audience the brand is for. The
aesthetic judgement that it looks like more care than the competitor set is
**my judgement, not evidence**.

---

## What a human with a printer and a tablet must still do

**Printer**
1. Print A4 at 100% / "Actual size"; confirm trim and the 15 mm margins.
2. **Greyscale laser proof of page 3** — the decisive one. Can you see the
   rings at 2/4/6/8/10 at all? They measure delta 19–25 of 255.
3. Mark up the wheel with a real pen. Are the odd-value ticks findable on the
   diagonal spokes? Can you join eight marks into a readable shape?
4. Circle a score on page 2's 5.2 mm rings without catching the neighbour.
5. Write on the page-2 "why" lines (**6.6 mm on A4, 6.0 mm on Letter — not the
   7.5 mm the build log states**) and the page-4 9 mm rules, with large
   handwriting.
6. Print Letter on real US Letter stock; confirm it is a re-layout, not a
   scaled A4.
7. Colour proof: the brass dot on p.3 and the brass rule on p.4.

**Tablet**
8. Import the tablet PDF into GoodNotes and Notability (and Samsung Notes if
   the listing will claim it). Tap all **6** internal links.
9. Confirm the page is not flattened on import and the text stays selectable.
10. Annotate the wheel with a stylus at tablet scale.

Nothing in this critique claims any of the above was done.
