---
name: listing-copy
description: Write and validate the selling copy for a digital product listing — SEO title and tags within platform limits, the description structure that converts, pricing and discount policy, disclaimers, FAQ and the fillable/annotate-only statement — with gates that check every claim against the actually-shipped files, per format, and every product or URL against the live catalogue. Use when writing, reviewing or publishing an Etsy or Gumroad listing.
---

# Listing copy and SEO

The listing is where exaggeration is most tempting and most damaging: one more
page in the count, a format we never shipped, a proof number nobody earned. So
the copy lives in a machine-readable `listing.json`. `check_listing.py` compares its
claims against the real PDFs in `dist/`, and `release_check.py --listing` compares
every product name and URL against `catalogue.md`.

## `listing.json` — the single source

```json
{
  "product_id": "PB-006",
  "product_name": "The One-Page Year",
  "price_usd": 0,
  "launch_price_usd": null,
  "claims": { "pages": 2, "formats": ["A4", "Letter", "Tablet"], "interaction": "annotate-only", "undated": true },
  "disclaimer": "A structured self-reflection tool. Not therapy, diagnosis or financial advice.",
  "etsy":    { "title": "...", "tags": ["...13..."], "description": "...", "category": "..." },
  "gumroad": { "name": "...", "summary": "...", "description": "...", "tiers": [] },
  "assumptions": ["support contact not yet set"]
}
```

- `product_id` is internal. It never appears in any customer-facing field.
- Everything else — the instruction PDF, the image headlines, the pin copy — is
  written *from* this file, so there is one place a price or a page count can be wrong.

## Platform limits

| | Etsy | Gumroad |
|---|---|---|
| Title | **≤140 characters** | no hard limit; keep under ~60 for display |
| Tags | **exactly 13, each ≤20 characters** | free-form |
| Images | up to 20 | cover 16:9 + square thumbnail |
| Type | digital download | digital product |

Re-check these before a release; platforms change them and this file is not
authority.

## Title

Front-load the head keyword — the search grid truncates around 50–60 characters,
so the first phrase does the work.

```
<Head keyword> | <benefit in plain words> | <format + specs>
Focus Audit Printable | Find the 20% That Matters | A4 + Letter PDF, Undated
```

No emoji, no ALL CAPS, no keyword stuffing that reads like a robot wrote it. The
words a buyer would actually type, in an order a human would actually read.

## Tags

Thirteen, no waste. Mix **head terms** (what it is) with **long-tail** (who it's
for and when). Do not spend two tags on the same root word. Never use a
trademarked method name — `check_listing.py` loads the ban list and fails.

Keyword clusters for our categories are in the research report,
§"SEO & copy insights": focus audit · 80/20 · pareto · time audit · energy audit ·
life audit · self assessment · core values · life purpose · goal planner ·
kaizen · undated planner · printable workbook.

## Description — the structure that converts

From the research (§"SEO & copy insights"), in this order, in the line's locked
voice (`brands/<line>/voice.md`):

1. **Benefit headline**
2. **One-line definition** — what it actually is
3. **Who it's for / not for** — the "not for" earns trust and cuts refunds
4. **What's inside**, with counts
5. **How it works**, in three steps
6. **Formats and compatibility** — plain text, no app logos. Say plainly whether it
   is **fillable** (typed-in form fields) or **annotate-only** (write or draw on
   it in a notes app or on paper), exactly as `claims.interaction` says.
7. **FAQ — including the price objection by name** ("Is it worth $19?"). The
   highest-converting shop in the study does this on every listing
8. **Refunds / guarantee**
9. **Next step or bundle** — only products that are live in `catalogue.md`

Then a changelog line with a real "last updated" date, and a polite rating
request in the delivery file — review capture is the cheapest ranking lever we
have.

## Licences and tiers

The standard purchase is the **personal-use licence**. Where the spec sells a
**practitioner licence** (a coach or therapist using the pages with clients), it
is a separate Gumroad tier or Etsy listing at its own price. The price is set by
the owner in `brands/SHOP.md`; never invent it. The listing says what each licence
allows in one plain line each, and never implies the pages are a clinical tool.

## Pricing and discounts

From the product plan: each product launches at **roughly 20% off for exactly two
weeks**, then goes to list price and **stays there**. No permanent sales, no
struck-through price that was never charged, no countdown that never expires.

**The guarantee is an open owner question.** Do not state one in any listing
until the owner decides — `banned_terms.py` fails the word "guarantee" inside a
product for exactly this reason.

## Disclaimers

- **Every reflection or audit product:** *"A structured self-reflection tool. Not
  therapy, diagnosis or financial advice."*
- **Money products** add *"Educational only — not financial advice."*

These appear in the listing **and** on the product's start page.

## Gates

```bash
PY=.venv/bin/python
Q=.claude/skills/product-qa/scripts
L=.claude/skills/listing-copy/scripts
$PY $L/check_listing.py "<product>/Listing/listing.json" --dist "<product>/dist" --json "<product>/Listing/qa/listing.json"
$PY $Q/banned_terms.py  "<product>/Listing/listing.json" "<product>/Listing/Listing Instructions.md" --require-disclaimer reflection
$PY scripts/release_check.py "<product>" --listing      # orchestrator, after images and pins exist
```

**`check_listing.py`:**
- counts the title and tags, and demands the nine sections
- rejects unearned proof claims ("bestseller", "500+ sold")
- requires `claims.interaction`
- **cross-checks the claimed page count and formats against the shipped PDFs, per
  format.** A listing that promises a Letter edition we did not build, or 24 pages
  when the Letter file has 22, fails there, not in a refund request.

**`release_check.py --listing`:**
- every URL resolves
- every product named is live
- no internal IDs
- the interaction claim matches the spec
- the slot brief was approved and not changed since
- the pins' destinations are live, or pending this listing
