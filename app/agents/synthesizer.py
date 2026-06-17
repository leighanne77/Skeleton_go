"""app/agents/synthesizer.py — the ONE place an answer is written, reachable ONLY
on the gate's pass edge.

`make_candidate` is the SPECIALIST step (drafts a grounded candidate + claims from
retrieved chunks). `finalize` is the SYNTHESIZER step (assembles the delivered
AnswerEnvelope). They are separated so the graph can gate the draft *before* it is
ever finalized: a failed gate routes to withhold and `finalize` never runs.
"""

from __future__ import annotations

from app.models import AnswerEnvelope, Citation, Claim, Quote, RetrievedChunk, Verdict


def _first_sentence(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("**"):
            return s[:400]
    return text.strip()[:400]


def make_candidate(retrieved: list[RetrievedChunk]) -> tuple[str, list[Claim]]:
    """SPECIALIST: draft a candidate answer + a cited claim from the top chunk."""
    top = retrieved[0]
    span = _first_sentence(top.text)
    citation = Citation(
        source_id=top.source_id,
        chunk_id=top.chunk_id,
        doc_title=top.doc_title,
        span=span,
    )
    answer = f"{span}"
    return answer, [Claim(text=span, citation=citation)]


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
