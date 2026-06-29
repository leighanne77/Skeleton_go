"""app/eval/judge.py — stage-2 support + rubric judge (the gate's model tiers).

Deterministic and offline by default:
  • supports(span, claim) — lexical entailment: the cited span must cover the claim.
  • relevant(answer, query) — the answer must address the question (rubric: relevance).
  • conflicting(chunks)    — flag mutually contradictory sources (never silently pick).

`supports` is the gate's stage-2 SUPPORT tier and is now wired to a **live cross-family
LLM judge** (OpenAI — a different family than the Claude generator, so a model never
grades its own output unchecked) when `USE_REAL_LLM` + an OpenAI key are set; it falls
back to the deterministic lexical proxy otherwise, so the test suite stays hermetic and
the demo runs keyless. (`relevant`/`conflicting` keep their deterministic proxies; the
DeBERTa-class NLI tier swaps in behind the same calls.)
"""

from __future__ import annotations

import re

from app.agents import llm

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


_JUDGE_SYSTEM = (
    "You are an independent entailment judge for a regulated decision agent. Given a "
    "SPAN of source text and a CLAIM, decide whether the span ENTAILS the claim (the "
    "claim is fully supported by the span, no outside knowledge). Answer with exactly "
    "one word: YES or NO. Default to NO if unsure."
)


def judge_mode() -> str:
    """Which support tier is live — for the operator/glass-box read-out."""
    return "cross-family LLM (openai)" if llm.openai_enabled() else "deterministic"


def _supports_lexical(span: str, claim: str, threshold: float) -> bool:
    claim_terms = _terms(claim)
    if not claim_terms:
        return False
    covered = sum(1 for t in claim_terms if t in _terms(span)) / len(claim_terms)
    return covered >= threshold


def supports(span: str, claim: str, threshold: float = 0.6) -> bool:
    """Does the cited span entail the claim? Live cross-family LLM judge (OpenAI) when
    keyed — a model never grades its own output unchecked — else the deterministic
    lexical-coverage proxy for NLI entailment. Fails soft to lexical on any judge error."""
    if llm.openai_enabled():
        verdict = llm.openai_text(_JUDGE_SYSTEM, f"SPAN:\n{span}\n\nCLAIM:\n{claim}")
        if verdict is not None:
            return verdict.strip().lower().startswith("y")
    return _supports_lexical(span, claim, threshold)


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
