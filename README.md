# Arbitrage Scout

Find profitable flips between Facebook Marketplace and eBay — categories: video
games, antiques/collectibles, electronics, and tools. Alerts you by email when
a listing clears your profit threshold (30% net margin and $15 absolute by
default) after eBay fees and shipping.

## Why "manual-assist" instead of direct Marketplace scraping

Facebook's Terms of Service prohibit automated scraping of Marketplace, they
fingerprint and rate-limit aggressively, and accounts that get caught get
banned. This tool deliberately keeps **you** in the browsing loop and only
automates the comp lookup, the math, and the alert — the parts that don't put
your Facebook account at risk.

The workflow:

1. You scroll Marketplace on your phone or laptop like normal.
2. When you see something interesting, copy/paste the listing into the tool
   (or append it to `data/queue.txt`).
3. Scout queries eBay's official API for sold comps in the same category,
   computes net profit after fees and shipping, and emails you if the deal
   clears your threshold.

For a fully hands-off version, the upgrade path is to add a paid scraping
provider (Apify, Bright Data) — see "Future work" at the bottom.

## Setup

### 1. Install

```bash
cd arbitrage_scout
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Get an eBay API key (free)

1. Sign up at <https://developer.ebay.com/> — pick "Individual" account.
2. Go to **My Account → Application Keysets** and create a **Production** keyset.
   You'll get an **App ID (Client ID)** and **Cert ID (Client Secret)**.
3. (Optional but recommended) Apply for the **Marketplace Insights API** at
   <https://developer.ebay.com/api-docs/buy/marketplace-insights/overview.html>.
   Approval is usually a couple of days. Without it, the tool falls back to
   active listings (less accurate — those are asking prices, not sale prices).

### 3. Get a Yahoo Mail app password

Yahoo blocks SMTP logins that use your real password. Generate a 16-character
app password at <https://login.yahoo.com/account/security> → "Generate app
password" → name it "arbitrage-scout".

### 4. Configure

Copy `.env.example` to `.env` and fill it in:

```bash
cp .env.example .env
# edit .env with your eBay keys + Yahoo app password
set -a; source .env; set +a    # load into shell
```

Tune the thresholds in `config.yaml` if 30% margin / $15 floor isn't what you
want.

## Usage

### Analyze a single listing

```bash
echo "Sealed Nintendo 64 with 4 games
$120 · Boston, MA
https://www.facebook.com/marketplace/item/1234567890" | python -m src.engine analyze
```

You'll get a JSON result on stdout and (if it qualifies) an email in your inbox.

### Watch a queue of listings

Append listings to a text file, separated by `---`:

```
DeWalt 20V Max XR Brushless Drill
$75 · Cambridge, MA
https://www.facebook.com/marketplace/item/9876543210
---
Antique cast iron Singer sewing machine
$30 · Quincy, MA
https://www.facebook.com/marketplace/item/1111111111
```

Then process them in one shot:

```bash
python -m src.engine watch data/example_queue.txt
```

Every analyzed listing is appended to `data/scouted.jsonl` so you can review the
history (and feed it into a spreadsheet or dashboard later).

### Dry run (no email, no spam)

```bash
python -m src.engine --no-alert watch data/example_queue.txt
```

## How the profit math works

For each listing, Scout:

1. Cleans up the title into a search query and classifies the item into one of
   the eight eBay categories defined in `src/ebay_client.py`.
2. Queries eBay's Marketplace Insights API for the last 90 days of sold comps
   in the same category and (if specified) the same condition.
3. Takes the **median** sold price as the estimated sale price. (Median, not
   mean, so a single weird auction doesn't skew the estimate.)
4. Subtracts fees: `13.25% * (sale + shipping_charged) + $0.30 per order`.
5. Subtracts a category-typical shipping cost (you pay it — see `src/fees.py`).
6. Compares the resulting net revenue to the Marketplace asking price.
7. If margin ≥ 30% AND absolute profit ≥ $15, sends the alert email.

You can swap in your own fee table — e.g. if you have an eBay Store
subscription, or sell in a category eBay charges differently for — by editing
`FEE_RATES` in `src/fees.py`.

## Running it as a daemon

The "watch" mode is one-shot, but the engine is cheap to call. The simplest
hands-off setup is a cron job that drains a queue file every 10 minutes:

```
*/10 * * * * cd ~/arbitrage_scout && /usr/bin/flock -n .lock python -m src.engine watch data/queue.txt && truncate -s 0 data/queue.txt
```

Then your phone workflow is: see a listing on Marketplace → share it to a note
app → periodically paste new items into `queue.txt`. Or set up a shortcut that
appends to the file directly.

## Future work

- **Paid scraping back-end.** Plug in Apify's Facebook Marketplace actor or
  Bright Data to enumerate listings automatically. ~$30–$100/mo, shifts the ToS
  risk to them. The engine already has a clean `Listing` interface — you'd just
  add a `src/sources/apify.py` that yields Listings and feed them into
  `analyze_one`.
- **OfferUp / Craigslist sources.** Same interface, public-ish data.
- **eBay live-auction sniping.** Use the same Insights data to find auctions
  ending soon below the sold median — pure eBay-to-eBay arbitrage with zero ToS
  friction.
- **Title similarity scoring.** Right now the title goes into eBay's search
  more or less verbatim. Embedding-based matching (sentence-transformers) would
  catch better comps when sellers use vague titles like "Vintage Nintendo lot".

## Files

```
arbitrage_scout/
├── README.md
├── config.yaml              # thresholds + behavior
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── ebay_client.py       # eBay Browse + Marketplace Insights API
│   ├── fees.py              # fee model + ProfitBreakdown dataclass
│   ├── listing.py           # parse pasted Marketplace blobs → Listing
│   ├── alert.py             # SMTP email alerter
│   └── engine.py            # CLI: `analyze` and `watch`
├── tests/
│   ├── test_fees.py
│   └── test_listing.py
└── data/
    ├── example_queue.txt
    └── scouted.jsonl        # created on first run
```
