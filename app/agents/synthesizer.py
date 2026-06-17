"""app/agents/synthesizer.py — the ONE place an answer is written, reachable ONLY
on the gate's pass edge.

`make_candidate` is the SPECIALIST step (drafts a grounded candidate + claims from
retrieved chunks). `finalize` is the SYNTHESIZER step (assembles the delivered
AnswerEnvelope). They are separated so the graph can gate the draft *before* it is
ever finalized: a failed gate routes to withhold and `finalize` never runs.
"""

from __future__ import annotations

import re

from app.guardrails import scan_injection
from app.models import AnswerEnvelope, Citation, Claim, Quote, RetrievedChunk, Verdict

_WORD = re.compile(r"[a-z0-9]+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _top_sentences(text: str, query: str, k: int = 3) -> list[str]:
    """The k substantive sentences in the chunk most relevant to the query (skips
    title/heading lines), in document order. Each is a resolvable citation span."""
    qterms = {w for w in _WORD.findall(query.lower()) if len(w) >= 3}
    candidates: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("**"):
            continue
        candidates.extend(p.strip() for p in _SENT_SPLIT.split(s))
    # deliver-with-exclusion: drop any sentence carrying an instruction-injection
    # (the injected command is excluded from the answer, never followed).
    candidates = [
        s for s in candidates if 40 <= len(s) <= 400 and not scan_injection(s)
    ]
    if not candidates:
        return [text.strip()[:400]]
    scored = sorted(
        (
            (sum(1 for t in qterms if t in s.lower()), i, s)
            for i, s in enumerate(candidates)
        ),
        key=lambda t: (-t[0], t[1]),
    )
    chosen = [s for score, _, s in scored[:k] if score > 0] or [scored[0][2]]
    order = {s: candidates.index(s) for s in chosen}
    return sorted(chosen, key=lambda s: order[s])  # back to document order


def make_candidate(
    retrieved: list[RetrievedChunk], query: str = ""
) -> tuple[str, list[Claim]]:
    """SPECIALIST: draft a candidate answer + cited claims from the top chunk — the
    sentences most relevant to the query (each a resolvable span)."""
    top = retrieved[0]
    spans = _top_sentences(top.text, query)
    claims = [
        Claim(
            text=span,
            citation=Citation(
                source_id=top.source_id,
                chunk_id=top.chunk_id,
                doc_title=top.doc_title,
                span=span,
            ),
        )
        for span in spans
    ]
    return " ".join(spans), claims


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
