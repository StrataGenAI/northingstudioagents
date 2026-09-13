# NORTHING STUDIO — the shop

**Status:** the owner decided on 2026-09-13 (see `MULTI_AGENT_PLAN.md`, "Decisions you
made"). **NORTHING STUDIO is the shop and account name.** Quiet Compass is a product
line inside it, not the shop. Each line keeps its brand kit, voice and fonts under
`brands/<line>/`, so another line can sit beside it later.

## Shop facts (read by scripts)

Scripts parse the `key: value` lines in the block below. An empty value means *not
decided*. A script that needs one fails loudly; it never fills in a guess.

```
shop_name: NORTHING STUDIO
file_prefix: NorthingStudio_
licensor: Northing Studio
support_contact:
gumroad: https://northingstudio.gumroad.com
etsy_shop:
practitioner_licence_price_usd:
```

| Field | Value | Source |
|---|---|---|
| Shop / account name | NORTHING STUDIO | owner decision, 2026-09-13 |
| Wordmark | "NORTHING STUDIO", Fraunces, letter-spaced caps | `brands/quiet-compass/brand-kit.md` §Visual system |
| File prefix | `NorthingStudio_` for every line | owner decision, 2026-09-13 (overrides "keep QuietCompass_") |
| Gumroad | `northingstudio.gumroad.com`, registered | brand kit v2 |
| Etsy | shop name not yet claimed | brand kit v2: the owner will claim it directly |
| Licensor | Northing Studio | **[Assumption]** Licences may need the owner's legal name or entity. Confirm when the licence text is reviewed (M3). |
| Support contact | **not set** | Owner to supply (M2). `release_check.py` fails any file that still carries a placeholder. |
| Practitioner licence price | **not set** | Owner to set (M3) |

## Product lines

| Line | Folder | Scope |
|---|---|---|
| Quiet Compass | `brands/quiet-compass/` | reflective planning, audits, goal and focus tools. All current products (PB-001 to PB-006, PB-022) |

Every line has four things:
- `brand-kit.md`: palette, type, devices, listing image rules
- `voice.md`: locked voice rules
- `fonts/`: static OFL faces plus a manifest with PostScript names, which `verify_pdf.py --fonts` checks
- `artboard.css`: the listing image and pin system

Shop-level pieces live here, not in a line:
- `brands/licences/`: licence templates; the shop is the licensor
- `catalogue.md`: what is live
- `OUTCOMES.md`: what happened after listing

## Open owner notes

These are recorded here so no agent resolves them by guessing.

1. **The brand screen contradicts itself.** The brand kit's screen table says a
   "Northing Studio" conflict was *found and knowingly accepted*, with specific
   hits (`northing.studio`, "The Art of Northing™", NORTHING Bergen). Its v2
   changelog says "Northing Studio" *remains unscreened*. Both statements cannot be
   right. A professional trademark search is still outstanding either way.
2. **"Quiet Compass" was dropped as a shop name because it was unavailable on
   Etsy.** Using it as a product-line name in listing titles still carries that
   exposure. This is the owner's risk, accepted on 2026-09-13.
3. **The Etsy shop name** is still to be claimed and confirmed in Etsy's shop-name
   field.
