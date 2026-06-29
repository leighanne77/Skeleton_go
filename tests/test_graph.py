"""tests/test_graph.py — T3: the governed graph traverses correctly and the
synthesizer is reachable ONLY on the gate's pass edge (R1).

The PROPOSE layer is two parallel analyst agents (filings-analyst ‖ market-context);
they feed the gate, but the single synthesizer on the pass edge stays fenced — the
invariant test below is exactly the test the parallelism must NOT break.
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


def test_traverses_orchestrator_through_parallel_agents_to_gate() -> None:
    _env, trace = run(
        "What standard governs broker-dealer recommendations to retail customers?"
    )
    # both parallel analyst agents ran and the aggregate unioned their findings
    for nid in (
        "orchestrator",
        "retriever",
        "filings-analyst",
        "market-context",
        "aggregate",
        "gate",
    ):
        assert _node(trace, nid) == NodeStatus.DONE
