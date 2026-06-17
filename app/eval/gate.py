"""app/eval/gate.py — the control-plane gate (full cascade, T6).

Runs in order, fail-closed (the gate only ever *withholds*; it never writes the answer):

  1. DETERMINISTIC FLOOR (no model) — empty retrieval → withhold · no candidate/citation
     → withhold · each claim's cited span must exist in a retrieved chunk · conflicting
     sources → withhold (never silently pick).
  2. STAGE-2 SUPPORT — each cited span must *entail* its claim (judge.supports; a
     cross-family LLM / NLI tier swaps in behind this call).
  3. RUBRIC — the answer must be relevant to the request (judge.relevant).

The floor runs BEFORE any judge, so a judge can never rubber-stamp an answer whose
citations don't resolve (Trap 3). PII/injection are handled guard-first upstream
(app/guardrails.py); their failure reasons surface here too.
"""

from __future__ import annotations

from app.eval import judge
from app.models import AgentState, FailureReason, GateResult, GateStage


def evaluate(state: AgentState, query: str | None = None) -> GateResult:
    reasons: list[FailureReason] = []
    stage = GateStage.DETERMINISTIC_FLOOR

    # ── guard-first results surfaced at the gate ──────────────────────────────
    if state.guardrails is not None:
        if state.guardrails.injection_detected:
            reasons.append(FailureReason.INJECTION_DETECTED)
        if state.guardrails.blocked:
            reasons.append(FailureReason.GUARDRAIL_BLOCK)

    # ── 1. deterministic floor ────────────────────────────────────────────────
    if not state.retrieved:
        reasons.append(FailureReason.RETRIEVAL_EMPTY)
    elif not state.candidate_answer or not state.claims:
        reasons.append(FailureReason.NO_CITATION)
    else:
        corpus = "\n".join(c.text for c in state.retrieved)
        for claim in state.claims:
            span = claim.citation.span if claim.citation else ""
            if not span or span not in corpus:
                reasons.append(FailureReason.UNGROUNDED)
                break
        if judge.conflicting([c.text for c in state.retrieved]):
            reasons.append(FailureReason.UNGROUNDED)  # conflicting sources → withhold

        # ── 2. stage-2 support (only if the floor held) ──────────────────────
        if not reasons:
            stage = GateStage.STAGE2_SUPPORT
            for claim in state.claims:
                span = claim.citation.span if claim.citation else ""
                if not judge.supports(span, claim.text):
                    reasons.append(FailureReason.SUPPORT_FAILED)
                    break

        # ── 3. rubric: relevance ─────────────────────────────────────────────
        if not reasons:
            stage = GateStage.RUBRIC_JUDGE
            answer = state.candidate_answer or ""
            if query and not judge.relevant(answer, query):
                reasons.append(FailureReason.RUBRIC_FAILED)

    detail: dict[str, object] = {
        "retrieved": len(state.retrieved),
        "claims": len(state.claims),
        "stage_reached": stage.value,
    }
    return GateResult(
        stage=stage,
        passed=not reasons,
        detail=detail,
        failure_reasons=reasons,
    )
