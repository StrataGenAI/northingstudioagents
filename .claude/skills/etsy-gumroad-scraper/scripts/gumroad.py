#!/usr/bin/env python3
"""Gumroad research fetcher (public endpoints, no login needed).

Usage:
  gumroad.py search  "<query>" [--pages 3] [--details]   Discover search (9 results per page)
  gumroad.py profile <username|profile_url> [--details]  every product on a creator's profile
  gumroad.py product <product_url>                       full product data incl. sales_count
  gumroad.py images  <product_url> --out DIR             download cover + description images

--details fetches each product's .json to add sales_count (slower, ~1 request per product).
JSON goes to stdout, progress to stderr. sales_count is null when the creator hides it.
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
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})


def log(*a):
    print(*a, file=sys.stderr)


def get(url, **kw):
    r = None
    for attempt in range(4):
        try:
            r = S.get(url, timeout=40, **kw)
        except requests.RequestException as e:
            log(f"  network error ({e}); retrying")
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code == 429:
            time.sleep(8 * (attempt + 1))
            continue
        return r
    return r


def clean_url(u):
    return (u or "").split("?")[0]


def price(cents, cur):
    return None if cents is None else round(cents / 100, 2)


def html_to_text(h):
    h = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", h or "", flags=re.I)
    h = re.sub(r"<li[^>]*>", "- ", h, flags=re.I)
    t = htmllib.unescape(re.sub(r"<[^>]+>", "", h))
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def summarize(p):
    seller = p.get("seller") or {}
    ratings = p.get("ratings") or {}
    return {
        "name": p.get("name"),
        "url": clean_url(p.get("url")),
        "seller": seller.get("name"),
        "seller_profile": clean_url(seller.get("profile_url")),
        "price": price(p.get("price_cents"), p.get("currency_code")),
        "currency": p.get("currency_code"),
        "pay_what_you_want": p.get("is_pay_what_you_want"),
        "ratings_count": ratings.get("count"),
        "ratings_avg": ratings.get("average"),
        "thumbnail": p.get("thumbnail_url"),
        "type": p.get("native_type"),
        "recurrence": p.get("recurrence"),
    }


def product_json(url):
    r = get(clean_url(url) + ".json")
    if r is None or r.status_code != 200:
        return None
    return r.json()


def add_details(items):
    for i, it in enumerate(items, 1):
        d = product_json(it["url"])
        if d:
            it["sales_count"] = d.get("sales_count")
            it["created_at"] = d.get("created_at")
            it["summary"] = d.get("summary")
        log(f"  details {i}/{len(items)} {it['name'][:50]!r} sales={it.get('sales_count')}")
        time.sleep(0.6)
    return items


def cmd_search(q, pages, details, sort=None):
    # sort: most_reviewed (best proxy for best sellers), highest_rated, hot_and_new, newest, price_asc
    items, tags, total = [], None, None
    for pg in range(pages):
        params = {"query": q, "from": pg * 9 + 1}
        if sort:
            params["sort"] = sort
        r = get("https://gumroad.com/products/search", params=params,
                headers={"Accept": "application/json"})
        if r is None or r.status_code != 200:
            log(f"  search page {pg + 1} failed")
            break
        d = r.json()
        total = d.get("total")
        tags = tags or d.get("tags_data")
        batch = [summarize(p) for p in d.get("products", [])]
        if not batch:
            break
        items += batch
        time.sleep(0.6)
    seen, uniq = set(), []
    for it in items:
        if it["url"] not in seen:
            seen.add(it["url"]); uniq.append(it)
    if details:
        add_details(uniq)
    return {"query": q, "total_matches": total, "top_tags": tags, "results": uniq}


def page_data(url):
    r = get(url)
    if r is None or r.status_code != 200:
        sys.exit(f"Could not load {url} ({getattr(r, 'status_code', '?')})")
    m = re.search(r'data-page="([^"]+)"', r.text)
    if not m:
        sys.exit(f"No embedded page data on {url}")
    return json.loads(htmllib.unescape(m.group(1)))


def cmd_profile(ref, details):
    user = re.sub(r"^https?://", "", ref).split(".gumroad.com")[0].strip("/")
    url = f"https://{user}.gumroad.com/"
    props = page_data(url)["props"]
    products, sections = {}, []

    def walk(o, section=None):
        if isinstance(o, dict):
            if "permalink" in o and "name" in o and "price_cents" in o:
                it = summarize(o); it["section"] = section
                products.setdefault(it["url"], it)
                return
            for v in o.values():
                walk(v, section)
        elif isinstance(o, list):
            for v in o:
                walk(v, section)

    for s in props.get("sections") or []:
        name = s.get("header") or s.get("type")
        sr = s.get("search_results") or {}
        sections.append({"section": name, "shown": len(sr.get("products") or []), "total": sr.get("total")})
        walk(s, name)
    cp = props.get("creator_profile") or {}
    expected = sum(s["total"] or 0 for s in sections)
    if expected > len(products) and cp.get("name"):
        # profile sections only embed the first 9 products; find the rest via Discover search
        log(f"  profile shows {len(products)} of {expected} products; searching Discover for the rest")
        for it in cmd_search(cp["name"], pages=6, details=False)["results"]:
            if f"//{user}.gumroad.com" in (it.get("seller_profile") or "") + it["url"]:
                it["section"] = "found via search"
                products.setdefault(it["url"], it)
    items = list(products.values())
    if details:
        add_details(items)
    return {
        "creator": cp.get("name"), "profile_url": url, "bio": html_to_text(props.get("bio") or ""),
        "reputation": cp.get("reputation"), "sections": sections,
        "products_expected": expected, "product_count_found": len(items), "products": items,
        "note": "Products that are unlisted from Discover can still be missing; if found < expected, "
                "mention it in your notes.",
    }


def cmd_product(url):
    d = product_json(url)
    if not d:
        sys.exit(f"Could not load {clean_url(url)}.json")
    desc_html = d.get("description_html") or d.get("description") or ""
    seller = d.get("seller") or {}
    ratings = d.get("ratings") or {}
    return {
        "name": d.get("name"), "url": clean_url(d.get("url") or url), "seller": seller.get("name"),
        "price": price(d.get("price_cents"), d.get("currency_code")), "currency": d.get("currency_code"),
        "price_formatted": d.get("price_formatted"), "pay_what_you_want": d.get("is_pay_what_you_want"),
        "sales_count": d.get("sales_count"), "ratings_count": ratings.get("count"),
        "ratings_avg": ratings.get("average"), "ratings_breakdown_1to5_pct": ratings.get("percentages"),
        "created_at": d.get("created_at"), "updated_at": d.get("updated_at"),
        "summary": d.get("summary"), "attributes": d.get("attributes"),
        # tiered products often have a $0 base price; each option's real price = base + difference
        "options": [{"name": o.get("name"),
                     "price": price((d.get("price_cents") or 0) + (o.get("price_difference_cents") or 0), None),
                     "description": o.get("description")} for o in d.get("options") or []],
        "is_physical": d.get("is_physical"), "refund_policy": (d.get("refund_policy") or {}).get("title"),
        "covers": [{"type": c.get("type"), "url": c.get("original_url") or c.get("url"),
                    "size": f"{c.get('native_width')}x{c.get('native_height')}"} for c in d.get("covers") or []],
        "thumbnail": d.get("thumbnail_url"),
        "description_images": re.findall(r'<img[^>]+src="([^"]+)"', desc_html),
        "description_text": html_to_text(desc_html),
    }


def cmd_images(url, out):
    p = cmd_product(url)
    os.makedirs(out, exist_ok=True)
    urls = [("cover", c["url"]) for c in p["covers"] if c["type"] == "image" and c["url"]]
    urls += [("thumbnail", p["thumbnail"])] if p["thumbnail"] else []
    urls += [("description", u) for u in p["description_images"]]
    manifest = []
    for i, (kind, u) in enumerate(urls, 1):
        r = get(u)
        path = None
        if r is not None and r.status_code == 200:
            ct = r.headers.get("content-type", "")
            ext = ".png" if "png" in ct else ".gif" if "gif" in ct else ".webp" if "webp" in ct else ".jpg"
            path = os.path.join(out, f"{i:02d}-{kind}{ext}")
            with open(path, "wb") as f:
                f.write(r.content)
        manifest.append({"n": i, "kind": kind, "file": path, "url": u})
        log(f"  {i:02d} {kind} {'ok' if path else 'FAILED'}")
        time.sleep(0.4)
    info = {k: p[k] for k in ("name", "url", "seller", "price", "currency", "sales_count", "ratings_count")}
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump({"product": info, "images": manifest}, f, indent=2)
    video = [c["url"] for c in p["covers"] if c["type"] != "image"]
    return {"product": info, "downloaded": sum(1 for m in manifest if m["file"]), "out": out,
            "video_or_embed_covers": video}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("--pages", type=int, default=3)
    p.add_argument("--details", action="store_true")
    p.add_argument("--sort", choices=["most_reviewed", "highest_rated", "hot_and_new", "newest", "price_asc"])
    p = sub.add_parser("profile"); p.add_argument("ref"); p.add_argument("--details", action="store_true")
    sub.add_parser("product").add_argument("url")
    p = sub.add_parser("images"); p.add_argument("url"); p.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "search":
        res = cmd_search(a.query, a.pages, a.details, a.sort)
    elif a.cmd == "profile":
        res = cmd_profile(a.ref, a.details)
    elif a.cmd == "product":
        res = cmd_product(a.url)
    else:
        res = cmd_images(a.url, a.out)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
