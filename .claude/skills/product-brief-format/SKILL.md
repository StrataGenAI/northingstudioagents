---
name: product-brief-format
description: The fixed formats for digital-product planning (planners, journals, workbooks, audits, budgeting templates) — product briefs (PB-IDs) with evidence, opportunity scoring, page list, design direction, pricing and licence tiers, Etsy/Gumroad listing copy limits, a listing slot plan and a five-pin Pinterest plan; bundles (BN-IDs); launch lineups; the line brand kit; and page-by-page build specs with the required release fields (interaction, font set, protection, practitioner licence, cross-references). Use whenever writing or reading product ideas, briefs, bundles, launch plans, brand kits or build specs.
---

# Product brief format

Every product idea must use this exact structure. That lets the research agent write ideas, the Product Planning Agent compare and select them, and builders build from them without any back-and-forth.

## Rules
1. **ID scheme.** Products are `PB-001`, `PB-002`... Bundles are `BN-01`... Keep IDs stable; never renumber. **IDs are internal**: never in a customer filename, customer text, listing or pin.
2. **Every idea needs evidence.** Link at least one competitor listing, audit file, review quote or buyer-complaint theme (BC-ID) that shows demand or a gap. Ideas without evidence go in a separate "Speculative" list.
3. **Differentiate, don't clone.** State the competitor it's positioned against and the specific difference.
4. **Platform limits** (current Etsy rules; check again if they change): title ≤ 140 characters, 13 tags of ≤ 20 characters each, up to 20 listing images plus 1 video. Gumroad has no tag limit that matters. Its cover images display at 1280×720 (landscape) and the thumbnail is square. Pinterest: pin title ≤ 100, description ≤ 500, alt text ≤ 500 characters (checked 2026-09-13).
5. Use the **role codes** from the `listing-image-audit` skill for the image plan.
6. **Shop and lines.** The shop is NORTHING STUDIO (`brands/SHOP.md`). Every product belongs to a line with its own `brands/<line>/brand-kit.md` and locked `voice.md`. File names use the `NorthingStudio_` prefix.

## Brief template (copy exactly)

```markdown
### PB-0XX — <Working name>
| Field | Value |
|---|---|
| Line | quiet-compass · or a new line under brands/ |
| Category | one of: digital planner · reflective planning · purpose compass · goal planner · journaling pages · self-audit · 80/20 focus audit · money organization · goal workbook · concise goal sheet · Kaizen planner · budgeting |
| Target buyer | who, life situation, trigger moment (e.g. "new-year reset", "first salary") |
| Job to be done | the problem, in the buyer's words |
| Positioned against | competitor listing(s) + link |
| Our difference | 1–3 concrete differences (content, format, design, price, bundle) |
| Evidence | links to listings / audits / review quotes / BC-IDs (≥1) |
| Formats | printable PDF (A4+Letter) · tablet PDF (hyperlinked, screen layout) · Canva template · Notion · Google Sheets/Excel |
| Interaction | fillable · annotate-only |
| Dated / undated | ... |
| Size & orientation | A4 / US Letter / A5 / tablet portrait/landscape |
| Page count (est.) | n |
| Price & tiers | Basic $x · Pro $y · Bundle $z · Practitioner licence $p (or none); launch discount %; anchor price |
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
- Description outline: hook → what's inside → who it's for → how to use → compatibility (fillable / annotate-only) → FAQ → cross-sell (live products only)

**Listing image plan**
| Slot | Role | Content & headline | Source page | Visual notes |
|---|---|---|---|---|
| 1 | HERO | formats · page count · undated | cover / page stack | readable at 220px, one promise |
| 2 | DECISION page | ... | p. n | |
| 3 | CHARTER / OUTPUT page | ... | p. n | |
| 4 | INCL | ... | | |
| 5 | DEMO | ... | | |
| 6 | PAGES | ... | | |
| 7 | COMPAT | ... | | |
| 8 | SIZE | ... | | |
| 9 | HOWTO | ... | | |
| 10 | BUNDLE / BONUS | ... | | |

**Pinterest plan (5 pins)**
| Pin | Job | Source page | Title draft (≤100) |
|---|---|---|---|
| 1 | at a glance | | |
| 2 | the decision | | |
| 3 | the output | | |
| 4 | how it works | | |
| 5 | one exercise, readable | | |

**Risks & open questions**
- ...
```

## Scoring guide
- **Demand:** 5 = several competitors with 1k+ sales or bestseller badges; 1 = no evidence of sales.
- **Gap:** 5 = recurring review complaints (BC themes) or no strong listing serving this angle; 1 = crowded with excellent listings.
- **Ease:** 5 = under 15 simple pages, reuses our templates; 1 = complex hyperlinks or spreadsheet formulas, 100+ pages.
- **Price potential:** 5 = can sell at $15+ or anchors a bundle; 1 = under $3 commodity.
- **Brand fit:** 5 = core to the line's voice and brand kit; 1 = off-brand.

## Bundle template

```markdown
### BN-0X — <Bundle name>
Includes: PB-.., PB-.., PB-.. · Price: $x (sum of parts $y, saves z%) · Story: why these belong together · Hero concept: ...
```

## Launch lineup template

```markdown
| Order | ID | Name | Line | Why now | Format | Price | Dependencies |
|---|---|---|---|---|---|---|---|
```

## Brand kit template (planning stage → `brands/<line>/brand-kit.md`)

```markdown
# Brand kit — <Line name> line · NORTHING STUDIO (v<N>, YYYY-MM-DD)
## Positioning
One sentence: for <buyer> who <need>, <line> is the <category> that <difference>. Evidence: <links>
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
3 adjectives · pointer to the locked `voice.md` in this folder
## Visual system
Logo/wordmark direction · signature device · icon style · line weights · corner radius · texture/none
## Listing image and pin rules
Thumbnail formula · mockup style · headline rules (≤6 words, readable at 220 px) · pin composition · grid consistency rules
## Changelog
- vN YYYY-MM-DD: ...
```

A new line also gets `brands/<line>/voice.md` (same structure as `brands/quiet-compass/voice.md`: stance, numbered rules, banned words synced with `banned.json`, worked on/off-voice examples), `fonts/` (static instances via `fetch_fonts.py`) and `artboard.css`.

## Build spec template (one file per launch product → `Product Plans/specs/PB-0XX <Name>.md`)

```markdown
# Build spec — PB-0XX <Name> (v<N>)
Brief: <link to plan section> · Brand kit: brands/<line>/brand-kit.md v<N> · Voice: brands/<line>/voice.md · Owner decisions pending: <list or "none">

**Interaction:** fillable | annotate-only
**Font set:** brands/<line>/fonts
**Protection:** print + tablet editions | none — free lead magnet
**Practitioner licence:** yes | no
**Tablet margin max:** 8%            (optional; default 8% of the page width)

## Deliverables
| File | Format | Size / orientation | Notes |
|---|---|---|---|
| NorthingStudio_<Name>_A4.pdf | printable PDF | A4 210×297 mm portrait | ink-friendly |
| NorthingStudio_<Name>_Letter.pdf | printable PDF | US Letter 8.5×11 in | separate layout |
| NorthingStudio_<Name>_Tablet.pdf | tablet PDF | 1620×2160 px portrait, screen layout | links for every page reference; GoodNotes/Notability tested by the owner |
| README.txt + /licences | text | — | fillable/annotate-only statement, version stamp, LICENCE.txt pointer, support contact |

## Page setup
Margins · grid (columns/gutter) · baseline/line spacing for writing lines (e.g. 7–8 mm) · fonts + sizes per style · colours (hex from brand kit) · header/footer rules · page numbering · version stamp (`v1.0 · YYYY-MM`) on every edition

## Page-by-page
| # | Page | Purpose | Layout | Elements & exact copy | Writing space | Links (digital) |
|---|---|---|---|---|---|---|
| 1 | Cover | ... | ... | Title "...", subtitle "..." | — | → Start here |
| 2 | Start here | ... | ... | Full instruction text: "..." | — | → sections |
| 3 | ... | ... | ... | Prompt 1: "..." · Prompt 2: "..." | 6 lines each | ← index |
(repeat pages: state "×N" and what changes per copy)

## Cross-references
Every "page N" / "p. N" / "from page N" the copy uses, so the release gate can prove it still lands after any layout change. Write "None." if there are none.

| Reference text | Target page | Target heading | Editions |
|---|---|---|---|
| Copy your Day-0 scores from page 4 | 4 | Where you are today | all |
| p. 3 | 3 | Your wheel | Tablet |

## Hyperlink / tab map (digital)
Tab list and order · every link source → target · "back to index" rule · every cross-reference above is a link in the tablet edition

## Assets
Icons (style, count), illustrations, mockups needed for listing images and pins, licences

## Build plan
Order of work · estimated hours per step · total

## QA checklist
- [ ] Fonts embedded, brand faces only, text readable at 100% print
- [ ] All links tested in GoodNotes + Notability by the owner (and Samsung Notes if claimed)
- [ ] A4 and Letter both correct, nothing clipped in margins
- [ ] Tablet edition is a screen layout, not a zoomed print page
- [ ] Ink-friendly version prints cleanly in greyscale
- [ ] Files within platform limits (Etsy: currently max 5 files × 20 MB — re-check), named consistently, no internal IDs
- [ ] Copy proofread against voice.md; no competitor wording, no trademarks, required disclaimers present; cross-sells name live products only
```

The `## Cross-references` table header must not start with `#`. `spec_coverage.py` reads only the Page-by-page table, whose header does.

## Quality checklist (run before handing off)
- [ ] Every brief has all table fields, a page list, a design direction with hex codes, a listing copy draft, a listing image plan and a Pinterest plan
- [ ] Every brief links at least one piece of evidence
- [ ] Every spec has Interaction, Font set, Protection, Practitioner licence and a Cross-references section
- [ ] Titles are ≤140 characters; tags are ≤20 characters and there are 13
- [ ] No competitor trademarks or brand names in titles or tags
- [ ] Opportunity scores add up correctly, and ideas are sorted by score within each priority
