"""
eBay API client for arbitrage comp lookups.

Uses two eBay APIs:
  1. Browse API           – currently active listings (what's for sale right now)
  2. Marketplace Insights – sold/completed listings in the last 90 days (true market value)

The Marketplace Insights API requires approval from eBay (free, but you must apply).
If you don't have access, set USE_INSIGHTS=False and the client falls back to using
active listings only (less accurate — current asking prices, not actual sale prices).

Auth: eBay uses OAuth 2.0 client credentials flow. You need:
  - EBAY_CLIENT_ID
  - EBAY_CLIENT_SECRET
Get them at https://developer.ebay.com/my/keys (free developer account).
"""

from __future__ import annotations

import base64
import logging
import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional

import requests

log = logging.getLogger(__name__)

EBAY_ENV = os.getenv("EBAY_ENV", "production")  # or "sandbox"
LOCALE = os.getenv("LOCALE", "AU").upper()       # "AU" or "US"

# eBay's API endpoints are the same regardless of marketplace — the marketplace
# is selected via the X-EBAY-C-MARKETPLACE-ID header, set in _headers() below.
TOKEN_URL = (
    "https://api.ebay.com/identity/v1/oauth2/token"
    if EBAY_ENV == "production"
    else "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
)
BROWSE_URL = (
    "https://api.ebay.com/buy/browse/v1/item_summary/search"
    if EBAY_ENV == "production"
    else "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
)
INSIGHTS_URL = (
    "https://api.ebay.com/buy/marketplace_insights/v1_beta/item_sales/search"
    if EBAY_ENV == "production"
    else "https://api.sandbox.ebay.com/buy/marketplace_insights/v1_beta/item_sales/search"
)

LOCALE_CONFIG = {
    "AU": {"marketplace_id": "EBAY_AU", "currency": "AUD", "country": "AU"},
    "US": {"marketplace_id": "EBAY_US", "currency": "USD", "country": "US"},
}


# Category IDs we care about. eBay has thousands of leaf categories,
# but these top-level ones give us good filtering coverage.
CATEGORY_IDS = {
    "video_games":    "1249",   # Video Games & Consoles
    "antiques":       "20081",  # Antiques
    "collectibles":   "1",      # Collectibles
    "electronics":    "293",    # Consumer Electronics
    "computers":      "58058",  # Computers/Tablets & Networking
    "cell_phones":    "15032",  # Cell Phones & Accessories
    "cameras":        "625",    # Cameras & Photo
    "tools":          "631",    # Home Improvement > Tools
}


@dataclass
class CompResult:
    """Result of looking up comparable sales for an item."""
    query: str
    sold_count: int = 0
    active_count: int = 0
    sold_prices: list[float] = field(default_factory=list)
    active_prices: list[float] = field(default_factory=list)
    sample_titles: list[str] = field(default_factory=list)
    source: str = "insights"  # "insights" or "active_fallback"

    @property
    def median_sold(self) -> Optional[float]:
        return statistics.median(self.sold_prices) if self.sold_prices else None

    @property
    def median_active(self) -> Optional[float]:
        return statistics.median(self.active_prices) if self.active_prices else None

    @property
    def best_estimate(self) -> Optional[float]:
        """Best estimate of what we could realistically sell this for.
        Prefer sold-listing median (actual market clearing price); fall back to
        active listings discounted 15% (since asking prices > sale prices on average).
        """
        if self.median_sold is not None:
            return self.median_sold
        if self.median_active is not None:
            return round(self.median_active * 0.85, 2)
        return None


class EbayClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        use_insights: Optional[bool] = None,
    ):
        self.client_id = client_id or os.environ["EBAY_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["EBAY_CLIENT_SECRET"]
        # Marketplace Insights requires a separate eBay-side approval (the
        # "Application Growth Check"). Default OFF; turn on with USE_INSIGHTS=1
        # env var once you've been granted access. Until then we use the
        # Browse API alone, which works on the default public OAuth scope.
        if use_insights is None:
            use_insights = os.environ.get("USE_INSIGHTS", "").lower() in ("1", "true", "yes")
        self.use_insights = use_insights
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    # ------------------------------------------------------------------ auth

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        # Default public scope (covers Browse API). Only add the Insights scope
        # if the caller has been granted access to that restricted API.
        scopes = ["https://api.ebay.com/oauth/api_scope"]
        if self.use_insights:
            scopes.append("https://api.ebay.com/oauth/api_scope/buy.marketplace.insights")
        scope = " ".join(scopes)
        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        resp = requests.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": scope},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = time.time() + int(data.get("expires_in", 7200))
        return self._token

    def _headers(self) -> dict:
        cfg = LOCALE_CONFIG.get(LOCALE, LOCALE_CONFIG["AU"])
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "X-EBAY-C-MARKETPLACE-ID": cfg["marketplace_id"],
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------ search

    def find_comps(
        self,
        query: str,
        category_hint: Optional[str] = None,
        condition_hint: Optional[str] = None,
        limit: int = 25,
    ) -> CompResult:
        """Look up sold + active comps for a query string.

        category_hint: one of the keys in CATEGORY_IDS (e.g. "video_games")
        condition_hint: "NEW" | "USED" | None — narrows comps to similar condition
        """
        category_id = CATEGORY_IDS.get(category_hint) if category_hint else None
        result = CompResult(query=query)

        # --- sold listings (Marketplace Insights) -------------------------------
        if self.use_insights:
            try:
                sold = self._search(INSIGHTS_URL, query, category_id, condition_hint, limit)
                for item in sold:
                    price = _price(item)
                    if price:
                        result.sold_prices.append(price)
                        if len(result.sample_titles) < 5:
                            result.sample_titles.append(item.get("title", "")[:80])
                result.sold_count = len(result.sold_prices)
                result.source = "insights"
            except requests.HTTPError as e:
                log.warning("Marketplace Insights unavailable (%s); falling back to active", e)
                self.use_insights = False  # don't retry this session

        # --- active listings (Browse API) ---------------------------------------
        try:
            active = self._search(BROWSE_URL, query, category_id, condition_hint, limit)
            for item in active:
                price = _price(item)
                if price:
                    result.active_prices.append(price)
                    if not result.sample_titles and len(result.sample_titles) < 5:
                        result.sample_titles.append(item.get("title", "")[:80])
            result.active_count = len(result.active_prices)
            if not result.sold_prices:
                result.source = "active_fallback"
        except requests.HTTPError as e:
            log.error("Browse API failed: %s", e)

        return result

    def _search(
        self,
        url: str,
        query: str,
        category_id: Optional[str],
        condition_hint: Optional[str],
        limit: int,
    ) -> Iterable[dict]:
        params = {"q": query, "limit": str(min(limit, 200))}
        filters = []
        if category_id:
            params["category_ids"] = category_id
        if condition_hint:
            # eBay condition IDs: 1000=New, 3000=Used
            cond_id = "1000" if condition_hint.upper() == "NEW" else "3000"
            filters.append(f"conditionIds:{{{cond_id}}}")
        # Restrict to the same country as the locale so shipping costs and
        # condition norms match what you'd actually sell into.
        cfg = LOCALE_CONFIG.get(LOCALE, LOCALE_CONFIG["AU"])
        filters.append(f"itemLocationCountry:{cfg['country']}")
        if filters:
            params["filter"] = ",".join(filters)

        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Marketplace Insights returns "itemSales", Browse returns "itemSummaries"
        return data.get("itemSales") or data.get("itemSummaries") or []


def _price(item: dict) -> Optional[float]:
    """Pull a price out of an eBay item record in the locale's currency."""
    cfg = LOCALE_CONFIG.get(LOCALE, LOCALE_CONFIG["AU"])
    expected_currency = cfg["currency"]
    price = item.get("price") or item.get("lastSoldPrice")
    if not price:
        return None
    try:
        value = float(price.get("value", 0))
        currency = price.get("currency", expected_currency)
        if currency != expected_currency or value <= 0:
            return None
        return value
    except (TypeError, ValueError):
        return None
