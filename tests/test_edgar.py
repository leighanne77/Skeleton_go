"""tests/test_edgar.py — EDGAR filings tool.

Offline: the submissions parser is exercised against a recorded-shape sample, never
a live call. The network path is gated behind `use_real_market_data` (enabled()).
"""

from __future__ import annotations

import app.tools.edgar as edgar
from app.tools.edgar import _parse_submissions, _strip_html, key_excerpts

# Minimal EDGAR submissions shape (data.sec.gov/submissions/CIK##########.json).
SAMPLE = {
    "name": "MICROSOFT CORP",
    "filings": {
        "recent": {
            "form": ["8-K", "4", "10-Q", "8-K", "10-K"],
            "filingDate": [
                "2026-06-05",
                "2026-05-02",
                "2026-04-29",
                "2026-04-29",
                "2025-07-30",
            ],
            "accessionNumber": [
                "0000789019-26-000050",
                "0000320193-26-000011",
                "0000789019-26-000040",
                "0000789019-26-000041",
                "0000789019-25-000080",
            ],
            "primaryDocument": [
                "d8k.htm",
                "f4.xml",
                "msft-10q.htm",
                "d2-8k.htm",
                "msft-10k.htm",
            ],
        }
    },
}


def test_parse_submissions_filters_forms_and_builds_urls() -> None:
    refs = _parse_submissions(SAMPLE, "0000789019", ("10-K", "10-Q", "8-K"), limit=4)
    forms = [r.form for r in refs]
    assert forms == ["8-K", "10-Q", "8-K", "10-K"]  # the Form 4 is filtered out
    top = refs[0]
    assert top.filed == "2026-06-05"
    assert top.title == "MICROSOFT CORP — 8-K"
    # accession dashes stripped; CIK un-padded in the archive path
    assert (
        top.url
        == "https://www.sec.gov/Archives/edgar/data/789019/000078901926000050/d8k.htm"
    )


def test_parse_submissions_respects_limit() -> None:
    assert (
        len(_parse_submissions(SAMPLE, "0000789019", ("10-K", "10-Q", "8-K"), limit=2))
        == 2
    )


def test_disabled_offline_returns_empty() -> None:
    # conftest forces EDGAR off → no network, empty results
    assert edgar.enabled() is False
    assert edgar.get_recent_filings("MSFT") == []
    assert edgar.summarize_latest("MSFT", "liquidity risk") == (None, [])


def test_strip_html() -> None:
    raw = "<html><style>x{}</style><body><p>Net&nbsp;income rose.</p><script>z()</script></body></html>"
    assert _strip_html(raw) == "Net income rose."


def test_key_excerpts_returns_relevant_real_spans() -> None:
    text = (
        "The Company sells software. "
        "Our liquidity position remains strong with ample cash reserves on hand. "
        "Risk factors include competition from larger firms in the cloud market segment. "
        "The cafeteria menu changed last quarter for employees."
    )
    out = key_excerpts(text, "liquidity and risk factors", n=2)
    assert len(out) == 2
    assert all(s in text for s in out)  # every excerpt is an exact substring (citable)
    assert any("liquidity" in s.lower() for s in out)
    assert all("cafeteria" not in s.lower() for s in out)  # off-topic excluded
