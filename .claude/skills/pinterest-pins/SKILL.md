---
name: pinterest-pins
description: Build the five vertical Pinterest pins (1000×1500) for a digital product from its real rendered pages, with pin titles, descriptions, alt text and destination links in pins.json, validated by check_pins.py. Pinterest is the studio's primary traffic channel, so pins are a first-class release output with their own gate and Drive folder. Use when creating or revising a product's pins.
---

# Pinterest pins

Pinterest is where most buyers will first see a Northing Studio product. A pin is
seen at feed width, in a column of other pins, for about as long as a thumb takes
to scroll past. So pins get the same discipline as listing images: real pages,
one promise, readable small. They also get their own gate.

**We never post.** There is no Pinterest API use, no login and no automation. The
pipeline prepares the pins; the owner pins them by hand from Drive
`<product>/pinterest/`.

## What ships

```
Products/PB-0XX <Name>/Pinterest/
  build/pin-1.html … pin-5.html     artboards (working files, not uploaded)
  images/pin-1.png … pin-5.png      1000×1500, the files the owner pins
  pins.json                         titles, descriptions, alt text, destinations, sources
  Pinterest Instructions.md         how to pin them, in order, field by field
  qa/pins-check.json                check_pins.py output (required before upload)
```

## Five pins, five jobs

Each pin comes from a **different real page**. Name the exact page in `pins.json`.

| Pin | Job | Built from |
|---|---|---|
| 1 | The product at a glance: title, the one promise, formats | the cover or the page stack |
| 2 | The decision the product forces | the interior decision page (same as listing slot 2) |
| 3 | What the buyer ends up with | the charter or output page (listing slot 3) |
| 4 | How it works, in three steps | the start-here or how-to page |
| 5 | One exercise, close enough to read the prompts | a working page cropped so its prompts are legible |

If a product has fewer than five distinct useful pages (a 2-page freebie), reuse a
page only with a different crop and job. `check_pins.py` warns on repeats. Say why
in `Pinterest Instructions.md`.

## Composition

- **Size** 1000 × 1500 (2:3), rendered with `render_artboard.py --size 1000x1500`
  from an artboard that uses `.art.art--pin` in `brands/<line>/artboard.css`.
- **The headline** is 6 words or fewer, set in Fraunces. It must still read when the
  pin is shrunk to 236 px wide. Shrink it and look.
- **One accent per pin**, same as the listing rules. It never carries text.
- **Real pages only.** A page image comes from `qa/pages/<edition>/` (render_pages.py
  on the shipped PDF). Never redraw or mock a page.
- **Brand strip.** `NORTHING STUDIO` kicker at the top, in the same position on every pin.
- No hands, no desk scenes, no device mockups unless the pin's job is the tablet
  edition, no third-party logos, no invented proof.

## pins.json

```json
{"pins": [{
  "image": "images/pin-1.png",
  "source_pdf": "NorthingStudio_10-Minute-Life-Audit_A4.pdf",
  "source_page": 3,
  "source_png": "qa/pages/a4/NorthingStudio_10-Minute-Life-Audit_A4-p03.png",
  "title": "…",
  "description": "…",
  "alt": "…",
  "destination": "pending-own-listing"
}]}
```

- **title**: 100 characters or fewer. The search phrase comes first, then the benefit.
  Voice rules apply (`brands/<line>/voice.md`).
- **description**: 500 characters or fewer. The first ~50 characters show in the
  feed, so they say what it is. Then what the buyer does with it, the formats, and
  the disclaimer where the product needs one. No hashtags stacks, no urgency, no
  proof numbers.
- **alt**: 500 characters or fewer. Describe what is actually on the pin, for someone
  who cannot see it.
- **destination**: the product's live listing URL from `catalogue.md`. Until the
  listing is live, write `pending-own-listing`; `release_check.py --listing` accepts
  that only while the product has no live row. Never point a pin at another product
  that is not live.

Limits were checked on 2026-09-13: title 100, description 500, alt 500. Re-check
before a release; platforms change them.

## Gate

```bash
PY=.venv/bin/python
$PY .claude/skills/pinterest-pins/scripts/check_pins.py "Products/PB-0XX <Name>"
```

It fails on:
- anything other than five pins
- a wrong image size
- a pin whose source page is not real
- over-limit or empty copy
- a bad destination
- an internal ID in a filename
- any blocking `banned_terms.py` finding in the pin copy

`release_check.py --listing` then checks the destinations and copy against the
catalogue. The upload refuses to run without both.
