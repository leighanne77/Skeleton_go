"""tests/conftest.py — keep the suite hermetic.

The OpenAI embedder may be configured in .env (USE_REAL_EMBED + key), which would
make `retrieve()` call the live API during tests. Force the deterministic keyword
backend for every test so the suite is offline, free, and reproducible. The live
semantic path is exercised only by tests explicitly opted in via RUN_EMBED_TESTS.
"""

from __future__ import annotations

import pytest

from app.agents import embeddings
from app.tools import edgar


@pytest.fixture(autouse=True)
def _hermetic(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force the offline paths so the suite never calls a network/LLM API, regardless
    # of what .env has set: keyword retrieval (not OpenAI embeddings) + EDGAR off.
    monkeypatch.setattr(embeddings, "embed_enabled", lambda: False)
    monkeypatch.setattr(edgar, "enabled", lambda: False)
