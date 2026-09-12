---
name: product-qa
description: Critique and gate a finished digital product (planner, workbook, journal, audit) across print quality, design craft, copywriting, instructional value, originality, marketability, accessibility and compliance — with deterministic scripts for spec coverage and banned terms so findings are evidence, not opinion. Use when reviewing, critiquing or signing off a product build.
---

# Product QA and critique

A critique is only useful if the builder cannot argue with it. So every finding
carries **evidence** (a measurement, a quoted string, or a rendered page the
reviewer actually opened) and a **severity**. Anything else is an opinion and is
labelled as one.

## Deterministic gates — run these before writing a single sentence of critique

```bash
P=.claude/skills/printable-pdf/scripts
Q=.claude/skills/product-qa/scripts
D="Products/PB-001 The Focus Audit"

python3 $P/verify_pdf.py "$D/dist/…_A4.pdf" --size a4 --expect-pages 24 \
        --sparse-pages 1 --json "$D/qa/verify-a4.json"      # print gates
python3 $Q/spec_coverage.py "Product Plans/specs/PB-001 The Focus Audit.md" \
        "$D/dist/…_A4.pdf" --ledger "$D/build/new-copy.md" --json "$D/qa/coverage.json"
python3 $Q/banned_terms.py "$D/dist/…_A4.pdf" --require-disclaimer reflection \
        --json "$D/qa/terms.json"
python3 $P/render_pages.py "$D/dist/…_A4.pdf" --out "$D/qa/pages" --grey
```

`spec_coverage.py` is the anti-hallucination gate: it reports copy the spec
ordered but the PDF lacks (**MISSING**) and sentences the PDF contains that the
spec never authorised (**NEW**). Unjustified new copy fails the build; the
builder justifies additions in `build/new-copy.md`, one bullet each.

Then **open the rendered pages with Read**. No statement about how a page looks,
reads or feels may be made without having opened it.

## The nine dimensions

Score each 1–5 and give the reason. 3 = shippable, 5 = would win the category.

| # | Dimension | What to interrogate |
|---|---|---|
| 1 | **Print & production** | gate output: trim, embedded static fonts, 9 pt floor, ink ≤8%, greyscale legibility, page count matches the listing claim, file naming, licences folder |
| 2 | **Design craft** | grid discipline, one idea per page, type hierarchy (three sizes max), consistent furniture, the accent used once per page, real optical balance — half-empty pages and cramped pages are both defects |
| 3 | **Copywriting** | the brand voice (calm · specific · kind-but-firm), second person, concrete verbs, no hype, no shaming, prompts that a tired person can answer in one line, no instruction longer than it needs to be |
| 4 | **Instructional quality** | can a stranger complete this alone? Is every exercise defined before it is demanded? Is there a worked example where the task is ambiguous? Does each page produce an output the next page uses? |
| 5 | **Uniqueness** | what here exists nowhere in the research set? Name the competitor product closest to each page. A page that any template could produce is a liability |
| 6 | **Productivity value** | does completing it change a decision, or only feel nice? Is the time cost honest? Does it survive a bad week (a restart path), and does it close the loop (a re-audit)? |
| 7 | **Marketability** | perceived value against the price band, thumbnail legibility at 220 px, does the page set photograph well, does the spec strip match the file, is the cross-sell honest |
| 8 | **Accessibility** | contrast of every text colour on paper, never colour alone for meaning, writing lines usable by large handwriting, screen-reader text path intact |
| 9 | **Compliance & IP** | banned names (`banned_terms.py`), no borrowed method names or diagrams, disclaimers present, fonts licensed with a manifest entry, no competitor phrasing |

## Severity

| Severity | Meaning | Consequence |
|---|---|---|
| **BLOCKER** | a gate fails, or the product would mislead, infringe or embarrass | cannot ship; must be fixed this round |
| **MAJOR** | a buyer would notice and think less of it; or a promise in the spec is unmet | fix this round unless the owner decides otherwise |
| **MINOR** | craft polish, tightening, consistency | fix if cheap; may be deferred with a note |
| **IDEA** | an improvement beyond the spec's scope | never fixed silently — goes to the owner or the next version |

## Finding format (use exactly)

```markdown
### [BLOCKER] p.5 — the time log has no rows to write in
- **Dimension:** 2 Design craft · 4 Instructional quality
- **Evidence:** qa/pages/…-p05.png — the page is empty below the worked example;
  qa/verify-a4.json → page 5 `max_gap_pct` 27.4. The spec orders "16 log rows".
- **Why it matters:** the page promises a time audit and gives the buyer nowhere
  to do it; this is the single most visible defect in the product.
- **Fix:** build the 16-row `table.log` the spec specifies, 8 mm rows.
- **Verdict:** CONFIRMED (measured)
```

`CONFIRMED` = backed by a gate output or a quoted string. `PLAUSIBLE` = a
judgement from reading the page; say so, and never let a PLAUSIBLE finding block
a release on its own.

## Rules for the reviewer

1. **No invented facts.** Do not claim what competitors do, what buyers expect or
   what "research shows" unless it is in `Research Reports/` or `research/` — cite
   the file. Otherwise say "my judgement, not evidence".
2. **Read the spec first, the product second.** Most defects are unmet
   requirements, not taste.
3. **Quote, don't paraphrase.** Every copy criticism quotes the actual string.
4. **Count, don't estimate.** Pages, rows, links and millimetres come from the
   gate output.
5. **Separate taste from defect.** If it is preference, mark it MINOR or IDEA.
6. **Do not rewrite the product.** Say what is wrong and what the fix must
   achieve; the builder writes the copy.
7. **Sign off explicitly** — list every gate with its result, and state plainly
   what remains unverifiable without a physical printer or a tablet.
