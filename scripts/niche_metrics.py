#!/usr/bin/env python3
"""Compute niche-scout's numbers from the owner's exported CSVs. Never from guesses.

niche-scout does not crawl Etsy. The owner exports keyword and competitor data from
their research tool, uploads it to Drive 'Northing Studio/research/input/', and
upload_to_drive.py --pull-inputs brings it to data/research-input/. This script
validates those files and computes every number the agent may quote. A missing
file, a missing column, or a blank or unreadable required cell ends the run with
exit 1. Nothing is defaulted or estimated.

  niche_metrics.py [--dir data/research-input] [--json research/niche-metrics-<date>.json]

Expected files (header templates: scripts/templates/):

  keywords.csv     niche, keyword, platform, monthly_searches, competing_listings,
                   avg_price_usd, source_tool, export_date
  competitors.csv  niche, platform, listing_url, shop, title, price_usd, review_count,
                   rating_avg, est_monthly_sales, is_digital, source_tool, export_date
                   (rating_avg and est_monthly_sales may be blank)

Types:
- platform: etsy or gumroad
- numbers: plain digits, no currency symbols
- is_digital: yes or no
- export_date: YYYY-MM-DD

Per niche it reports:
  density  searches per live listing (median across the niche's keywords)
  price    digital listings at $10 or more that show transactions (sales or reviews).
           Fewer than 3 means kill: the niche is not transacting at $10+.
  moat     median review count of the top 10 digital listings by reviews
  gaps     a niche present in only one file, or files exported more than
           --max-age-days ago (warnings the agent must repeat)
"""
import argparse
import csv
import datetime
import json
import os
import statistics
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FILES = {
    "keywords.csv": (["niche", "keyword", "platform", "monthly_searches", "competing_listings",
                      "avg_price_usd", "source_tool", "export_date"], set()),
    "competitors.csv": (["niche", "platform", "listing_url", "shop", "title", "price_usd", "review_count",
                         "rating_avg", "est_monthly_sales", "is_digital", "source_tool", "export_date"],
                        {"rating_avg", "est_monthly_sales"}),
}
INT_COLS = {"monthly_searches", "competing_listings", "review_count", "est_monthly_sales"}
FLOAT_COLS = {"avg_price_usd", "price_usd", "rating_avg"}
BOOL = {"yes": True, "y": True, "true": True, "1": True, "no": False, "n": False, "false": False, "0": False}


def load(path, cols, optional, errors):
    name = os.path.basename(path)
    if not os.path.exists(path):
        errors.append(f"{name} is missing from {os.path.relpath(os.path.dirname(path), ROOT)}/ - export it "
                      f"from your research tool with columns: {', '.join(cols)}")
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [h.strip().lower() for h in (reader.fieldnames or [])]
        missing = [c for c in cols if c not in header]
        if missing:
            errors.append(f"{name} is missing column(s): {', '.join(missing)}")
            return []
        rows = []
        for n, raw in enumerate(reader, start=2):
            row = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            bad = False
            for c in cols:
                v = row.get(c, "")
                if v == "":
                    if c not in optional:
                        errors.append(f"{name} line {n}: '{c}' is blank")
                        bad = True
                    row[c] = None
                    continue
                try:
                    if c in INT_COLS:
                        row[c] = int(v.replace(",", ""))
                    elif c in FLOAT_COLS:
                        row[c] = float(v.replace(",", "").lstrip("$"))
                    elif c == "is_digital":
                        row[c] = BOOL[v.lower()]
                    elif c == "export_date":
                        row[c] = datetime.date.fromisoformat(v)
                    elif c == "platform":
                        if v.lower() not in ("etsy", "gumroad"):
                            raise ValueError(v)
                        row[c] = v.lower()
                except (ValueError, KeyError):
                    errors.append(f"{name} line {n}: '{c}' = {v!r} is not a valid value")
                    bad = True
            if not bad:
                rows.append(row)
        if not rows and not any(e.startswith(name) for e in errors):
            errors.append(f"{name} has no data rows")
        return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=os.path.join(ROOT, "data", "research-input"))
    ap.add_argument("--json")
    ap.add_argument("--max-age-days", type=int, default=45)
    a = ap.parse_args()

    errors = []
    data = {name: load(os.path.join(a.dir, name), cols, opt, errors) for name, (cols, opt) in FILES.items()}
    if errors:
        print("FAIL - the research inputs cannot be used. Nothing is estimated in their place:", file=sys.stderr)
        for e in errors[:60]:
            print(f"  {e}", file=sys.stderr)
        if len(errors) > 60:
            print(f"  ... and {len(errors) - 60} more", file=sys.stderr)
        return 1

    today = datetime.date.today()
    warnings = []
    for name, rows in data.items():
        oldest = min(r["export_date"] for r in rows)
        if (today - oldest).days > a.max_age_days:
            warnings.append(f"{name}: oldest export is {oldest} ({(today - oldest).days} days old, "
                            f"limit {a.max_age_days})")

    kw, comp = data["keywords.csv"], data["competitors.csv"]
    niches = sorted({r["niche"] for r in kw} | {r["niche"] for r in comp})
    results = []
    for niche in niches:
        k = [r for r in kw if r["niche"] == niche]
        c = [r for r in comp if r["niche"] == niche]
        rec = {"niche": niche, "data_gaps": []}
        if not k:
            rec["data_gaps"].append("no rows in keywords.csv")
        if not c:
            rec["data_gaps"].append("no rows in competitors.csv")
        if k:
            ratios = [r["monthly_searches"] / max(r["competing_listings"], 1) for r in k]
            rec["density"] = {"keywords": len(k),
                              "monthly_searches_total": sum(r["monthly_searches"] for r in k),
                              "competing_listings_median": statistics.median(r["competing_listings"] for r in k),
                              "searches_per_listing_median": round(statistics.median(ratios), 4),
                              "platforms": sorted({r["platform"] for r in k})}
        if c:
            digital = [r for r in c if r["is_digital"]]
            transacting = [r for r in digital if r["price_usd"] >= 10
                           and ((r["est_monthly_sales"] or 0) > 0 or r["review_count"] > 0)]
            rec["price"] = {"listings": len(c), "digital_listings": len(digital),
                            "physical_excluded": len(c) - len(digital),
                            "median_digital_price_usd": round(statistics.median(r["price_usd"] for r in digital), 2)
                            if digital else None,
                            "transacting_at_10_plus": len(transacting),
                            "max_transacting_price_usd": max((r["price_usd"] for r in transacting), default=None),
                            "kill": len(transacting) < 3}
            if rec["price"]["kill"]:
                rec["price"]["kill_reason"] = (f"not transacting at $10+: {len(transacting)} digital listing(s) "
                                               f"at $10 or more show sales or reviews (3 needed)")
            top = sorted(digital, key=lambda r: r["review_count"], reverse=True)[:10]
            rec["moat"] = {"top_n": len(top),
                           "median_reviews_top10": statistics.median(r["review_count"] for r in top) if top else None,
                           "max_reviews": top[0]["review_count"] if top else None}
        results.append(rec)

    report = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "inputs": {name: {"rows": len(rows), "oldest_export": str(min(r["export_date"] for r in rows)),
                                "newest_export": str(max(r["export_date"] for r in rows)),
                                "source_tools": sorted({r["source_tool"] for r in rows})}
                         for name, rows in data.items()},
              "warnings": warnings, "niches": results}
    out = a.json or os.path.join(ROOT, "research", f"niche-metrics-{today.isoformat()}.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(report, open(out, "w", encoding="utf-8"), indent=2)

    print(f"{'niche':<34} {'srch/listing':>12} {'$10+ txn':>9} {'moat':>7}  status")
    for r in results:
        dens = r.get("density", {}).get("searches_per_listing_median")
        txn = r.get("price", {}).get("transacting_at_10_plus")
        moat = r.get("moat", {}).get("median_reviews_top10")
        status = ("DATA GAP: " + "; ".join(r["data_gaps"]) if r["data_gaps"]
                  else "KILL: " + r["price"]["kill_reason"] if r["price"]["kill"] else "candidate")
        print(f"{r['niche'][:34]:<34} {dens if dens is not None else '-':>12} "
              f"{txn if txn is not None else '-':>9} {moat if moat is not None else '-':>7}  {status}")
    for w in warnings:
        print(f"  WARN  {w}")
    print(f"\n  wrote {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
