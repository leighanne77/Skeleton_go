"""app/config.py — typed configuration, read once from .env (pydantic-settings).

Nothing else in the app touches the environment directly. Keys absent → the
keyless stub path runs (CLAUDE.md principle 1: zero-keys-to-run). `USE_REAL_*`
toggles flip individual subsystems to real providers when keyed.

The build agent is denied read access to .env (.claude/settings.json); this module
defines the *contract* (the same keys that live, with no secrets, in .env.example).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── vertical / policy ─────────────────────────────────────────────────────
    policy_pack: str = "financial_services_us"  # the loaded demo vertical
    policies_dir: str = "policies"

    # ── secrets (absent → stub path) ──────────────────────────────────────────
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    market_data_api_key: str | None = None  # absent → offline quote fixture

    # ── stub-vs-real toggles ──────────────────────────────────────────────────
    use_real_llm: bool = False
    use_real_embed: bool = False
    use_real_market_data: bool = False
    market_data_provider: str = (
        "alpha_vantage"  # live adapter when use_real_market_data
    )

    # ── reasoning LLM ─────────────────────────────────────────────────────────
    llm_provider: str = "anthropic"
    llm_model: str = "claude-opus-4-8"
    judge_provider: str = "openai"  # cross-family judge (independent gate)
    judge_model: str = "gpt-4o-mini"

    # ── embeddings / vector store ─────────────────────────────────────────────
    embed_model: str = "text-embedding-3-small"  # offline fallback: nomic
    embed_dim: int = 1536
    vector_backend: str = "chroma"  # chroma | pgvector
    chroma_dir: str = "data/chroma"
    pg_table: str = "chunks"

    # ── data paths ────────────────────────────────────────────────────────────
    corpus_root: str = "data/corpus"
    market_data_fixture: str = "data/market/quotes.json"
    golden_root: str = "golden"
    audit_log_path: str = "data/audit_log.jsonl"

    # ── cost caps (fail-closed budgets) ───────────────────────────────────────
    max_llm_calls_per_run: int = 8
    max_llm_calls_per_session: int = 64
    max_llm_tokens_per_run: int = 60_000
    max_embed_calls_per_run: int = 32

    # ── gate retries ──────────────────────────────────────────────────────────
    max_self_correct_attempts: int = 2

    @property
    def corpus_dir(self) -> str:
        """Corpus path for the loaded vertical."""
        return f"{self.corpus_root}/{self.vertical_slug}"

    @property
    def vertical_slug(self) -> str:
        """`financial_services_us` → `financial_services` (drops the `_us` suffix)."""
        return (
            self.policy_pack[:-3]
            if self.policy_pack.endswith("_us")
            else self.policy_pack
        )

    @property
    def golden_file(self) -> str:
        return f"{self.golden_root}/golden_{self.vertical_slug}.jsonl"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — read .env once."""
    return Settings()
