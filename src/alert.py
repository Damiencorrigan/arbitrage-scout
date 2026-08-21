"""
Email alerter — sends a deal notification via SMTP.

Tested against Yahoo Mail (smtp.mail.yahoo.com:465). For Yahoo you need an
"app password" (not your regular login password). Generate one at:
  https://login.yahoo.com/account/security  →  "Generate app password"

Set these env vars:
  SMTP_HOST       e.g. smtp.mail.yahoo.com
  SMTP_PORT       e.g. 465
  SMTP_USER       your full email address
  SMTP_APP_PASS   the 16-char app password
  ALERT_TO        where alerts go (defaults to SMTP_USER)
"""

from __future__ import annotations

import html
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from .fees import ProfitBreakdown
from .listing import Listing

log = logging.getLogger(__name__)


def render_html(listing: Listing, breakdown: ProfitBreakdown,
                comp_count: int, comp_source: str) -> str:
    esc = html.escape
    title = esc(listing.title)
    loc = esc(listing.location or "—")
    cond = esc(listing.condition or "Not specified")
    url = listing.url or "#"
    return f"""
    <html><body style="font-family: -apple-system, Segoe UI, sans-serif;">
      <h2 style="margin-bottom:4px;">💰 Deal alert: {breakdown.margin_pct:+.0f}% margin</h2>
      <p style="color:#555;margin-top:0;">Estimated profit: <b>${breakdown.profit:.2f}</b></p>

      <h3>{title}</h3>
      <ul>
        <li><b>Asking price:</b> ${breakdown.buy_price:.2f}</li>
        <li><b>Condition:</b> {cond}</li>
        <li><b>Location:</b> {loc}</li>
        <li><b>FB Marketplace:</b> <a href="{esc(url)}">{esc(url)}</a></li>
      </ul>

      <h3>eBay comp analysis</h3>
      <ul>
        <li><b>Estimated sale price:</b> ${breakdown.sell_price:.2f}
            (median of {comp_count} {esc(comp_source)} listings)</li>
        <li><b>eBay fees:</b> ${breakdown.total_fees:.2f}
            (FVF {breakdown.fvf_rate*100:.2f}% + $0.30/order)</li>
        <li><b>Shipping cost:</b> ${breakdown.shipping_cost:.2f}</li>
        <li><b>Net revenue:</b> ${breakdown.net_revenue:.2f}</li>
      </ul>

      <p style="color:#888;font-size:12px;">
        Reply STOP to stop alerts. This is an estimate — verify the comps match
        the exact item / condition before buying.
      </p>
    </body></html>
    """


def send_alert(listing: Listing, breakdown: ProfitBreakdown,
               comp_count: int, comp_source: str,
               to_addr: Optional[str] = None) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    pw   = os.environ["SMTP_APP_PASS"]
    to   = to_addr or os.environ.get("ALERT_TO") or user

    msg = EmailMessage()
    msg["Subject"] = f"[Scout] {breakdown.margin_pct:+.0f}% profit — {listing.title[:60]}"
    msg["From"] = user
    msg["To"] = to

    plain = (
        f"{listing.title}\n"
        f"{breakdown.summary()}\n\n"
        f"Link: {listing.url or '(no URL)'}\n"
        f"Based on {comp_count} {comp_source} listings.\n"
    )
    msg.set_content(plain)
    msg.add_alternative(render_html(listing, breakdown, comp_count, comp_source),
                        subtype="html")

    ctx = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
            s.login(user, pw)
            s.send_message(msg)
    else:  # 587 / STARTTLS
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls(context=ctx)
            s.login(user, pw)
            s.send_message(msg)

    log.info("Alert sent to %s", to)
