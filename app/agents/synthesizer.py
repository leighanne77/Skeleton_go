"""app/agents/synthesizer.py — the ONE place an answer is written, reachable ONLY
on the gate's pass edge (the DISPOSE step).

The parallel analyst agents (`app/agents/analysts.py`) PROPOSE cited findings upstream
of the gate; the aggregate node unions them into one candidate. `finalize` is the
SYNTHESIZER step that assembles the delivered `AnswerEnvelope` from that gate-passed
candidate. It is kept separate from proposal/aggregation so the graph can gate the draft
*before* it is ever finalized: a failed gate routes to withhold and `finalize` never
runs. Parallel agents propose; the single synthesizer disposes.
"""

from __future__ import annotations

from app.models import AnswerEnvelope, Claim, Quote, Verdict


def finalize(
    answer: str,
    claims: list[Claim],
    audit_ref: str,
    quote: Quote | None = None,
) -> AnswerEnvelope:
    """SYNTHESIZER: assemble the delivered envelope (pass edge only)."""
    citations = [c.citation for c in claims if c.citation is not None]
    return AnswerEnvelope(
        status=Verdict.DELIVERED,
        answer_text=answer,
        citations=citations,
        claims=claims,
        audit_ref=audit_ref,
        quote=quote,
    )
