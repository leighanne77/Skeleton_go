"""tests/test_retriever.py — T4 retriever acceptance (R3, R4).

Tested on the deterministic keyword backend (conftest forces it) so the suite is
hermetic — a green eval is never trusted over an untested retriever (Trap 3). An
opt-in test exercises the real OpenAI-embedding + Chroma path when RUN_EMBED_TESTS
is set.
"""

from __future__ import annotations

import os

import pytest

from app.agents import embeddings
from app.agents.retriever import retrieve

SAR_Q = "When must a suspicious activity report be filed after detection?"
REGBI_Q = "What standard governs broker-dealer recommendations to retail customers?"
MNPI_Q = "Project Atlas pre-announcement deal terms acquirer target offer per share"


def test_retrieval_determinism() -> None:
    a = [c.chunk_id for c in retrieve(SAR_Q, [])]
    b = [c.chunk_id for c in retrieve(SAR_Q, [])]
    assert a and a == b  # identical ordered chunk_ids


def test_controlling_chunk_returned() -> None:
    assert retrieve(SAR_Q, [])[0].source_id == "bsa_sar"
    assert retrieve(REGBI_Q, [])[0].source_id == "reg_bi"


def test_entitlement_filtered_retrieval() -> None:
    # mnpi_dealbook is tagged [mnpi] in the manifest → invisible without clearance.
    unentitled = {c.source_id for c in retrieve(MNPI_Q, [], k=20)}
    entitled = {c.source_id for c in retrieve(MNPI_Q, ["mnpi_cleared"], k=20)}
    assert "mnpi_dealbook" not in unentitled
    assert "mnpi_dealbook" in entitled


def test_off_corpus_query_returns_empty() -> None:
    # off-corpus → no content-term overlap → empty (→ gate withholds upstream)
    assert retrieve("crypto-custody licensing in Wyoming for 2027", []) == []


@pytest.mark.skipif(
    not os.getenv("RUN_EMBED_TESTS"), reason="needs OPENAI_API_KEY + network"
)
def test_semantic_path_controlling_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        embeddings, "embed_enabled", lambda: True
    )  # re-enable for this test
    assert retrieve(SAR_Q, [])[0].source_id == "bsa_sar"
