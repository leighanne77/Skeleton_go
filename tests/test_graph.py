"""tests/test_graph.py — T3: the governed graph traverses correctly and the
synthesizer is reachable ONLY on the gate's pass edge (R1).
"""

from __future__ import annotations

from app.models import NodeStatus, Verdict
from app.orchestrator import run


def _node(trace, nid: str) -> NodeStatus:  # type: ignore[no-untyped-def]
    return next(n.status for n in trace.nodes if n.id == nid)


def test_happy_path_delivers_through_synthesizer() -> None:
    # an in-corpus question retrieves, grounds, passes the floor, and synthesizes
    env, trace = run(
        "What standard governs broker-dealer recommendations to retail customers?"
    )
    assert env.status == Verdict.DELIVERED
    assert env.answer_text and env.citations
    assert _node(trace, "synthesizer") == NodeStatus.DONE


def test_synthesizer_unreachable_on_fail() -> None:
    # nothing in the corpus covers this → empty retrieval → gate withholds →
    # the synthesizer node is structurally unreachable.
    env, trace = run("Tell me about crypto-custody licensing in Wyoming for 2027.")
    assert env.status == Verdict.ROUTED_FOR_REVIEW
    assert env.answer_text is None
    assert _node(trace, "synthesizer") == NodeStatus.UNREACHABLE
    assert _node(trace, "gate") == NodeStatus.WITHHELD


def test_traverses_orchestrator_to_gate() -> None:
    _env, trace = run(
        "What standard governs broker-dealer recommendations to retail customers?"
    )
    for nid in ("orchestrator", "retriever", "specialist", "gate"):
        assert _node(trace, nid) == NodeStatus.DONE
