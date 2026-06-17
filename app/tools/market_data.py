"""app/tools/market_data.py — the stock-briefing quote source (T4b).

A thin, swappable market-data tool. Two backends behind one interface:

  • OFFLINE FIXTURE (default, keyless) — reads data/market/quotes.json. Deterministic,
    runs with zero keys/network (CLAUDE.md principle 1). This is what the demo and the
    tests use.
  • LIVE ADAPTER (opt-in, key-gated) — a quote pull from a provider behind
    `market_data_provider` (both US-domiciled, clean provenance per principle 3):
      - `alpha_vantage` — GLOBAL_QUOTE, **delayed end-of-day** close (free tier;
        intraday is premium).
      - `finnhub` — /quote, **real-time** US quotes (free tier, 60/min).
    Activated ONLY when `use_real_market_data` is true AND a key is present. Any live
    failure (no network, rate-limit, parse error) falls back to the fixture. Quotes are
    informational and NEVER execution-grade — the `no_realtime_quote` guardrail still
    applies (a trade-now / execution-price ask routes to a human regardless of source).

REPEATABLE BY DESIGN: nothing here is Microsoft-specific. The tool is ticker-agnostic
— `MSFT` is the worked *live* example, `MRB` the worked *offline/synthetic* example,
and any US ticker flows the same path. No pip dependency (stdlib `urllib`).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.models import Quote

# Convenience name/exchange enrichment (the GLOBAL_QUOTE endpoint omits these).
# Optional — any unknown symbol still resolves, just without the friendly name.
# Curated top-50 US large-caps (exchange labeled correctly — NASDAQ vs NYSE).
SYMBOL_META: dict[str, tuple[str, str]] = {
    # NASDAQ
    "AAPL": ("Apple Inc.", "NASDAQ"),
    "MSFT": ("Microsoft Corporation", "NASDAQ"),
    "NVDA": ("NVIDIA Corporation", "NASDAQ"),
    "AMZN": ("Amazon.com, Inc.", "NASDAQ"),
    "GOOGL": ("Alphabet Inc.", "NASDAQ"),
    "META": ("Meta Platforms, Inc.", "NASDAQ"),
    "TSLA": ("Tesla, Inc.", "NASDAQ"),
    "AVGO": ("Broadcom Inc.", "NASDAQ"),
    "COST": ("Costco Wholesale Corporation", "NASDAQ"),
    "NFLX": ("Netflix, Inc.", "NASDAQ"),
    "AMD": ("Advanced Micro Devices, Inc.", "NASDAQ"),
    "ADBE": ("Adobe Inc.", "NASDAQ"),
    "CSCO": ("Cisco Systems, Inc.", "NASDAQ"),
    "INTC": ("Intel Corporation", "NASDAQ"),
    "QCOM": ("QUALCOMM Incorporated", "NASDAQ"),
    "TXN": ("Texas Instruments Incorporated", "NASDAQ"),
    "AMGN": ("Amgen Inc.", "NASDAQ"),
    "PEP": ("PepsiCo, Inc.", "NASDAQ"),
    "CMCSA": ("Comcast Corporation", "NASDAQ"),
    "INTU": ("Intuit Inc.", "NASDAQ"),
    "HON": ("Honeywell International Inc.", "NASDAQ"),
    "AMAT": ("Applied Materials, Inc.", "NASDAQ"),
    # NYSE
    "JPM": ("JPMorgan Chase & Co.", "NYSE"),
    "V": ("Visa Inc.", "NYSE"),
    "WMT": ("Walmart Inc.", "NYSE"),
    "UNH": ("UnitedHealth Group Incorporated", "NYSE"),
    "XOM": ("Exxon Mobil Corporation", "NYSE"),
    "MA": ("Mastercard Incorporated", "NYSE"),
    "ORCL": ("Oracle Corporation", "NYSE"),
    "HD": ("The Home Depot, Inc.", "NYSE"),
    "PG": ("The Procter & Gamble Company", "NYSE"),
    "JNJ": ("Johnson & Johnson", "NYSE"),
    "BAC": ("Bank of America Corporation", "NYSE"),
    "ABBV": ("AbbVie Inc.", "NYSE"),
    "KO": ("The Coca-Cola Company", "NYSE"),
    "CRM": ("Salesforce, Inc.", "NYSE"),
    "CVX": ("Chevron Corporation", "NYSE"),
    "MRK": ("Merck & Co., Inc.", "NYSE"),
    "WFC": ("Wells Fargo & Company", "NYSE"),
    "TMO": ("Thermo Fisher Scientific Inc.", "NYSE"),
    "LIN": ("Linde plc", "NASDAQ"),
    "ACN": ("Accenture plc", "NYSE"),
    "MCD": ("McDonald's Corporation", "NYSE"),
    "ABT": ("Abbott Laboratories", "NYSE"),
    "DHR": ("Danaher Corporation", "NYSE"),
    "GE": ("GE Aerospace", "NYSE"),
    "IBM": ("International Business Machines Corp.", "NYSE"),
    "DIS": ("The Walt Disney Company", "NYSE"),
    "CAT": ("Caterpillar Inc.", "NYSE"),
    "VZ": ("Verizon Communications Inc.", "NYSE"),
    "PFE": ("Pfizer Inc.", "NYSE"),
    # the synthetic filing issuer (not a market ticker)
    "MRB": ("Meridian Regional Bancorp, Inc.", "NASDAQ"),
}

# Top-50 US large-caps offered as one-click live quotes (MRB excluded — it's the
# synthetic filing issuer, not a market ticker). The tool works for ANY ticker.
TOP_TICKERS: tuple[str, ...] = tuple(t for t in SYMBOL_META if t != "MRB")


class QuoteUnavailable(Exception):
    """Raised when neither the live adapter nor the fixture can supply a quote."""


def _meta(symbol: str) -> tuple[str, str | None]:
    name, exch = SYMBOL_META.get(symbol, (symbol, None))
    return name, exch


# ── offline fixture backend ───────────────────────────────────────────────────
def _fixture_quote(symbol: str) -> Quote | None:
    try:
        data = json.loads(Path(get_settings().market_data_fixture).read_text())
        raw = data["quotes"][symbol]
    except (OSError, KeyError, ValueError):
        return None
    return Quote(**{k: v for k, v in raw.items() if k in Quote.model_fields})


# ── live adapter: Alpha Vantage GLOBAL_QUOTE (delayed/EOD) ─────────────────────
def _parse_global_quote(payload: dict[str, object], symbol: str) -> Quote | None:
    """Pure parser for Alpha Vantage GLOBAL_QUOTE JSON → Quote. Testable offline.

    Returns None for empty/rate-limited responses (AV returns {"Note"/"Information"}
    instead of "Global Quote" when throttled).
    """
    gq = payload.get("Global Quote")
    if not isinstance(gq, dict) or not gq:
        return None

    def g(key: str) -> str:
        return str(gq.get(key, "")).strip()

    try:
        last = float(g("05. price"))
    except ValueError:
        return None
    name, exch = _meta(symbol)
    as_of = g("07. latest trading day") or "unknown"

    def _f(key: str) -> float | None:
        try:
            return float(g(key).rstrip("%"))
        except ValueError:
            return None

    vol = g("06. volume")
    return Quote(
        symbol=g("01. symbol") or symbol,
        name=name,
        last=last,
        as_of=as_of,
        label=f"Delayed end-of-day quote · as-of {as_of} · via Alpha Vantage. "
        "Informational — not a live execution price.",
        grade="delayed_eod",
        execution_grade=False,
        currency="USD",
        exchange=exch,
        change=_f("09. change"),
        change_pct=_f("10. change percent"),
        prev_close=_f("08. previous close"),
        day_high=_f("03. high"),
        day_low=_f("04. low"),
        volume=int(vol) if vol.isdigit() else None,
    )


def _fetch_alpha_vantage(
    symbol: str, api_key: str, timeout: float = 10.0
) -> dict[str, object]:
    """Network fetch (the only line that touches the wire). Kept tiny + isolated."""
    params = urllib.parse.urlencode(
        {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key}
    )
    url = f"https://www.alphavantage.co/query?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "northwind-briefing/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (https, fixed host)
        result: dict[str, object] = json.loads(resp.read().decode("utf-8"))
    return result


# ── live adapter: Finnhub /quote (free real-time US quotes) ───────────────────
def _parse_finnhub(payload: dict[str, object], symbol: str) -> Quote | None:
    """Pure parser for Finnhub /quote JSON → Quote. Testable offline.

    Finnhub returns {c: current, d: change, dp: change%, h, l, o, pc: prev close,
    t: unix ts}. `c == 0` means an unknown symbol / no data → None.
    """

    def num(key: str) -> float | None:
        v = payload.get(key)
        return float(v) if isinstance(v, (int, float)) else None

    last = num("c")
    if not last:  # 0 or missing → invalid symbol / no data
        return None
    name, exch = _meta(symbol)
    ts = payload.get("t")
    as_of = (
        datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
        if isinstance(ts, (int, float)) and ts
        else "live"
    )
    return Quote(
        symbol=symbol,
        name=name,
        last=last,
        as_of=as_of,
        label="Real-time market quote via Finnhub. Informational — not an execution price.",
        grade="realtime",
        execution_grade=False,
        currency="USD",
        exchange=exch,
        change=num("d"),
        change_pct=num("dp"),
        prev_close=num("pc"),
        day_high=num("h"),
        day_low=num("l"),
    )


def _fetch_finnhub(
    symbol: str, api_key: str, timeout: float = 10.0
) -> dict[str, object]:
    params = urllib.parse.urlencode({"symbol": symbol, "token": api_key})
    url = f"https://finnhub.io/api/v1/quote?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "northwind-briefing/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (https, fixed host)
        result: dict[str, object] = json.loads(resp.read().decode("utf-8"))
    return result


def _live_quote(symbol: str, api_key: str, provider: str) -> Quote | None:
    if provider == "alpha_vantage":
        return _parse_global_quote(_fetch_alpha_vantage(symbol, api_key), symbol)
    if provider == "finnhub":
        return _parse_finnhub(_fetch_finnhub(symbol, api_key), symbol)
    raise QuoteUnavailable(f"unknown market_data_provider: {provider!r}")


# ── the tool ──────────────────────────────────────────────────────────────────
class MarketDataTool:
    """One interface, two backends. `quote(symbol)` returns a delayed/as-of Quote."""

    def quote(self, symbol: str) -> Quote:
        sym = symbol.strip().upper()
        s = get_settings()

        if s.use_real_market_data and s.market_data_api_key:
            try:
                live = _live_quote(sym, s.market_data_api_key, s.market_data_provider)
            except Exception:  # noqa: BLE001 — any live failure must fall back, never crash
                live = None
            if live is not None:
                return live

        fixture = _fixture_quote(sym)
        if fixture is not None:
            return fixture
        raise QuoteUnavailable(sym)

    def try_quote(self, symbol: str) -> Quote | None:
        """Non-raising variant for callers that tolerate a missing symbol."""
        try:
            return self.quote(symbol)
        except QuoteUnavailable:
            return None
