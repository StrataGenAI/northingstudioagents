#!/usr/bin/env python3
"""Etsy research fetcher for public shop/listing data.

Access order (automatic):
  1. Official Etsy Open API v3, if ETSY_API_KEY is set (format "keystring:shared_secret").
     Etsy's API Terms forbid analytics use without Etsy's written permission: set the key only for
     your own shop or an authorised use case.
  2. Otherwise the latest Wayback Machine snapshot of the page (web.archive.org). etsy.com itself is
     never fetched (Etsy's Terms of Use forbid crawling/scraping it). Images come from i.etsystatic.com.

Usage:
  etsy.py ping                                   check the API key works (API only)
  etsy.py listing <listing_id|url>               JSON summary of one listing (+ reviews)
  etsy.py images  <listing_id|url> --out DIR     download every listing image (full size) + manifest.json
  etsy.py shop    <ShopName|url>                 shop stats, sections, featured + all active listings
  etsy.py reviews <ShopName|url> [--max 500]     shop-wide reviews incl. buyer photos (API only)
  etsy.py batch   <id> [<id> ...]                up to 100 listings per call, with images (API only)
  etsy.py search  "<keywords>" [--taxonomy ID] [--min-price N] [--max-price N]
                  [--sort score|created|price|updated] [--limit 100] [--digital-only]   (API only)
  etsy.py taxonomy "<name fragment>"             find category ids, e.g. "planner" (API only)

JSON goes to stdout, progress/log lines to stderr. Every result carries "source"
("api" | "direct" | "wayback") and, for wayback, "archived_at" - report it.
API reference: https://developers.etsy.com/documentation/reference (spec: etsy.com/openapi/generated/oas/3.0.0.json)
"""
import argparse
import html as htmllib
import json
import os
import re
import sys
import time

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
API = "https://openapi.etsy.com/v3/application"
KEY = os.environ.get("ETSY_API_KEY")

S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})


def log(*a):
    print(*a, file=sys.stderr)


def get(url, retries=4, **kw):
    r = None
    for attempt in range(retries):
        try:
            r = S.get(url, timeout=45, **kw)
        except requests.RequestException as e:
            log(f"  network error ({e}); retrying")
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code == 429 and "openapi.etsy.com" in url:
            wait = int(r.headers.get("retry-after", "0") or 0) or 2 * (attempt + 1)
            log(f"  Etsy API rate limit hit; waiting {wait}s (retry-after)")
            time.sleep(wait)
            continue
        if r.status_code in (429, 503) and "archive.org" in url:
            wait = 8 * (attempt + 1)
            log(f"  {r.status_code} from archive.org, waiting {wait}s")
            time.sleep(wait)
            continue
        return r
    return r


def wayback(prefix, pick=None):
    """Newest archived HTTP-200 snapshot for a URL prefix -> (html, snapshot_url, timestamp)."""
    since = time.strftime("%Y", time.gmtime(time.time() - 3 * 365 * 86400))
    cdx = get("https://web.archive.org/cdx/search/cdx",
              params={"url": prefix + "*", "output": "json", "filter": "statuscode:200",
                      "from": since, "fl": "timestamp,original"})
    if cdx is None or cdx.status_code != 200 or not cdx.text.strip():
        return None, None, None
    # CDX sorts by URL, not date, so re-sort to try the newest copies first
    rows = sorted(cdx.json()[1:], key=lambda r: r[0], reverse=True)
    if pick:
        rows = [r for r in rows if pick(r[1])] or rows
    for ts, orig in rows[:5]:
        snap = f"https://web.archive.org/web/{ts}id_/{orig}"
        time.sleep(1.5)
        r = get(snap)
        if r is not None and r.status_code == 200 and len(r.text) > 20000:
            return r.text, snap, ts
    return None, None, None


def fetch_page(url, prefix, pick=None):
    # Etsy's Terms of Use forbid crawling/scraping etsy.com, so pages are never fetched from Etsy directly;
    # only third-party archive copies are read. `url` is kept for reporting.
    log(f"  reading archived copy of {url}")
    html, snap, ts = wayback(prefix, pick)
    if not html:
        return None
    age = int((time.time() - time.mktime(time.strptime(ts[:8], "%Y%m%d"))) // 86400)
    return {"html": html, "source": "wayback", "fetched_url": snap,
            "archived_at": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}", "age_days": age}


def text_of(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", htmllib.unescape(t))


def first(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def listing_id(s):
    m = re.search(r"(\d{6,})", str(s))
    if not m:
        sys.exit(f"Could not find a listing id in {s!r}")
    return m.group(1)


def shop_name(ref):
    return re.sub(r".*/shop/", "", ref).split("?")[0].strip("/")


# ---------------------------------------------------------------- API helpers

def need_key(what):
    if not KEY:
        sys.exit(f"`{what}` needs ETSY_API_KEY (\"keystring:shared_secret\"). Without it use WebSearch "
                 "(allowed_domains=['etsy.com']) and `etsy.py listing/shop`, which fall back to the Wayback Machine.")


def api(path, **params):
    """GET an Open API v3 endpoint. List params are sent comma-separated, with a repeated-param retry."""
    flat = {k: ",".join(map(str, v)) if isinstance(v, (list, tuple)) else v
            for k, v in params.items() if v is not None}
    r = get(f"{API}{path}", headers={"x-api-key": KEY}, params=flat)
    if r is not None and r.status_code == 400 and any(isinstance(v, (list, tuple)) for v in params.values()):
        r = get(f"{API}{path}", headers={"x-api-key": KEY},
                params={k: v for k, v in params.items() if v is not None})
    if r is None or r.status_code != 200:
        sys.exit(f"Etsy API error {getattr(r, 'status_code', '?')} on {path}: {getattr(r, 'text', '')[:300]}")
    left = r.headers.get("x-remaining-today")
    if left is not None and left.isdigit() and int(left) < 200:
        log(f"  warning: only {left} Etsy API calls left in the 24h window")
    time.sleep(0.15)  # stay well under the per-second limit
    return r.json()


def paged(path, max_items, **params):
    out, offset = [], 0
    while len(out) < max_items:
        page = api(path, limit=min(100, max_items - len(out)), offset=offset, **params)
        res = page.get("results", [])
        out += res
        offset += len(res)
        if not res or offset >= page.get("count", 0):
            break
    return out


def money(p):
    if isinstance(p, dict) and "amount" in p:
        return round(p["amount"] / (p.get("divisor") or 100), 2), p.get("currency_code")
    return None, None


def api_listing_summary(l):
    price, cur = money(l.get("price"))
    return {
        "listing_id": l.get("listing_id"), "title": l.get("title"), "url": l.get("url"),
        "price": price, "currency": cur, "favorites": l.get("num_favorers"), "views": l.get("views"),
        "listing_type": l.get("listing_type"), "file_data": l.get("file_data"), "tags": l.get("tags"),
        "taxonomy_id": l.get("taxonomy_id"), "shop_section_id": l.get("shop_section_id"),
        "featured_rank": l.get("featured_rank"), "created": l.get("original_creation_timestamp"),
        "updated": l.get("updated_timestamp"),
    }


def api_images(imgs):
    return [{"url": im.get("url_fullxfull"), "caption": im.get("alt_text"), "rank": im.get("rank"),
             "etsy_hex": ("#" + im["hex_code"]) if im.get("hex_code") else None,
             "size": f"{im['full_width']}x{im['full_height']}" if im.get("full_width") else None}
            for im in sorted(imgs or [], key=lambda i: i.get("rank") or 0)]


def api_reviews(results):
    return [{"rating": rv.get("rating"), "date": time.strftime("%Y-%m-%d", time.gmtime(rv.get("create_timestamp") or 0)),
             "text": htmllib.unescape(rv.get("review") or ""), "listing_id": rv.get("listing_id"),
             "buyer_photo": rv.get("image_url_fullxfull")} for rv in results]


# ---------------------------------------------------------------- listing

def ld_product(html):
    for m in re.finditer(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        for it in d if isinstance(d, list) else [d]:
            if isinstance(it, dict) and it.get("@type") == "Product":
                return it
    return {}


def listing_from_html(lid, page):
    html = page["html"]
    ld = ld_product(html)
    txt = text_of(html)
    offers = ld.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    rating = ld.get("aggregateRating") or {}
    images = []
    for im in ld.get("image") or []:
        if isinstance(im, dict):
            images.append({"url": im.get("contentURL") or im.get("url"), "caption": im.get("description")})
        elif isinstance(im, str):
            images.append({"url": im, "caption": None})
    if not images:
        urls = sorted(set(re.findall(r"https://i\.etsystatic\.com/[^\"\s\\]*?il_fullxfull\.[^\"\s\\]*?\.(?:jpg|png|webp)", html)))
        images = [{"url": u, "caption": None} for u in urls]
    reviews = [{"rating": (rv.get("reviewRating") or {}).get("ratingValue"), "date": rv.get("datePublished"),
                "text": htmllib.unescape(rv.get("reviewBody") or "")} for rv in ld.get("review") or []]
    demand = sorted(set(m.strip() for m in re.findall(
        r"([^.<>]{0,40}(?:in \d+\+? carts|in their carts?|bought this in the last 24 hours|sold in the last 24 hours|people bought)[^.<>]{0,20})",
        txt, re.I)))
    brand = ld.get("brand")
    return {
        "listing_id": lid,
        "url": ld.get("url") or f"https://www.etsy.com/listing/{lid}",
        "title": ld.get("name"),
        "shop": brand.get("name") if isinstance(brand, dict) else brand,
        "price": offers.get("price") or offers.get("lowPrice"),
        "price_high": offers.get("highPrice"),
        "currency": offers.get("priceCurrency"),
        "original_price": first(r"Original Price:?\s*[A-Z]{0,3}\$?\s*([\d.,]+)", txt),
        "rating": rating.get("ratingValue"),
        "review_count": rating.get("reviewCount"),
        "favorites": first(r"has ([\d,]+) favorites", html),
        "bestseller_badge": bool(re.search(r">\s*Bestseller\s*<", html)),
        "etsys_pick": "Etsy's Pick" in txt or "Etsy’s Pick" in txt,
        "demand_signals": demand,
        "is_digital_download": "Digital download" in txt or "Instant Download" in txt,
        "digital_file_types": first(r"Digital file type\(s\):?\s*([^|]{1,60}?)(?:\s{2,}|Instant|Your files|$)", txt),
        "listed_on": first(r"Listed on ([A-Z][a-z]{2,8} \d{1,2}, \d{4})", txt),
        "shop_sales": first(r"([\d,.]+k?)\s+sales\b", txt),
        "category": ld.get("category"),
        "description": ld.get("description"),
        "images": images,
        "reviews_sample": reviews,
        "source": page["source"],
        "fetched_url": page["fetched_url"],
        "archived_at": page.get("archived_at"),
        "age_days": page.get("age_days"),
    }


def listing_from_api(lid, max_reviews=100):
    d = api(f"/listings/{lid}", includes=["Images", "Shop", "Videos"])
    shop = d.get("shop") or {}
    out = api_listing_summary(d)
    out.update({
        "shop": shop.get("shop_name"), "shop_sales": shop.get("transaction_sold_count"),
        "is_digital_download": d.get("listing_type") in ("download", "both"),
        "materials": d.get("materials"), "style": d.get("style"), "when_made": d.get("when_made"),
        "is_customizable": d.get("is_customizable"), "is_personalizable": d.get("is_personalizable"),
        "description": d.get("description"),
        "images": api_images(d.get("images")),
        "has_video": bool(d.get("videos")),
        "source": "api", "fetched_url": f"{API}/listings/{lid}",
    })
    out["reviews_sample"] = api_reviews(paged(f"/listings/{lid}/reviews", max_reviews))
    return out


def get_listing(ref):
    lid = listing_id(ref)
    if KEY:
        return listing_from_api(lid)
    url = ref if str(ref).startswith("http") else f"https://www.etsy.com/listing/{lid}"
    page = fetch_page(url, f"etsy.com/listing/{lid}")
    if not page:
        sys.exit(f"Listing {lid}: blocked directly and no Wayback snapshot. "
                 "Use WebSearch snippets / third-party sources and mark the data as unavailable.")
    return listing_from_html(lid, page)


# ---------------------------------------------------------------- shop

def shop_from_html(name, page):
    html, txt = page["html"], text_of(page["html"])
    listings = {}
    for lid, slug in re.findall(r"/listing/(\d{6,})/([a-z0-9-]+)", html):
        listings.setdefault(lid, slug.replace("-", " "))
    return {
        "shop": name,
        "url": f"https://www.etsy.com/shop/{name}",
        "title": first(r'<meta property="og:title" content="([^"]+)"', html),
        "description": first(r'<meta name="description" content="([^"]+)"', html),
        "total_sales": first(r"([\d,.]+k?)\s+Sales\b", txt, 0),
        "on_etsy_since": first(r"On Etsy since\s*(\d{4})", txt),
        "admirers": first(r"([\d,.]+k?)\s+Admirers", txt),
        "rating": first(r"(\d(?:\.\d+)?) out of 5 stars?\s*\(\s*[\d,.]+k?\s*\)", txt),
        "review_count": first(r"\d(?:\.\d+)? out of 5 stars?\s*\(\s*([\d,.]+k?)\s*\)", txt),
        "star_seller": bool(re.search(r">\s*Star Seller\s*<", html)),
        "listings_found": [{"listing_id": k, "slug_title": v, "url": f"https://www.etsy.com/listing/{k}"}
                           for k, v in listings.items()],
        "note": "HTML shows only the first page of the shop; archived pages may be out of date.",
        "source": page["source"],
        "fetched_url": page["fetched_url"],
        "archived_at": page.get("archived_at"),
        "age_days": page.get("age_days"),
    }


def shop_id_for(name):
    res = api("/shops", shop_name=name).get("results") or []
    exact = [s for s in res if (s.get("shop_name") or "").lower() == name.lower()]
    if not (exact or res):
        sys.exit(f"No shop named {name!r} in the Etsy API")
    return (exact or res)[0]["shop_id"]


def shop_from_api(name):
    sid = shop_id_for(name)
    s = api(f"/shops/{sid}")
    sections = api(f"/shops/{sid}/sections").get("results", [])
    featured = api(f"/shops/{sid}/listings/featured", limit=100).get("results", [])
    listings = paged(f"/shops/{sid}/listings/active", 1000)
    return {
        "shop": s.get("shop_name"), "shop_id": sid, "url": s.get("url"), "title": s.get("title"),
        "total_sales": s.get("transaction_sold_count"), "review_count": s.get("review_count"),
        "review_average": s.get("review_average"), "admirers": s.get("num_favorers"),
        "active_listings": s.get("listing_active_count"), "digital_listings": s.get("digital_listing_count"),
        "created": s.get("create_date"), "location": s.get("shop_location_country_iso"),
        "announcement": s.get("announcement"), "sale_message": s.get("sale_message"),
        "digital_sale_message": s.get("digital_sale_message"), "refund_policy": s.get("policy_refunds"),
        "icon": s.get("icon_url_fullxfull"), "banner": s.get("image_url_760x100"),
        "sections": [{"id": x.get("shop_section_id"), "title": x.get("title"),
                      "active_listings": x.get("active_listing_count")} for x in sections],
        "featured_listings": [api_listing_summary(l) for l in featured],
        "listings_found": [api_listing_summary(l) for l in listings],
        "note": "`views` is not returned by the shop listing endpoint; use `etsy.py listing` for one listing's views.",
        "source": "api", "fetched_url": f"{API}/shops/{sid}",
    }


def get_shop(ref):
    name = shop_name(ref)
    if KEY:
        return shop_from_api(name)
    page = fetch_page(f"https://www.etsy.com/shop/{name}", f"etsy.com/shop/{name}",
                      pick=lambda orig: re.search(rf"/shop/{re.escape(name)}/?(\?.*)?$", orig, re.I) is not None)
    if not page:
        sys.exit(f"Shop {name}: blocked directly and no Wayback snapshot.")
    return shop_from_html(name, page)


# ---------------------------------------------------------------- other commands

def download(url, dest_noext):
    r = get(url)
    if r is None or r.status_code != 200:
        return None
    ctype = r.headers.get("content-type", "")
    ext = ".png" if "png" in ctype else ".webp" if "webp" in ctype else ".jpg"
    path = dest_noext + ext
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def cmd_images(ref, out):
    data = get_listing(ref)
    os.makedirs(out, exist_ok=True)
    manifest = []
    for i, im in enumerate(data["images"], 1):
        if not im.get("url"):
            continue
        path = download(im["url"], os.path.join(out, f"{i:02d}"))
        manifest.append({"n": i, "file": path, "url": im["url"], "caption": im.get("caption"),
                         "etsy_hex": im.get("etsy_hex")})
        log(f"  {i:02d} {'ok' if path else 'FAILED'} {im['url'][-50:]}")
        time.sleep(0.4)
    info = {k: data.get(k) for k in ("listing_id", "url", "title", "shop", "price", "currency",
                                     "review_count", "favorites", "source", "archived_at")}
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump({"listing": info, "images": manifest}, f, indent=2)
    return {"listing": info, "downloaded": sum(1 for m in manifest if m["file"]), "out": out}


def cmd_reviews(ref, max_items):
    need_key("reviews")
    name = shop_name(ref)
    sid = shop_id_for(name)
    revs = api_reviews(paged(f"/shops/{sid}/reviews", max_items))
    stars = {n: sum(1 for r in revs if r["rating"] == n) for n in range(1, 6)}
    return {"shop": name, "fetched": len(revs), "stars": stars, "reviews": revs, "source": "api"}


def cmd_batch(ids):
    need_key("batch")
    ids = [listing_id(i) for i in ids][:100]
    res = api("/listings/batch", listing_ids=ids, includes=["Images", "Shop"]).get("results", [])
    out = []
    for l in res:
        it = api_listing_summary(l)
        it["shop"] = (l.get("shop") or {}).get("shop_name")
        it["images"] = api_images(l.get("images"))
        out.append(it)
    return {"count": len(out), "results": out, "source": "api"}


def cmd_search(q, limit, taxonomy, min_price, max_price, sort, digital_only):
    need_key("search")
    res = paged("/listings/active", limit, keywords=q, taxonomy_id=taxonomy, min_price=min_price,
                max_price=max_price, sort_on=sort, sort_order="desc")
    out = [api_listing_summary(l) | {"shop_id": l.get("shop_id")} for l in res]
    if digital_only:
        out = [l for l in out if l["listing_type"] in ("download", "both")]
    return {"query": q, "taxonomy_id": taxonomy, "sort": sort, "results": out, "source": "api"}


def cmd_taxonomy(fragment):
    need_key("taxonomy")
    nodes = api("/seller-taxonomy/nodes").get("results", [])
    hits = []

    def walk(ns, path):
        for n in ns:
            p = path + [n.get("name")]
            if fragment.lower() in (n.get("name") or "").lower():
                hits.append({"id": n.get("id"), "path": " > ".join(p)})
            walk(n.get("children") or [], p)
    walk(nodes, [])
    return {"query": fragment, "matches": hits, "source": "api"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ping")
    sub.add_parser("listing").add_argument("ref")
    p = sub.add_parser("images"); p.add_argument("ref"); p.add_argument("--out", required=True)
    sub.add_parser("shop").add_argument("ref")
    p = sub.add_parser("reviews"); p.add_argument("ref"); p.add_argument("--max", type=int, default=500)
    sub.add_parser("batch").add_argument("ids", nargs="+")
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("--limit", type=int, default=100)
    p.add_argument("--taxonomy", type=int); p.add_argument("--min-price", type=float)
    p.add_argument("--max-price", type=float)
    p.add_argument("--sort", default="score", choices=["score", "created", "price", "updated"])
    p.add_argument("--digital-only", action="store_true")
    sub.add_parser("taxonomy").add_argument("fragment")
    a = ap.parse_args()
    if os.environ.get("ETSY_ENABLED") != "1":
        sys.exit("Etsy research is paused (project decision, 2026-09-12). Run with ETSY_ENABLED=1 to re-enable.")
    if a.cmd == "ping":
        need_key("ping")
        res = api("/openapi-ping")
    elif a.cmd == "listing":
        res = get_listing(a.ref)
    elif a.cmd == "images":
        res = cmd_images(a.ref, a.out)
    elif a.cmd == "shop":
        res = get_shop(a.ref)
    elif a.cmd == "reviews":
        res = cmd_reviews(a.ref, a.max)
    elif a.cmd == "batch":
        res = cmd_batch(a.ids)
    elif a.cmd == "search":
        res = cmd_search(a.query, a.limit, a.taxonomy, a.min_price, a.max_price, a.sort, a.digital_only)
    else:
        res = cmd_taxonomy(a.fragment)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
