"""app/eval/judge.py — stage-2 support + rubric judge (the gate's model tiers).

Deterministic and offline by default:
  • supports(span, claim) — lexical entailment: the cited span must cover the claim.
  • relevant(answer, query) — the answer must address the question (rubric: relevance).
  • conflicting(chunks)    — flag mutually contradictory sources (never silently pick).

These are the seams for the production tiers: a **cross-family** LLM judge (OpenAI,
a different family than the Claude generator — so a model never grades its own output
unchecked) and a DeBERTa-class NLI model. Keeping the defaults deterministic makes the
test suite hermetic and the demo keyless; the LLM tier swaps in behind the same calls.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "the a an and or but of to in on for with at by from as is are was were be been "
    "this that these those it its their our your his her not no a per its such".split()
)
# polarity markers used to spot contradictory sources
_NEG = re.compile(
    r"\b(not|no|never|fail(?:ed|s)?|without|non-?compliant|unreviewed|missing|denied|"
    r"exceeded|breach(?:ed)?|late)\b",
    re.IGNORECASE,
)


def _terms(s: str) -> set[str]:
    return {w for w in _WORD.findall(s.lower()) if len(w) >= 3 and w not in _STOP}


def supports(span: str, claim: str, threshold: float = 0.6) -> bool:
    """Does the cited span entail the claim? Lexical-coverage proxy for NLI entailment."""
    claim_terms = _terms(claim)
    if not claim_terms:
        return False
    covered = sum(1 for t in claim_terms if t in _terms(span)) / len(claim_terms)
    return covered >= threshold


def relevant(answer: str, query: str, threshold: float = 0.08) -> bool:
    """Rubric (lenient deterministic proxy): does the answer share the query's key
    content? Conversational/specific queries give a short extractive answer low
    lexical overlap, so the bar is low here; STRICT relevance is the cross-family
    LLM-rubric tier that swaps in behind this call."""
    q = _terms(query)
    if not q:
        return True
    return sum(1 for t in q if t in _terms(answer)) / len(q) >= threshold


def _content_ngrams(text: str, n: int = 4) -> set[str]:
    """n-grams over CONTENT words (stopwords dropped) — so a shared *phrase* counts,
    not incidental shared vocabulary between unrelated documents."""
    words = [w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) >= 3]
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def conflicting(texts: list[str]) -> bool:
    """Two sources contradict iff they share a multi-word content PHRASE but one
    negates it (a precise stand-in for the NLI-contradiction tier — incidental term
    overlap between unrelated docs does NOT trip it)."""
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if _content_ngrams(texts[i]) & _content_ngrams(texts[j]) and (
                bool(_NEG.search(texts[i])) != bool(_NEG.search(texts[j]))
            ):
                return True
    return False
