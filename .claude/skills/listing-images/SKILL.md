---
name: listing-images
description: Build the 8-10 listing images that sell a digital product on Etsy and Gumroad — exact-size artboards rendered from brand CSS and real product pages via headless Chrome, with the 220px search-grid test. Use when creating or revising listing images, thumbnails, hero images or shop graphics.
---

# Listing images

The listing images are the shop. A buyer decides in a search grid **at about
220 px wide**, before reading one word of the description. Every rule here comes
from that fact.

## Sizes

| Slot | Render at | Used for |
|---|---|---|
| Square | **2000 × 2000** | Etsy primary + Gumroad square thumbnail |
| 16:9 hero | **2560 × 1440** | Gumroad cover (it displays at 1280×720; render 2× so it stays crisp) |
| Tall | **2000 × 2500** | Etsy 4:5, the tallest Etsy shows without cropping |

Verify the current platform limits before a release — they change, and this file
is not authority on them.

## Pipeline

```bash
P=.claude/skills/printable-pdf/scripts
L=.claude/skills/listing-images/scripts
D="Products/PB-006 The One-Page Year"

# 1. real product pages as PNGs — never redraw a page by hand
python3 $P/render_pages.py "$D/dist/NorthingStudio_One-Page-Year_A4.pdf" \
        --out "$D/Listing/build/pages" --width 1600

# 2. write one artboard HTML per slot, linking the shared CSS
#    <link rel="stylesheet" href="../../../_assets/fonts/fonts.css">
#    <link rel="stylesheet" href="../../../_assets/artboard.css">

# 3. render each at its exact size
python3 $L/render_artboard.py "$D/Listing/build/01-hero.html" \
        -o "$D/Listing/images/01-hero.png" --size 2560x1440

# 4. the test that matters
sips -Z 220 "$D/Listing/images/02-thumb.png" --out /tmp/t.png   # then LOOK at it
```

## The ten slots

Use the role codes from `listing-image-audit`; the per-product plan in
`Product Plans/` already specifies the content of each slot for each product.

| # | Role | Job |
|---|---|---|
| 1 | HERO 16:9 | One benefit in ≤6 words, product shown once |
| 2 | HERO square | The grid thumbnail — a different composition, not a crop |
| 3 | INCL | What you get, with counts, in the spec strip |
| 4 | FEAT | One framework's anatomy, callout-labelled |
| 5 | DEMO | The method in use — a filled-in page, real pen marks |
| 6 | PAGES | Interior pages at a size where prompts are readable |
| 7 | COMPAT | Print / tablet / app support, honestly |
| 8 | PAGES or PROOF | The payoff page, or real proof once it exists |
| 9 | SIZE | Formats and dimensions, plain text |
| 10 | BUNDLE | The bundle maths, no invented savings |

Eight is the floor; ten is the standard. Free products earn their images too —
the research shows most free competitors ship 0–2, which is our cheapest edge.

## Rules

1. **Readable at 220 px.** Headline ≥ 110 px on a 2000 px artboard. If you cannot
   read it shrunk, it does not ship.
2. **≤6 words in a headline**, one promise per image, never two headlines.
3. **One accent per image.** Brass marks one thing; it never carries text.
4. **Real pages only.** Page images come from `render_pages.py` on the shipped
   PDF. Never redraw, never mock a page that does not exist.
5. **Soft drop shadows are allowed only on mockup page stacks** — nowhere else in
   the brand.
6. **A device or a page stack, never both** in one frame.
7. **No stock photography, no third-party logos or badges.** "Works with
   GoodNotes and Notability" is plain text.
8. **No invented proof** — no "bestseller", no sales counts, no star ratings, no
   struck-through price that was never charged.
9. **Honest comparisons.** If a COMPAT table lists a competitor gap, it must be
   true and checkable.
10. **Same ground, same kicker position, same type sizes** across every listing,
    so the shop grid reads as one brand.

## Verify before handing over

- `render_artboard.py` fails if the pixel size is off — platforms crop, we don't.
- Shrink every image to 220 px and **open it**. No claim about legibility counts
  without that.
- Check the greyscale/colour-blind read of anything where colour carries meaning.
- Confirm every number on an image matches the shipped files (page counts,
  formats). `check_listing.py` does this for the copy; images need your eye.
