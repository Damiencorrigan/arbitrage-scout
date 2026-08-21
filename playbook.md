# Scout Playbook — AU FB Marketplace → eBay AU

Quick reference while scrolling Marketplace. Pull up on phone, scan, hunt.

---

## Tier 1 — Best signal-to-noise (start here)

### Power tools (especially "bare tool / skin only")
Sellers don't realise specific model numbers carry premium. A "drill" listed at A$80 can resell for A$220 if the model number's right.

- **DeWalt** 20V XR (DCD791, DCF887, DCH273, DCS367)
- **Milwaukee** M18 / M12 (M18FID2, M12FID20)
- **Makita** LXT 18V (DHP484, DTD171)
- **Festool** anything
- **Stihl** chainsaws (MS180, MS250, MS261)
- **Snap-On / Mac Tools** hand tools (always premium)

Bonus signal: kits with batteries + charger + bag undervalued vs sum of parts. "Skin only" = bare tool = often great margin if a buyer needs just the tool.

### Sealed video games & cards
Sealed factory shrink = collector premium.

- Nintendo (N64, GBA, GameCube, sealed Switch games)
- PlayStation 1 sealed titles
- Pokémon TCG sealed boxes/packs (any era)
- Magic: The Gathering older sets (Revised, Modern Horizons)

CIB ("complete in box") = decent but verify completeness in person.

### Apple gear that holds value
- AirPods Max
- AirPods Pro 2nd gen
- Apple Watch Ultra (1st or 2nd gen)
- M-series MacBooks within 2 generations
- iPad Pro M-series

**Skip current-gen iPhones.** Sellers price-check easily, margins are razor-thin.

---

## Tier 2 — Reliable but more work

### Kitchen
- **KitchenAid** mixers in vintage colours (turquoise, raspberry, pistachio = A$600+; white sells for ~A$300)
- **Dyson V11 / V15** vacuums with motorhead
- **Vitamix** blenders
- **Breville Barista Express** (BES870, not the cheaper Café Roma)

### Cameras & lenses
- Canon AE-1, Nikon FM2, Pentax K1000, Olympus OM-1/OM-2
- Prime lenses (50mm f/1.4 etc.) for any mount
- Sony A7 series accessories (grips, batteries, viewfinders)

Always check shutter count / lens fungus before buying.

### Outdoor gear with brand recognition
- Yeti Tundra coolers
- Weber kettle BBQs (limited colours especially)
- Stanley vintage lunchboxes
- Coleman lanterns/stoves (vintage)

---

## Tier 3 — High variance, big when they hit

### Estate sale / "cleaning out grandad's"
- Cast iron pans — Griswold or Wagner makers' marks (A$300+ for #8, looks identical to A$15 no-brand)
- Sterling silver flatware
- Vintage watches — Seiko 5, Citizen Bull Heads, vintage Omega Seamaster
- Vintage tools — Stanley hand planes (especially type 4-13), Disston saws with proper medallion

You need product knowledge here. Big upside, big risk of buying junk.

### Trading cards
- Pokémon — Charizard ANY era, holographics from Base/Jungle/Fossil
- Sports cards — NRL/AFL Select sets, Bradman cricket cards
- Vintage MTG — Revised, Alpha/Beta if you ever see them (you won't, but)

---

## Words and phrases that scream "underpriced"

> "Need to sell quick"
> "Moving overseas / interstate"
> "Cleaning out shed/garage"
> "Deceased estate"
> "Selling for a friend"
> "Was a gift, never used"
> "Don't really know what it's worth"

Seller-doesn't-care signal = where margins live.

---

## Words and phrases to be skeptical of

> "Rare!" · "Very limited" · "Worth $X" · "Valued at" · "Firm, no offers"
> 🔥🔥🔥
> Single grainy photo with no detail shots
> "Offers welcome" with a price already 50% above retail

Usually means the seller already googled and is anchoring high.

---

## Hard avoids

- **Current-gen iPhones / Galaxy flagships** — too easy to price-check, no margin
- **TVs** — shipping eats profit
- **Furniture** — local pickup only kills resale
- **Designer bags / watches without serial verification** — counterfeits everywhere
- **Cars, motorbikes, gym equipment** — too heavy / too cheap to ship
- **Perishables** — obvious
- **Anything you can't ship insured for under 10% of resale**

---

## The five-second test before you Scout an item

Ask yourself:

1. **Is the brand specific enough to comp on eBay?** ("DeWalt DCD791D2" ✓ · "cordless drill" ✗)
2. **Can I ship it for under 10% of resale price?** (A$300 item should ship for under A$30)
3. **Is the title underselling the item?** ("old Nintendo box" might hide a Pokémon set)
4. **Does the seller seem motivated?** (urgency words, generic phrasing, low photo count)
5. **Could the item be a fake / broken / missing parts?** (especially designer goods, electronics)

If 3+ are yes, copy the link, fire it through Scout, see what eBay AU says.

---

## Quick eBay AU search hacks

- Always check **"Sold listings"** filter when manually verifying — that's actual market clearing price, not asking price.
- Filter by **"Buy It Now"** + **"Completed listings"** to remove auction skew.
- Sort by **"Recently sold"** to see this month's prices, not historical highs.
- For sealed items, search both `"sealed [item]"` and `[item] NEW SEALED` — different sellers tag differently.

---

# BIG-TICKET MODE — A$500+ profit per flip

**Strategy shift:** stop chasing 50 small flips for A$30 each. Chase 2-3 big flips for A$500+ each. Different game, different categories.

**Capital reality:** A$500 net profit usually means buying in the A$1,500–A$5,000 range. Be ready to tie up A$2,000+ per item for 2-4 weeks while you find an eBay buyer.

**Scout config for this mode** (in `config.yaml`):

```yaml
min_margin_pct:       20.0      # was 30 — % margins compress on big-ticket
min_profit_dollars:   500.00    # was 15 — only alert on real money
```

---

## Tier 1 — Best for Sydney market

### Festool tools
Strong Sydney woodworking community. People upgrade and offload mid-tier kits constantly.

- **CSC SYS 50** track saw — RRP A$1500, used A$900-1100
- **Domino DF 500 / DF 700** biscuit joiners — A$1500-2500
- **OF 2200** routers — A$1800
- **TS 55 / TS 60** track saws with rails
- **MFT/3** multifunction tables

### Snap-On tool chests
Mechanics retire, divorce, or upgrade. They underprice because the resale market is opaque.

- **KRA series** (A$5k-10k new, A$3k-6k used)
- **KRL series** (A$10k-15k new, A$6k-9k used)
- Always check: latches, drawer slides, lock condition

### High-end bicycles
MAMILs (middle-aged men in lycra) in Sydney constantly upgrade. RRP $5k-15k, used $2.5k-7k.

- **Specialized S-Works** (Tarmac, Roubaix, Aethos)
- **Trek Madone, Émonda SLR**
- **Cervélo R5, S5**
- **Pinarello Dogma**

### eBikes
Rapidly growing market, sellers often don't realize resale value.

- **Specialized Turbo Levo, Kenevo, Vado**
- **Trek Rail, Fuel EXe**
- **Stealth Bomber** (Australian-made, premium)

### Hilti commercial gear
Tradies offloading. Commercial-grade so resale holds up.

- **TE / SDS chipping hammers** (A$1500-3000)
- **PR / PM laser levels** (A$1500-4000)
- Older Hilti tools still resell strong

---

## Tier 2 — Higher risk but bigger upside

### Pro cameras & big lenses
- **Sony A7R V, A1** (A$3-6k)
- **Canon R5, R6 Mark II** (A$3-5k)
- **Fujifilm GFX 50S/100S** (A$5-10k)
- Big telephoto: **Canon RF 100-500**, **Sony 200-600** (A$2-4k)
- Always verify: shutter count, lens for fungus/separation

### Vintage / pro musical gear
- **Gibson Les Paul Standard / Custom USA** (A$3-8k)
- **Fender American Original / Vintera** (A$2-4k)
- Vintage tube amps: **Marshall JCM800, Fender Twin Reverb, Vox AC30** (A$2-5k)
- Synths: **Moog Subsequent 37, Sequential Prophet** (A$3-5k)

### Sealed LEGO
- **UCS Millennium Falcon** (75192) — RRP A$1500, sealed A$3000+
- **Death Star** (75159) — RRP A$1500, sealed A$2500+
- **AT-AT** (75313), **Razor Crest**, **Tantive IV**
- Boxes must be unopened, no shelf wear

### High-end espresso machines
- **La Marzocco Linea Mini** (A$8k new, A$5k used)
- **Rocket Appartamento, R58, Mozzafiato** (A$2-5k)
- **ECM Synchronika** (A$5k new, A$3k used)
- **Lelit Bianca** (A$3k new, A$2k used)

---

## Tier 3 — Riskier, but huge if it hits

### Watches (high counterfeit risk — verify or skip)
Only buy with original papers + box + serial check. Counterfeits are everywhere.

- **Tudor Black Bay** (A$4-6k)
- **Omega Seamaster / Speedmaster** (A$5-10k)
- **Grand Seiko** (A$5-15k)
- Avoid **Rolex** unless you can authenticate via dealer

### Sealed graded trading cards
- Sealed **PSA-10 Pokemon** Charizard-era boxes (A$3-10k)
- Vintage **MTG** sealed packs (Revised, Alpha, Beta — you won't find these but if you do, jackpot)
- Sports cards: rare Bradman, full Select sets

---

## Sydney-specific search terms (paste one at a time)

```
Festool
Snap-on tool box
S-Works
Specialized Turbo Levo
Hilti laser
Trek Madone
Canon R5
Sony A7R
Gibson Les Paul
Fender American
La Marzocco
Rocket Appartamento
sealed LEGO UCS
PSA 10 Pokemon
```

Sort: **Newest first**, price A$1500-A$8000, within 50km Sydney.

---

## The big-ticket buyer's checklist

Before driving anywhere to inspect a A$2000+ item:

1. **Video call the seller.** Five minutes of FaceTime / WhatsApp video showing the serial number, model number, current condition, and the seller's face beats a five-hour wasted round trip.
2. **Get the model number / serial in writing** before you commit to inspect. If they refuse, walk away.
3. **Look up the eBay AU sold-comp median yourself** — don't trust just Scout. Scout's estimate is a starting point. Cross-reference 5+ recently sold listings.
4. **Decide your walk-away price before you go.** Sellers will price-anchor on the listed price. Have your max in your head.
5. **Bring cash, not bank transfer.** Cash gives you negotiation leverage on the day ("here's A$X right now") and protects you from scam transfer reversals.
6. **Inspect in daylight on neutral ground if possible.** A coffee shop carpark beats a sketchy garage at night.

---

## Hard avoids in big-ticket mode

- **Items that can't ship** (large furniture, gym equipment, BBQs) — local-only on eBay kills your buyer pool
- **Anything requiring registration** (cars, motorbikes, jet skis, trailers) — transfer paperwork is its own minefield
- **Items needing repair/restoration** unless you have the skills — "needs minor work" usually means major work
- **Anything where the seller asks for a holding deposit before inspection** — almost always a scam
- **Items pictured only as stock photos** — seller probably doesn't have it
