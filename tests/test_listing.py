"""Verify pasted-Marketplace blob parsing + category classifier."""
from src.listing import parse_pasted


def test_parse_video_game_listing():
    text = """Sealed Nintendo 64 with 4 games and 2 controllers
$120 · Listed 2 hours ago in Boston, MA
Used - good condition.
https://www.facebook.com/marketplace/item/1234567890"""
    l = parse_pasted(text)
    assert "Nintendo 64" in l.title
    assert l.price == 120.0
    assert l.url and "1234567890" in l.url
    assert l.condition == "USED"
    assert l.location == "Boston, MA"
    assert l.category_hint == "video_games"


def test_parse_dewalt_tool_listing():
    text = """DeWalt 20V Max XR Brushless Drill Kit
$75 · Cambridge, MA
Brand new in box."""
    l = parse_pasted(text)
    assert l.price == 75.0
    assert l.condition == "NEW"
    assert l.category_hint == "tools"


def test_parse_antique_listing():
    text = """Antique cast iron Singer sewing machine
$30 in Quincy, MA
Vintage decor piece."""
    l = parse_pasted(text)
    assert l.price == 30.0
    assert l.category_hint == "antiques"


def test_search_query_strips_noise():
    text = """Nintendo Switch for sale OBO firm no trades
$200"""
    l = parse_pasted(text)
    q = l.search_query()
    assert "obo" not in q.lower()
    assert "firm" not in q.lower()
    assert "Nintendo Switch" in q


def test_unknown_category_falls_to_default():
    text = """Random thingamajig
$50 in Nowhere, ZZ"""
    l = parse_pasted(text)
    assert l.category_hint == "default"
