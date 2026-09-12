---
name: listing-image-audit
description: Standard method for visually auditing Etsy/Gumroad listing images and template pages — contact sheets, thumbnail search-grid test, colour palette extraction (hex), image-role coding, typography/mockup/style vocabulary and a 1–5 scoring rubric — so every listing is analysed the same comparable way. Use when analysing competitor listing photos, thumbnails, mockups or interior template pages, and when planning our own listing images.
---

# Listing image audit

This skill makes image analysis **consistent and comparable** across sellers, so the Product Planning Agent can aggregate it. Use the fixed codes and vocabularies below. Don't invent new labels unless nothing fits, and if you do, add them under "Other" with a short definition.

Scripts (macOS, dependency-free, need Google Chrome):
```bash
A=.claude/skills/listing-image-audit/scripts
python3 $A/contact_sheet.py research/assets/etsy/<seller>/<listing>/ --out research/assets/etsy/<seller>/<listing>/_sheet.png --cols 5 --cell 300
python3 $A/palette.py research/assets/etsy/<seller>/<listing>/01.jpg     # -> "#F4EFE8 41%  #A3B18A 22% ..."
```

## Workflow per listing

1. **Get the images.** Run `etsy.py images` / `gumroad.py images` (skill `etsy-gumroad-scraper`). Captions in `manifest.json` often describe the image; use them.
2. **Overview.** Build a contact sheet and `Read` it. This shows the whole image sequence in one view.
3. **Detail.** `Read` each image at full size to read its text overlays, fonts and page layouts. The contact sheet is too small for text.
4. **Palette.** Run `palette.py` on the hero plus 2–3 interior-page images. Report the hex codes it gives. Don't guess them. Separate background colours (large share, light) from accents (small share, saturated).
5. **Fill in the audit template** below and save it as `research/audits/<platform>-<seller-slug>-<listing-id>.md`.
6. **Thumbnail test (per category).** Put image 01 of the top ~10 competing listings on one sheet at search-grid size and compare them side by side:
   ```bash
   python3 $A/contact_sheet.py research/assets/etsy/*/*/01.jpg --out research/audits/thumbs-<category>.png --cols 5 --cell 220
   ```
   Ask: which ones can you read at this size? Which stand out on colour or contrast? Which promise is readable in under 2 seconds?

## Image role codes

| Code | Role | Code | Role |
|---|---|---|---|
| HERO | Main thumbnail / first image | NAV | Hyperlink / tab navigation demo |
| INCL | "Everything you get" / what's included | COMPAT | Apps/devices compatibility |
| PAGES | Interior page previews (grid or single) | SIZE | Page size / print info (A4, Letter, A5) |
| FEAT | Feature/benefit callouts | HOWTO | Download / usage instructions |
| DEMO | In-use shot (hand + stylus, writing, lifestyle) | VAR | Colour/cover variants |
| PROOF | Reviews, "20,000 sold", ratings screenshot | BONUS | Bonuses, stickers, freebies |
| BUNDLE | Bundle / value stack / "save X%" | VIDEO | Video or GIF slot |
| BRAND | Brand story / the maker / guarantee | OTHER | Define it |

**Sequence string.** Write the order compactly: `HERO > INCL > FEAT > PROOF > NAV > NAV > PAGES > BONUS > PAGES > VAR > COMPAT > FEAT > HOWTO > HOWTO > BUNDLE`.

## Vocabularies

- **Mockup:** iPad-portrait, iPad-landscape, iPad+pencil-hand, multi-device, flat-page (no device), printed-on-desk, clipboard/binder, laptop/screen (Sheets/Notion), phone, collage, none.
- **Background:** solid-light, solid-dark, gradient, textured-paper, marble, desk-scene, floral/illustrated, photo-lifestyle.
- **Typography:** serif-classic, serif-high-contrast (Didone), sans-geometric, sans-humanist, script/handwritten, display/bold-condensed, mono. Record the **pairing** (e.g. "serif-classic headings + script accent + sans body") and the **hierarchy** (how many text sizes are on the hero).
- **Aesthetic tags (pick 1–3):** minimal-neutral, beige-latte, sage-earthy, terracotta-boho, pastel-soft, blush-feminine, floral-botanical, dark-academia, dark-mode, bold-colour, corporate-clean, Scandinavian, Y2K/retro, kawaii/cute, luxury-gold, faith/christian, masculine-dark.
- **Badge/callout devices:** starburst, ribbon, circle-seal, pill-label, arrow-annotation, number-callout ("65+ templates"), price-strike, "NEW", "BESTSELLER", "INSTANT DOWNLOAD".
- **Interior layout:** grid, columns, boxed-sections, lined, dotted, blank, table/matrix, wheel/radial, checklist, timeline, calendar-grid, prompt-and-answer.

## Scoring rubric (1–5 per criterion)

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| **Thumbnail legibility** (at 220px) | text unreadable, busy | main words readable | the product and its promise are clear in under 2 s |
| **Promise clarity** | no benefit stated | features listed | one clear outcome/benefit up front |
| **Contents proof** | can't tell what's inside | some pages shown | every page type shown, with counts |
| **Visual hierarchy** | everything the same weight | some order | one focal point, then 2–3 tiers |
| **Palette cohesion** | clashing / random | mostly consistent | deliberate 3–5 colour system |
| **Mockup realism/fit** | distorted, low-res | fine | premium and suits the buyer's context |
| **Brand consistency** (across the shop) | every listing different | partial | recognisable at a glance in the shop grid |
| **Objection handling** | none | compatibility or how-to only | covers compatibility, size, delivery, guarantee and FAQ |

## Audit file template

```markdown
# <Seller> — <Listing title (short)>
Platform: Etsy | Gumroad · URL: <url> · Price: <price> (was <orig>) · Reviews: <n> · Sales/favorites: <..> · Source: <api/wayback YYYY-MM-DD>
Images: <n> · Sheet: research/assets/.../_sheet.png

## Sequence
HERO > INCL > ...

## Per-image
| # | Role | What's shown | Mockup | Background | Palette (hex) | Typography | Text overlay (short quote) | Badges | Works / weak |
|---|---|---|---|---|---|---|---|---|---|

## Interior template pages observed
| Page type | Layout | Notable details (prompts, icons, tabs, white space, ink use) |

## Scores
| Legibility | Promise | Contents | Hierarchy | Palette | Mockup | Brand | Objections | **Avg** |

## Principles to borrow (not copy)
- ...
## Weaknesses → our opportunity
- ...

<!-- summary row for aggregation -->
| <seller> | <listing-id> | <n images> | <sequence> | <aesthetic tags> | <3 main hex> | <avg score> |
```

## Example (real, from LetsPlanPlanners, Etsy listing 1126658970, Wayback 2026-07-26)

- **Sequence:** `HERO > INCL > FEAT/DEMO > PROOF > NAV > NAV > PAGES > BONUS > PAGES > VAR > COMPAT > FEAT > DEMO > HOWTO > BUNDLE` (15 images).
- **Hero:** floral-cover iPad on a dark teal background, with stacked circle-seal badges ("300+ planner covers", "3,500+ digital stickers", "Over 20,000 sold") and a bulleted feature list at the bottom.
- **Palette:** blush and mauve on warm white. Serif-classic headings with a script accent.
- **Principle:** every image is a single job with a serif headline; social proof and volume numbers ("65+ templates") are repeated on 4 or more images.
- **Weakness:** the hero is very text-dense and hard to read at thumbnail size, which is our opportunity for a cleaner, more readable hero.

## Rules
- Describe and measure. Never recommend copying a specific image, artwork, wording or layout.
- Keep quotes of on-image text short.
- Every audit must link back to the image files, so the planning agent and designers can open them.
