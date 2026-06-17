"""ui/theme.py — Munich-Re-inspired design system for the advisor UI.

A single source of brand tokens + a CSS injector that re-skins Streamlit into an
institutional, airy, navy+turquoise surface. Approximation of the Munich Re look
(deep navy, turquoise accent, generous whitespace, clean humanist sans, flat
components) — repin PALETTE / FONT_STACK to exact brand tokens when available.

Offline-first (CLAUDE.md principle 1): NO runtime web-font fetch. We use a
high-quality *system* font stack (San Francisco / Segoe / Helvetica Neue), so the
UI styles fully with zero network calls. To use the exact custom font, bundle a
.woff2 in the repo and @font-face it here — still offline.
"""

from __future__ import annotations

import streamlit as st

from app.models import Verdict

# ── brand tokens (Munich-Re-inspired — confirm exact hex when available) ───────
PALETTE = {
    "navy": "#0A2240",  # header band, primary buttons, headings
    "blue": "#005AA0",  # links, secondary accents
    "turquoise": "#00B2A9",  # the brand "spark" — citation rules, focus
    "canvas": "#FFFFFF",
    "section": "#F4F6F8",  # alternating band / cards
    "slate": "#1A2329",  # body text
    "muted": "#5B6770",  # captions
    "hairline": "#E1E5EA",
    "delivered": "#1E7D52",  # DELIVERED verdict (calm green, not lime)
    "delivered_bg": "#E8F3ED",
    "routed": "#B26B00",  # ROUTED verdict (serious amber, not alarm-red)
    "routed_bg": "#FBF1E0",
}

# Offline system stack that reads as a clean humanist sans (Inter-adjacent).
FONT_STACK = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", '
    "Helvetica, Arial, sans-serif"
)


def inject_css() -> None:
    """Inject the brand stylesheet + hide default Streamlit chrome."""
    p = PALETTE
    st.markdown(
        f"""
        <style>
          /* hide default Streamlit chrome for a product feel */
          #MainMenu {{visibility: hidden;}}
          footer {{visibility: hidden;}}
          header[data-testid="stHeader"] {{display: none;}}
          .stDeployButton {{display: none;}}

          html, body, [class*="css"], .stMarkdown, p, span, div, label, input, button {{
            font-family: {FONT_STACK};
            color: {p["slate"]};
          }}
          .block-container {{padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1080px;}}

          h1, h2, h3, h4 {{ color: {p["navy"]}; font-weight: 600; letter-spacing: -0.01em; }}
          h1 {{ font-weight: 300; font-size: 2.4rem; }}

          a, a:visited {{ color: {p["blue"]}; }}

          /* ── navy header band ───────────────────────────────────────────── */
          .nw-header {{
            background: {p["navy"]}; color: #fff; border-radius: 6px;
            padding: 14px 22px; margin-bottom: 6px;
            display: flex; align-items: center; justify-content: space-between;
          }}
          .nw-brand {{ font-weight: 600; letter-spacing: .14em; font-size: .82rem; color:#fff; }}
          .nw-brand .spark {{ color: {p["turquoise"]}; }}
          .nw-id {{ font-size: .82rem; color: #C7D2DE; }}
          .nw-id b {{ color: #fff; font-weight: 600; }}

          /* ── hero ───────────────────────────────────────────────────────── */
          .nw-hero-sub {{ color: {p["muted"]}; font-size: 1.02rem; margin-top: -.4rem; }}

          /* ── welcome card ───────────────────────────────────────────────── */
          .nw-welcome {{
            border: 1px solid {p["hairline"]}; border-top: 4px solid {p["turquoise"]};
            border-radius: 8px; padding: 30px 34px; background: {p["canvas"]};
            box-shadow: 0 2px 10px #0a224012; margin: 14px 0 18px 0;
          }}
          .nw-welcome h2 {{ margin-top: 0; font-weight: 300; font-size: 1.9rem; }}
          .nw-welcome p {{ color: {p["slate"]}; font-size: 1.04rem; line-height: 1.6; }}
          .nw-welcome .lead {{ color: {p["muted"]}; }}
          .nw-welcome ul {{ color: {p["slate"]}; line-height: 1.7; }}
          .nw-welcome b {{ color: {p["navy"]}; }}

          /* ── verdict banners ────────────────────────────────────────────── */
          .nw-verdict {{
            border-radius: 6px; padding: 14px 18px; margin: 6px 0 4px 0;
            font-weight: 600; font-size: 1.05rem; display: flex; gap: 10px; align-items: center;
          }}
          .nw-delivered {{ background: {p["delivered_bg"]}; color: {p["delivered"]};
                           border: 1px solid {p["delivered"]}33; }}
          .nw-routed {{ background: {p["routed_bg"]}; color: {p["routed"]};
                        border: 1px solid {p["routed"]}33; }}

          /* ── quote stat card ────────────────────────────────────────────── */
          .nw-quote {{
            border: 1px solid {p["hairline"]}; border-left: 4px solid {p["turquoise"]};
            border-radius: 6px; padding: 16px 20px; background: {p["canvas"]};
            display: flex; align-items: baseline; gap: 18px; box-shadow: 0 1px 3px #0a224010;
          }}
          .nw-quote .px {{ font-size: 2.0rem; font-weight: 700; color: {p["navy"]}; }}
          .nw-quote .chg-up {{ color: {p["delivered"]}; font-weight: 600; }}
          .nw-quote .chg-dn {{ color: #B22222; font-weight: 600; }}
          .nw-quote .nm {{ color: {p["slate"]}; font-weight: 600; }}
          .nw-quote .asof {{ color: {p["muted"]}; font-size: .82rem; }}

          /* ── citation expanders → turquoise left rule ───────────────────── */
          [data-testid="stExpander"] {{
            border: 1px solid {p["hairline"]}; border-left: 3px solid {p["turquoise"]};
            border-radius: 6px; margin-bottom: 8px;
          }}

          /* ── buttons: flat navy, WHITE label (override the global dark text) ─ */
          .stButton > button {{
            background: {p["navy"]} !important; border: 0; border-radius: 4px;
            font-weight: 600; padding: .5rem 1.1rem;
          }}
          /* the label text lives in inner <p>/<span>/<div> — force them white too */
          .stButton > button, .stButton > button * {{ color: #ffffff !important; fill: #ffffff !important; }}
          .stButton > button:hover {{ background: {p["blue"]} !important; }}
          .stButton > button:hover, .stButton > button:hover * {{ color: #ffffff !important; }}

          /* ⚙ gear buttons (open "Show my work"): big, spinning, icon-only, ghost */
          @keyframes nw-gear-spin {{ to {{ transform: rotate(360deg); }} }}
          .st-key-to_operator button, .st-key-audit_gear button {{
            background: transparent !important; border: 1px solid {p["hairline"]} !important;
            font-size: 2.7rem !important; line-height: 1; padding: 0 .45rem !important;
            border-radius: 12px;
          }}
          .st-key-to_operator button:hover, .st-key-audit_gear button:hover {{
            background: {p["section"]} !important;
          }}
          .st-key-to_operator button p, .st-key-audit_gear button p {{
            color: {p["navy"]} !important;
            display: inline-block;
            animation: nw-gear-spin 4s linear infinite;
          }}
          /* spin faster on hover */
          .st-key-to_operator button:hover p, .st-key-audit_gear button:hover p {{
            animation-duration: 1s;
          }}

          /* section divider */
          hr {{ border-color: {p["hairline"]}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header_band(identity: str) -> None:
    """The navy top bar: wordmark left, advisor identity right."""
    st.markdown(
        f"""
        <div class="nw-header">
          <span class="nw-brand">NORTHWIND&nbsp;SECURITIES <span class="spark">·</span> RESEARCH</span>
          <span class="nw-id">{identity}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def verdict_banner(status: Verdict) -> None:
    if status == Verdict.DELIVERED:
        st.markdown(
            '<div class="nw-verdict nw-delivered">✓&nbsp; DELIVERED</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="nw-verdict nw-routed">⤴&nbsp; ROUTED FOR HUMAN REVIEW</div>',
            unsafe_allow_html=True,
        )


def quote_card_html(
    symbol: str,
    name: str,
    exchange: str,
    last: float,
    change_pct: float | None,
    asof_label: str,
) -> str:
    chg = ""
    if change_pct is not None:
        cls = "chg-up" if change_pct >= 0 else "chg-dn"
        arrow = "▲" if change_pct >= 0 else "▼"
        chg = f'<span class="{cls}">{arrow} {change_pct:+.2f}%</span>'
    return f"""
    <div class="nw-quote">
      <span class="px">${last:,.2f}</span>
      {chg}
      <span style="flex:1">
        <span class="nm">{symbol}</span> · {name} · {exchange}<br>
        <span class="asof">🕒 {asof_label}</span>
      </span>
    </div>
    """
