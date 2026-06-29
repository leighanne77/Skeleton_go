"""app/models.py — Pydantic v2 schemas + StrEnums for the governed skeleton.

Single source of truth for state/verdict/case-type values (enums) and every
wire/state schema (design.md §3–§4). No separate enums.py — the enums live at the
top of this file by decision (design.md rev3).

Two citation shapes on purpose:
  • Citation       — the STRICT runtime citation (a resolved retrieved chunk):
                     source_id + chunk_id + doc_title + span. Produced once we
                     actually have a retrieval hit, and carried on AnswerEnvelope.
  • GoldenCitation — the LOOSE authoring citation used in golden/*.jsonl: a gold
                     answer is written against (source_id, exact span) BEFORE any
                     retrieval, so chunk_id/doc_title are not yet known. This is the
                     de-facto contract validate_golden has always enforced (its
                     inline mirror's _CitationLite); modelling it here keeps the
                     T0.5 gate CLEAN once it imports the real GoldenRecord.
"""

from __future__ import annotations

import operator
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


# ── Enums (design.md §3) ──────────────────────────────────────────────────────
class Verdict(StrEnum):
    DELIVERED = "delivered"
    ROUTED_FOR_REVIEW = "routed_for_review"


class ClaimVerdict(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


class GateStage(StrEnum):
    GUARDRAILS = "guardrails"
    DETERMINISTIC_FLOOR = "deterministic_floor"
    STAGE2_SUPPORT = "stage2_support"
    RUBRIC_JUDGE = "rubric_judge"


class SensitiveHandling(StrEnum):
    """= the packs' `handling:` field."""

    REDACT = "redact"
    MASK = "mask"
    BLOCK_UNLESS_ENTITLED = "block_unless_entitled"
    BLOCK_IN_DECISION = "block_in_decision"


class CaseBucket(StrEnum):
    """Harness REPORTING bucket (17 case_types → 8) — NOT the type of case_type."""

    HAPPY_PATH = "happy_path"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    OUT_OF_SCOPE = "out_of_scope"
    PROMPT_INJECTION = "prompt_injection"
    PII_LEAK = "pii_leak"
    EMPTY_RETRIEVAL = "empty_retrieval"
    CONFLICTING_SOURCES = "conflicting_sources"
    VERTICAL_NEGATIVE = "vertical_negative"


class FailureReason(StrEnum):
    SCHEMA_INVALID = "schema_invalid"
    NO_CITATION = "no_citation"
    UNGROUNDED = "ungrounded"
    INCOMPLETE = "incomplete"
    RETRIEVAL_EMPTY = "retrieval_empty"
    SUPPORT_FAILED = "support_failed"
    RUBRIC_FAILED = "rubric_failed"
    GUARDRAIL_BLOCK = "guardrail_block"
    INJECTION_DETECTED = "injection_detected"
    PII_IN_OUTPUT = "pii_in_output"
    ATTEMPTS_EXHAUSTED = "attempts_exhausted"
    MODEL_ERROR = "model_error"


# ── Citations ─────────────────────────────────────────────────────────────────
class Citation(BaseModel):
    """Strict runtime citation — resolves to a retrieved chunk."""

    source_id: str
    chunk_id: str
    doc_title: str
    span: str
    char_start: int | None = None
    char_end: int | None = None


class GoldenCitation(BaseModel):
    """Loose authoring citation used in golden/*.jsonl (source_id + exact span)."""

    source_id: str
    span: str = ""
    chunk_id: str | None = None
    doc_title: str | None = None


# ── Claims / retrieval / principal ────────────────────────────────────────────
class Claim(BaseModel):
    text: str  # one atomic, single-sentence claim
    citation: Citation | None = None
    verdict: ClaimVerdict | None = None
    support_score: float | None = None


class Finding(BaseModel):
    """A PROPOSAL from one upstream analyst agent — a grounded, cited claim plus the
    role that produced it. Parallel analysts emit Findings concurrently (merged via a
    reducer on AgentState.findings); the aggregate node unions them into the single
    candidate the gate adjudicates. Analysts PROPOSE; the synthesizer DISPOSES."""

    agent: str  # the analyst role that produced this (e.g. "filings-analyst")
    claim: Claim
    rationale: str = ""  # why this analyst surfaced it (operator-view colour)


class RetrievedChunk(BaseModel):
    chunk_id: str
    source_id: str
    doc_title: str
    text: str
    score: float
    # PRIMARY entitlement gate — deterministic, manifest-driven (proto AND prod).
    # Keyword/classifier detectors are a secondary screen, never the gate.
    entitlement_tags: list[str] = Field(default_factory=list)


class Principal(BaseModel):
    """Stubbed in the demo; real in prod."""

    user_id: str
    entitlements: list[str] = Field(default_factory=list)


# ── Market data (the stock-briefing quote source — design.md §12a) ────────────
class Quote(BaseModel):
    """A delayed/as-of market snapshot. NEVER execution-grade.

    The market-data tool returns this from a keyless local fixture by default and
    from a key-gated delayed adapter when MARKET_DATA_API_KEY is set. The
    no_realtime_quote guardrail requires `as_of` + the delayed label to be shown
    and forbids turning a quote into advice.
    """

    symbol: str
    name: str
    last: float
    as_of: str  # RFC3339; pinned in the fixture so eval stays deterministic
    label: str  # human-facing "delayed — not a live execution price" notice
    grade: str = "delayed_snapshot"
    execution_grade: bool = False
    delay_minutes: int | None = None
    currency: str | None = None
    exchange: str | None = None
    change: float | None = None
    change_pct: float | None = None
    prev_close: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    volume: int | None = None
    market_cap: float | None = None


class FilingRef(BaseModel):
    """A pointer to a recent SEC filing (EDGAR). Metadata + link, not the contents."""

    form: str  # 10-K | 10-Q | 8-K | ...
    filed: str  # filing date (YYYY-MM-DD)
    title: str  # e.g. "MICROSOFT CORP — 10-Q"
    url: str  # link to the primary document on sec.gov


# ── Request / guardrails / gate ───────────────────────────────────────────────
class RunRequest(BaseModel):
    """── INPUT ──"""

    query: str
    principal: Principal
    policy_pack: str  # e.g. "financial_services_us"
    scenario: str | None = None


class GuardrailResult(BaseModel):
    blocked: bool
    actions: list[dict[str, object]] = Field(default_factory=list)
    injection_detected: bool = False


class GateResult(BaseModel):
    stage: GateStage
    passed: bool
    detail: dict[str, object] = Field(default_factory=dict)
    failure_reasons: list[FailureReason] = Field(default_factory=list)


# ── Audit (append-only, hash-chained) ─────────────────────────────────────────
class AuditRecord(BaseModel):
    seq: int
    timestamp: str  # RFC3339 UTC
    event_type: str  # e.g. "retrieval", "guardrail", "gate", "decision"
    payload: dict[str, object] = Field(default_factory=dict)
    entitlement_scope: list[str] = Field(default_factory=list)
    prev_hash: str
    hash: str  # sha256(prev_hash + canonical(payload))


# ── Output / state ────────────────────────────────────────────────────────────
class AnswerEnvelope(BaseModel):
    """── OUTPUT (to UI) ── always an envelope, never a bare string."""

    status: Verdict
    answer_text: str | None = None  # present only if DELIVERED
    citations: list[Citation] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    withhold_reason: list[FailureReason] = Field(default_factory=list)
    audit_ref: str
    quote: Quote | None = None  # the briefing's delayed quote, when present


class AgentState(BaseModel):
    """LangGraph state = tier-2 working memory = audit source."""

    request: RunRequest
    retrieved: list[RetrievedChunk] = Field(default_factory=list)
    # findings carries a REDUCER so the parallel analyst agents can write concurrently
    # (LangGraph fan-out merges their proposals with operator.add — no last-writer-wins).
    findings: Annotated[list[Finding], operator.add] = Field(default_factory=list)
    candidate_answer: str | None = None
    claims: list[Claim] = Field(default_factory=list)
    quote: Quote | None = None
    guardrails: GuardrailResult | None = None
    gate_results: list[GateResult] = Field(default_factory=list)
    verdict: Verdict | None = None
    attempts: int = 0
    audit_events: list[AuditRecord] = Field(default_factory=list)


# ── Golden record (golden/golden_<vertical>.jsonl, one per line) ──────────────
class GoldenRecord(BaseModel):
    id: str
    input: str
    gold_answer: str | None = None
    gold_citations: list[GoldenCitation] = Field(default_factory=list)
    expected_verdict: Verdict
    case_type: str  # open pack vocab; harness buckets via CaseBucket for reporting
    # None=default · []=unentitled · [..]=entitled scopes (the signature flip)
    principal_entitlements: list[str] | None = None
    category: str | None = None  # universal_negative | vertical_negative | happy_path
    notes: str | None = None


# ── Run trace (the Operator-view contract — design.md §5b / ui_build_prompt.md) ─
# A display-only shaping of what the run already produced (graph node statuses, gate
# stages, the entitlement decision, audit-chain rows). The UI recolors a FIXED
# topology from this post-run — never a mocked or animated graph. Canned at T1,
# emitted by the real LangGraph run at T3+.
class NodeStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    WITHHELD = "withheld"
    UNREACHABLE = "unreachable"
    SKIPPED = "skipped"


class NodeTrace(BaseModel):
    id: str  # fixed-topology node id: orchestrator|retriever|market_data|specialist|gate|synthesizer
    status: NodeStatus
    detail: str = ""


class GateStageTrace(BaseModel):
    name: str  # GateStage value, or "entitlement"
    passed: bool
    detail: str = ""


class AuditRow(BaseModel):
    n: int
    hash: str


class RunTrace(BaseModel):
    nodes: list[NodeTrace] = Field(default_factory=list)
    gate_stages: list[GateStageTrace] = Field(default_factory=list)
    entitlement_decision: dict[str, list[str]] = Field(
        default_factory=dict
    )  # {filtered, principal}
    verdict: Verdict | None = None
    route: str | None = None
    audit_rows: list[AuditRow] = Field(default_factory=list)
