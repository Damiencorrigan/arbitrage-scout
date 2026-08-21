"""Verify the eBay fee math against hand-computed scenarios."""
import math
from src.fees import compute_profit, FEE_RATES, PER_ORDER_FEE


def test_basic_video_game_flip():
    # Buy a sealed game for $40 on Marketplace, sell for $100 on eBay.
    # Free shipping (buyer pays $0), we pay $6 USPS, video_games FVF 13.25%.
    b = compute_profit(buy_price=40, sell_price=100, category_hint="video_games")
    expected_fvf = 100 * 0.1325                       # = 13.25
    expected_total_fees = expected_fvf + PER_ORDER_FEE  # = 13.55
    expected_shipping = 6.00                           # video_games default
    expected_net = 100 - expected_total_fees - expected_shipping  # 80.45
    expected_profit = expected_net - 40               # 40.45

    assert math.isclose(b.fvf, round(expected_fvf, 2))
    assert math.isclose(b.total_fees, round(expected_total_fees, 2))
    assert math.isclose(b.shipping_cost, expected_shipping)
    assert math.isclose(b.net_revenue, round(expected_net, 2))
    assert math.isclose(b.profit, round(expected_profit, 2))
    # Margin = profit / buy_price = 40.45 / 40 ≈ 101%
    assert 100 < b.margin_pct < 102


def test_break_even_is_not_a_deal():
    # Buy $50, sell $60 — fees + shipping wipe out the margin.
    b = compute_profit(buy_price=50, sell_price=60, category_hint="electronics")
    # 60 * 0.1325 = 7.95 + 0.30 + 15 shipping = 23.25 in costs
    # net = 60 - 23.25 = 36.75, profit = -13.25
    assert b.profit < 0


def test_buyer_paid_shipping_increases_fvf_but_offsets_cost():
    # Buyer covers shipping: charged 6, FVF charged on full 106
    b = compute_profit(
        buy_price=40, sell_price=100,
        category_hint="video_games",
        shipping_charged=6.00,
    )
    expected_fvf = 106 * 0.1325  # 14.045
    assert math.isclose(b.fvf, round(expected_fvf, 2))
    # The buyer's $6 cancels our $6 shipping cost, so we keep more profit
    # vs the test_basic_video_game_flip baseline.
    baseline = compute_profit(40, 100, "video_games")
    assert b.profit > baseline.profit


def test_custom_fvf_override():
    b = compute_profit(buy_price=10, sell_price=100, custom_fvf=0.15)
    assert math.isclose(b.fvf, 15.0)


def test_all_categories_have_a_rate():
    # Make sure we haven't left any category without a fee rate
    for cat in ["video_games", "antiques", "collectibles",
                "electronics", "computers", "cell_phones",
                "cameras", "tools", "default"]:
        assert cat in FEE_RATES
