"""tests/conftest.py — keep the suite hermetic.

The OpenAI embedder may be configured in .env (USE_REAL_EMBED + key), which would
make `retrieve()` call the live API during tests. Force the deterministic keyword
backend for every test so the suite is offline, free, and reproducible. The live
semantic path is exercised only by tests explicitly opted in via RUN_EMBED_TESTS.
"""

from __future__ import annotations

import pytest

from app.agents import embeddings


@pytest.fixture(autouse=True)
def _force_keyword_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(embeddings, "embed_enabled", lambda: False)
