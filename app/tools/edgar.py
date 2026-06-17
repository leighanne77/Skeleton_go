"""app/tools/edgar.py — recent SEC filings for a ticker (EDGAR), the filings tool.

Pulls an issuer's recent 10-K / 10-Q / 8-K from SEC EDGAR (data.sec.gov / sec.gov —
free, US-government, clean provenance per CLAUDE.md §1; stdlib `urllib`, no pip dep).

Offline-first: this is a NETWORK call, so it is **opt-in** — enabled only when
`use_real_market_data` is true (the same "live data" toggle as live quotes). Keyless
(EDGAR needs no key, only a descriptive User-Agent). Any failure returns `[]` — the
briefing degrades to quote-only, never crashes.

Two capabilities: (1) `get_recent_filings` — the recent filing *list* (form · date ·
link); (2) `summarize_latest` — fetches the latest filing and returns **extractive**
key excerpts (the top query-relevant sentences). Extractive on purpose: every
"highlight" is an exact substring of the filing → a resolvable citation span, so the
governance story holds with no LLM. An LLM synthesis layer can sit on top later.
"""

from __future__ import annotations

import html as _html
import json
import re
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


# ── filing-content summarization (extractive: every highlight is a real span) ──
_SENTENCE = re.compile(r"[^.!?]*[.!?]")
_WORD = re.compile(r"[a-z0-9]+")


def _strip_html(raw: str) -> str:
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", _html.unescape(t)).strip()


def key_excerpts(text: str, query: str, n: int = 4) -> list[str]:
    """Top-n query-relevant sentences from a filing — each an exact substring (a
    resolvable citation span). Deterministic; no LLM. Pure → testable offline."""
    qterms = {w for w in _WORD.findall(query.lower()) if len(w) >= 4}
    if not qterms:  # generic filing-salient terms when the query is just a ticker
        qterms = {
            "risk",
            "results",
            "liquidity",
            "revenue",
            "income",
            "material",
            "capital",
        }
    scored: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for i, m in enumerate(_SENTENCE.finditer(text)):
        s = m.group().strip()
        if not (60 <= len(s) <= 320) or s[:80] in seen:
            continue
        terms = set(_WORD.findall(s.lower()))
        score = sum(1 for t in qterms if t in terms)
        if score > 0:
            seen.add(s[:80])
            scored.append((-score, i, s))  # by score desc, then document order
    scored.sort()
    return [s for _, _, s in scored[:n]]


def fetch_filing_text(url: str, max_chars: int = 400_000, timeout: float = 30.0) -> str:
    """Fetch a filing's primary document and strip it to clean text. '' on failure."""
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001 — network/decode failure → no summary
        return ""
    return _strip_html(raw)[:max_chars]


def summarize_latest(
    ticker: str, query: str, prefer: tuple[str, ...] = ("10-Q", "10-K", "8-K")
) -> tuple[FilingRef | None, list[str]]:
    """Pick the most recent preferred filing, fetch it, return (ref, key excerpts).
    (None, []) if disabled or unavailable."""
    if not enabled():
        return None, []
    filings = get_recent_filings(ticker, forms=prefer, limit=8)
    chosen = next((f for form in prefer for f in filings if f.form == form), None)
    if chosen is None:
        return None, []
    text = fetch_filing_text(chosen.url)
    return chosen, key_excerpts(text, query) if text else []
