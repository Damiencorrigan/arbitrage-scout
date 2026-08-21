"""
Main arbitrage engine — ties the parser, eBay client, fee calc, and alerter
together. Two entry modes:

  python -m src.engine analyze        # read one listing from stdin, print result
  python -m src.engine watch queue.txt # process every listing in a queue file

A queue file is a plain text file with listings separated by lines of '---'.
Each listing block is what you'd paste into 'analyze'.

Config: see config.yaml in the project root.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import sys
from dataclasses import asdict
from typing import Optional

import yaml

from .alert import send_alert
from .ebay_client import EbayClient
from .fees import compute_profit
from .listing import Listing, parse_pasted

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "min_margin_pct": 30.0,        # alert threshold
    "min_profit_dollars": 15.00,   # also require absolute floor — 30% of $10 isn't worth driving for
    "shipping_charged_to_buyer": 0.0,
    "alert_email_enabled": True,
    "log_path": "data/scouted.jsonl",
}


def load_config(path: Optional[str] = None) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    path = path or os.environ.get("SCOUT_CONFIG", "config.yaml")
    if pathlib.Path(path).exists():
        with open(path) as f:
            cfg.update(yaml.safe_load(f) or {})
    return cfg


def analyze_one(listing: Listing, client: EbayClient, cfg: dict) -> dict:
    """Look up comps, compute profit, optionally alert. Returns a result dict."""
    cat = listing.classify()
    query = listing.search_query()
    log.info("Analyzing: %r  (category=%s, asking=$%.2f)",
             query, cat, listing.price)

    comps = client.find_comps(
        query=query,
        category_hint=cat,
        condition_hint=listing.condition,
    )

    estimate = comps.best_estimate
    if estimate is None or listing.price <= 0:
        result = {
            "listing": asdict(listing),
            "decision": "skip",
            "reason": "no comps found" if estimate is None else "no asking price",
            "comp_count": comps.sold_count + comps.active_count,
        }
        _log_result(result, cfg)
        return result

    breakdown = compute_profit(
        buy_price=listing.price,
        sell_price=estimate,
        category_hint=cat,
        shipping_charged=cfg["shipping_charged_to_buyer"],
    )

    is_deal = (
        breakdown.margin_pct >= cfg["min_margin_pct"]
        and breakdown.profit >= cfg["min_profit_dollars"]
    )

    result = {
        "listing": asdict(listing),
        "comp_source": comps.source,
        "comp_count": comps.sold_count if comps.sold_prices else comps.active_count,
        "median_sold": comps.median_sold,
        "median_active": comps.median_active,
        "estimated_sell_price": estimate,
        "breakdown": asdict(breakdown),
        "decision": "alert" if is_deal else "skip",
    }

    if is_deal and cfg.get("alert_email_enabled", True):
        try:
            send_alert(
                listing=listing,
                breakdown=breakdown,
                comp_count=result["comp_count"],
                comp_source=comps.source,
            )
            result["alert_sent"] = True
        except Exception as e:
            log.exception("Failed to send alert: %s", e)
            result["alert_sent"] = False
            result["alert_error"] = str(e)

    _log_result(result, cfg)
    return result


def _log_result(result: dict, cfg: dict) -> None:
    path = pathlib.Path(cfg["log_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(result, default=str) + "\n")


# ----------------------------------------------------------------------- CLI

def _read_stdin() -> str:
    return sys.stdin.read()


def _split_queue(text: str) -> list[str]:
    blocks, current = [], []
    for line in text.splitlines():
        if line.strip() == "---":
            if current:
                blocks.append("\n".join(current).strip())
                current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return [b for b in blocks if b]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="scout")
    parser.add_argument("--config", help="path to config.yaml")
    parser.add_argument("--no-alert", action="store_true",
                        help="dry-run: do all the analysis, never send email")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("analyze", help="analyze one listing read from stdin")
    watch = sub.add_parser("watch", help="process every listing in a queue file")
    watch.add_argument("queue_file")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    cfg = load_config(args.config)
    if args.no_alert:
        cfg["alert_email_enabled"] = False

    client = EbayClient()

    if args.cmd == "analyze":
        listing = parse_pasted(_read_stdin())
        result = analyze_one(listing, client, cfg)
        print(json.dumps(result, indent=2, default=str))
        return 0

    if args.cmd == "watch":
        with open(args.queue_file) as f:
            text = f.read()
        for block in _split_queue(text):
            listing = parse_pasted(block)
            result = analyze_one(listing, client, cfg)
            margin = result.get("breakdown", {}).get("margin_pct", "—")
            print(f"[{result['decision'].upper():5}] {margin}% — {listing.title[:60]}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
