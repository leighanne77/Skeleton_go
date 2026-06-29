"""tests/conftest.py — keep the suite hermetic.

The OpenAI embedder may be configured in .env (USE_REAL_EMBED + key), which would
make `retrieve()` call the live API during tests. Force the deterministic keyword
backend for every test so the suite is offline, free, and reproducible. Likewise force
the analyst-generator (Claude) and the cross-family support judge (OpenAI) to their
deterministic fallbacks. The live paths are exercised only by tests explicitly opted in
via RUN_EMBED_TESTS / RUN_LLM_TESTS.
"""

from __future__ import annotations

import pytest

from app.agents import embeddings, llm
from app.tools import edgar


@pytest.fixture(autouse=True)
def _hermetic(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force the offline paths so the suite never calls a network/LLM API, regardless
    # of what .env has set: keyword retrieval (not OpenAI embeddings) + EDGAR off +
    # both LLM families (Claude analysts, OpenAI judge) to their deterministic fallbacks.
    monkeypatch.setattr(embeddings, "embed_enabled", lambda: False)
    monkeypatch.setattr(edgar, "enabled", lambda: False)
    monkeypatch.setattr(llm, "anthropic_enabled", lambda: False)
    monkeypatch.setattr(llm, "openai_enabled", lambda: False)
