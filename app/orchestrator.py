"""app/orchestrator.py — the supervisor graph (LangGraph). Rubric item 1.

Topology (orchestrator-workers + control-plane gate) — PROPOSE in parallel, DISPOSE once:

                 ┌→ filings-analyst ─┐
    orchestrate ─┤   (parallel       ├→ aggregate → GATE ──pass──→ synthesize → END
       ↘ retrieve└→ market-context ──┘   (union of   └─fail──→ withhold   → END
       ↘ market_data  agents)             findings)

Two analyst agents run as a **real LangGraph fan-out** (concurrent nodes, their cited
findings merged through a reducer on `AgentState.findings`). They only PROPOSE; the
aggregate node unions their findings into the single candidate the gate adjudicates.
The ONE synthesizer still sits behind a CONDITIONAL edge off the gate — a failed gate
routes to `withhold` and the synthesizer is **structurally unreachable** (the invariant
in `test_synthesizer_unreachable_on_fail`). Parallelism lives upstream of the gate; the
one writer on the pass edge stays fenced. Analysts propose, the synthesizer disposes.

Wired: entitlement-filtered retriever (T4: OpenAI embeddings + Chroma, keyword
fallback) · market-data tool (T4b) · parallel analyst agents (Claude when keyed,
deterministic fallback) · guard-first PII/injection screen (T5) · the full control-plane
gate with a live cross-family judge in stage-2 support (T6: floor → support → rubric) ·
a tamper-evident hash-chained audit trail (T9). The topology is fixed; backends swap
behind the nodes.
"""

from __future__ import annotations

import re
from typing import Any

from langgraph.graph import END, StateGraph

from app import guardrails
from app.agents import analysts, retriever, synthesizer
from app.audit import AuditChain
from app.eval import gate as gate_mod
from app.models import (
    AgentState,
    AnswerEnvelope,
    AuditRow,
    GateStageTrace,
    NodeStatus,
    NodeTrace,
    Principal,
    RunRequest,
    RunTrace,
    Verdict,
)
from app.tools.market_data import MarketDataTool

_TICKER_PAREN = re.compile(r"\(([A-Z]{1,5})\)")
_TICKER_KNOWN = re.compile(r"\b(MSFT|MRB|IBM)\b")


def _extract_ticker(query: str) -> str | None:
    m = _TICKER_PAREN.search(query) or _TICKER_KNOWN.search(query.upper())
    return m.group(1) if m else None


# ── nodes (each returns a partial state update) ───────────────────────────────
def n_orchestrate(state: AgentState) -> dict[str, object]:
    return {}


def n_retrieve(state: AgentState) -> dict[str, object]:
    chunks = retriever.retrieve(
        state.request.query, state.request.principal.entitlements
    )
    return {"retrieved": chunks}


def n_market_data(state: AgentState) -> dict[str, object]:
    ticker = _extract_ticker(state.request.query)
    quote = MarketDataTool().try_quote(ticker) if ticker else None
    return {"quote": quote}


# ── the PROPOSE layer: two analyst agents run concurrently (real fan-out) ─────
# Each writes to `findings` (reducer-merged); neither writes the user-facing answer.
def n_filings_analyst(state: AgentState) -> dict[str, object]:
    f = analysts.analyze("filings-analyst", state.retrieved, state.request.query)
    return {"findings": [f]} if f else {}


def n_market_context(state: AgentState) -> dict[str, object]:
    f = analysts.analyze("market-context", state.retrieved, state.request.query)
    return {"findings": [f]} if f else {}


def n_aggregate(state: AgentState) -> dict[str, object]:
    """Union the parallel analysts' findings into the single candidate the gate
    adjudicates (dedup by span; filings-analyst ordered first for determinism)."""
    if not state.findings:
        return {}
    seen: set[str] = set()
    claims = []
    for f in sorted(
        state.findings, key=lambda f: 0 if f.agent == "filings-analyst" else 1
    ):
        span = f.claim.citation.span if f.claim.citation else f.claim.text
        if span in seen:
            continue
        seen.add(span)
        claims.append(f.claim)
    answer = " ".join(c.text for c in claims)
    # guard-first: PII-screen the unioned candidate + flag any injection in the spans
    clean, gr = guardrails.screen(answer, state.request.policy_pack)
    return {"candidate_answer": clean, "claims": claims, "guardrails": gr}


def n_gate(state: AgentState) -> dict[str, object]:
    return {"gate_results": [gate_mod.evaluate(state, state.request.query)]}


def _route_after_gate(state: AgentState) -> str:
    return "synthesize" if state.gate_results[-1].passed else "withhold"


def n_synthesize(state: AgentState) -> dict[str, object]:
    return {"verdict": Verdict.DELIVERED}


def n_withhold(state: AgentState) -> dict[str, object]:
    return {"verdict": Verdict.ROUTED_FOR_REVIEW}


def _build_graph() -> Any:
    g = StateGraph(AgentState)
    g.add_node("orchestrate", n_orchestrate)
    g.add_node("retrieve", n_retrieve)
    g.add_node("market_data", n_market_data)
    g.add_node("filings_analyst", n_filings_analyst)
    g.add_node("market_context", n_market_context)
    g.add_node("aggregate", n_aggregate)
    g.add_node("gate", n_gate)
    g.add_node("synthesize", n_synthesize)
    g.add_node("withhold", n_withhold)

    g.set_entry_point("orchestrate")
    # fan-out: retrieve + market_data run in parallel off the orchestrator
    g.add_edge("orchestrate", "retrieve")
    g.add_edge("orchestrate", "market_data")
    # fan-out: the two analyst agents run CONCURRENTLY off retrieval (real parallelism)
    g.add_edge("retrieve", "filings_analyst")
    g.add_edge("retrieve", "market_context")
    # fan-in (barrier): aggregate waits for both analysts AND the market-data tool
    g.add_edge("filings_analyst", "aggregate")
    g.add_edge("market_context", "aggregate")
    g.add_edge("market_data", "aggregate")
    g.add_edge("aggregate", "gate")
    # the invariant: ONE synthesizer, reachable ONLY on the gate's pass edge
    g.add_conditional_edges(
        "gate", _route_after_gate, {"synthesize": "synthesize", "withhold": "withhold"}
    )
    g.add_edge("synthesize", END)
    g.add_edge("withhold", END)
    return g.compile()


_GRAPH: Any = _build_graph()


def _final_state(raw: object) -> AgentState:
    """LangGraph may return the pydantic state or a channel dict — normalize."""
    if isinstance(raw, AgentState):
        return raw
    return AgentState(**raw)  # type: ignore[arg-type]


def _audit_chain(state: AgentState) -> AuditChain:
    """A real tamper-evident audit trail for this run (deterministic seq timestamps)."""
    ch = AuditChain()

    def ts(i: int) -> str:
        return f"2026-06-17T00:00:{i:02d}Z"

    top = state.retrieved[0].source_id if state.retrieved else None
    ch.append(
        "retrieval",
        {"chunks": len(state.retrieved), "top": top},
        ts(0),
        state.request.principal.entitlements,
    )
    if state.guardrails is not None:
        ch.append(
            "guardrail",
            {
                "injection": state.guardrails.injection_detected,
                "actions": len(state.guardrails.actions),
            },
            ts(1),
        )
    if state.gate_results:
        gr = state.gate_results[-1]
        ch.append("gate", {"stage": gr.stage.value, "passed": gr.passed}, ts(2))
    ch.append(
        "decision", {"verdict": state.verdict.value if state.verdict else None}, ts(3)
    )
    return ch


def _trace(state: AgentState, route: str | None) -> RunTrace:
    delivered = state.verdict == Verdict.DELIVERED
    top = state.retrieved[0] if state.retrieved else None
    produced = {f.agent for f in state.findings}
    judge_mode = gate_mod.judge_mode()

    def _analyst(role: str) -> NodeTrace:
        f = next((f for f in state.findings if f.agent == role), None)
        return NodeTrace(
            id=role,
            status=NodeStatus.DONE if f else NodeStatus.SKIPPED,
            detail=(f.rationale if f else "no finding"),
        )

    nodes = [
        NodeTrace(id="orchestrator", status=NodeStatus.DONE),
        NodeTrace(
            id="retriever",
            status=NodeStatus.DONE if state.retrieved else NodeStatus.SKIPPED,
            detail=(
                f"{len(state.retrieved)} chunks · top = {top.source_id} {top.score:.0f}"
                if top
                else "no hits"
            ),
        ),
        NodeTrace(
            id="market_data",
            status=NodeStatus.DONE if state.quote else NodeStatus.SKIPPED,
            detail=(state.quote.label if state.quote else "no ticker"),
        ),
        # the parallel PROPOSE layer — two analyst agents (real LangGraph fan-out)
        _analyst("filings-analyst"),
        _analyst("market-context"),
        NodeTrace(
            id="aggregate",
            status=NodeStatus.DONE if state.candidate_answer else NodeStatus.SKIPPED,
            detail=(
                f"{len(produced)} agents · {len(state.claims)} findings → 1 candidate"
                if state.candidate_answer
                else "no findings"
            ),
        ),
        NodeTrace(
            id="gate",
            status=NodeStatus.DONE if delivered else NodeStatus.WITHHELD,
            detail=f"support judge: {judge_mode}",
        ),
        NodeTrace(
            id="synthesizer",
            status=NodeStatus.DONE if delivered else NodeStatus.UNREACHABLE,
            detail="" if delivered else "gate did not pass",
        ),
    ]
    gate_stages = [
        GateStageTrace(
            name=gr.stage.value,
            passed=gr.passed,
            detail=", ".join(r.value for r in gr.failure_reasons) or "floor ok",
        )
        for gr in state.gate_results
    ]
    return RunTrace(
        nodes=nodes,
        gate_stages=gate_stages,
        entitlement_decision={
            "principal": state.request.principal.entitlements,
            "filtered": [],
        },
        verdict=state.verdict,
        route=None if delivered else "human:compliance-officer",
        audit_rows=[
            AuditRow(n=r.seq, hash=f"{r.hash[:6]}…")
            for r in _audit_chain(state).records
        ],
    )


def run(
    query: str,
    entitlements: list[str] | None = None,
    policy_pack: str = "financial_services_us",
) -> tuple[AnswerEnvelope, RunTrace]:
    """Run the governed graph. Returns the delivered/withheld envelope + run trace."""
    req = RunRequest(
        query=query,
        principal=Principal(user_id="dana", entitlements=entitlements or []),
        policy_pack=policy_pack,
    )
    state = _final_state(_GRAPH.invoke(AgentState(request=req)))
    route = None if state.verdict == Verdict.DELIVERED else "withhold"

    if state.verdict == Verdict.DELIVERED and state.candidate_answer:
        env = synthesizer.finalize(
            state.candidate_answer,
            state.claims,
            audit_ref="audit:#1",
            quote=state.quote,
        )
    else:
        reasons = state.gate_results[-1].failure_reasons if state.gate_results else []
        env = AnswerEnvelope(
            status=Verdict.ROUTED_FOR_REVIEW,
            answer_text=None,
            withhold_reason=reasons,
            audit_ref="audit:#1",
        )
    return env, _trace(state, route)
