"""app/eval/gate.py — the control-plane gate (STUB floor for T3; full cascade at T6).

T3 implements only the **deterministic floor**, which already enforces fail-closed:
  • empty retrieval            → withhold (RETRIEVAL_EMPTY)
  • no candidate / no citation → withhold (NO_CITATION)
  • a claim's span not present in any retrieved chunk → withhold (UNGROUNDED)

T6 adds lexical-grounding scoring, the cross-family stage-2 support judge, and the
rubric judge. The gate only ever *withholds*; it never writes the answer.
"""

from __future__ import annotations

from app.models import AgentState, FailureReason, GateResult, GateStage


def evaluate(state: AgentState) -> GateResult:
    reasons: list[FailureReason] = []

    if not state.retrieved:
        reasons.append(FailureReason.RETRIEVAL_EMPTY)
    if not state.candidate_answer or not state.claims:
        reasons.append(FailureReason.NO_CITATION)
    else:
        # every claim's cited span must appear in some retrieved chunk
        corpus = "\n".join(c.text for c in state.retrieved)
        for claim in state.claims:
            span = claim.citation.span if claim.citation else ""
            if not span or span not in corpus:
                reasons.append(FailureReason.UNGROUNDED)
                break

    passed = not reasons
    detail: dict[str, object] = {
        "retrieved": len(state.retrieved),
        "claims": len(state.claims),
        "checks": "deterministic_floor",
    }
    return GateResult(
        stage=GateStage.DETERMINISTIC_FLOOR,
        passed=passed,
        detail=detail,
        failure_reasons=reasons,
    )
