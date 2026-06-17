"""app/tools/edgar.py — recent SEC filings for a ticker (EDGAR), the filings tool.

Pulls an issuer's recent 10-K / 10-Q / 8-K from SEC EDGAR (data.sec.gov / sec.gov —
free, US-government, clean provenance per CLAUDE.md §1; stdlib `urllib`, no pip dep).

Offline-first: this is a NETWORK call, so it is **opt-in** — enabled only when
`use_real_market_data` is true (the same "live data" toggle as live quotes). Keyless
(EDGAR needs no key, only a descriptive User-Agent). Any failure returns `[]` — the
briefing degrades to quote-only, never crashes.

This first version pulls the filing *list* (form · date · link). Summarizing the
filing *contents* is a downstream step (the corpus path already does that for the
worked synthetic issuer).
"""

from __future__ import annotations

import json
import urllib.request
from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.models import FilingRef

# SEC asks for a descriptive User-Agent identifying the caller.
_UA = {"User-Agent": "Northwind Briefing Demo (compliance@northwind.example)"}
_DEFAULT_FORMS = ("10-K", "10-Q", "8-K")


def enabled() -> bool:
    """EDGAR is a network call → gated behind the live-data toggle (offline-first)."""
    return get_settings().use_real_market_data


def _get_json(url: str, timeout: float = 15.0) -> Any:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (https, fixed host)
        return json.loads(resp.read().decode("utf-8"))


@lru_cache(maxsize=1)
def _ticker_cik_map() -> dict[str, str]:
    """{TICKER → zero-padded 10-digit CIK} from SEC's company_tickers.json."""
    data = _get_json("https://www.sec.gov/files/company_tickers.json")
    out: dict[str, str] = {}
    for row in data.values():
        out[str(row["ticker"]).upper()] = f"{int(row['cik_str']):010d}"
    return out


def _parse_submissions(
    data: dict[str, Any], cik: str, forms: tuple[str, ...], limit: int
) -> list[FilingRef]:
    """Pure parser for the EDGAR submissions JSON → recent FilingRefs. Testable offline."""
    name = str(data.get("name", ""))
    recent = data.get("filings", {}).get("recent", {})
    rows = zip(
        recent.get("form", []),
        recent.get("filingDate", []),
        recent.get("accessionNumber", []),
        recent.get("primaryDocument", []),
    )
    cik_int = int(cik)
    out: list[FilingRef] = []
    for form, filed, accession, doc in rows:
        if form not in forms:
            continue
        acc = str(accession).replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/{doc}"
        out.append(
            FilingRef(
                form=str(form), filed=str(filed), title=f"{name} — {form}", url=url
            )
        )
        if len(out) >= limit:
            break
    return out


def get_recent_filings(
    ticker: str, forms: tuple[str, ...] = _DEFAULT_FORMS, limit: int = 4
) -> list[FilingRef]:
    """Recent 10-K/10-Q/8-K for a ticker. Returns [] if disabled or on any failure."""
    if not enabled():
        return []
    try:
        cik = _ticker_cik_map().get(ticker.strip().upper())
        if not cik:
            return []
        data = _get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        return _parse_submissions(data, cik, forms, limit)
    except Exception:  # noqa: BLE001 — network/parse failure degrades to quote-only
        return []
