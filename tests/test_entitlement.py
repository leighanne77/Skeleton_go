"""tests/test_entitlement.py — T7 entitlement enforcement (R10 + the BFSI signature).

The vertical signature money-shot, through the REAL graph: the SAME query routes for
an unentitled principal and delivers the restricted source for an entitled one —
because retrieval is entitlement-filtered by manifest tags (conftest forces the
deterministic keyword backend so this is hermetic).
"""

from __future__ import annotations

from app.orchestrator import run

MNPI_Q = "Project Atlas pre-announcement deal terms acquirer offer per share"


def test_entitled_user_gets_mnpi() -> None:
    env, _ = run(MNPI_Q, ["mnpi_cleared"])
    sources = {c.source_id for c in env.citations}
    assert "mnpi_dealbook" in sources  # the restricted source is delivered


def test_unentitled_user_never_sees_mnpi() -> None:
    env, _ = run(MNPI_Q, [])
    sources = {c.source_id for c in env.citations}
    assert (
        "mnpi_dealbook" not in sources
    )  # filtered at retrieval — structurally invisible


def test_entitlement_changes_the_outcome() -> None:
    # the entitlement flip is the whole point: same query, different cited source set
    unentitled = {c.source_id for c in run(MNPI_Q, [])[0].citations}
    entitled = {c.source_id for c in run(MNPI_Q, ["mnpi_cleared"])[0].citations}
    assert unentitled != entitled
