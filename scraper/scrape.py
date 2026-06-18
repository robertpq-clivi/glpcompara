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
import os, json, re, time, sys, datetime, pathlib
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
    """Farmacias del Ahorro (Magento). Prices are JS-rendered on category pages,
    but the Magento GraphQL API is open. We POST (no query string → robots-clean)
    and read name + final price + url_key."""
    gql = ('{products(search:"%s",pageSize:30){items{name url_key '
           'price_range{minimum_price{final_price{value}}}}}}' % query)
    # fahorro's WAF rejects non-browser User-Agents on /graphql, so use a
    # browser UA + standard headers for this API call.
    bh = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "application/json", "Content-Type": "application/json",
        "Accept-Language": "es-MX,es;q=0.9", "Store": "default",
        "Origin": "https://www.fahorro.com", "Referer": "https://www.fahorro.com/control-de-peso.html",
    }
    r = requests.post("https://www.fahorro.com/graphql",
                      data=json.dumps({"query": gql}), headers=bh, timeout=TIMEOUT)
    r.raise_for_status()
    items = (r.json().get("data") or {}).get("products", {}).get("items", []) or []
    out = []
    for it in items:
        try:
            v = it["price_range"]["minimum_price"]["final_price"]["value"]
        except (KeyError, TypeError):
            continue
        if not v:
            continue
        uk = it.get("url_key") or ""
        url = f"https://www.fahorro.com/{uk}.html" if uk else "https://www.fahorro.com/control-de-peso/"
        out.append({"title": it.get("name", ""), "price": round(v), "url": url})
    return out

# ── ANTI-BOT PROXY (Guadalajara & San Pablo) ────────────────────────────────
# These sites block datacenter IPs (Akamai / WAF), so we route requests through
# an anti-bot scraping API with residential proxies. Set SCRAPER_API_KEY (and
# optionally SCRAPER_PROVIDER=zenrows|scraperapi) as an env var / GitHub secret.
# Take the last whitespace-delimited token, so a key pasted with stray labels
# or newlines (e.g. "SCRAPER_PROVIDER = zenrows\n<key>") still resolves cleanly.
_raw_key = os.environ.get("SCRAPER_API_KEY", "")
SCRAPER_KEY = _raw_key.split()[-1] if _raw_key.split() else ""
SCRAPER_PROVIDER = os.environ.get("SCRAPER_PROVIDER", "zenrows").strip().lower()

def via_proxy(target_url):
    if not SCRAPER_KEY:
        raise RuntimeError("SCRAPER_API_KEY not set")
    if SCRAPER_PROVIDER == "scraperapi":
        r = requests.get("https://api.scraperapi.com/", params={
            "api_key": SCRAPER_KEY, "url": target_url, "premium": "true", "country_code": "mx"},
            timeout=70)
    else:  # zenrows
        r = requests.get("https://api.zenrows.com/v1/", params={
            "apikey": SCRAPER_KEY, "url": target_url, "premium_proxy": "true", "proxy_country": "mx"},
            timeout=70)
    r.raise_for_status()
    return r.text

def vtex_search(base, query):
    """VTEX public catalog API (common in MX pharmacies), fetched via the proxy."""
    url = f"{base}/api/catalog_system/pub/products/search?ft={query}&_from=0&_to=23"
    data = json.loads(via_proxy(url))
    out = []
    for p in data if isinstance(data, list) else []:
        name = p.get("productName", "")
        link = p.get("link") or (base + "/" + p.get("linkText", "") + "/p")
        price = None
        for it in p.get("items", []):
            for s in it.get("sellers", []):
                co = s.get("commertialOffer", {})
                if co.get("Price"):
                    price = co["Price"]; break
            if price: break
        if name and price:
            out.append({"title": name, "price": round(price), "url": link})
    return out

def scrape_guadalajara(query):
    return vtex_search("https://www.farmaciasguadalajara.com", query)

def scrape_sanpablo(query):
    return vtex_search("https://www.farmaciasanpablo.com.mx", query)

# Clivi has no per-dose public pages (membership pricing), so prices are curated
# manually in scraper/clivi_prices.json (keyed by canonical product name).
CLIVI = json.loads((ROOT / "scraper" / "clivi_prices.json").read_text(encoding="utf-8"))

SCRAPERS = {
    "Benavides": scrape_benavides,
    "Ahorro":    scrape_ahorro,
}
# Guadalajara & San Pablo only run when an anti-bot proxy key is configured.
if SCRAPER_KEY:
    SCRAPERS["Guadalajara"] = scrape_guadalajara
    SCRAPERS["SanPablo"]    = scrape_sanpablo

# Column order shown in data/prices.json
SOURCE_ORDER = ["Clivi", "Ahorro", "Benavides", "Guadalajara", "SanPablo"]

# ── MATCHING ───────────────────────────────────────────────────────────────
def norm(s):
    s = s.lower()
    s = re.sub(r"(\d)\s*mg", r"\1 mg", s)   # "5mg" / "12.5Mg" → "5 mg" / "12.5 mg"
    return re.sub(r"\s+", " ", s)

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
    mn = prod.get("min_price")
    if mn:
        cands = [p for p in cands if p["price"] >= mn]  # filter wrong-pack outliers
    if not cands:
        return None
    return min(cands, key=lambda p: p["price"])  # cheapest matching variant

# ── RECON (diagnose Guadalajara / San Pablo through the proxy; never prints key) ──
def recon():
    for base in ["https://www.farmaciasguadalajara.com", "https://www.farmaciasanpablo.com.mx"]:
        print(f"\n===== RECON {base} =====")
        try:
            h = via_proxy(base + "/")
            print(f"  home: {len(h)} chars")
            sig = {k: (k.lower() in h.lower()) for k in ['vtex', '__NEXT_DATA__', 'magento', 'algolia', 'graphql', 'ng-version', 'data-beasties', 'shopify', 'salesforce', 'demandware']}
            print(f"  signals: {sig}")
            scripts = sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', h)))
            print(f"  scripts ({len(scripts)}):")
            for s in scripts[:18]:
                print("    ", s)
            apis = sorted(set(re.findall(r'https?://[a-z0-9.\-]*(?:api|graphql|search)[a-z0-9.\-]*', h, re.I)
                              + re.findall(r'/(?:api|graphql|rest|search|buscar|busqueda)[a-z0-9/_\-]*', h, re.I)))
            print(f"  api/search hints ({len(apis)}): {apis[:25]}")
            forms = re.findall(r'<form[^>]+action="([^"]+)"', h)
            print(f"  form actions: {forms[:6]}")
        except Exception as e:
            print(f"  home error: {type(e).__name__}: {e}")

# ── ORCHESTRATION ──────────────────────────────────────────────────────────
def main():
    if os.environ.get("SCRAPER_RECON"):
        recon(); return
    raw = {src: {} for src in SCRAPERS}
    # scrape each source once per family, cache results
    for src, fn in SCRAPERS.items():
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
        for src in SOURCE_ORDER:
            row[src] = None
        # scraped sources
        for src in SCRAPERS:
            hit = pick(raw[src].get(fam, []), prod)
            if hit:
                row[src] = hit["price"]
                row["sources"][src] = {"price": hit["price"], "url": hit["url"], "title": hit["title"]}
                matched_count += 1
        # Clivi (curated)
        if name in CLIVI["prices"]:
            row["Clivi"] = CLIVI["prices"][name]
            row["sources"]["Clivi"] = {"price": CLIVI["prices"][name], "url": CLIVI["url"], "title": CLIVI["note"]}
            matched_count += 1
        prices[name] = row

    out = {"generated_at": now, "currency": "MXN", "prices": prices}
    (ROOT / "data" / "prices.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "data" / "prices_raw.json").write_text(json.dumps({"generated_at": now, "raw": raw}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote data/prices.json — {matched_count} source-prices matched across {len(prices)} products.")

if __name__ == "__main__":
    main()
