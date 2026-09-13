---
name: listing-images
description: Plan and build the 8-10 listing images that sell a digital product on Etsy and Gumroad — an explicit slot brief the owner approves first (slot 1 hero, slot 2 decision page, slot 3 charter/output page, each slot naming its exact source page), then exact-size artboards rendered from brand CSS and real product pages via headless Chrome, with the 220px search-grid test. Use when creating or revising listing images, thumbnails, hero images or shop graphics.
---

# Listing images

The listing images are the shop. A buyer decides in a search grid **at about
220 px wide**, before reading one word of the description. Every rule here comes
from that fact.

Run everything from the repository root with `PY=.venv/bin/python`. Pinterest pins
share the artboard system but have their own skill (`pinterest-pins`).

## Sizes

| Artboard | Render at | Used for |
|---|---|---|
| Square `.art--sq` | **2000 × 2000** | Etsy primary + Gumroad square thumbnail |
| 16:9 hero `.art--hero` | **2560 × 1440** | Gumroad cover (it displays at 1280×720; render 2× so it stays crisp) |
| Tall `.art--tall` | **2000 × 2500** | Etsy 4:5, the tallest Etsy shows without cropping |
| Pin `.art--pin` | **1000 × 1500** | Pinterest (see `pinterest-pins`) |

Verify the current platform limits before a release — they change, and this file
is not authority on them.

## Step 1 — The slot brief (the owner approves it before any image exists)

`Products/PB-0XX <Name>/Listing/slot-brief.md`, one table row per slot:

```markdown
| # | Role | Artboard | Source PDF | Page | Source PNG | Overlay text |
|---|---|---|---|---|---|---|
| 1 | HERO | 2560x1440 | NorthingStudio_Focus-Audit_A4.pdf | 1 | qa/pages/a4/NorthingStudio_Focus-Audit_A4-p01.png | Find the 20% that matters · 24 pages · A4 + Letter + Tablet · undated |
| 2 | DECISION page — the Vital Few selection | 2000x2000 | NorthingStudio_Focus-Audit_A4.pdf | 14 | qa/pages/a4/NorthingStudio_Focus-Audit_A4-p14.png | Three, not thirteen |
| 3 | CHARTER / OUTPUT — the Focus Charter | 2000x2000 | NorthingStudio_Focus-Audit_A4.pdf | 17 | qa/pages/a4/NorthingStudio_Focus-Audit_A4-p17.png | The page you pin up |
| 4 | … | | | | | |
```

| # | Role | Rule |
|---|---|---|
| 1 | **HERO** | the formats, the page count and (when the product is undated) "undated", all from `dist/` |
| 2 | **Interior DECISION page** | the page where the method makes the buyer choose |
| 3 | **CHARTER / OUTPUT page** | what the buyer ends up holding |
| 4–10 | the rest of the tour | INCL (what you get, with counts) · DEMO (a filled-in page, real pen marks) · PAGES (prompts readable) · COMPAT (print / tablet / apps, honestly) · SIZE (formats and dimensions) · HOWTO · BUNDLE (only real bundle maths) |

- **Every filled slot names its exact source page.** That means the shipped PDF,
  the page number, and that page's render in `qa/pages/<edition>/`
  (`<pdf stem>-pNN.png`).
- **A slot that cannot be filled** writes `N/A - <reason>` in Role (e.g. a 2-page
  freebie has no separate charter page).
- **Eight filled slots is the floor; ten is the standard.**

```bash
$PY scripts/check_slot_brief.py "Products/PB-0XX <Name>"             # validates the brief
$PY scripts/upload_to_drive.py --product "Products/PB-0XX <Name>" --stage brief   # orchestrator: send it for review
$PY scripts/check_slot_brief.py "Products/PB-0XX <Name>" --approve   # orchestrator, ONLY after the owner says yes
```

`--approve` writes `Listing/slot-brief.APPROVED` with the brief's sha256.
`release_check.py --listing` fails if the brief changes afterwards. A changed slot
means a new brief and a new approval.

## Step 2 — Build the approved images

```bash
L=.claude/skills/listing-images/scripts
D="Products/PB-006 The One-Page Year"

# 1. real product pages are already rendered by the build: qa/pages/<edition>/*.png
#    (never redraw a page by hand)

# 2. write one artboard HTML per approved slot, linking the brand CSS
#    <link rel="stylesheet" href="../../../../brands/quiet-compass/fonts/fonts.css">
#    <link rel="stylesheet" href="../../../../brands/quiet-compass/artboard.css">

# 3. render each at its exact size
$PY $L/render_artboard.py "$D/Listing/build/01-hero.html" \
        -o "$D/Listing/images/01-hero.png" --size 2560x1440

# 4. the test that matters: shrink to 220 px, then LOOK at it with Read
$PY -c "from PIL import Image; im=Image.open('$D/Listing/images/02-thumb.png'); im.thumbnail((220,220)); im.save('/tmp/t.png')"
```

## Rules

1. **Readable at 220 px.** Headline ≥ 110 px on a 2000 px artboard. If you cannot
   read it shrunk, it does not ship.
2. **≤6 words in a headline**, one promise per image, never two headlines.
3. **One accent per image.** Brass marks one thing; it never carries text.
4. **Real pages only.** Page images come from the shipped PDF's renders. Never
   redraw, never mock a page that does not exist.
5. **Soft drop shadows are allowed only on mockup page stacks** — nowhere else in
   the brand.
6. **A device or a page stack, never both** in one frame.
7. **No stock photography, no third-party logos or badges.** "Works with
   GoodNotes and Notability" is plain text.
8. **No invented proof** — no "bestseller", no sales counts, no star ratings, no
   struck-through price that was never charged.
9. **Honest comparisons.** If a COMPAT table lists a competitor gap, it must be
   true and checkable. Say "annotate-only" or "fillable" exactly as the spec does.
10. **Same ground, same kicker position, same type sizes** across every listing,
    so the shop grid reads as one brand.
11. **No internal IDs** (PB-/BN-) in image filenames or on images.

## Verify before handing over

- `render_artboard.py` fails if the pixel size is off — platforms crop, we don't.
- Shrink every image to 220 px and **open it**. No claim about legibility counts
  without that.
- Check the greyscale/colour-blind read of anything where colour carries meaning.
- Confirm every number on an image matches the shipped files (page counts,
  formats). `check_listing.py` does this for the copy; images need your eye.
