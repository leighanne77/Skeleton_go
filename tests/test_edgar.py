"""tests/test_edgar.py — EDGAR filings tool.

Offline: the submissions parser is exercised against a recorded-shape sample, never
a live call. The network path is gated behind `use_real_market_data` (enabled()).
"""

from __future__ import annotations

import app.tools.edgar as edgar
from app.tools.edgar import _parse_submissions

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
    # use_real_market_data defaults False in tests → no network, empty list
    assert edgar.enabled() is False
    assert edgar.get_recent_filings("MSFT") == []
