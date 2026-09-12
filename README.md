# Northing Studio — product agents

An agent pipeline that researches a market, plans a product line, builds the
actual sale-ready PDFs, audits them, and prepares the shop listings. Built for
[Claude Code](https://claude.com/claude-code); the agents and skills are plain
Markdown and Python, so they are readable and editable without running anything.

## The chain

| Agent | Does | Produces |
|---|---|---|
| `digital-product-researcher` | Studies top-earning sellers, listings, images and design patterns | A dated research report |
| `product-planner` | Turns evidence into a buildable plan | Brand kit, product ladder, page-by-page build specs |
| `product-builder` | Composes the real pages and renders them | Print-exact A4 / Letter / tablet PDFs, README, licences |
| `product-critic` | Audits the build independently across 9 dimensions | Evidence-bound findings, SHIP / FIX / REBUILD |
| `listing-creator` | Writes the SEO copy and builds the shop images | Instruction PDF, 8–10 listing images, `listing.json` |

The builder and critic run as a **build → critique → revise loop**, three rounds
maximum, orchestrated by `/build-product`.

## Why you can trust its output

Every agent in this pipeline is prevented from making things up, structurally
rather than by instruction:

- **One source of truth.** The build spec decides the product's copy. New
  sentences must be justified in a ledger, or `spec_coverage.py` fails the build.
- **Claims are measurements.** Page counts, trim sizes, embedded fonts, ink
  coverage, type sizes and dead space all come from scripts, never from memory.
- **Look before judging.** No statement about how a page looks is allowed without
  the agent having opened the rendered image.
- **Fix means re-measure.** A finding is only closed when the gate that caught it
  is re-run and its new output pasted in.
- **Listings cannot lie about the file.** `check_listing.py` cross-checks the
  claimed page count and formats against the actual shipped PDFs.

## Skills

`printable-pdf` · `listing-images` · `listing-copy` · `product-qa` ·
`product-build-loop` · `product-brief-format` · `listing-image-audit` ·
`pdf-report` · `pdf-protect` · `etsy-gumroad-scraper`

## Platform facts these scripts encode

Each of these cost real debugging time and is handled automatically:

- Chrome renders **variable fonts as Type3 outlines** in PDF output —
  unselectable, unsearchable, rejected by print shops. `fetch_fonts.py` pulls
  static instances instead.
- **CSS `opacity` on text silently corrupts the PDF text layer**: glyphs are
  emitted separately and out of order, so "IF YOU WANT MORE" extracts as
  "I F  Y O U…". Fade with `color-mix` toward the paper instead.
- Chrome `--headless=new` often **writes the file then never exits**, and a
  stalled write looks identical to a finished one by byte count. The builders
  wait for `%%EOF`.
- Chrome's A4 is **209.89 mm**, so every page box is normalised after rendering.
- Raster checks fix resolution in **pixels per millimetre**, not per sheet —
  otherwise hairlines vanish on larger sheets and a page reads as 14.7% empty on
  A4 and 54.4% on tablet.
- `font-size` inside SVG is in **user units, not points**, so it scales with the
  viewBox and clips labels.

## Requirements

macOS, Google Chrome, `python3`, and `pip3 install pypdf markdown`.

## Not in this repository

Competitor research — around a thousand third-party listing images and the
scraped JSON behind them — is deliberately excluded. It is not ours to
redistribute, and the platforms' terms forbid it.
