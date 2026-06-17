"""app/agents/embeddings.py — the embedding-model seam (rubric item 3).

Chosen embedder: **OpenAI `text-embedding-3-small`** (1536-dim), enabled only when
`USE_REAL_EMBED` is true AND `OPENAI_API_KEY` is set. When it isn't, retrieval falls
back to the deterministic keyword scorer (retriever.py) so the skeleton still runs
keyless (CLAUDE.md principle 1). One embedding space per index — no mixing models/dims.
"""

from __future__ import annotations

from app.config import get_settings


def embed_enabled() -> bool:
    """True iff the real embedder is configured (key + toggle)."""
    s = get_settings()
    return bool(s.use_real_embed and s.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed with OpenAI text-embedding-3-small. Callers must gate on embed_enabled().

    Lazy import so the keyless path never imports the OpenAI client.
    """
    s = get_settings()
    from openai import OpenAI

    client = OpenAI(api_key=s.openai_api_key)
    resp = client.embeddings.create(model=s.embed_model, input=texts)
    return [list(d.embedding) for d in resp.data]
