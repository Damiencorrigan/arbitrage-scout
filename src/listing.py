"""
Parsing/normalising a Facebook Marketplace listing.

Per the design conversation, we DON'T scrape Facebook directly. The user supplies
the listing — either by pasting the URL (and a copy of the title + price), or by
filling a small structured form. This module:

  1. Holds the Listing dataclass
  2. Parses pasted Marketplace blobs into Listing objects (best-effort regex on
     the typical mobile-share format)
  3. Auto-classifies the listing into one of our category hints, which feeds
     the eBay comp search and the fee model
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Keywords -> our internal category_hint. First match wins.
CATEGORY_KEYWORDS = [
    ("video_games", [
        "nintendo", "playstation", "ps1", "ps2", "ps3", "ps4", "ps5", "xbox",
        "gamecube", "switch", "snes", "sega", "atari", "n64", "gameboy",
        "gba", "ds lite", "3ds", "wii", "game ", " game", "cartridge", "cib",
        "video game",
    ]),
    ("antiques", [
        "antique", "vintage", "victorian", "art deco", "mid-century",
        "mid century", "primitive", "estate", "depression glass",
    ]),
    ("collectibles", [
        "collectible", "funko", "pop figure", "trading card", "pokemon card",
        "magic the gathering", "mtg", "comic book", "vinyl", "lp record",
        "coin", "stamp",
    ]),
    ("cell_phones", [
        "iphone", "samsung galaxy", "pixel", "android phone", "smartphone",
        "unlocked phone",
    ]),
    ("cameras", [
        "canon", "nikon", "sony alpha", "sony a7", "sony a6", "leica",
        "fujifilm", "mirrorless", "dslr", "camera lens", "vintage camera",
        " camera", "camera ",   # plain "camera" with whitespace boundary
    ]),
    ("computers", [
        "macbook", "imac", "thinkpad", "laptop", "desktop pc", "gaming pc",
        "monitor", "graphics card", "rtx", "gpu",
    ]),
    ("electronics", [
        "tv", "soundbar", "speaker", "headphone", "airpods", "kindle",
        "ipad", "tablet", "drone", "amplifier", "receiver",
    ]),
    ("tools", [
        "dewalt", "milwaukee", "makita", "snap-on", "snap on", "ridgid",
        "table saw", "drill", "impact driver", "tool set", "tool box",
        "wrench set",
    ]),
]


@dataclass
class Listing:
    title: str
    price: float
    url: Optional[str] = None
    description: str = ""
    condition: Optional[str] = None      # "NEW" / "USED" / None
    location: Optional[str] = None
    photo_url: Optional[str] = None
    category_hint: Optional[str] = None
    raw: str = ""

    def classify(self) -> str:
        """Pick a category_hint from the title + description, set + return it."""
        if self.category_hint:
            return self.category_hint
        haystack = f"{self.title} {self.description}".lower()
        for cat, keywords in CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw in haystack:
                    self.category_hint = cat
                    return cat
        self.category_hint = "default"
        return "default"

    def search_query(self) -> str:
        """A cleaned-up version of the title suitable for an eBay search."""
        # Strip common Marketplace noise
        q = re.sub(r"\bfor sale\b|\bobo\b|\bfirm\b|\bno trades\b",
                   "", self.title, flags=re.I)
        q = re.sub(r"\s+", " ", q).strip()
        return q


# ---------------------------------------------------------------------- parsers

# Accepts $220, A$220, AU$220, US$220, AUD 220, $220.00, $1,500, $1850, $15000
# The comma-formatted alternative requires a comma group; un-comma'd numbers
# fall through to the plain-digits alternative so values like 1850 stay intact.
_PRICE_RE = re.compile(
    r"(?:A\$|AU\$|US\$|AUD\s*|USD\s*|\$)\s*"
    r"([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{2})?|[0-9]+(?:\.[0-9]{2})?)",
    re.I,
)
# Match both formats Facebook hands out:
#   facebook.com/marketplace/item/1234567890     (when copied from desktop)
#   facebook.com/share/abcDEFxyz                 (when copied from the iOS Share Sheet)
_FBMP_URL_RE = re.compile(
    r"https?://(?:www\.|m\.)?facebook\.com/(?:marketplace/item/\d+|share/[A-Za-z0-9]+)"
)


def parse_pasted(text: str) -> Listing:
    """Best-effort parser for whatever the user pastes from Marketplace.

    Handles:
      - Mobile share format: "TITLE\\n$PRICE · Listed N days ago in CITY, STATE"
      - URL on its own line + freeform text the user typed
      - Bullet-list paste with "Condition: Used" etc.
    """
    text = text.strip()
    url_match = _FBMP_URL_RE.search(text)
    url = url_match.group(0) if url_match else None

    # First non-empty, non-URL line is usually the title
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = next(
        (l for l in lines if not l.startswith("http") and "$" not in l),
        lines[0] if lines else "",
    )

    price_match = _PRICE_RE.search(text)
    price = float(price_match.group(1).replace(",", "")) if price_match else 0.0

    # Check USED patterns first — they're more specific than NEW keywords
    # like "sealed", which often appears in titles of used-condition listings.
    cond = None
    if re.search(
        r"\b(used|pre[- ]?owned|good condition|fair condition|"
        r"like new|condition:\s*used)\b",
        text, re.I,
    ):
        cond = "USED"
    elif (
        re.search(
            r"\b(brand new|new in box|nib|sealed|unopened|condition:\s*new)\b",
            text, re.I,
        )
        # FB Marketplace also displays the condition as a standalone label like
        # "New" or "New, in stock". Capital-N "New" as a word counts as NEW.
        or re.search(r"(?:^|[·:|]\s*)New\b", text, re.M)
        or re.search(r"\bNew(?=,|\s+in\s+stock\b)", text)
    ):
        cond = "NEW"

    # Match "Sydney, NSW" / "Boston, MA" / "Port Augusta, SA" — a capitalized
    # city of 1–3 capitalized words, comma, then a 2–4 letter state code.
    # Restricting each word to [A-Z][a-z]+ prevents the greedy old regex from
    # swallowing prefixes like "Listed in Sydney" or "Brand new Sydney".
    loc_match = re.search(
        r"(?<![A-Za-z])"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"   # 1–3 capitalized words
        r",\s*([A-Z]{2,4})\b",                     # , STATE
        text,
    )
    location = f"{loc_match.group(1)}, {loc_match.group(2)}" if loc_match else None

    listing = Listing(
        title=title,
        price=price,
        url=url,
        description=text,
        condition=cond,
        location=location,
        raw=text,
    )
    listing.classify()
    return listing
