# GLPcompara — price scraper

Scrapes real GLP-1 prices from pharmacy sites, matches them to the canonical
catalog and writes `data/prices.json` (consumed by the front-end) and
`data/prices_raw.json` (every product found, for tuning matches).

## Run locally
```bash
pip install -r scraper/requirements.txt
python scraper/scrape.py
```

## Files
- `scraper/products.json` — canonical catalog. `name` must match `RAW_DATA` names
  in `index.html`. `match_all` / `match_any` / `exclude` tokens select the right
  dose variant within a family's search results. Tune these against `prices_raw.json`.
- `scraper/scrape.py` — orchestrator + per-source parsers.
- `data/prices.json` — `{ generated_at, currency, prices: { "<name>": { Benavides, Ahorro, Clivi, sources:{…} } } }`
- `.github/workflows/scrape-prices.yml` — daily cron; commits refreshed data → Vercel auto-deploys.

## Source status
| Source | Status | Notes |
|---|---|---|
| **Benavides** | ✅ working | Magento `catalogsearch`, server-rendered prices. 16/20 SKUs matched. |
| **Farmacias del Ahorro** | 🟡 stub | Magento; robots disallows `?q=`. Use product/category paths + embedded price JSON. |
| **Clivi** | 🟡 stub | Membership pricing, no per-dose pages. Needs the per-presentation prices (best from an internal source). |
| **Farmacias Guadalajara** | 🔴 phase 2 | Edge-blocked (HTTP 000) — needs headless browser (Playwright) + proxy. |
| **San Pablo** | 🔴 phase 2 | Akamai 403 — needs headless + stealth/proxy. |

## Adding / fixing a source
1. Add a `scrape_<name>(query)` returning `[{title, price, url}]`.
2. Register it in `SOURCES`.
3. Run, inspect `data/prices_raw.json`, then tune `match_*`/`exclude` tokens in `products.json`.

## Compliance
- Identifies as `GLPcompara-PriceBot`, throttles between requests, respects robots.txt
  intent (e.g. Benavides allows `/catalogsearch`; Ahorro disallows `?q=` for generic bots).
- Prices are shown as *orientativos* on the site. Prefer official APIs / written
  permission for production-scale scraping.
