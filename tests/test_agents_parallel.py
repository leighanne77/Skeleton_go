"""tests/test_agents_parallel.py — the PROPOSE layer: parallel analyst agents +
the live cross-family support judge (with deterministic fallbacks).

These lock in the rebuild's two claims: (1) two analyst agents each emit a grounded,
cited finding and the gate adjudicates their union; (2) the gate's stage-2 support is a
cross-family judge seam that swaps a live OpenAI call in behind the same call, failing
soft to the lexical proxy. The graph-level parallelism (both analyst nodes DONE, single
synthesizer fenced) is asserted in test_graph.py.
"""

from __future__ import annotations

import pytest

from app.agents import analysts, llm
from app.eval import judge
from app.models import AgentState, Principal, RetrievedChunk, RunRequest
from app.orchestrator import _GRAPH, _final_state

_CHUNKS = [
    RetrievedChunk(
        chunk_id="c1",
        source_id="reg_bi",
        doc_title="Regulation Best Interest",
        text=(
            "Regulation Best Interest establishes a best interest standard of conduct "
            "for broker-dealers when making a recommendation to a retail customer."
        ),
        score=9.0,
    ),
    RetrievedChunk(
        chunk_id="c2",
        source_id="finra_2111",
        doc_title="FINRA Rule 2111",
        text=(
            "FINRA Rule 2111 requires that a member have a reasonable basis to believe "
            "a recommended transaction is suitable for the customer."
        ),
        score=7.0,
    ),
]

_QUERY = "What standard governs broker-dealer recommendations to retail customers?"


def test_each_analyst_emits_a_grounded_finding() -> None:
    for role in analysts.ANALYST_ROLES:
        f = analysts.analyze(role, _CHUNKS, _QUERY)
        assert f is not None
        assert f.agent == role
        # the cited span must be a verbatim substring of a retrieved chunk (grounding)
        span = f.claim.citation.span
        assert any(span in c.text for c in _CHUNKS)


def test_analysts_diversify_across_sources() -> None:
    # with two distinct chunks the two agents ground in different sources — that source
    # diversity is the point of running them in parallel.
    filings = analysts.analyze("filings-analyst", _CHUNKS, _QUERY)
    market = analysts.analyze("market-context", _CHUNKS, _QUERY)
    assert filings and market
    assert filings.claim.citation.source_id != market.claim.citation.source_id


def test_analyst_handles_empty_retrieval() -> None:
    assert analysts.analyze("filings-analyst", [], _QUERY) is None


def test_judge_mode_reports_deterministic_when_offline() -> None:
    # conftest forces openai_enabled False → the deterministic floor judge
    assert judge.judge_mode() == "deterministic"


def test_support_falls_back_to_lexical_when_offline() -> None:
    span = "Regulation Best Interest establishes a best interest standard of conduct."
    assert judge.supports(span, "best interest standard of conduct") is True
    assert (
        judge.supports("an unrelated sentence about weather", "best interest") is False
    )


def test_live_judge_is_used_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    # wire the cross-family judge "live" without a network call: the OpenAI seam is
    # exercised, proving supports() defers to the model verdict when enabled.
    monkeypatch.setattr(llm, "openai_enabled", lambda: True)
    monkeypatch.setattr(judge.llm, "openai_enabled", lambda: True)
    monkeypatch.setattr(judge.llm, "openai_text", lambda system, prompt: "NO")
    # lexically this WOULD pass; the live judge overrides to NO → not supported
    assert judge.supports("best interest standard", "best interest standard") is False
    assert judge.judge_mode() == "cross-family LLM (openai)"
    monkeypatch.setattr(judge.llm, "openai_text", lambda system, prompt: "YES")
    assert judge.supports("anything", "totally different claim") is True


def test_parallel_findings_merge_in_graph_state() -> None:
    """The crux of 'real parallel': both analyst agents' writes must SURVIVE in
    AgentState.findings via the reducer. If the merge were last-writer-wins, only one
    agent would appear — so this is the test that fails if the fan-out isn't real."""
    req = RunRequest(
        query="What standard governs broker-dealer recommendations to retail customers?",
        principal=Principal(user_id="t", entitlements=[]),
        policy_pack="financial_services_us",
    )
    state = _final_state(_GRAPH.invoke(AgentState(request=req)))
    agents = {f.agent for f in state.findings}
    assert agents == {
        "filings-analyst",
        "market-context",
    }  # BOTH concurrent writes kept
    assert len(state.findings) >= 2


def test_llm_clients_disabled_in_hermetic_env() -> None:
    # conftest forces both families off → the keyless contract holds (deterministic paths)
    assert llm.anthropic_enabled() is False
    assert llm.openai_enabled() is False
