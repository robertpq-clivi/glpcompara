#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLPcompara price scraper.

Scrapes GLP-1 medication prices from supported pharmacies, matches them to the
canonical catalog (scraper/products.json) and writes:
  - data/prices.json      → matched prices consumed by the front-end
  - data/prices_raw.json  → every product found per source (for tuning matches)

Sources (phase 1): Benavides (working), Farmacias del Ahorro (best-effort),
Clivi (best-effort / plan price). Guadalajara & San Pablo are phase 2
(bot-protected — need a headless browser + proxy).

Usage:  python scraper/scrape.py
Respects robots.txt intent, throttles requests, and identifies itself.
"""
import json, re, time, sys, datetime, pathlib
import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG  = json.loads((ROOT / "scraper" / "products.json").read_text(encoding="utf-8"))
UA   = "GLPcompara-PriceBot/1.0 (+https://glpcompara.com.mx; price comparison)"
HEADERS = {"User-Agent": UA, "Accept-Language": "es-MX,es;q=0.9"}
TIMEOUT = 25
THROTTLE = 2.0  # seconds between requests to the same site

def get(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def money(text):
    m = re.search(r"([0-9][0-9,]*\.?[0-9]*)", text.replace("$", "").strip())
    return float(m.group(1).replace(",", "")) if m else None

# ── SOURCES ────────────────────────────────────────────────────────────────
def scrape_benavides(query):
    """Magento catalogsearch — server-rendered product cards with prices."""
    url = f"https://www.benavides.com.mx/catalogsearch/result/?q={query}"
    soup = BeautifulSoup(get(url), "lxml")
    out = []
    for item in soup.select("li.product-item, .product-item"):
        a = item.select_one("a.product-item-link")
        price_el = item.select_one("[data-price-amount]") or item.select_one(".price")
        if not a:
            continue
        title = a.get_text(" ", strip=True)
        price = None
        if price_el and price_el.has_attr("data-price-amount"):
            price = float(price_el["data-price-amount"])
        elif price_el:
            price = money(price_el.get_text())
        if title and price:
            out.append({"title": title, "price": round(price), "url": a.get("href", url)})
    return out

def scrape_ahorro(query):
    """Farmacias del Ahorro (Magento). robots disallows ?q= for generic bots,
    so we read the category/product JSON embedded in the page instead. Best-effort."""
    # TODO(phase-1b): use product/category path URLs (not ?q=) per robots.txt,
    # and parse the embedded Magento price JSON. Returns [] until wired.
    return []

def scrape_clivi(query):
    """Clivi is membership-based; no per-dose product pages. Best-effort plan price.
    TODO: replace with the exact per-presentation prices (internal source)."""
    return []

SOURCES = {
    "Benavides": scrape_benavides,
    "Ahorro":    scrape_ahorro,
    "Clivi":     scrape_clivi,
}

# ── MATCHING ───────────────────────────────────────────────────────────────
def norm(s):
    return re.sub(r"\s+", " ", s.lower())

def matches(title, prod):
    t = norm(title)
    for ex in prod.get("exclude", []):
        if ex.lower() in t:
            return False
    if "match_all" in prod and not all(tok.lower() in t for tok in prod["match_all"]):
        return False
    if "match_any" in prod and not any(tok.lower() in t for tok in prod["match_any"]):
        return False
    return True

def pick(products, prod):
    cands = [p for p in products if matches(p["title"], prod)]
    if not cands:
        return None
    return min(cands, key=lambda p: p["price"])  # cheapest matching variant

# ── ORCHESTRATION ──────────────────────────────────────────────────────────
def main():
    raw = {src: {} for src in SOURCES}
    # scrape each source once per family, cache results
    for src, fn in SOURCES.items():
        for fam, meta in CFG["families"].items():
            try:
                items = fn(meta["query"])
                raw[src][fam] = items
                print(f"  {src}/{fam}: {len(items)} products")
            except Exception as e:
                raw[src][fam] = []
                print(f"  {src}/{fam}: ERROR {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(THROTTLE)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prices = {}
    matched_count = 0
    for prod in CFG["products"]:
        name, fam = prod["name"], prod["family"]
        row = {"sources": {}}
        for src in SOURCES:
            hit = pick(raw[src].get(fam, []), prod)
            if hit:
                row[src] = hit["price"]
                row["sources"][src] = {"price": hit["price"], "url": hit["url"], "title": hit["title"]}
                matched_count += 1
            else:
                row[src] = None
        prices[name] = row

    out = {"generated_at": now, "currency": "MXN", "prices": prices}
    (ROOT / "data" / "prices.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "data" / "prices_raw.json").write_text(json.dumps({"generated_at": now, "raw": raw}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote data/prices.json — {matched_count} source-prices matched across {len(prices)} products.")

if __name__ == "__main__":
    main()
