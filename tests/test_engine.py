"""End-to-end engine test with a mocked eBay client + no real email."""
import json
import os
import pathlib
import tempfile
from unittest.mock import MagicMock

from src.engine import analyze_one
from src.ebay_client import CompResult
from src.listing import parse_pasted


def make_mock_client(sold_prices):
    client = MagicMock()
    client.find_comps.return_value = CompResult(
        query="x",
        sold_count=len(sold_prices),
        sold_prices=list(sold_prices),
        source="insights",
        sample_titles=["mocked"],
    )
    return client


def test_engine_flags_a_deal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {
        "min_margin_pct": 30.0,
        "min_profit_dollars": 15.0,
        "shipping_charged_to_buyer": 0.0,
        "alert_email_enabled": False,   # don't actually email
        "log_path": str(tmp_path / "scouted.jsonl"),
    }
    listing = parse_pasted(
        "Sealed Nintendo 64 with 4 games\n$120 in Boston, MA"
    )
    # Mock eBay says comparable lots are selling for ~$220 median
    client = make_mock_client([200, 215, 220, 230, 245])
    result = analyze_one(listing, client, cfg)
    assert result["decision"] == "alert", result
    # 220 - (220*0.1325 + 0.30) - 6 = 220 - 29.45 - 6 = 184.55; profit = 64.55
    assert result["breakdown"]["profit"] > 60
    assert result["breakdown"]["margin_pct"] >= 30


def test_engine_skips_non_deal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {
        "min_margin_pct": 30.0,
        "min_profit_dollars": 15.0,
        "shipping_charged_to_buyer": 0.0,
        "alert_email_enabled": False,
        "log_path": str(tmp_path / "scouted.jsonl"),
    }
    listing = parse_pasted(
        "iPhone 13 in Cambridge, MA\n$400"
    )
    # Mock: comps are only ~$420 — fees eat the margin
    client = make_mock_client([400, 410, 420, 425, 430])
    result = analyze_one(listing, client, cfg)
    assert result["decision"] == "skip", result


def test_engine_skips_when_no_comps(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {
        "min_margin_pct": 30.0,
        "min_profit_dollars": 15.0,
        "shipping_charged_to_buyer": 0.0,
        "alert_email_enabled": False,
        "log_path": str(tmp_path / "scouted.jsonl"),
    }
    listing = parse_pasted("Something obscure\n$10 in Boston, MA")
    client = make_mock_client([])
    result = analyze_one(listing, client, cfg)
    assert result["decision"] == "skip"
    assert "no comps" in result["reason"]


def test_engine_appends_to_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_path = tmp_path / "scouted.jsonl"
    cfg = {
        "min_margin_pct": 30.0,
        "min_profit_dollars": 15.0,
        "shipping_charged_to_buyer": 0.0,
        "alert_email_enabled": False,
        "log_path": str(log_path),
    }
    listing = parse_pasted("Nintendo Switch\n$120 in Boston, MA")
    client = make_mock_client([220, 230, 240])
    analyze_one(listing, client, cfg)
    assert log_path.exists()
    record = json.loads(log_path.read_text().strip().splitlines()[0])
    assert record["decision"] == "alert"
