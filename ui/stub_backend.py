"""ui/stub_backend.py — canned backend for the T1 UI shell.

Returns a real-shaped `(AnswerEnvelope, RunTrace)` for each demo scenario so the UI
can be built and screenshotted BEFORE the governed graph exists (T3+). The data is
canned but the *shapes* are the real models, and the values are grounded in the
corpus + golden set (MRB filings, the entitlement flip). Swap `run()` for the real
graph at T3 — the UI does not change.

Honesty note: this is explicitly a stub (no retrieval, no gate runs here). The
Operator view renders a canned trace at T1; it becomes the real run trace at T3+.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import get_settings
from app.models import (
    AnswerEnvelope,
    AuditRow,
    Citation,
    FailureReason,
    GateStageTrace,
    NodeStatus,
    NodeTrace,
    Quote,
    RunTrace,
    Verdict,
)
from app.tools import edgar
from app.tools.market_data import SYMBOL_META, TOP_TICKERS, MarketDataTool

# Fixed topology for the BFSI stock-briefing demo (recolored post-run, never animated).
FIXED_TOPOLOGY = [
    "orchestrator",
    "retriever",
    "market_data",
    "specialist",
    "gate",
    "synthesizer",
]

COMPLIANCE_ROUTE = "human:compliance-officer"

# Task-console presets (label → free-text query). The Q&A box resolves to the same ids.
PRESETS: list[tuple[str, str]] = [
    (
        "📊 Brief me on MRB — liquidity risk (10-K)",
        "Summarize the key liquidity and funding risks from Meridian Regional Bancorp's latest 10-K.",
    ),
    (
        "📈 MRB — most recent quarter (10-Q)",
        "Brief me on Meridian Regional Bancorp's most recent quarter from its latest 10-Q.",
    ),
    (
        "🗂️ MRB — latest 8-K event",
        "What material event did Meridian Regional Bancorp disclose in its most recent 8-K?",
    ),
    (
        "⛔ Live price right now to place a trade",
        "Give me MRB's live, real-time execution price right now so I can place a trade for my client.",
    ),
    (
        "🔒 Project Atlas pre-announcement deal terms",
        "What are the Project Atlas pre-announcement deal terms?",
    ),
]

# The flagship ESCALATION example for the demo: a personalized-advice ask an advisor
# is tempted to make → withheld + routed to a human compliance reviewer (Reg BI).
ESCALATION_EXAMPLE = (
    "⚠️ Escalation example — “Should I buy this for my client?”",
    "Given my client's situation, should they buy MRB for their portfolio?",
)
PRESETS.insert(3, ESCALATION_EXAMPLE)


def _mrb_quote() -> Quote:
    """The delayed MRB snapshot — read from the real offline fixture when present."""
    fallback = Quote(
        symbol="MRB",
        name="Meridian Regional Bancorp, Inc.",
        last=48.27,
        as_of="2026-06-16T20:00:00Z",
        label="Delayed snapshot (as-of close 2026-06-16). Not a live execution price.",
        delay_minutes=15,
        currency="USD",
        exchange="NASDAQ",
        change=0.62,
        change_pct=1.30,
        prev_close=47.65,
    )
    try:
        data = json.loads(Path(get_settings().market_data_fixture).read_text())
        raw = data["quotes"]["MRB"]
        return Quote(**{k: v for k, v in raw.items() if k in Quote.model_fields})
    except Exception:  # noqa: BLE001 — stub: any fixture issue falls back to the canned quote
        return fallback


def _nodes(statuses: dict[str, tuple[NodeStatus, str]]) -> list[NodeTrace]:
    """Build the fixed topology, defaulting any unspecified node to DONE."""
    out: list[NodeTrace] = []
    for nid in FIXED_TOPOLOGY:
        status, detail = statuses.get(nid, (NodeStatus.DONE, ""))
        out.append(NodeTrace(id=nid, status=status, detail=detail))
    return out


# ── DELIVERED briefings (grounded in the golden positives) ────────────────────
def _briefing(
    answer: str, citations: list[Citation], top_detail: str
) -> tuple[AnswerEnvelope, RunTrace]:
    env = AnswerEnvelope(
        status=Verdict.DELIVERED,
        answer_text=answer,
        citations=citations,
        withhold_reason=[],
        audit_ref="audit:#108",
        quote=_mrb_quote(),
    )
    trace = RunTrace(
        nodes=_nodes(
            {
                "retriever": (NodeStatus.DONE, top_detail),
                "market_data": (
                    NodeStatus.DONE,
                    "MRB delayed snapshot, as-of 2026-06-16 (labeled)",
                ),
                "specialist": (NodeStatus.DONE, "filings-summarizer"),
            }
        ),
        gate_stages=[
            GateStageTrace(
                name="deterministic_floor",
                passed=True,
                detail="schema ✓ · span-exists ✓ · grounded ✓ · complete ✓",
            ),
            GateStageTrace(
                name="entitlement",
                passed=True,
                detail="public filing — no sensitive class touched",
            ),
            GateStageTrace(
                name="stage2_support",
                passed=True,
                detail="every claim entailed by its cited span",
            ),
            GateStageTrace(
                name="rubric_judge", passed=True, detail="faithfulness ✓ · relevance ✓"
            ),
        ],
        entitlement_decision={"filtered": [], "principal": []},
        verdict=Verdict.DELIVERED,
        route=None,
        audit_rows=[
            AuditRow(n=105, hash="3f9a…"),
            AuditRow(n=106, hash="b7c1…"),
            AuditRow(n=107, hash="e22d…"),
            AuditRow(n=108, hash="91ff…"),
        ],
    )
    return env, trace


def _briefing_10k() -> tuple[AnswerEnvelope, RunTrace]:
    return _briefing(
        "MRB's latest 10-K flags funding concentration as its main liquidity risk: as of December 31, 2025 "
        "uninsured deposits were about 38% of total deposits, and a rapid withdrawal could force asset sales at a "
        "loss or costly borrowing. Management has raised on-balance-sheet liquidity to 14.2% of total assets "
        "(from 11.0%) to mitigate that concentration.",
        [
            Citation(
                source_id="mrb_10k",
                chunk_id="mrb_10k::c3",
                doc_title="Meridian Regional Bancorp — Form 10-K (FY2025) excerpt (synthetic)",
                span="As of December 31, 2025, our uninsured deposits represented approximately 38% of total deposits, and a rapid withdrawal of these deposits could require us to sell securities at a loss or borrow at unfavorable rates.",
            ),
            Citation(
                source_id="mrb_10k",
                chunk_id="mrb_10k::c5",
                doc_title="Meridian Regional Bancorp — Form 10-K (FY2025) excerpt (synthetic)",
                span="Management has increased on-balance-sheet liquidity to 14.2% of total assets, up from 11.0% in the prior year, to mitigate the funding concentration described in Item 1A.",
            ),
        ],
        "3 chunks · top = mrb_10k 0.89",
    )


def _briefing_10q() -> tuple[AnswerEnvelope, RunTrace]:
    return _briefing(
        "In Q1 2026 MRB reported net income of $42.3M ($0.91 per diluted share), up from $38.7M ($0.83) a year "
        "earlier. Credit quality softened modestly: non-performing loans rose to 0.74% of total loans (from 0.61%), "
        "concentrated in office commercial real estate.",
        [
            Citation(
                source_id="mrb_10q",
                chunk_id="mrb_10q::c1",
                doc_title="Meridian Regional Bancorp — Form 10-Q (Q1 2026) excerpt (synthetic)",
                span="For the first quarter of 2026, net income was $42.3 million, or $0.91 per diluted share, compared with $38.7 million, or $0.83 per diluted share, in the first quarter of 2025.",
            ),
            Citation(
                source_id="mrb_10q",
                chunk_id="mrb_10q::c2",
                doc_title="Meridian Regional Bancorp — Form 10-Q (Q1 2026) excerpt (synthetic)",
                span="Non-performing loans were 0.74% of total loans at March 31, 2026, up from 0.61% a year earlier, concentrated in office commercial real estate.",
            ),
        ],
        "3 chunks · top = mrb_10q 0.87",
    )


def _briefing_8k() -> tuple[AnswerEnvelope, RunTrace]:
    return _briefing(
        "In its 8-K dated June 2, 2026, MRB reported that it completed its previously announced acquisition of "
        "Cedar Valley Savings, F.S.B., adding about $1.2 billion in total assets and 14 branches across the "
        "upper-Midwest market.",
        [
            Citation(
                source_id="mrb_8k",
                chunk_id="mrb_8k::c1",
                doc_title="Meridian Regional Bancorp — Form 8-K (Jun 2026) excerpt (synthetic)",
                span="On June 2, 2026, Meridian Regional Bancorp, Inc. completed its previously announced acquisition of Cedar Valley Savings, F.S.B., adding approximately $1.2 billion in total assets and 14 branch locations across the upper-Midwest market.",
            ),
        ],
        "2 chunks · top = mrb_8k 0.91",
    )


# ── ROUTED scenarios ──────────────────────────────────────────────────────────
def _routed(
    failed_stage: str,
    stage_detail: str,
    reason: FailureReason,
    filtered: list[str],
    principal: list[str],
    market_detail: str = "",
) -> tuple[AnswerEnvelope, RunTrace]:
    env = AnswerEnvelope(
        status=Verdict.ROUTED_FOR_REVIEW,
        answer_text=None,
        citations=[],
        withhold_reason=[reason],
        audit_ref="audit:#108",
        quote=None,
    )
    gate_stages = [
        GateStageTrace(
            name="deterministic_floor",
            passed=True,
            detail="schema ✓ · span-exists ✓ · grounded ✓",
        )
    ]
    gate_stages.append(
        GateStageTrace(name=failed_stage, passed=False, detail=stage_detail)
    )
    trace = RunTrace(
        nodes=_nodes(
            {
                "market_data": (NodeStatus.DONE, market_detail)
                if market_detail
                else (NodeStatus.DONE, ""),
                "gate": (NodeStatus.WITHHELD, stage_detail),
                "synthesizer": (NodeStatus.UNREACHABLE, "gate did not pass"),
            }
        ),
        gate_stages=gate_stages,
        entitlement_decision={"filtered": filtered, "principal": principal},
        verdict=Verdict.ROUTED_FOR_REVIEW,
        route=COMPLIANCE_ROUTE,
        audit_rows=[
            AuditRow(n=105, hash="3f9a…"),
            AuditRow(n=106, hash="b7c1…"),
            AuditRow(n=107, hash="c40e…"),
        ],
    )
    return env, trace


def _realtime_quote() -> tuple[AnswerEnvelope, RunTrace]:
    return _routed(
        failed_stage="guardrail:no_realtime_quote",
        stage_detail="execution-grade / trade-now requested — the tool serves a delayed snapshot only",
        reason=FailureReason.GUARDRAIL_BLOCK,
        filtered=[],
        principal=[],
        market_detail="MRB delayed snapshot only (as-of 2026-06-16); execution-grade requested",
    )


def _advice() -> tuple[AnswerEnvelope, RunTrace]:
    return _routed(
        failed_stage="guardrail:no_personalized_advice",
        stage_detail="personalized buy/sell recommendation — Reg BI suitability, not a research briefing",
        reason=FailureReason.GUARDRAIL_BLOCK,
        filtered=[],
        principal=[],
    )


def _out_of_scope() -> tuple[AnswerEnvelope, RunTrace]:
    return _routed(
        failed_stage="deterministic_floor:empty_retrieval",
        stage_detail="no filing in the corpus covers this issuer/question — nothing to ground a briefing on",
        reason=FailureReason.RETRIEVAL_EMPTY,
        filtered=[],
        principal=[],
    )


def _mnpi(entitlements: list[str]) -> tuple[AnswerEnvelope, RunTrace]:
    """The money-shot flip: same query, routes for [] and delivers for [mnpi_cleared]."""
    if "mnpi_cleared" in entitlements:
        env = AnswerEnvelope(
            status=Verdict.DELIVERED,
            answer_text="Project Atlas (wall-crossed): proposed all-cash tender at $62.00/share, ~28% premium to the "
            "undisturbed price; signing targeted for the week of June 22, pending board approval. Handle under "
            "information-barrier controls — not for distribution.",
            citations=[
                Citation(
                    source_id="mnpi_dealbook",
                    chunk_id="mnpi_dealbook::c2",
                    doc_title="Project Atlas — Deal Book (restricted, MNPI)",
                    span="Proposed consideration: $62.00 per share in cash, a premium of approximately 28% to the undisturbed share price.",
                )
            ],
            withhold_reason=[],
            audit_ref="audit:#108",
            quote=None,
        )
        trace = RunTrace(
            nodes=_nodes(
                {
                    "retriever": (
                        NodeStatus.DONE,
                        "1 chunk · top = mnpi_dealbook 0.88",
                    ),
                    "specialist": (NodeStatus.DONE, "compliance"),
                }
            ),
            gate_stages=[
                GateStageTrace(
                    name="deterministic_floor",
                    passed=True,
                    detail="schema ✓ · span-exists ✓ · grounded ✓",
                ),
                GateStageTrace(
                    name="entitlement",
                    passed=True,
                    detail="mnpi requires mnpi_cleared — principal holds it ✓",
                ),
                GateStageTrace(
                    name="rubric_judge",
                    passed=True,
                    detail="faithfulness ✓ · relevance ✓",
                ),
            ],
            entitlement_decision={"filtered": [], "principal": ["mnpi_cleared"]},
            verdict=Verdict.DELIVERED,
            route=None,
            audit_rows=[
                AuditRow(n=106, hash="b7c1…"),
                AuditRow(n=107, hash="d51a…"),
                AuditRow(n=108, hash="91ff…"),
            ],
        )
        return env, trace
    return _routed(
        failed_stage="entitlement",
        stage_detail="mnpi requires mnpi_cleared — principal has none",
        reason=FailureReason.GUARDRAIL_BLOCK,
        filtered=["mnpi"],
        principal=[],
        market_detail="",
    )


# ── live-quote example (ticker-agnostic; any of the top 50, MSFT etc.) ────────
def _extract_ticker(query: str) -> str | None:
    m = re.search(r"\(([A-Z]{1,5})\)", query)
    if m and m.group(1) in SYMBOL_META:
        return m.group(1)
    up = query.upper()
    for t in TOP_TICKERS:
        if re.search(rf"\b{t}\b", up):
            return t
    return None


def _ticker_quote(query: str) -> tuple[AnswerEnvelope, RunTrace]:
    ticker = _extract_ticker(query)
    quote = MarketDataTool().try_quote(ticker) if ticker else None
    name = SYMBOL_META.get(ticker or "", (ticker or "the stock", ""))[0]

    if quote is None:
        # offline + not in the fixture subset → honest data-availability note (not a
        # governance withhold). Enable USE_REAL_MARKET_DATA for the full top-50 live.
        env = AnswerEnvelope(
            status=Verdict.DELIVERED,
            answer_text=(
                f"Live market data isn't enabled for {name} in this offline session. "
                "Set `USE_REAL_MARKET_DATA=true` + a key to pull any of the top-50 tickers "
                "live (Alpha Vantage); the offline fixture ships a curated subset."
            ),
            citations=[],
            audit_ref="audit:#112",
            quote=None,
        )
        trace = RunTrace(
            nodes=_nodes(
                {
                    "retriever": (NodeStatus.SKIPPED, "quote-only request"),
                    "market_data": (
                        NodeStatus.SKIPPED,
                        f"{ticker or '?'} not in offline fixture",
                    ),
                    "specialist": (NodeStatus.SKIPPED, "quote-only briefing"),
                }
            ),
            gate_stages=[
                GateStageTrace(
                    name="deterministic_floor",
                    passed=True,
                    detail="no claims to ground",
                )
            ],
            entitlement_decision={"filtered": [], "principal": []},
            verdict=Verdict.DELIVERED,
            route=None,
            audit_rows=[AuditRow(n=110, hash="a1b2…")],
        )
        return env, trace

    src = {
        "realtime": "live real-time quote (Finnhub)",
        "delayed_eod": "live delayed quote (Alpha Vantage)",
    }.get(quote.grade, "offline fixture snapshot")
    answer = (
        f"Latest available quote for {name} ({quote.symbol}, {quote.exchange or 'US'}), "
        f"as-of {quote.as_of} and clearly labeled."
    )

    # SEC filings are pulled alongside the price (EDGAR, when live data is enabled).
    citations: list[Citation] = []
    filings = edgar.get_recent_filings(quote.symbol)
    if filings:
        answer += "\n\n**Recent SEC filings (EDGAR):**\n" + "\n".join(
            f"- **{f.form}** · {f.filed} — [{f.title}]({f.url})" for f in filings
        )
        # extractive summary of the latest filing — each highlight is a real span
        chosen, excerpts = edgar.summarize_latest(quote.symbol, query)
        if chosen and excerpts:
            answer += (
                f"\n\n**Key information from the latest {chosen.form} "
                f"({chosen.filed}) — cited below:**"
            )
            citations = [
                Citation(
                    source_id=f"{quote.symbol}_{chosen.form}",
                    chunk_id=f"edgar::{i}",
                    doc_title=f"{chosen.title} ({chosen.filed})",
                    span=ex,
                )
                for i, ex in enumerate(excerpts)
            ]
        retr_node = (
            NodeStatus.DONE,
            f"EDGAR: {len(filings)} filings; {len(citations)} cited excerpts from {quote.symbol}",
        )
    else:
        answer += (
            "\n\n_Recent SEC filings: enable live data (`USE_REAL_MARKET_DATA`) to pull this "
            "issuer's 10-K / 10-Q / 8-K from SEC EDGAR alongside the quote._"
        )
        retr_node = (
            NodeStatus.SKIPPED,
            f"EDGAR off — no live filings for {quote.symbol}",
        )

    env = AnswerEnvelope(
        status=Verdict.DELIVERED,
        answer_text=answer,
        citations=citations,
        withhold_reason=[],
        audit_ref="audit:#112",
        quote=quote,
    )
    trace = RunTrace(
        nodes=_nodes(
            {
                "retriever": retr_node,
                "market_data": (NodeStatus.DONE, f"{quote.symbol} quote — {src}"),
                "specialist": (NodeStatus.SKIPPED, "quote + filing-list briefing"),
            }
        ),
        gate_stages=[
            GateStageTrace(
                name="deterministic_floor",
                passed=True,
                detail="quote labeled as-of ✓ · no uncited filing claims ✓",
            ),
            GateStageTrace(
                name="no_realtime_quote",
                passed=True,
                detail="informational as-of quote · not execution-grade ✓",
            ),
        ],
        entitlement_decision={"filtered": [], "principal": []},
        verdict=Verdict.DELIVERED,
        route=None,
        audit_rows=[
            AuditRow(n=110, hash="a1b2…"),
            AuditRow(n=111, hash="c3d4…"),
            AuditRow(n=112, hash="e5f6…"),
        ],
    )
    return env, trace


# ── resolver ──────────────────────────────────────────────────────────────────
def _resolve(query: str) -> str:
    q = query.lower()
    if "project atlas" in q or "deal terms" in q or "mnpi" in q:
        return "mnpi"
    if any(
        k in q
        for k in (
            "real-time",
            "live",
            "execution price",
            "place a trade",
            "right now",
            "to the second",
        )
    ):
        return "realtime_quote"
    if any(
        k in q
        for k in (
            "should i buy",
            "should they buy",
            "recommend",
            "for my portfolio",
            "for their portfolio",
        )
    ):
        return "advice"
    if _extract_ticker(query):  # a top-50 ticker quote request
        return "ticker_quote"
    if any(k in q for k in ("10-q", "10q", "quarter", "earnings")):
        return "briefing_10q"
    if any(k in q for k in ("8-k", "8k", "material event", "acquisition")):
        return "briefing_8k"
    if any(
        k in q
        for k in (
            "10-k",
            "10k",
            "liquidity",
            "funding",
            "risk",
            "brief",
            "mrb",
            "meridian",
        )
    ):
        return "briefing_10k"
    return "out_of_scope"


def run(query: str, entitlements: list[str]) -> tuple[AnswerEnvelope, RunTrace, str]:
    """Stub entrypoint. Returns (envelope, trace, scenario_id). Swap for the real graph at T3."""
    scenario = _resolve(query)
    if scenario == "mnpi":
        env, trace = _mnpi(entitlements)
    elif scenario == "ticker_quote":
        env, trace = _ticker_quote(query)
    elif scenario == "realtime_quote":
        env, trace = _realtime_quote()
    elif scenario == "advice":
        env, trace = _advice()
    elif scenario == "briefing_10q":
        env, trace = _briefing_10q()
    elif scenario == "briefing_8k":
        env, trace = _briefing_8k()
    elif scenario == "briefing_10k":
        env, trace = _briefing_10k()
    else:
        env, trace = _out_of_scope()
    return env, trace, scenario
