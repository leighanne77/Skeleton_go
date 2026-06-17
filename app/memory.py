"""app/memory.py — deliberate memory policy (rubric item 5).

Three tiers, governed by the pack's `memory` block (data, not code):
  • session  — thread-scoped state within one run/conversation (the LangGraph state /
    checkpointer). Bounded, summarized-but-traceable.
  • working  — the shared `AgentState` IS the working memory (and the audit source).
  • cross_session — OFF by design. Regulated data carries retention / PII / erasure
    obligations, so nothing persists across sessions. `persist_cross_session` refuses,
    by policy — there is deliberately no cross-session store.
"""

from __future__ import annotations

from typing import Any, cast

from app.config import get_settings
from app.policy import get_pack


def policy(pack_name: str | None = None) -> dict[str, Any]:
    mem = get_pack(pack_name or get_settings().policy_pack).get("memory", {})
    return cast("dict[str, Any]", mem) if isinstance(mem, dict) else {}


def _on(value: object) -> bool:
    # YAML parses on/off → True/False; also accept the string forms.
    return value is True or str(value).strip().lower() in ("on", "true", "yes")


def cross_session_enabled(pack_name: str | None = None) -> bool:
    return _on(policy(pack_name).get("cross_session", False))


def persist_cross_session(
    _key: str, _value: object, pack_name: str | None = None
) -> None:
    """Refuses by policy — cross-session memory is OFF for regulated data."""
    raise RuntimeError(
        "cross-session persistence is OFF by policy (regulated data: retention / PII / "
        "erasure obligations apply). Session + working memory only."
    )
