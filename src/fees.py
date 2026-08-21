"""
eBay fee + profit math.

Default model (eBay standard, no store subscription, US managed payments):
  - Final Value Fee:       13.25% of (item price + shipping charged to buyer)
  - Per-order fee:         $0.30
  - Payment processing:    ~2.9% (bundled into FVF for managed payments, but we
                            keep it broken out so the model is easy to tweak)

These are aggressive defaults — actual FVF varies by category (some are 14.95%,
trading cards are 13.25% capped, etc). Edit FEE_RATES below if you sell mostly
in a category with a different rate, or pass a custom dict at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Per-category overrides for the final value fee. The default applies to anything
# not listed here. Source: https://www.ebay.com/help/selling/fees-credits-invoices/selling-fees
FEE_RATES = {
    "default":      0.1325,
    "video_games":  0.1325,
    "antiques":     0.1325,
    "collectibles": 0.1325,
    "electronics":  0.1325,
    "computers":    0.1325,
    "cell_phones":  0.1325,
    "cameras":      0.1325,
    "tools":        0.1325,
    # If you ever start selling sneakers/watches/clothing those have very
    # different rates — adjust here.
}

PER_ORDER_FEE = 0.30


@dataclass
class ProfitBreakdown:
    buy_price: float          # what you'd pay on Marketplace
    sell_price: float         # estimated eBay sale price (median of sold comps)
    shipping_cost: float      # what you pay to ship
    fvf_rate: float           # final value fee rate used
    fvf: float                # final value fee dollars
    per_order_fee: float
    total_fees: float
    net_revenue: float        # sell_price - total_fees - shipping_cost
    profit: float             # net_revenue - buy_price
    margin_pct: float         # profit / buy_price * 100

    def summary(self) -> str:
        return (
            f"Buy ${self.buy_price:.2f} → Sell ${self.sell_price:.2f}\n"
            f"  Fees:     ${self.total_fees:.2f}  "
            f"(FVF {self.fvf_rate*100:.2f}% = ${self.fvf:.2f}, "
            f"per-order ${self.per_order_fee:.2f})\n"
            f"  Shipping: ${self.shipping_cost:.2f}\n"
            f"  Net rev:  ${self.net_revenue:.2f}\n"
            f"  Profit:   ${self.profit:.2f}  ({self.margin_pct:+.1f}%)"
        )


def estimate_shipping(category_hint: Optional[str]) -> float:
    """Very rough USPS Ground Advantage / UPS estimates by category."""
    table = {
        "video_games":  6.00,   # small flat-rate box
        "antiques":    18.00,   # heavier / fragile
        "collectibles": 8.00,
        "electronics": 15.00,
        "computers":   25.00,
        "cell_phones":  6.00,
        "cameras":     12.00,
        "tools":       20.00,
    }
    return table.get(category_hint or "", 12.00)


def compute_profit(
    buy_price: float,
    sell_price: float,
    category_hint: Optional[str] = None,
    shipping_cost: Optional[float] = None,
    shipping_charged: float = 0.0,
    custom_fvf: Optional[float] = None,
) -> ProfitBreakdown:
    """Compute net profit on a flip.

    shipping_cost:    what YOU pay to ship to the buyer (deducted from your profit)
    shipping_charged: what the BUYER pays for shipping (added to FVF basis)
                      default 0 = free shipping (eats your margin but typical)
    """
    if shipping_cost is None:
        shipping_cost = estimate_shipping(category_hint)

    fvf_rate = custom_fvf if custom_fvf is not None else FEE_RATES.get(
        category_hint or "default", FEE_RATES["default"]
    )
    fvf = (sell_price + shipping_charged) * fvf_rate
    total_fees = fvf + PER_ORDER_FEE

    net_revenue = sell_price + shipping_charged - total_fees - shipping_cost
    profit = net_revenue - buy_price
    margin_pct = (profit / buy_price * 100) if buy_price > 0 else 0.0

    return ProfitBreakdown(
        buy_price=buy_price,
        sell_price=sell_price,
        shipping_cost=shipping_cost,
        fvf_rate=fvf_rate,
        fvf=round(fvf, 2),
        per_order_fee=PER_ORDER_FEE,
        total_fees=round(total_fees, 2),
        net_revenue=round(net_revenue, 2),
        profit=round(profit, 2),
        margin_pct=round(margin_pct, 2),
    )
