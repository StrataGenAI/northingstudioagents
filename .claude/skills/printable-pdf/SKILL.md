---
name: printable-pdf
description: Build a sale-ready printable product PDF on a headless Linux server — exact A4/Letter page boxes, a real screen-proportioned tablet edition, embedded OFL brand fonts checked against the line's font manifest, real writing space, measured ink coverage and required page rasters — from hand-written HTML and CSS via headless Chrome, then verify it against print gates. Use when producing or revising a digital planner, workbook, journal or audit product for Etsy/Gumroad, not for reports (use pdf-report for those).
---

# Printable product PDF

The product a buyer prints is the product. This skill turns a build spec into
paper-exact PDFs and then **measures** them, so quality is a number, not an
opinion.

Reports use `pdf-report` (Markdown in, report out). This skill is for products:
you hand-write the HTML so every page is composed deliberately.

**Environment.** A headless Linux server with no display:
- `scripts/setup.sh` installs Google Chrome, poppler (`pdftoppm`), the brand fonts
  and `.venv` with the pinned Python packages.
- Run everything from the repository root with `PY=.venv/bin/python`.
- Chrome is found and driven by `scripts/lib/chromium.py`
  (`--headless=new --no-sandbox --disable-dev-shm-usage`; override with `CHROME_BIN`).
- Rasters come from `scripts/lib/raster.py`.

## Folder layout

```
brands/quiet-compass/
  fonts/                    fonts.css, *.woff (static), OFL-*.txt, manifest.json (with PostScript names), FONT-LICENCES.md
  brand-kit.md · voice.md
Products/
  _assets/product-base.css  the page system (copy of this skill's asset)
  PB-0XX <Name>/
    build/    a4.html · letter.html · tablet.html · product.css · new-copy.md · assets/*.svg
    dist/     NorthingStudio_<Name>_A4.pdf · _Letter.pdf · _Tablet.pdf · README.txt · licences/
    qa/       verify-*.json · coverage.json · pages/a4/ · pages/letter/ · pages/tablet/
```

## Pipeline

```bash
PY=.venv/bin/python
S=.claude/skills/printable-pdf/scripts
F=brands/quiet-compass/fonts
D="Products/PB-001 The Focus Audit"

# 0. once per machine (setup.sh does this): static fonts + licences + PostScript names, installed for fontconfig
$PY $S/fetch_fonts.py --dir $F
$PY $S/fetch_fonts.py --dir $F --install-system
$PY $S/fetch_fonts.py --dir $F --check --check-system      # before every release

# 1. render each edition from its own <body class="size-*">
$PY $S/build_pdf.py "$D/build/a4.html" -o "$D/dist/NorthingStudio_Focus-Audit_A4.pdf" --size a4

# 2. measure it — this is the only acceptable evidence of print quality
#    --fonts FAILS on any font that is not a brand face (a silent substitute).
#    --source is repeatable and FAILS the run if a source is newer than the PDF.
#    Pass every file the edition is built from: otherwise a half-finished revision
#    ships one rebuilt edition beside two stale ones, and every other gate passes
#    them, because each file is internally valid.
$PY $S/verify_pdf.py "$D/dist/NorthingStudio_Focus-Audit_A4.pdf" \
  --size a4 --expect-pages 24 --max-ink 8 --min-type 9 --sparse-pages 1 \
  --fonts $F/manifest.json \
  --source "$D/build/a4.html" --source Products/_assets/product-base.css \
  --json "$D/qa/verify-a4.json"

# 3. rasterise every page — a required build output, and the only way to look at a page
$PY $S/render_pages.py "$D/dist/NorthingStudio_Focus-Audit_A4.pdf" --out "$D/qa/pages/a4" --grey
```

Then `product-qa` for copy and content gates, `scripts/release_check.py` for the
release gate, and `pdf-protect` last of all.

## The page system

Link the line's `fonts/fonts.css` and `Products/_assets/product-base.css`. From
`build/` those links are `../../../brands/quiet-compass/fonts/fonts.css` and
`../../_assets/product-base.css`. Set the sheet on `<body>`, and write one
`<section class="page">` per printed page.

```html
<body class="size-a4 print-build">
  <section class="page page--cover">
    <p class="kicker">Northing Studio</p>
    <h1>The Focus Audit</h1>
    <p class="accent-line">Find the 20% that moves your life.</p>
    <div class="fill"></div>
    <p class="spec-strip">24 pages · 7 days · 20 min a day · A4 + Letter · undated</p>
  </section>
</body>
```

| Class | What it is |
|---|---|
| `size-a4` `size-letter` `size-a5` `size-tablet` | the sheet; must match `--size` on build_pdf.py |
| `print-build` | hides the tab rail — paper editions have no tabs |
| `ink-light` | panels lose their fill; use for the printable build |
| `.page` `.page--cover` | one printed page; content is clipped at the trim |
| `.fill` | eats the leftover height, so footers sit at the foot |
| `.runhead` `.runfoot` `.kicker` `.spec-strip` | page furniture |
| `.accent-line` | the one italic serif line per page |
| `.lines > i` | ruled writing lines at 7.5 mm |
| `.field` + `.label` + `.rule` | a labelled single-line answer |
| `.box` `.box--accent` | an open answer box (outline, never a fill). Content sits at the top so the space below stays writable; add `.box--center` only for a short label box. A `.chip` inside a box loses its frame so the number lines up with the text under it |
| `.grow` | lets boxes share a column's leftover height, so they bottom-align with a tall neighbour (a matrix or wheel) instead of stopping short |
| `table.log` | a grid the buyer writes in, 8 mm rows |
| `table.log--grid` | adds vertical rules between columns — use it whenever the columns are different *kinds* of thing, or a filled-in log reads as one smear |
| `.time` (`<i><b>:</b><i>`) | a `__ : __` clock or duration entry |
| `.tick` | a 5 mm box the buyer marks with a tick or a cross |
| `.mark` | our drawn tick/cross for legends — **never type ✓ or ✗**, they are missing from all three brand fonts and silently fall back to a system face (which `verify_pdf.py --fonts` now fails) |
| `.device` `.device--cover` | a brand device (compass, Kaizen loop, 80/20 bars) as inline SVG |
| `.panel` | worked example / quiet aside (stone) |
| `.matrix` + `.q1…q4` + `.axis` | a 2×2 drawn in rules, near-zero ink |
| `.tabrail a` + `.is-current` | digital tab rail, right edge |
| `.chip` `.marker` `.rule-accent` `.rule-soft` | small devices |

Colours and type come from the line's `brand-kit.md` via CSS variables (`--ink`,
`--paper`, `--primary`, `--accent`, `--support`, `--stone`). Never hard-code a hex
in a product file.

## Composition rigour

These rules are the part of the old `frontend-design` reference that applies to
paper. Its taste brief never did: the aesthetic is decided in the brand kit.
- **One idea per page.** If a page needs two headings of the same weight, it is two pages.
- **No generic layout.** Every page is composed for its one job; a grid any product
  could wear is a defect, not a starting point.
- **Three type sizes at most** per page, and a clear first place for the eye to land.
- **No web habits on paper:** no motion, gradients, dark themes, drop shadows or
  decorative cards.

## Rules that fail a build

1. **Static fonts only.** Chrome turns a *variable* font into Type3 outlines:
   unselectable, unsearchable, rejected by print shops. `fetch_fonts.py` fetches
   static instances; `verify_pdf.py` fails on any Type3 face. If you add a font,
   it needs a licence check recorded in `manifest.json`.
2. **Brand fonts only.** A server with no font packages substitutes silently
   (DejaVu, Liberation) when `fonts.css` does not load. The page count and every
   other gate still pass, so `verify_pdf.py --fonts <manifest>` compares every
   embedded font with the manifest's PostScript names and fails on a stranger.
3. **Exact trim.** Chrome's own A4 is 209.9 mm. `build_pdf.py` normalises every
   page box to the true size; never ship a PDF it has not normalised.
4. **9 pt floor.** No text smaller than 9 pt, ever.
5. **≤8% ink** on printable editions. That is a selling point in this market, and
   it is measured per page.
6. **Real writing space.** The gate measures the largest *empty band* on each
   page, because a page of ruled lines is mostly paper and perfectly finished,
   while a 25% strip of nothing between two blocks is not. It measures **per
   column as well as across the sheet**: on a two-column page a full-width scan
   counts a row as filled whenever *either* column has content, so one column can
   be a third empty while the sheet scores a few percent. Fill it with the
   writing space the spec promised, or list the page in `--sparse-pages` because
   it is deliberately airy (covers, section openers).
   **Known blind spot:** it cannot see emptiness *inside a filled panel*. A stone
   box's background marks every row as content, so a panel can be 80% empty and
   score clean. Filled panels must be judged by eye, every time.
7. **Rasters are required.** `render_pages.py` writes one PNG per page plus a
   manifest (PDF hash, page count) into `qa/pages/<edition>/`. It fails if
   `pdftoppm` is missing or a page is not rendered, and `verify_pdf.py` fails —
   never skips — when a page cannot be rasterised. `release_check.py` fails any
   edition without a full, current render.
8. **Letter is a re-layout, not a scale.** Build it from its own HTML with
   `size-letter`. Scaling A4 to Letter shifts every margin and is visible.
9. **The tablet edition is a screen edition, not an A4 re-export.** `size-tablet`
   (1620×2160 px, 3:4), composed for the screen. `release_check.py` fails:
   - A4 proportions, or the A4 file's dimensions
   - trim or bleed boxes
   - side margins over 8% of the page width (unless the spec sets `**Tablet margin max:**`)
   - any "page N" or "p. N" without a link that lands on that page
10. **Greyscale must work.** Render with `--grey` and read the image: matrices,
    quadrant labels and the accent marker must all still be legible.
11. **A4 and Letter carry no tab rail**; the tablet edition does, and every tab
    must resolve (the link gate counts dead annotations).

## When a page looks wrong

| Symptom | Cause |
|---|---|
| Type3 fonts in the report | a variable `.ttf` slipped into `fonts.css` |
| `font DejaVuSans… is not in the brand font set` | `fonts.css` not linked, or a path that does not resolve from the HTML (the brand folder moved to `brands/<line>/fonts/`) |
| Text bleeds past the trim | content taller than `.page`; it is clipped, not reflowed — shorten it or split the page |
| Blank trailing page | a stray `page-break-after` on the last `.page`, or a trailing element after it |
| Ink over budget | a filled `.panel` or a large coloured block; switch the body to `ink-light` |
| Chrome renders before the fonts load | raise `--budget` (default 15000 ms) |
| `FAIL: Chrome's PDF is incomplete` | the write stalled or Chrome was killed mid-write; render again, never measure the partial file |
| Text extracts as `O P A C I T Y`; copy-paste, search and screen readers break | **CSS `opacity` on text.** Chrome draws a faded run in its own transparency group and emits every glyph separately, out of document order. The page looks perfect, so only the text-layer gate finds it. Fade with a colour instead — `color-mix(in srgb, var(--ink) 75%, var(--paper))`. (If *every* letter-spaced kicker fails this gate, check that `.venv` has the pinned pypdf 6.16.1: later versions split letter-spaced text themselves.) |
| Tablet fails "print margins" | the tablet HTML is the print layout zoomed up; recompose it for the 3:4 screen with screen margins |
| SVG labels clipped, or absurdly large | `font-size` inside `<svg>` is in **user units**, not points, so it scales with the viewBox. A "9 pt" label on a 120-unit viewBox rendered at 120 mm comes out around 27 pt and clips. Size SVG text against the viewBox, or set the label in HTML outside the SVG |
