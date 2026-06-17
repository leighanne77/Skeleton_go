"""tests/test_market_data.py — T4b market-data tool.

Tested on its own (Trap 3): a tool the briefing depends on is never trusted on a
green eval alone. All offline — the Alpha Vantage parser is exercised against a
recorded sample, never a live call.
"""

from __future__ import annotations

import pytest

import app.tools.market_data as md
from app.tools.market_data import (
    MarketDataTool,
    _fixture_quote,
    _parse_finnhub,
    _parse_global_quote,
)

# Recorded Alpha Vantage GLOBAL_QUOTE response (demo key, IBM) — the locked shape.
SAMPLE = {
    "Global Quote": {
        "01. symbol": "IBM",
        "02. open": "270.8700",
        "03. high": "276.6200",
        "04. low": "268.6100",
        "05. price": "270.8100",
        "06. volume": "4917642",
        "07. latest trading day": "2026-06-16",
        "08. previous close": "268.7100",
        "09. change": "2.1000",
        "10. change percent": "0.7815%",
    }
}


def test_fixture_quote_offline_deterministic() -> None:
    q1 = _fixture_quote("MSFT")
    q2 = _fixture_quote("MSFT")
    assert q1 is not None and q2 is not None
    assert q1 == q2  # deterministic, keyless
    assert q1.symbol == "MSFT" and q1.exchange == "NASDAQ"


def test_stale_quote_labeled() -> None:
    q = _fixture_quote("MSFT")
    assert q is not None
    assert q.execution_grade is False  # never execution-grade
    assert q.as_of  # carries an as-of timestamp
    assert "live execution price" in q.label.lower() or "not a live" in q.label.lower()


def test_fixture_unknown_symbol_is_none() -> None:
    assert _fixture_quote("ZZZZ") is None


def test_alpha_vantage_parse_from_sample() -> None:
    q = _parse_global_quote(SAMPLE, "IBM")
    assert q is not None
    assert q.symbol == "IBM"
    assert q.last == pytest.approx(270.81)
    assert q.change_pct == pytest.approx(0.7815)
    assert q.prev_close == pytest.approx(268.71)
    assert q.execution_grade is False
    assert q.grade == "delayed_eod"
    assert "Alpha Vantage" in q.label


def test_finnhub_parse_from_sample() -> None:
    # Finnhub /quote shape: c=current, d=change, dp=change%, pc=prev close, t=unix
    payload = {
        "c": 384.27,
        "d": -9.56,
        "dp": -2.43,
        "h": 395.2,
        "l": 383.1,
        "o": 394.0,
        "pc": 393.83,
        "t": 1718568000,
    }
    q = _parse_finnhub(payload, "MSFT")
    assert q is not None
    assert q.last == pytest.approx(384.27)
    assert q.change_pct == pytest.approx(-2.43)
    assert q.prev_close == pytest.approx(393.83)
    assert q.grade == "realtime"
    assert q.execution_grade is False
    assert "Finnhub" in q.label


def test_finnhub_unknown_symbol_returns_none() -> None:
    # Finnhub returns c=0 for an unknown symbol
    assert _parse_finnhub({"c": 0, "d": None, "dp": None}, "ZZZZ") is None


def test_alpha_vantage_rate_limited_returns_none() -> None:
    # AV returns {"Information"/"Note"} (no "Global Quote") when throttled
    assert _parse_global_quote({"Information": "rate limit"}, "MSFT") is None
    assert _parse_global_quote({"Global Quote": {}}, "MSFT") is None


def test_tool_uses_fixture_when_live_off(monkeypatch: pytest.MonkeyPatch) -> None:
    class _S:
        use_real_market_data = False
        market_data_api_key = None
        market_data_provider = "alpha_vantage"
        market_data_fixture = "data/market/quotes.json"

    monkeypatch.setattr(md, "get_settings", lambda: _S())
    q = MarketDataTool().quote("msft")  # case-insensitive
    assert q.symbol == "MSFT" and q.execution_grade is False


def test_tool_unknown_symbol_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    class _S:
        use_real_market_data = False
        market_data_api_key = None
        market_data_provider = "alpha_vantage"
        market_data_fixture = "data/market/quotes.json"

    monkeypatch.setattr(md, "get_settings", lambda: _S())
    assert MarketDataTool().try_quote("ZZZZ") is None
    with pytest.raises(md.QuoteUnavailable):
        MarketDataTool().quote("ZZZZ")
