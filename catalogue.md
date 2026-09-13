# Catalogue — live products

**Only products that are live and buyable belong here.** `scripts/release_check.py`
reads this table. Any product or URL a customer file mentions must match a row, or
the release fails. Planned and specced products live in `Product Plans/`, not here.

Add a row only once the listing is live and its URL opens. `release_check.py`
re-checks every URL on each run.

**Columns:**
- **id:** internal PB-/BN- ID (never shown to customers)
- **line:** product-line folder under `brands/`
- **name:** the exact customer-facing product name
- **platform:** `gumroad` or `etsy`
- **url:** the live listing URL
- **price_usd:** list price (`0` for free)
- **formats:** shipped formats, comma-separated (`A4, Letter, Tablet`)
- **interaction:** `fillable` or `annotate-only`
- **listed:** date the listing went live, YYYY-MM-DD

| id | line | name | platform | url | price_usd | formats | interaction | listed |
|---|---|---|---|---|---|---|---|---|

_No product is live yet (2026-09-13)._
