"""app/agents/synthesizer.py — the ONE place an answer is written, reachable ONLY
on the gate's pass edge.

`make_candidate` is the SPECIALIST step (drafts a grounded candidate + claims from
retrieved chunks). `finalize` is the SYNTHESIZER step (assembles the delivered
AnswerEnvelope). They are separated so the graph can gate the draft *before* it is
ever finalized: a failed gate routes to withhold and `finalize` never runs.
"""

from __future__ import annotations

import re

from app.models import AnswerEnvelope, Citation, Claim, Quote, RetrievedChunk, Verdict

_WORD = re.compile(r"[a-z0-9]+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _best_sentence(text: str, query: str) -> str:
    """The substantive sentence in the chunk most relevant to the query (skips
    title/heading lines). Falls back to the first real sentence."""
    qterms = {w for w in _WORD.findall(query.lower()) if len(w) >= 3}
    candidates: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("**"):
            continue
        candidates.extend(p.strip() for p in _SENT_SPLIT.split(s))
    candidates = [s for s in candidates if 40 <= len(s) <= 400]
    if not candidates:
        return text.strip()[:400]
    scored = max(
        candidates,
        key=lambda s: sum(1 for t in qterms if t in s.lower()),
    )
    return scored


def make_candidate(
    retrieved: list[RetrievedChunk], query: str = ""
) -> tuple[str, list[Claim]]:
    """SPECIALIST: draft a candidate answer + a cited claim from the top chunk —
    the sentence most relevant to the query (a resolvable span)."""
    top = retrieved[0]
    span = _best_sentence(top.text, query)
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
