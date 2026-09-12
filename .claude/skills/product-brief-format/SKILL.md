---
name: product-brief-format
description: The fixed formats for digital-product planning (planners, journals, workbooks, audits, budgeting templates) — product briefs (PB-IDs) with evidence, opportunity scoring, page list, design direction, pricing tiers, Etsy/Gumroad listing copy limits and a 10-slot image plan; bundles (BN-IDs); launch lineups; the brand kit; and page-by-page build specs for designers. Use whenever writing or reading product ideas, briefs, bundles, launch plans, brand kits or build specs.
---

# Product brief format

Every product idea must use this exact structure. That lets the research agent write ideas, the Product Planning Agent compare and select them, and designers build from them without any back-and-forth.

## Rules
1. **ID scheme.** Products are `PB-001`, `PB-002`... Bundles are `BN-01`... Keep IDs stable; never renumber.
2. **Every idea needs evidence.** Link at least one competitor listing, audit file or review quote that shows demand or a gap. Ideas without evidence go in a separate "Speculative" list.
3. **Differentiate, don't clone.** State the competitor it's positioned against and the specific difference.
4. **Platform limits** (current Etsy rules; check again if they change): title ≤ 140 characters, 13 tags of ≤ 20 characters each, up to 20 listing images plus 1 video. Gumroad has no tag limit that matters. Its cover images display at 1280×720 (landscape) and the thumbnail is square.
5. Use the **role codes** from the `listing-image-audit` skill for the image plan.

## Brief template (copy exactly)

```markdown
### PB-0XX — <Working name>
| Field | Value |
|---|---|
| Category | one of: digital planner · reflective planning · purpose compass · goal planner · journaling pages · self-audit · 80/20 focus audit · money organization · goal workbook · concise goal sheet · Kaizen planner · budgeting |
| Target buyer | who, life situation, trigger moment (e.g. "new-year reset", "first salary") |
| Job to be done | the problem, in the buyer's words |
| Positioned against | competitor listing(s) + link |
| Our difference | 1–3 concrete differences (content, format, design, price, bundle) |
| Evidence | links to listings / audits / review quotes (≥1) |
| Formats | printable PDF (A4+Letter) · hyperlinked PDF (GoodNotes/Notability) · Canva template · Notion · Google Sheets/Excel |
| Dated / undated | ... |
| Size & orientation | A4 / US Letter / A5 / tablet portrait/landscape |
| Page count (est.) | n |
| Price & tiers | Basic $x · Pro $y · Bundle $z; launch discount %; anchor price |
| Opportunity score | Demand _/5 · Gap _/5 · Ease _/5 · Price potential _/5 · Brand fit _/5 → **total _/25** |
| Bundle partners | PB-.. , PB-.. |
| Priority | Launch · Next · Later |

**Page list (in order)**
1. Cover — ...
2. How to use — ...
3. ... (name every page type, count repeats: "Weekly spread ×52")

**Design direction**
- Aesthetic tags: (from the listing-image-audit vocabulary)
- Palette: `#......` background · `#......` primary · `#......` accent · `#......` ink (4–5 hex)
- Typography: heading style + body style (+ accent), e.g. "serif-classic (Cormorant-like) + sans-humanist (Inter-like)"
- Layout notes: grid, white space, writing-space rules, ink-friendly version yes/no
- Navigation (digital): tab placement, hyperlink map

**Listing copy draft**
- Etsy title (≤140 chars): ...
- Tags (13 × ≤20 chars): tag1, tag2, ...
- Gumroad name + one-line summary: ...
- Description outline: hook → what's inside → who it's for → how to use → compatibility → FAQ → cross-sell

**Listing image plan (10 slots)**
| Slot | Role | Content & headline | Visual notes |
|---|---|---|---|
| 1 | HERO | ... | readable at 220px, one promise |
| 2 | INCL | ... | |
| 3 | PAGES | ... | |
| 4 | FEAT | ... | |
| 5 | DEMO | ... | |
| 6 | NAV / PAGES | ... | |
| 7 | PROOF / BRAND | ... | |
| 8 | COMPAT / SIZE | ... | |
| 9 | HOWTO | ... | |
| 10 | BUNDLE / BONUS | ... | |

**Risks & open questions**
- ...
```

## Scoring guide
- **Demand:** 5 = several competitors with 1k+ sales or bestseller badges; 1 = no evidence of sales.
- **Gap:** 5 = recurring review complaints or no strong listing serving this angle; 1 = crowded with excellent listings.
- **Ease:** 5 = under 15 simple pages, reuses our templates; 1 = complex hyperlinks or spreadsheet formulas, 100+ pages.
- **Price potential:** 5 = can sell at $15+ or anchors a bundle; 1 = under $3 commodity.
- **Brand fit:** 5 = core to a reflective / self-development / Kaizen brand; 1 = off-brand.

## Bundle template

```markdown
### BN-0X — <Bundle name>
Includes: PB-.., PB-.., PB-.. · Price: $x (sum of parts $y, saves z%) · Story: why these belong together · Hero concept: ...
```

## Launch lineup template

```markdown
| Order | ID | Name | Why now | Format | Price | Dependencies |
|---|---|---|---|---|---|---|
```

## Brand kit template (planning stage → `Product Plans/brand-kit.md`)

```markdown
# Brand kit — <Brand name> (v<N>, YYYY-MM-DD)
## Positioning
One sentence: for <buyer> who <need>, <brand> is the <category> that <difference>. Evidence: <links>
## Name
Chosen: ... · Shortlist: ... · Conflict screen: <what was searched, what was found> (not a legal clearance)
## Palette
| Role | Hex | Use |
|---|---|---|
| Paper/background | `#......` | page and listing backgrounds |
| Ink/text | `#......` | body text, rules |
| Primary | `#......` | headers, tabs |
| Accent | `#......` | highlights, badges (≤10% of any image) |
| Support | `#......` | fills, secondary blocks |
| Print-friendly variant | ... | ink-saving version rules |
## Typography (commercial-use licensed)
| Role | Font | Licence (link) | Sizes (print) |
|---|---|---|---|
| Headings | ... | OFL / commercial | ... |
| Body / prompts | ... | ... | ≥9 pt |
| Accent (optional) | ... | ... | ... |
## Voice
3 adjectives · do/don't table with example lines
## Visual system
Logo/wordmark direction · signature device · icon style · line weights · corner radius · texture/none
## Listing image rules
Thumbnail formula · mockup style · headline rules (≤6 words, readable at 220 px) · grid consistency rules
## Changelog
- vN YYYY-MM-DD: ...
```

## Build spec template (one file per launch product → `Product Plans/specs/PB-0XX <Name>.md`)

```markdown
# Build spec — PB-0XX <Name> (v<N>)
Brief: <link to plan section> · Brand kit: brand-kit.md v<N> · Owner decisions pending: <list or "none">

## Deliverables
| File | Format | Size / orientation | Notes |
|---|---|---|---|
| <Name>_A4.pdf | printable PDF | A4 210×297 mm portrait | ink-friendly |
| <Name>_Letter.pdf | printable PDF | US Letter 8.5×11 in | |
| <Name>_Tablet.pdf | hyperlinked PDF | tablet portrait (e.g. 1620×2160 px) | GoodNotes/Notability tested |
| (optional) Notion / Sheets link | template | — | delivered via PDF with link |

## Page setup
Margins · grid (columns/gutter) · baseline/line spacing for writing lines (e.g. 7–8 mm) · fonts + sizes per style · colours (hex from brand kit) · header/footer rules · page numbering

## Page-by-page
| # | Page | Purpose | Layout | Elements & exact copy | Writing space | Links (digital) |
|---|---|---|---|---|---|---|
| 1 | Cover | ... | ... | Title "...", subtitle "..." | — | → Start here |
| 2 | Start here | ... | ... | Full instruction text: "..." | — | → sections |
| 3 | ... | ... | ... | Prompt 1: "..." · Prompt 2: "..." | 6 lines each | ← index |
(repeat pages: state "×N" and what changes per copy)

## Hyperlink / tab map (digital)
Tab list and order · every link source → target · "back to index" rule

## Assets
Icons (style, count), illustrations, mockups needed for listing images, licences

## Build plan
Order of work · tool (Canva/Affinity/Figma/Notion) · estimated hours per step · total

## QA checklist
- [ ] Fonts embedded, text readable at 100% print
- [ ] All links tested in GoodNotes + Notability (and Samsung Notes if claimed)
- [ ] A4 and Letter both correct, nothing clipped in margins
- [ ] Ink-friendly version prints cleanly in greyscale
- [ ] Files within platform limits (Etsy: currently max 5 files × 20 MB — re-check), named consistently
- [ ] Copy proofread; no competitor wording, no trademarks, required disclaimers present
```

## Quality checklist (run before handing off)
- [ ] Every brief has all table fields, a page list, a design direction with hex codes, a listing copy draft and a 10-slot image plan
- [ ] Every brief links at least one piece of evidence
- [ ] Titles are ≤140 characters; tags are ≤20 characters and there are 13
- [ ] No competitor trademarks or brand names in titles or tags
- [ ] Opportunity scores add up correctly, and ideas are sorted by score within each priority
