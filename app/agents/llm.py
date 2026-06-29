"""app/agents/llm.py — cross-family LLM clients (the live reasoning agents).

Two FAMILIES on purpose (CLAUDE.md §4: a model never grades its own output unchecked):
  • the **generator** family — Claude (Anthropic) — writes the analysts' findings.
  • the **judge** family — OpenAI — adjudicates those findings in the gate's stage-2
    support. Different vendor + different model lineage = an independent second opinion.

Both are gated behind `USE_REAL_LLM` + the relevant key and **fail soft**: any
unavailability/error returns None, and the caller falls back to its deterministic path
so the skeleton still runs keyless and the test suite stays hermetic (CLAUDE.md §1).
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings


def anthropic_enabled() -> bool:
    s = get_settings()
    return bool(s.use_real_llm and s.anthropic_api_key)


def openai_enabled() -> bool:
    s = get_settings()
    return bool(s.use_real_llm and s.openai_api_key)


def claude_text(system: str, prompt: str, max_tokens: int = 320) -> str | None:
    """Generator agent (Claude). None if disabled or on any failure."""
    if not anthropic_enabled():
        return None
    s = get_settings()
    try:
        from anthropic import Anthropic

        client: Any = Anthropic(api_key=s.anthropic_api_key)
        msg = client.messages.create(
            model=s.llm_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(getattr(b, "text", "") for b in msg.content).strip() or None
    except Exception:  # noqa: BLE001 — fail soft to the deterministic path
        return None


def openai_text(system: str, prompt: str, max_tokens: int = 10) -> str | None:
    """Judge agent (OpenAI, cross-family). None if disabled or on any failure."""
    if not openai_enabled():
        return None
    s = get_settings()
    try:
        from openai import OpenAI

        client: Any = OpenAI(api_key=s.openai_api_key)
        resp = client.chat.completions.create(
            model=s.judge_model,
            max_tokens=max_tokens,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        text: str | None = resp.choices[0].message.content
        return text.strip() if text else None
    except Exception:  # noqa: BLE001 — fail soft to the deterministic path
        return None
