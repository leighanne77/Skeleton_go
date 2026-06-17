"""app/agents/retriever.py — retrieval as a TOOL (not the spine).

Two backends behind ONE `retrieve()` interface (design.md §2):
  • SEMANTIC (T4) — OpenAI text-embedding-3-small + ChromaDB (persisted under
    `chroma_dir`). Used when the embedder is configured (USE_REAL_EMBED + key).
  • KEYWORD (fallback) — deterministic term-overlap scorer, keyless/offline. Used
    when embeddings aren't configured, and on any semantic-path failure.

Both are entitlement-filtered by manifest tags (a doc tagged `[mnpi]` is invisible to
a principal who lacks `mnpi_cleared`) and use the same deterministic tie-break
(score, then `chunk_id`). One chunk per doc, so the controlling-chunk id is stable
across both backends.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.agents import embeddings
from app.config import get_settings
from app.models import RetrievedChunk
from app.policy import get_pack

_WORD = re.compile(r"[a-z0-9]+")
# Drop stopwords so an off-corpus query scores 0 (→ empty retrieval → withhold)
# rather than matching on filler words.
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
    for line in (corpus_dir / "manifest.jsonl").read_text().splitlines():
        if line.strip():
            entry: dict[str, object] = json.loads(line)
            text = (corpus_dir / str(entry["path"])).read_text()
            out.append((entry, text))
    return out


def _tags_of(entry: dict[str, object]) -> list[str]:
    raw = entry.get("entitlement_tags")
    return [str(t) for t in raw] if isinstance(raw, list) else []


@lru_cache(maxsize=8)
def _class_entitlement_map(pack_name: str) -> dict[str, str]:
    """{sensitive-class name → required entitlement id} for block_unless_entitled classes."""
    out: dict[str, str] = {}
    for c in get_pack(pack_name).get("sensitive_classes", []):
        req = c.get("requires_entitlement")
        if req:
            out[str(c["name"])] = str(req)
    return out


def _entitled(tags: list[str], entitlements: set[str]) -> bool:
    """A doc is visible iff the principal holds the entitlement each of its class
    tags REQUIRES (manifest tags are class names like `mnpi`; principals hold ids
    like `mnpi_cleared`, mapped via the pack)."""
    cmap = _class_entitlement_map(get_settings().policy_pack)
    required = {cmap[t] for t in tags if t in cmap}
    return required <= entitlements


# ── KEYWORD backend (deterministic, keyless) ──────────────────────────────────
def _keyword_retrieve(
    query: str, entitlements: list[str], k: int, corpus_dir: Path
) -> list[RetrievedChunk]:
    qterms = _content_terms(query)
    ent = set(entitlements)
    hits: list[RetrievedChunk] = []
    for entry, text in _load_corpus(corpus_dir):
        tags = _tags_of(entry)
        if not _entitled(tags, ent):
            continue
        score = float(sum(1 for t in qterms if t in _content_terms(text)))
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
    hits.sort(key=lambda c: (-c.score, c.chunk_id))
    return hits[:k]


# ── SEMANTIC backend (OpenAI embeddings + Chroma) ─────────────────────────────
def _semantic_retrieve(
    query: str, entitlements: list[str], k: int, corpus_dir: Path
) -> list[RetrievedChunk]:
    import chromadb  # lazy: the keyless path never imports it

    docs = _load_corpus(corpus_dir)
    client: Any = chromadb.PersistentClient(path=get_settings().chroma_dir)
    coll: Any = client.get_or_create_collection(
        name=f"corpus_{corpus_dir.name}", metadata={"hnsw:space": "cosine"}
    )

    if coll.count() < len(docs):  # ingest once (idempotent upsert)
        ids, texts, metas = [], [], []
        for entry, text in docs:
            sid = str(entry["source_id"])
            ids.append(f"{sid}::c0")
            texts.append(text)
            metas.append(
                {
                    "source_id": sid,
                    "doc_title": str(entry["doc_title"]),
                    "entitlement_tags": ",".join(_tags_of(entry)),
                }
            )
        coll.upsert(
            ids=ids,
            embeddings=embeddings.embed_texts(texts),
            documents=texts,
            metadatas=metas,
        )

    qvec = embeddings.embed_texts([query])[0]
    res: Any = coll.query(query_embeddings=[qvec], n_results=max(coll.count(), 1))
    ent = set(entitlements)
    hits: list[RetrievedChunk] = []
    for cid, doc, meta, dist in zip(
        res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        tags = [t for t in str(meta.get("entitlement_tags", "")).split(",") if t]
        if not _entitled(tags, ent):
            continue
        hits.append(
            RetrievedChunk(
                chunk_id=str(cid),
                source_id=str(meta["source_id"]),
                doc_title=str(meta["doc_title"]),
                text=str(doc),
                score=round(1.0 - float(dist), 6),  # cosine distance → similarity
                entitlement_tags=tags,
            )
        )
    hits.sort(key=lambda c: (-c.score, c.chunk_id))
    return hits[:k]


def retrieve(
    query: str,
    entitlements: list[str],
    k: int = 3,
    corpus_dir: str | None = None,
) -> list[RetrievedChunk]:
    """Retrieve top-k entitlement-filtered chunks. Semantic when keyed, else keyword."""
    cdir = Path(corpus_dir or get_settings().corpus_dir)
    if embeddings.embed_enabled():
        try:
            return _semantic_retrieve(query, entitlements, k, cdir)
        except Exception:  # noqa: BLE001 — any embed/vector failure falls back, never crashes
            pass
    return _keyword_retrieve(query, entitlements, k, cdir)
