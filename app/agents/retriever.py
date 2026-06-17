"""app/agents/retriever.py — retrieval as a TOOL (not the spine).

T3 backend: a deterministic keyword retriever over the vertical corpus,
**entitlement-filtered** by manifest tags (a doc tagged `[mnpi]` is invisible to a
principal who lacks `mnpi_cleared`). T4 swaps the backend for embeddings + Chroma
behind this same `retrieve()` interface — nothing downstream changes.

Deterministic tie-break: score, then `chunk_id` (design.md §0).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import get_settings
from app.models import RetrievedChunk

_WORD = re.compile(r"[a-z0-9]+")
# T3 keyword retriever: drop stopwords so an off-corpus query scores 0 (→ empty
# retrieval → withhold) rather than matching on filler words. T4 (embeddings)
# removes the need for this heuristic.
_STOP = frozenset(
    "the a an and or but of to in on for with at by from as is are was were be been "
    "this that these those it its their our your my his her what which who whom how "
    "when where why me i we you they he she them us about into over under than then "
    "tell give show summarize summarise latest recent most more any all can could "
    "would should do does did has have had will shall may might me's s".split()
)


def _content_terms(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if len(w) >= 3 and w not in _STOP}


def _load_corpus(corpus_dir: Path) -> list[tuple[dict[str, object], str]]:
    out: list[tuple[dict[str, object], str]] = []
    manifest = corpus_dir / "manifest.jsonl"
    for line in manifest.read_text().splitlines():
        if line.strip():
            entry: dict[str, object] = json.loads(line)
            text = (corpus_dir / str(entry["path"])).read_text()
            out.append((entry, text))
    return out


def retrieve(
    query: str,
    entitlements: list[str],
    k: int = 3,
    corpus_dir: str | None = None,
) -> list[RetrievedChunk]:
    cdir = Path(corpus_dir or get_settings().corpus_dir)
    qterms = _content_terms(query)
    ent = set(entitlements)

    hits: list[RetrievedChunk] = []
    for entry, text in _load_corpus(cdir):
        raw_tags = entry.get("entitlement_tags")
        tags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) else []
        if tags and not set(tags) <= ent:
            continue  # entitlement gate: principal lacks a required clearance
        terms = _content_terms(text)
        score = float(sum(1 for t in qterms if t in terms))
        if score <= 0:
            continue
        sid = str(entry["source_id"])
        hits.append(
            RetrievedChunk(
                chunk_id=f"{sid}::c0",
                source_id=sid,
                doc_title=str(entry["doc_title"]),
                text=text,
                score=score,
                entitlement_tags=tags,
            )
        )

    hits.sort(key=lambda c: (-c.score, c.chunk_id))  # deterministic
    return hits[:k]
