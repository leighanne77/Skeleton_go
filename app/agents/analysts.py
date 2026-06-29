"""app/agents/analysts.py — the parallel analyst agents (the PROPOSE layer).

Two concurrent workers run upstream of the gate as a real LangGraph fan-out:

  • filings-analyst — grounds in the primary filing-of-record chunk (the regulated
    source); surfaces the sentence that most directly answers the question.
  • market-context  — grounds in a complementary chunk (a second source/lens); surfaces
    the sentence that adds the most market/business context.

Each emits a **Finding** — a grounded, cited proposal — NOT prose. The aggregate node
unions the findings into the single candidate the gate adjudicates, and only the one
synthesizer (on the gate's pass edge) ever writes the user-facing answer. Analysts
PROPOSE; the synthesizer DISPOSES.

Each analyst calls Claude (the generator family) when `USE_REAL_LLM` + a key are set,
and falls back to the deterministic extractor otherwise — so the fan-out is real models
when keyed and still runs hermetic/keyless for tests and the offline demo. Even on the
LLM path the returned sentence is validated to be a verbatim span of a retrieved chunk,
so the gate's grounding floor holds regardless of which path produced the finding.
"""

from __future__ import annotations

import re

from app.agents import llm
from app.guardrails import scan_injection
from app.models import Citation, Claim, Finding, RetrievedChunk

_WORD = re.compile(r"[a-z0-9]+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _top_sentences(text: str, query: str, k: int = 3) -> list[str]:
    """The k substantive sentences in the chunk most relevant to the query (skips
    title/heading lines), in document order. Each is a resolvable citation span — the
    deterministic, offline extractor each analyst falls back to when unkeyed."""
    qterms = {w for w in _WORD.findall(query.lower()) if len(w) >= 3}
    candidates: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("**"):
            continue
        candidates.extend(p.strip() for p in _SENT_SPLIT.split(s))
    # deliver-with-exclusion: drop any sentence carrying an instruction-injection
    # (the injected command is excluded from the finding, never followed).
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


# role → (preferred chunk index for source diversity, system prompt, operator rationale)
_ROLES: dict[str, tuple[int, str, str]] = {
    "filings-analyst": (
        0,
        "You are a SEC-filings analyst. From the retrieved filing excerpts, surface the "
        "ONE sentence that most directly and factually answers the user's question, "
        "grounded in the filing. Quote it VERBATIM from the provided context — do not "
        "paraphrase, do not add commentary. Return only that sentence.",
        "primary regulated source (filing of record)",
    ),
    "market-context": (
        1,
        "You are a market-context analyst. From the retrieved excerpts, surface the ONE "
        "sentence that adds the most relevant market or business context to the user's "
        "question. Quote it VERBATIM from the provided context — do not paraphrase. "
        "Return only that sentence.",
        "complementary market/context lens",
    ),
}

ANALYST_ROLES: tuple[str, ...] = tuple(_ROLES)


def _verbatim_span(text: str, retrieved: list[RetrievedChunk]) -> str | None:
    """An LLM finding only counts if it's a verbatim span of a retrieved chunk —
    keeps the gate's grounding floor intact on the model path. None if not found."""
    candidate = text.strip().strip('"').strip()
    if len(candidate) < 20:
        return None
    for chunk in retrieved:
        if candidate in chunk.text:
            return candidate
    return None


def analyze(role: str, retrieved: list[RetrievedChunk], query: str) -> Finding | None:
    """Run one analyst agent → a grounded, cited Finding (or None if no chunk)."""
    if not retrieved:
        return None
    pref_idx, system, rationale = _ROLES[role]
    source = retrieved[pref_idx] if pref_idx < len(retrieved) else retrieved[0]

    span: str | None = None
    # ── live path: the generator-family model (Claude), validated back to a span ──
    # scope each analyst to ITS lane (its source chunk) so the two agents ground in
    # different sources — that source diversity is the visible payoff of running them
    # in parallel, and it keeps the verbatim-span grounding floor intact.
    if llm.anthropic_enabled():
        context = f"[{source.doc_title}]\n{source.text}"
        out = llm.claude_text(system, f"QUESTION: {query}\n\nCONTEXT:\n{context}")
        if out:
            span = _verbatim_span(out, [source])

    # ── deterministic fallback: top query-relevant sentence from this analyst's chunk ──
    if span is None:
        spans = _top_sentences(source.text, query, k=1)
        span = spans[0] if spans else None
    if span is None:
        return None

    return Finding(
        agent=role,
        rationale=rationale,
        claim=Claim(
            text=span,
            citation=Citation(
                source_id=source.source_id,
                chunk_id=source.chunk_id,
                doc_title=source.doc_title,
                span=span,
            ),
        ),
    )
