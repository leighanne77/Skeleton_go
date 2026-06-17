"""tests/test_gate.py — T6 control-plane gate cascade (R2, R12).

Deterministic floor → stage-2 support → rubric. Fail-closed. Offline.
"""

from __future__ import annotations

from app.eval import judge
from app.eval.gate import evaluate
from app.models import (
    AgentState,
    Citation,
    Claim,
    FailureReason,
    Principal,
    RetrievedChunk,
    RunRequest,
)


def _chunk(sid: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{sid}::c0", source_id=sid, doc_title=sid, text=text, score=1.0
    )


def _state(
    chunks: list[RetrievedChunk], answer: str | None, claims: list[Claim]
) -> AgentState:
    return AgentState(
        request=RunRequest(
            query="q",
            principal=Principal(user_id="t"),
            policy_pack="financial_services_us",
        ),
        retrieved=chunks,
        candidate_answer=answer,
        claims=claims,
    )


def _claim(span: str, sid: str = "d1", text: str | None = None) -> Claim:
    return Claim(
        text=text if text is not None else span,
        citation=Citation(
            source_id=sid, chunk_id=f"{sid}::c0", doc_title=sid, span=span
        ),
    )


def test_grounded_relevant_answer_passes() -> None:
    text = "Regulation Best Interest governs broker-dealer recommendations to retail customers."
    res = evaluate(
        _state([_chunk("reg", text)], text, [_claim(text, "reg")]),
        "broker-dealer recommendations retail customers",
    )
    assert res.passed and not res.failure_reasons


def test_rejects_unsupported_span() -> None:
    # span resolves (it's in the chunk) but does NOT entail the claim → stage-2 fails
    span = "The sky is blue today."
    claim = _claim(
        span,
        "d1",
        text="The company reported record quarterly earnings of fifty million dollars.",
    )
    res = evaluate(_state([_chunk("d1", span)], "answer", [claim]), "earnings")
    assert not res.passed
    assert FailureReason.SUPPORT_FAILED in res.failure_reasons


def test_conflicting_detector_flags_contradiction() -> None:
    # judge.conflicting() catches a clear contradiction (shared phrase, one negated)…
    a = "All Q1 supervision reviews of representative recommendations were completed within the required thirty-day window under the policy."
    b = "Several Q1 supervision reviews of representative recommendations were not completed within the required thirty-day window under the policy."
    assert judge.conflicting([a, b]) is True
    # …but it is intentionally NOT gated (a lexical heuristic false-positives on related
    # docs like an issuer's own 10-K + 10-Q), so a grounded+supported claim still passes.
    res = evaluate(
        _state([_chunk("a", a), _chunk("b", b)], a, [_claim(a, "a")]),
        "supervision reviews completed within window",
    )
    assert res.passed


def test_empty_retrieval_withholds() -> None:
    res = evaluate(_state([], None, []), "q")
    assert not res.passed
    assert FailureReason.RETRIEVAL_EMPTY in res.failure_reasons


def test_ungrounded_span_withholds() -> None:
    # a claim whose span is NOT present in any retrieved chunk
    claim = _claim("this exact text is nowhere in the corpus", "d1")
    res = evaluate(
        _state([_chunk("d1", "totally different content here.")], "answer", [claim]),
        "q",
    )
    assert not res.passed
    assert FailureReason.UNGROUNDED in res.failure_reasons
