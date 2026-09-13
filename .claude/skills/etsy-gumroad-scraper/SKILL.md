---
name: etsy-gumroad-scraper
description: Fetch public Etsy and Gumroad seller/listing data for market research — shop stats, listing titles, prices, reviews, favorites, badges, sales counts, descriptions and full-size listing images. Etsy data comes from archived page copies (or the official API when authorised); Gumroad from its public JSON. Use whenever research needs real data from etsy.com or gumroad.com listings, or needs listing images downloaded for visual analysis.
---

# Etsy & Gumroad scraper

Two tested scripts in `scripts/` (run with `.venv/bin/python`, which has `requests`). JSON goes to stdout and logs go to stderr. Save raw output so nothing is fetched twice:

```bash
S=.claude/skills/etsy-gumroad-scraper/scripts
.venv/bin/python $S/etsy.py listing 1126658970 > research/raw/etsy/<shop>/listing-1126658970.json
```

## Terms & usage rules (read first)

- **What the terms say:**
  - Etsy's Terms of Use forbid crawling or scraping etsy.com without permission.
  - Etsy's API Terms forbid using the API "to collect, scan, or otherwise request Etsy content for purposes of analytics … unless expressly authorized in writing by Etsy".
  - Gumroad's terms forbid scrapers and crawlers.
- **The owner's decision:** on 2026-09-12 the project owner was told all of this and chose to keep these tools for **low-volume, internal research**.
- **Rules that follow from it:**
  - **Low volume.** The scripts pause between requests. Never run them in parallel loops, and fetch each page once (reuse `research/raw/`).
  - **Internal use only.** Never republish competitors' images, text or data. Record design *principles*, not copies.
  - **Never fetch etsy.com directly.** `etsy.py` reads archived copies only.
  - **API only when authorised.** Don't set `ETSY_API_KEY` for competitor research unless Etsy has approved that use in writing. API mode is for the owner's own shop or an authorised use case.
  - **Stop** if either platform objects.

## What works (tested 2026-09-12)

| Target | Route | Result |
|---|---|---|
| Etsy listing/shop pages | Wayback Machine snapshot | **Works** for popular listings/shops: full JSON-LD (title, price, rating, review count, all images + captions, sample reviews), favorites, Bestseller badge, shop sales |
| Etsy images | `i.etsystatic.com/...il_fullxfull...` | **Works** (full size, ~2000px). Wayback does not archive them |
| Etsy Open API v3 | `ETSY_API_KEY` | Official, and the richest source (see API mode). Only for authorised use |
| Gumroad search, profiles, product `.json`, images | public endpoints | **Works**, including `sales_count` on most products |

Every Etsy result has `source` and, for Wayback, `archived_at` and `age_days`. **Always report the archive date.** Flag snapshots older than about 6 months as possibly stale and cross-check them with WebSearch snippets.

**How old and how complete archived copies are** (measured 2026-09-12 on bestseller pages):
- The newest copy ranged from **48 to 239 days old**.
- **4 of 6 bestseller listings had no copy at all.** Coverage is best for big, popular shops and listings.
- In practice: expect data that's weeks to months old, and plan to fill gaps from WebSearch snippets (titles, prices and review counts often show there). Mark anything missing as "not accessible".
- Sales counts only ever grow, so an old copy gives a **minimum**. Say so, e.g. "≥41.6k sales as of 2026-01-16".

## Etsy commands

```bash
.venv/bin/python $S/etsy.py listing <id|url>              # one listing -> JSON (+ up to 100 reviews in API mode)
.venv/bin/python $S/etsy.py images  <id|url> --out DIR    # every listing image, numbered 01.jpg.. + manifest.json (captions)
.venv/bin/python $S/etsy.py shop    <ShopName|url>        # shop stats; API mode adds sections, featured listings, all active listings
# API mode only:
.venv/bin/python $S/etsy.py ping                          # test the key -> {"application_id": ...}
.venv/bin/python $S/etsy.py reviews  <ShopName> --max 500 # shop-wide reviews incl. buyer photos + star distribution
.venv/bin/python $S/etsy.py batch    <id> <id> ...        # up to 100 listings in one call, with images
.venv/bin/python $S/etsy.py taxonomy "planner"            # category ids, e.g. Design & Templates > Planner Templates
.venv/bin/python $S/etsy.py search "goal planner" --taxonomy <id> --digital-only --sort score --limit 200
```

Listing fields (archive mode): `title, shop, price, original_price, currency, rating, review_count, favorites, bestseller_badge, etsys_pick, demand_signals, is_digital_download, digital_file_types, listed_on, shop_sales, category, description, images[{url, caption}], reviews_sample`.

API mode adds: `views` (updated daily), all 13 `tags`, `file_data` (e.g. "1 PDF"), `taxonomy_id`, `featured_rank`, `shop_section_id`, `style`, `has_video`, the created/updated dates, and per image `etsy_hex` (Etsy's own dominant colour) and `rank`. Shops add `admirers`, `sections` (with listing counts), **`featured_listings`** (the seller's own chosen highlights, a strong best-seller signal), `digital_sale_message` and `refund_policy`.

### Finding Etsy sellers in archive mode
1. Use WebSearch with `allowed_domains: ["etsy.com"]`, e.g. `"goal planner printable bestseller"`, `"budget planner spreadsheet etsy bestseller"`, `"digital planner goodnotes bestseller"`. Result titles often include "BESTSELLER" and the shop name.
2. Run `etsy.py listing <url>` on each result to get the shop name, `shop_sales`, favorites and review count.
3. Run `etsy.py shop <ShopName>` for shop totals and the listings on the first page of the shop.
4. For more listings, WebSearch `site:etsy.com/listing "<ShopName>"` plus category keywords.
5. If a page has no Wayback snapshot, use what the WebSearch snippets show and mark the rest as "not accessible". Never guess.

## API mode (only with Etsy's authorisation)

These notes come from https://developers.etsy.com/documentation and the spec at https://www.etsy.com/openapi/generated/oas/3.0.0.json.

- **Key:** register at https://www.etsy.com/developers/register, then `export ETSY_API_KEY="<keystring>:<shared_secret>"`. It's sent as the `x-api-key` header on every request. New keys stay inactive until Etsy approves them. Test with `etsy.py ping`.
- **App types:**
  - **Seller App:** your own shop only, approved in minutes.
  - **Personal App:** beyond your own shop at limited scale; needs a reviewed use case.
  - **Commercial:** requires an approved Personal App first.
  - Reading other shops needs at least a Personal App approved for that use.
- **Public endpoints need only the key; no OAuth:** `findShops`, `getShop`, `getShopSections`, `getFeaturedListingsByShop`, `findAllActiveListingsByShop`, `getListing`, `getListingsByListingIds` (batch), `getListingImages`, `getReviewsByListing`, `getReviewsByShop`, `findAllListingsActive`, `getSellerTaxonomyNodes`.
- **Rate limits:** set per app (see the developer portal). The headers `x-remaining-this-second` and `x-remaining-today` show what's left; the 24-hour window is rolling. On a 429 the script waits for `retry-after`, and it warns when fewer than 200 calls are left for the day.
- **Freshness rule:** the terms don't allow listing data to be displayed if it's more than 6 hours older than Etsy's live data. For reports, record the fetch time and treat the numbers as a point-in-time snapshot.
- **Optional:** Etsy runs a documentation-only MCP server (`https://mcp.api.etsycloud.com/mcp`). It answers questions about endpoints and schemas, not shop data.

## Gumroad commands

```bash
.venv/bin/python $S/gumroad.py search  "<query>" [--pages 3] [--details]  # Discover search, 9 per page; --details adds sales_count
.venv/bin/python $S/gumroad.py profile <username|url> [--details]         # all products on a creator profile
.venv/bin/python $S/gumroad.py product <product_url>                      # full data: sales_count, ratings breakdown, tier prices, covers, description
.venv/bin/python $S/gumroad.py images  <product_url> --out DIR            # cover images (original resolution) + description images
```

Notes:
- `sales_count` is `null` when the creator hides it. In that case use `ratings_count` as a proxy and say so.
- **Tiered products** often have a `$0` base price. The real prices are in `options[].price` (e.g. Gamified Life OS: $19 discount tier / $38 full).
- Prices come in the product's own currency (`usd`, `sgd`, `eur`...). Convert to USD before ranking and note the rate you used.
- Search is broad: "goal planner" also returns Notion dashboards and unrelated products. Filter by relevance yourself.
- `profile` embeds only 9 products per section. The script then searches Discover by creator name for the rest and reports `products_expected` vs `product_count_found`. Products hidden from Discover can't be found this way.
- `price: 0` with high sales means a **free lead magnet**. Keep those out of revenue estimates, but record them as a funnel tactic.

## Revenue estimates
- Etsy: `shop total sales × median price of the shop's digital listings`. Label it **[Estimated]** and show the formula; if the median isn't measured, show a range from sale price to list price.
- Gumroad: `Σ(sales_count × price)` over paid products, using the tier price actually charged. Label it **[Estimated]**.
- Treat these as signals, never exact figures: `favorites`, `review_count` (roughly 1 review per 10–30 sales on Etsy digital goods; state that this is a heuristic), Bestseller badge, featured listings, "in N carts".

## Status and low-star reviews

**Etsy is enabled again** (owner decision, 2026-09-13; paused 2026-09-12). `etsy.py` no longer needs
`ETSY_ENABLED`. Every rule above still applies.

**Low-star reviews for `research/buyer-complaints.md`:**
- **Etsy, archive mode:** `listing` returns `reviews_sample` from the page's JSON-LD with rating, date and text.
  Keep ratings 1–3. Samples are small, so a theme needs reviews from several listings.
- **Etsy, API mode (authorised key only):** `listing` returns up to 100 reviews and `reviews <Shop>` returns shop-wide
  reviews with the star distribution. Keep ratings 1–3.
- **Gumroad** exposes `ratings_breakdown_1to5_pct` but **no review text**. Record the 1–3 star share as context,
  never as a quote.
- **Saving:** write every fetched review set to `research/reviews/` and never fetch it twice. Quote at most 25 words,
  always with the listing URL, star rating, date and route.
