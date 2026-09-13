# Northing Studio — product agents

An agent pipeline that:
- scouts a niche
- researches its market and its buyers' complaints
- plans a product line
- builds the actual sale-ready PDFs
- audits them against real complaints
- prepares Etsy and Gumroad listings and Pinterest pins
- delivers every file to Google Drive

Built for [Claude Code](https://claude.com/claude-code) on a **headless Linux server**. The agents and skills are plain Markdown and Python, so they are readable and editable without running anything.

**NORTHING STUDIO** is the shop. **Quiet Compass** is its first product line (`brands/quiet-compass/`); further lines sit beside it.

## The chain

| Step | Agent / command | Does | Produces |
|---|---|---|---|
| 1 | `niche-scout` · `/scout-niche` | Reads `OUTCOMES.md`, validates the owner's keyword and competitor CSVs, scores niches | A ranked shortlist of 3, with a kill reason for every rejection |
| 2 | `digital-product-researcher` · `/research` | Studies top Etsy and Gumroad sellers, listings, images and design; collects 1–3 star reviews | A dated research report and `research/buyer-complaints.md` |
| 3 | `product-planner` | Reads `OUTCOMES.md`, turns evidence into a buildable plan | Line brand kit, product ladder, page-by-page build specs |
| 4 | `product-builder` | Composes the real pages and renders them | Print-exact A4 / Letter PDFs, a real tablet edition, page rasters, README, licences |
| 5 | `product-critic` | Audits the build across 9 dimensions, with rubrics from real buyer complaints | Evidence-bound findings, Pages opened record, SHIP / FIX / REBUILD |
| 6 | `listing-creator` · `/list-product` | Writes the SEO copy and a slot brief for owner approval, then builds the images | `listing.json`, approved slot brief, 8–10 listing images, instruction PDF |
| 7 | `pinterest-creator` | Builds five vertical pins from real pages | 1000×1500 pins, `pins.json`, pinning guide |

The builder and critic run as a **build → critique → revise loop**, three rounds
maximum, orchestrated by `/build-product`, followed by:
- the release gate
- protection
- `SIGNOFF.md`
- a verified upload to Drive

## Why you can trust its output

Every agent in this pipeline is prevented from making things up, structurally
rather than by instruction:

- **One source of truth.** The build spec decides the product's copy. New
  sentences must be justified in a ledger, or `spec_coverage.py` fails the build.
- **Claims are measurements.** Page counts, trim sizes, embedded brand fonts, ink
  coverage, type sizes and dead space all come from scripts, never from memory.
- **Look before judging.** No statement about how a page looks is allowed without
  the agent having opened the rendered image. Page rasters are a required build
  output, and the critic must list every page it opened.
- **Fix means re-measure.** A finding is only closed when the gate that caught it
  is re-run and its new output pasted in.
- **The critic judges against real complaints.** Its rubric comes from 1–3 star
  reviews of comparable products, not generic taste.
- **The voice is locked.** `brands/<line>/voice.md` is ground truth, and its
  measurable rules block a release through `banned_terms.py`.
- **A release gate checks what shipped past the critic before.**
  `scripts/release_check.py` fails on:
  - dead or placeholder URLs
  - products named that are not live in `catalogue.md`
  - formats claimed but not shipped (checked per format)
  - internal SKUs in filenames
  - page cross-references that moved
  - mismatched version stamps
  - a tablet edition that is really an A4 re-export
  - an undeclared fillable/annotate-only mode
- **Delivered means verified.** Nothing uploads with an open BLOCKER or MAJOR.
  Uploads are checked by hash on Drive, `SIGNOFF.md` carries only links from the
  upload record, and a failed upload is a failed build.
- **Humans check what machines cannot.** Printing, writing with a pen, and the
  tablet file in GoodNotes and Notability stay unticked for the owner. No agent
  may tick them.

## Setup (headless Linux)

```bash
scripts/setup.sh           # installs and verifies everything; safe to re-run
scripts/setup.sh --check   # verify only
```

It installs and checks:
- Google Chrome (headless)
- poppler (`pdftoppm`)
- rclone
- the brand fonts, registered with fontconfig
- `.venv` with pinned `pypdf`, `markdown`, `requests` and `Pillow` (`scripts/requirements.txt`)

Then it renders and verifies a smoke test. Exit 0 means ready. Exit 2 means
everything works except Google Drive, which needs the one-time step below.

Run every script with `.venv/bin/python` from the repository root.

### One-time manual steps (the owner)

These are detailed in `MULTI_AGENT_PLAN.md`:

| Step | What |
|---|---|
| **M1** | Create the rclone Drive token from a laptop and put it on the server outside the repo, then set `GDRIVE_CREDENTIALS` to its path (mode 600). |
| **M2** | Set `support_contact` in `brands/SHOP.md`. |
| **M3** | Set the practitioner licence price, and have the draft licence text in `brands/licences/` reviewed. |
| **M4** (optional) | Get an Etsy Open API key (`ETSY_API_KEY`), for Etsy review text and verifying Etsy links. |
| **M5** | Upload `keywords.csv` and `competitors.csv` (templates in `scripts/templates/`) to Drive `Northing Studio/research/input/`. |

## Google Drive layout

```
Northing Studio/
  <PB-ID>_<Product-Name>/
    deliverables/     A4, Letter and tablet PDFs, README, licences (+ practitioner/)
    listing/          listing copy, slot brief, 8-10 listing images, instruction PDF
    pinterest/        the five vertical pins, pins.json, pinning guide
    qa/               SIGNOFF.md, page PNGs, check outputs, critiques
  research/           research reports, buyer-complaints.md, niche shortlists
    input/            the owner's CSV exports (pulled by /scout-niche)
```

## Repository map

| Path | What |
|---|---|
| `brands/SHOP.md` | shop facts scripts read (support contact, licensor), open owner notes |
| `brands/quiet-compass/` | brand kit, locked `voice.md`, fonts, listing/pin artboard CSS |
| `brands/licences/` | personal and practitioner licence templates |
| `catalogue.md` | live products only — the release gate's list of what may be mentioned |
| `OUTCOMES.md` | the owner's 14- and 30-day numbers per listing; read before scouting and planning |
| `Product Plans/` | plans and build specs |
| `Products/` | builds: `build/`, `dist/`, `qa/`, `critique/`, `Listing/`, `Pinterest/` |
| `scripts/` | `setup.sh`, `release_check.py`, `upload_to_drive.py`, `append_drive_links.py`, `make_licence.py`, `check_slot_brief.py`, `niche_metrics.py`, `check_voice_sync.py`, `lib/` |
| `.claude/agents/` · `.claude/commands/` · `.claude/skills/` | the agents, the orchestrating commands and their skills |

## Skills

`printable-pdf` · `listing-images` · `listing-copy` · `pinterest-pins` ·
`product-qa` · `product-build-loop` · `product-brief-format` ·
`listing-image-audit` · `pdf-report` · `pdf-protect` · `etsy-gumroad-scraper`

## Platform facts these scripts encode

Each of these cost real debugging time and is handled automatically:

**Chrome and PDF output**
- Chrome renders **variable fonts as Type3 outlines** in PDF output —
  unselectable, unsearchable, rejected by print shops. `fetch_fonts.py` pulls
  static instances instead.
- **CSS `opacity` on text silently corrupts the PDF text layer**: glyphs are
  emitted separately and out of order, so "IF YOU WANT MORE" extracts as
  "I F  Y O U…". Fade with `color-mix` toward the paper instead.
- Chrome `--headless=new` often **writes the file then never exits**, and a
  stalled write looks identical to a finished one by byte count. The render
  helper waits for `%%EOF` (or the image end marker) and kills Chrome's whole
  process group.
- Chrome's A4 is **209.89 mm**, so every page box is normalised after rendering.
- `font-size` inside SVG is in **user units, not points**, so it scales with the
  viewBox and clips labels.

**The Linux server**
- On a server **with no font packages, fontconfig substitutes silently** when
  `fonts.css` fails to load. The page count still passes, so `verify_pdf.py --fonts`
  compares every embedded font with the line's manifest of PostScript names.
- On a server, Chrome logs D-Bus noise continuously; **stderr goes to a file**,
  because a full pipe blocks the render. `/dev/shm` is small, so Chrome runs with
  `--disable-dev-shm-usage`.
- Ubuntu's `chromium` is snap-only, and snap's private `/tmp` breaks temp profiles
  and output paths, so setup installs Google Chrome's .deb.
- Some sites stall **browser-looking user agents from datacenter IPs**, so the link
  checker identifies itself plainly.

**Measurement**
- Raster checks fix resolution in **pixels per millimetre**, not per sheet —
  otherwise hairlines vanish on larger sheets and a page reads as 14.7% empty on
  A4 and 54.4% on tablet. Rasters come from poppler; a missing rasteriser is a
  failure, never a skipped check.
- **pypdf 6.16.2+ extracts letter-spaced text as single letters**, which breaks the
  split-text gate and spec coverage. pypdf is pinned at 6.16.1.

## Not in this repository

Kept out of git on purpose:
- **Competitor research:** around a thousand third-party listing images, the scraped JSON behind them, and collected buyer reviews. It is not ours to redistribute, and the platforms' terms forbid it. It goes only to the owner's private Drive.
- **The owner's CSV exports:** third-party tool data.
- **Drive credentials:** they live outside the repo.
