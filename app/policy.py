"""app/policy.py — the ONE seam to the Policies pillar (design.md §9).

A thin wrapper over `load_pack` so nothing else in the skeleton reads YAML directly.
Loads the chosen vertical pack — a deep-merge of `_base` + the vertical overlay
(lists concatenate, dicts deep-merge, scalars override). The guardrail / eval / audit
modules read fields off the returned dict and never hardcode a vertical rule.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import get_settings
from load_pack import load_pack


@lru_cache(maxsize=8)
def get_pack(name: str | None = None) -> dict[str, Any]:
    """Return the merged policy pack (defaults to the configured `policy_pack`).

    Cached per name. Treat the result as read-only — callers must not mutate it.
    """
    return load_pack(name or get_settings().policy_pack)
