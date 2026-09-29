# Buy-Side Plan — from eBay comps to buy-anywhere / sell-anywhere decision support

Date: 2026-09-27
Status: proposal (planning seat output — no code changes in this PR)
Owner: Damien
Scope boundary: **decision support only**

---

## 0. Bottom line

`arbitrage-scout` today answers one narrow question well: *"given a listing I
already found on Facebook Marketplace, what would this clear on eBay after
fees and shipping?"* (`src/engine.py:analyze_one`).

The buy side of TROVE needs to answer three bigger questions:

1. **Where should I be looking?** — sourcing scans across Gumtree and Facebook
   Marketplace, not just listings I happen to paste in.
2. **Where is this item most profitable to sell?** — a cross-marketplace margin
   matrix (eBay AU / eBay US / Gumtree resale / FB resale / local pickup), not a
   single eBay number.
3. **What deserves my attention right now?** — alert ranking across many items
   and sources, not a boolean `alert`/`skip` per listing.

This document specifies that extension. It changes **what the tool tells
Damien**, not what the tool does on Damien's behalf.

### Hard guardrails (non-negotiable, carry forward from the current design)

The tool must never, under any phase of this plan:

- **Auto-purchase** anything, place bids, or make offers.
- **Contact buyers or sellers** — no messages, enquiries, "is this still
  available" bots, no phone calls, no email to a counterparty.
- **Move money** — no payments, deposits, escrow, refunds, or card details.
- **Log in to a marketplace account** or use Damien's personal session/cookies
  to bypass rate limits or account-level blocks.
- **Impersonate Damien** to any platform.

Every action above is a **Damien's-hands** action. The tool's output is a
document: a ranked list of opportunities with an auditable estimate attached.
Damien decides, contacts, negotiates, inspects, and pays.

---

## 1. Where the code is now (grounded assessment)

| Piece | File | Current behaviour | Buy-side gap |
|---|---|---|---|
| Listing model | `src/listing.py` | `Listing` dataclass; parser only understands FB Marketplace URLs (`_FBMP_URL_RE`) and "TITLE\n$PRICE · …" mobile-share blobs | No Gumtree parser, no generic/structured intake, no "source" field |
| Comps | `src/ebay_client.py` | `EbayClient.find_comps()` → `CompResult` with sold median (Marketplace Insights) or active median ×0.85 fallback | Only one sell venue (eBay, one locale). No multi-venue pricing |
| Fee/profit | `src/fees.py` | `compute_profit()` → `ProfitBreakdown`; single `FEE_RATES` table (13.25% + $0.30) and USPS-flavoured `estimate_shipping()` | No venue parameter; AU locale still uses US shipping estimates; one fee model |
| Decision | `src/engine.py` | `is_deal = margin ≥ threshold AND profit ≥ floor` → `alert`/`skip` | Boolean only. No ranking, no confidence, no cross-venue comparison |
| Alert | `src/alert.py` | One SMTP email per qualifying listing | No batch/digest, no ranking order, no dedupe |
| Config | `config.yaml` | `locale: AU`, but `min_margin_pct: 20.0` / `min_profit_dollars: 500.00` hard-tuned for big-ticket mode | Thresholds are global, not per-category or per-venue |

Two real inconsistencies the buy-side work must fix in passing:

- `config.yaml` says `locale: AU`, `src/ebay_client.py` defaults `LOCALE="AU"`,
  but `src/fees.py:estimate_shipping()` is US carrier pricing and
  `FEE_RATES` is the US 13.25% table. The eBay AU final value fee is
  **UNKNOWN from this repo** — it is category-dependent and GST treatment
  changes the basis. Shipping would be AusPost. Neither the AU FVF rate nor the
  AusPost table is measured here and no web check was possible from this seat;
  look up eBay's current AU fee page (or read an actual seller invoice) before
  trusting any AU number. Any AU margin number today is approximately right at
  best.
- `README.md` still documents 30% / $15 defaults while `config.yaml` ships
  20% / $500. Doc drift; fix when docs are next touched.

**No secrets were found in this repo.** A gitleaks scan over the full git
history (2 commits) and the working tree returned 0 findings; `.env` is
gitignored and untracked; `.env.example` contains placeholders only. The only
personal data committed is the alert recipient address `damien.corrigan@yahoo.ie`
in `.env.example` (and the same address as the README's SMTP example). That is
PII, not a credential. Recommendation: **clean** on secrets; optionally make
private or scrub the address, because `playbook.md` is a genuinely useful
sourcing strategy document that is currently world-readable.

---

## 2. Target architecture

```
                 ┌──────────────────────────────────────────────┐
  sources        │  src/sources/                                │
  (read-only)    │   base.py     SourceAdapter ABC              │
                 │   facebook.py FB Marketplace (manual/paste)  │
                 │   gumtree.py  Gumtree AU search + detail     │
                 │   manual.py   pasted blob / CSV import       │
                 └───────────────┬──────────────────────────────┘
                                 │ yields Listing (+ source, source_id, seen_at)
                                 ▼
                 ┌──────────────────────────────────────────────┐
  pricing        │  sell-side venues                            │
  (read-only)    │   ebay_client.py  eBay AU / eBay US comps    │
                 │   (later) more venues via same interface     │
                 └───────────────┬──────────────────────────────┘
                                 ▼
                 ┌──────────────────────────────────────────────┐
  decision       │  src/matrix.py   cross-marketplace margins   │
                 │  src/rank.py     opportunity score + ranking │
                 └───────────────┬──────────────────────────────┘
                                 ▼
                 ┌──────────────────────────────────────────────┐
  output         │  src/alert.py    ranked digest email         │
                 │  src/engine.py   CLI: scan / matrix / rank   │
                 │  data/opportunities.jsonl  append-only log   │
                 └──────────────────────────────────────────────┘
```

Design rule: **sources produce `Listing`s; venues produce price estimates;
neither knows about the other.** The matrix combines them; the ranker orders
them; the CLI prints and emails. This is the same shape as the existing
`Listing` → `find_comps` → `compute_profit` pipeline, just with the middle and
last stages made plural.

---

## 3. Workstream A — Sourcing scans (Gumtree + Facebook Marketplace)

### A1. `SourceAdapter` interface

```python
# src/sources/base.py
class SourceAdapter(ABC):
    name: str                       # "gumtree_au", "fb_marketplace", "manual"

    @abstractmethod
    def scan(self, query: str, *, max_pages: int, max_age_hours: int) -> Iterable[Listing]:
        """Yield Listings for one search term. READ-ONLY. Never authenticates."""
```

Rules for every adapter:

- Read-only HTTP, no login, no cookie jars, no stored sessions.
- Identify with a stable, honest User-Agent string the operator controls.
- Per-host rate limit (start: 1 request / 3 s; tighten on 429).
- Respect `robots.txt` for the specific paths used; record the check in the
  scan log so the decision is auditable.
- Never follow a "contact seller" / "message" / "make offer" link.
- Store only fields needed for the decision: title, price, url, location,
  posted_at, condition, source, source_id, photo count. No seller identity
  beyond what the listing already publishes; no seller profile scraping.

### A2. Gumtree adapter (`src/sources/gumtree.py`)

Gumtree AU is the higher-value first target. Verified from this seat: nothing —
the following are **unverified assumptions** carried from the playbook, to be
confirmed against the live site before coding: that search/detail pages render
without login, that the search URL exposes `minPrice`/`maxPrice`/`sort`
parameters, and that result cards carry title/price/location in the HTML.

- Search URL pattern: `https://www.gumtree.com.au/s-search/<term>/k0?…`
  (exact parameter names to be confirmed against the live site before coding —
  this is an implementation task, not an assumption).
- Parse result cards → `Listing`; optional detail fetch per candidate for the
  description and condition.
- Category/price-band presets come from `playbook.md` ("Sydney-specific search
  terms", price A$1500–A$8000, 50 km).

### A3. Facebook Marketplace adapter (`src/sources/facebook.py`)

Facebook is the deliberate exception and must stay the narrow one.

- The current design correctly refuses to scrape Marketplace (README, "Why
  manual-assist"; `src/listing.py` docstring). Marketplace scraping is against
  Facebook's terms, aggressively fingerprinted, and puts Damien's account at
  risk. **This plan does not change that default.**
- What the adapter *does* support, in order of preference:
  1. **Manual/paste intake** — the existing `parse_pasted()` path, extended to
     accept a queue directory and record `source="fb_marketplace"`.
  2. **Saved-listings export** — if Facebook provides a user-initiated export,
     ingest that file. No login automation.
  3. **Paid third-party provider** (Apify / Bright Data actor) as an
     *opt-in, off-by-default* backend, per the README's existing "Future work".
     The provider bears the ToS risk; the adapter just consumes its JSON.
     Requires an explicit `--enable-third-party-fb` flag and a one-time written
     acknowledgement from Damien in `config.yaml` (`fb_third_party_ack: true`).
- Any future automated FB path must be reviewed by Damien before it is enabled.

### A4. Dedupe and provenance

- `source_id` (listing id, or a hash of `source + url`) is the dedupe key.
- `seen_at` timestamps support "new since last scan" ranking.
- `data/seen.jsonl` (append-only) prevents re-alerting the same listing.

---

## 4. Workstream B — Cross-marketplace margin matrix

### B1. Venue abstraction

Generalise `fees.py` and the sell-side call so a venue is a parameter, not an
assumption:

```python
@dataclass(frozen=True)
class Venue:
    key: str              # "ebay_au", "ebay_us", "gumtree_local", "fb_local"
    currency: str         # "AUD" / "USD"
    fvf_rate: float
    per_order_fee: float
    ships: bool           # False → local pickup only
    estimate_shipping_cost: Callable[[str], float]
```

`compute_profit()` gains `venue: Venue` and keeps its current signature
behaviour when a default venue is supplied (backwards compatible; existing
tests in `tests/test_fees.py` must keep passing).

### B2. The matrix

For one `Listing` (buy price + source marketplace) produce one row per viable
sell venue:

| sell venue | est. sale | fees | ship | net rev | profit | margin % | days-to-sale (est.) | confidence |
|---|---|---|---|---|---|---|---|---|
| ebay_au | … | … | … | … | … | … | … | … |
| ebay_us | … | … | … | … | … | … | … | … |
| gumtree_local | … | … | 0 (pickup) | … | … | … | … | … |
| fb_local | … | … | 0 (pickup) | … | … | … | … | … |

- `est. sale` for eBay venues comes from `CompResult.best_estimate` per locale
  (sold median preferred; active ×0.85 fallback, and the fallback must be
  **labelled** in the output — today `source` already carries it).
- Gumtree/FB **sell-side** estimates are the weak point: there is no sold-comps
  API. Use the *asking-price distribution* of comparable active listings,
  discounted (start at −20%, configurable), and mark confidence `low`.
  Never present a low-confidence local estimate as if it were an eBay sold
  median.
- `days-to-sale` is a coarse heuristic per category/venue, explicitly a guess;
  label it as such.
- Local venues with `ships: False` must not be recommended for items that
  cannot be picked up locally (see `playbook.md` "Hard avoids in big-ticket
  mode"). The matrix should mark such cells `infeasible`, not `0`.

### B3. Currency handling

- Store all internal numbers in the venue's native currency plus the locale
  base currency. Do not silently mix AUD and USD (the current `fees.py` US
  table under `locale: AU` is exactly this bug).
- One FX source with a cached daily rate; the rate and its date go into every
  result row. If FX is unavailable, fail loud rather than guess.

### B4. Data model

```python
@dataclass
class Opportunity:
    listing: Listing
    matrix: list[VenueEstimate]      # one row per venue
    best: VenueEstimate              # argmax by profit, ties → higher confidence
    rank_score: float
    reasons: list[str]               # human-readable, auditable
```

Append-only log: `data/opportunities.jsonl` (one JSON object per line, same
spirit as today's `data/scouted.jsonl`).

---

## 5. Workstream C — Alert ranking

Replace the boolean gate with a score and a ranked digest.

### C1. Scoring inputs (all already derivable)

| Signal | Source | Direction |
|---|---|---|
| absolute profit | matrix `best.profit` | higher better |
| margin % | matrix `best.margin_pct` | higher better |
| comp depth | `CompResult.sold_count` | higher better |
| comp confidence | sold median > active fallback | sold better |
| price consistency | IQR / MAD of `sold_prices` | tighter better |
| freshness | `seen_at` vs now | newer first |
| ship feasibility | shipping cost ÷ est. sale | under 10% better |
| category risk | `playbook.md` tiers (Tier 1 > 2 > 3) | lower risk better |
| capital lock-up | `buy_price` | lower better for equal profit |

### C2. Score

Start deliberately simple and transparent:

```
rank_score = 0.35·norm(profit)
           + 0.20·norm(margin_pct)
           + 0.20·comp_confidence      # 0..1
           + 0.10·freshness            # 0..1, half-life 24 h
           + 0.10·norm(comp_depth)
           + 0.05·shipping_feasibility
```

Hard filters stay as config floors (`min_margin_pct`,
`min_profit_dollars`) so nothing below the floor is ever emailed. Weights live
in `config.yaml` so they can be tuned without code changes.

### C3. Digest format

One email per scan (not one per listing), sorted by `rank_score`, with:

- top N (default 10) opportunities, each showing the winning venue and the
  reason it won;
- the full matrix row for the winner, plus the next-best venue for contrast;
- explicit confidence label and the fallback flag where relevant;
- a "suppressed" count (`below floor`, `duplicate`, `infeasible`) so silence is
  explainable.

Every alert keeps today's caveat: *estimate — verify comps against the exact
item and condition before buying.*

### C4. CLI surface

```
scout scan  --source gumtree_au --query "Festool" [--max-pages 3]
scout matrix data/queue.txt            # per-listing venue matrix, ranked
scout watch data/queue.txt             # existing behaviour, now ranking-aware
scout analyze                          # existing single-listing path
```

`--no-alert` continues to mean "analyse and print, send nothing".

---

## 6. Phased rollout

**Phase 0 — correctness (do first, small).**
Fix the AU locale fee/shipping mismatch; align README/config thresholds;
add a `source` field to `Listing` with a default of `"manual"`.
Exit: `tests/test_fees.py` green, AU shipping table in place, docs match config.

**Phase 1 — venue abstraction + matrix (no new sources).**
Add `Venue`, generalise `compute_profit`, add `src/matrix.py`. eBay AU + eBay US
only. Reuse the existing queue/paste intake.
Exit: `scout matrix` prints a two-venue table for the example queue; matrix is
unit-tested with fixed comp inputs (no network in tests).

**Phase 2 — ranking + digest.**
Add `src/rank.py`, weighted score, ranked digest email with suppression counts.
Exit: ranking unit tests; a dry-run digest against `data/example_queue.txt`
shown in the PR/issue as a receipt.

**Phase 3 — Gumtree sourcing.**
`SourceAdapter`, rate limiter, `src/sources/gumtree.py`, robots check, seen-log
dedupe.
Exit: a scan of one playbook search term produces a deduped, logged set of
listings; re-running does not re-alert.

**Phase 4 — local sell venues.**
Gumtree-local and FB-local columns with low-confidence asking-price estimates
and `infeasible` handling.

**Phase 5 (optional, gated) — third-party FB sourcing.**
Off by default; requires the explicit acknowledgement flag. Not started without
Damien's written go-ahead.

---

## 7. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Platform ToS / account ban (FB) | Damien's account, legal exposure | Keep FB manual/manual-export; third-party path off by default and gated |
| Rate-limit / IP block (Gumtree) | Scan failures | Honest UA, 3 s spacing, backoff on 429, cache pages |
| Sold-comps data quality | Wrong margin → bad purchase | Prefer sold median, label fallback, surface `comp_count` and confidence, keep the "verify" caveat |
| Single stale comp skews median | Overstated profit | Use robust spread (IQR/MAD) as a confidence signal; require min comp depth for high confidence |
| Currency mismatch | Silent 40% error | Venue-native storage + dated FX, fail loud if FX missing |
| Automation creep | Guardrail breach | The three prohibitions in §0 are enforced by absence of any credential/contact/payment code path; review checklist for every PR |
| Strategy doc public | Competitive leakage | Scrub PII / consider private (see §1) |

---

## 8. Explicit non-goals

- No automated purchasing, bidding, offers, or checkout.
- No buyer or seller messaging of any kind.
- No payment, deposit, or escrow handling.
- No marketplace login automation or session reuse.
- No account creation, captcha solving, or rate-limit circumvention.
- No storing seller personal data beyond what a public listing shows.

---

## 9. Open questions for Damien

1. Primary sell venue for the buy-side: eBay AU only, or AU + US from the start?
2. Gumtree sourcing cadence (hourly / daily) and the initial search-term set —
   reuse the playbook's Sydney list?
3. Keep the repo public (with PII scrubbed) or make it private?
4. Confirm eBay Marketplace Insights access status, since every sold-median
   estimate depends on it; without it the whole matrix is active-price-based.
