"""app — the governed decision-agent skeleton (vertical-free).

The package maps 1:1 to the scored rubric items (orchestration, eval, retrieval,
memory, guardrails, audit, UI). Vertical behavior is DATA (policies/*.yaml) loaded
at runtime — never hardcoded here. See design.md §9 for the layout.
"""

__all__ = ["models", "config"]
