"""ui/streamlit_app.py — the governed stock-briefing UI (Streamlit, Munich-Re-styled).

Two surfaces of the SAME run, bridged by a gear icon:
  • Advisor briefing (default) — the branded product surface for Dana, a
    wealth-management advisor. Plain language; the two never-blurred states
    (DELIVERED / ROUTED FOR HUMAN REVIEW); a delayed quote card; first-class
    citations. Login is just the advisor — no governance controls in her face.
  • "Show my work" (⚙) — the glass box for the technical reviewer: the fixed
    orchestration graph recolored by the run trace, the gate stages, the
    entitlement decision, the audit chain, and the reviewer entitlement toggle
    (flip mnpi_cleared → watch the same query deliver instead of route).

Backend is ui.stub_backend (canned, real-shaped) at T1; swap run() for the real
governed graph at T3+ — these surfaces do not change. Launch: python run.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import AnswerEnvelope, NodeStatus, RunTrace, Verdict  # noqa: E402
from app.tools.market_data import SYMBOL_META, TOP_TICKERS  # noqa: E402
from load_pack import load_pack  # noqa: E402
from ui import stub_backend, theme  # noqa: E402

POLICY_PACK = "financial_services_us"
ADVISOR_IDENTITY = "Dana &nbsp;·&nbsp; <b>Wealth-Management Advisor</b>"

# ── graph node fills (brand-colored) ─────────────────────────────────────────
_FILL = {
    NodeStatus.DONE: theme.PALETTE["delivered_bg"],
    NodeStatus.WITHHELD: theme.PALETTE["routed_bg"],
    NodeStatus.FAILED: "#F5D6D2",
    NodeStatus.UNREACHABLE: "#ECEFF2",
    NodeStatus.PENDING: "#FFFFFF",
    NodeStatus.SKIPPED: "#ECEFF2",
}
_LABELS = {
    "orchestrator": "Orchestrator",
    "retriever": "Retriever (tool)",
    "market_data": "Market-data (tool)",
    "filings-analyst": "Filings analyst",
    "market-context": "Market-context analyst",
    "aggregate": "Aggregate findings",
    "gate": "Control-plane GATE",
    "synthesizer": "Synthesizer",
}
_EDGES = [
    ("orchestrator", "retriever"),
    ("orchestrator", "market_data"),
    # parallel fan-out: two analyst agents run concurrently off retrieval
    ("retriever", "filings-analyst"),
    ("retriever", "market-context"),
    # fan-in: aggregate the analysts' findings + the market-data tool
    ("filings-analyst", "aggregate"),
    ("market-context", "aggregate"),
    ("market_data", "aggregate"),
    ("aggregate", "gate"),
    ("gate", "synthesizer"),
]
_BADGE = {
    NodeStatus.DONE: "✓",
    NodeStatus.WITHHELD: "⤴",
    NodeStatus.FAILED: "✗",
    NodeStatus.UNREACHABLE: "⃠",
    NodeStatus.PENDING: "·",
    NodeStatus.SKIPPED: "–",
}


@st.cache_data(show_spinner=False)
def _pack_entitlements() -> list[str]:
    return [e["id"] for e in load_pack(POLICY_PACK).get("entitlements", [])]


def _run(query: str, entitlements: list[str]) -> tuple[AnswerEnvelope, RunTrace, str]:
    """Dispatch to the canned demo backend or the real LangGraph graph."""
    if st.session_state.get("engine") == "live":
        from app.orchestrator import run as graph_run

        env, trace = graph_run(query, entitlements)
        return env, trace, "live"
    return stub_backend.run(query, entitlements)


def _dot(trace: RunTrace) -> str:
    navy = theme.PALETTE["navy"]
    by_id = {n.id: n for n in trace.nodes}
    out = [
        "digraph G {",
        "  rankdir=LR; bgcolor=transparent;",
        f'  node [shape=box style="rounded,filled" fontname="Helvetica" '
        f'fontsize=11 color="{navy}" penwidth=1.2];',
        '  edge [color="#9AA7B2" penwidth=1.1];',
    ]
    for nid in stub_backend.FIXED_TOPOLOGY:
        n = by_id.get(nid)
        status = n.status if n else NodeStatus.PENDING
        label = _LABELS[nid] + (f"\\n{_BADGE[status]} {status.value}" if n else "")
        out.append(f'  "{nid}" [label="{label}" fillcolor="{_FILL[status]}"];')
    out += [f'  "{a}" -> "{b}";' for a, b in _EDGES]
    out.append("}")
    return "\n".join(out)


# ── ADVISOR surface ───────────────────────────────────────────────────────────
def render_advisor() -> None:
    theme.header_band(ADVISOR_IDENTITY)

    st.markdown("# Stock Briefing")
    st.markdown(
        '<p class="nw-hero-sub">Get up to speed on a stock in minutes — '
        "a time-stamped quote and the key points from recent SEC filings, "
        "every fact linked to its source.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    ic, bc, gc = st.columns([5, 2, 1], vertical_alignment="center")
    typed = ic.text_input(
        "Type a question",
        placeholder="Type your own question — e.g. Summarize MRB's latest 10-K liquidity risk",
        key="q",
    )
    quick_none = "— none —"
    quick = ic.selectbox(
        "…or run a demo scenario (synthetic MRB filings + governance shots)",
        [quick_none] + [lbl for lbl, _ in stub_backend.PRESETS],
        key="quick",
    )
    ticker_none = "— none —"
    ticker_opts = [ticker_none] + [f"{t} · {SYMBOL_META[t][0]}" for t in TOP_TICKERS]
    picked = ic.selectbox(
        "…or pick a LIVE stock — top 50 US (real quote + recent SEC filings)",
        ticker_opts,
        key="ticker",
    )
    run = bc.button(
        "Run briefing  ›", type="primary", width="stretch", key="run_advisor"
    )
    with gc:
        if st.button(
            "⚙",
            key="audit_gear",
            help="Show my work — the orchestration graph, the gate stages, and the audit chain",
        ):
            st.session_state.surface = "operator"
            st.rerun()
    ic.caption(
        "Priority: your typed question → the live stock (if picked) → the demo scenario. "
        "A live stock fetches its SEC filings from EDGAR — that can take a few seconds."
    )

    if run:
        query = None
        if typed.strip():
            query = typed.strip()
        elif picked != ticker_none:
            query = f"Pull the latest quote for ({picked.split(' · ')[0]})."
        elif quick != quick_none:
            query = dict(stub_backend.PRESETS)[quick]

        if query is None:
            st.warning("Type a question, pick a live stock, or choose a demo scenario.")
        else:
            with st.spinner("Pulling the quote and recent SEC filings…"):
                env, trace, scenario = _run(
                    query, st.session_state.get("entitlements", [])
                )
            st.session_state.result = (env, trace, query, scenario)

    result = st.session_state.get("result")
    if not result:
        st.info(
            "Pick a quick task or type a question, then **Run briefing**. "
            "Every answer is **gated before it reaches you** — delivered with "
            "citations, or routed for human review. Never a confident guess.",
            icon="📊",
        )
    else:
        env, _trace, _query, _scenario = result
        _render_answer(env)


def _render_answer(env: AnswerEnvelope) -> None:
    theme.verdict_banner(env.status)

    if env.status == Verdict.DELIVERED:
        if env.quote is not None:
            q = env.quote
            st.markdown(
                theme.quote_card_html(
                    q.symbol, q.name, q.exchange or "", q.last, q.change_pct, q.label
                ),
                unsafe_allow_html=True,
            )
        st.markdown("#### Briefing")
        st.markdown(env.answer_text or "")
        if env.citations:
            st.markdown("##### Sources")
            for i, c in enumerate(env.citations, 1):
                with st.expander(f"Source {i} — {c.doc_title}"):
                    st.markdown(f"> {c.span}")
                    st.caption(f"`{c.source_id}` · chunk `{c.chunk_id}`")
    else:
        st.markdown(
            "This needs a cleared reviewer. It's been **sent to your compliance team** "
            "and was **not answered here** — by design, an uncertain or out-of-bounds "
            "request is withheld rather than guessed."
        )
        reasons = ", ".join(r.value for r in env.withhold_reason) or "policy gate"
        st.caption(
            f"Why: **{reasons}**  ·  see the gate decision under ⚙ Show my work."
        )

    with st.expander("How this was checked"):
        if env.status == Verdict.DELIVERED:
            st.markdown(
                "- Retrieved the controlling filing spans and **grounded every claim** in them\n"
                "- An **independent gate** confirmed each claim is supported by its citation\n"
                "- Checked your **entitlements** — nothing here needed a clearance you don't hold\n"
                "- The quote is **labeled as-of** and is never shown as a live price"
            )
        else:
            st.markdown(
                "- The **control-plane gate** withheld this before it could reach you\n"
                "- A failed / uncertain / out-of-bounds answer is **structurally unable** to be delivered\n"
                "- It was routed to a human reviewer and the decision was **audited**"
            )
    st.caption(
        f"Audit reference `{env.audit_ref}` · tamper-evident chain in Show my work (⚙ below)."
    )


# ── OPERATOR ("Show my work") surface ─────────────────────────────────────────
def render_operator() -> None:
    theme.header_band(
        ADVISOR_IDENTITY
        + " &nbsp;·&nbsp; <span style='color:#00B2A9'>operator view</span>"
    )

    top_l, top_r = st.columns([8, 2])
    top_l.markdown("# Show my work")
    top_l.markdown(
        '<p class="nw-hero-sub">The same run, opened up — the orchestration graph, '
        "the control-plane gate, the entitlement decision, and the audit chain.</p>",
        unsafe_allow_html=True,
    )
    top_r.write("")
    if top_r.button("‹  Back to briefing", key="to_advisor"):
        st.session_state.surface = "advisor"
        st.rerun()

    # engine toggle — Demo (scripted) vs the real LangGraph graph
    with st.container(border=True):
        st.markdown("**Run engine**")
        st.radio(
            "engine",
            ["demo", "live"],
            format_func=lambda x: (
                "Demo — scripted scenarios (guardrail money shots)"
                if x == "demo"
                else "Live graph — real LangGraph run (real RunTrace)"
            ),
            horizontal=True,
            key="engine",
            label_visibility="collapsed",
        )
        if st.session_state.get("engine") == "live":
            st.caption(
                "Live = the real `app.orchestrator` graph: orchestrator → retriever "
                "(entitlement-filtered) + market-data → **two parallel analyst agents** "
                "(filings-analyst ‖ market-context, real LangGraph fan-out) → aggregate → "
                "gate → synthesizer. The gate runs the full floor → support → rubric "
                "cascade; stage-2 support is a cross-family judge (OpenAI) when keyed, "
                "deterministic otherwise. One synthesizer, reachable only on the pass edge."
            )

    result = st.session_state.get("result")
    if not result:
        st.info(
            "Run a briefing first (‹ Back to briefing), then return here to see how it was produced."
        )
        return

    env, trace, query, _scenario = result

    # reviewer control — the entitlement flip lives here, not on the advisor surface
    with st.container(border=True):
        st.markdown("**Reviewer control — principal entitlements**")
        ent = st.multiselect(
            "Flip an entitlement and re-run to watch the gate change",
            options=_pack_entitlements(),
            default=st.session_state.get("entitlements", []),
            key="op_entitlements",
        )
        if st.button("Re-run with these entitlements", key="rerun_op"):
            st.session_state.entitlements = ent
            new_env, new_trace, scenario = _run(query, ent)
            st.session_state.result = (new_env, new_trace, query, scenario)
            st.rerun()

    st.caption(
        f'RUN  q="{query}"   principal={st.session_state.get("entitlements", []) or "[]"}'
    )
    st.graphviz_chart(_dot(trace), width="stretch")

    st.markdown("**Control-plane gate**")
    for s in trace.gate_stages:
        mark = "✓" if s.passed else "✗"
        (st.success if s.passed else st.error)(f"{mark}  {s.name} — {s.detail}")

    ed = trace.entitlement_decision
    st.markdown("**Entitlement decision**")
    st.code(
        f"principal = {ed.get('principal', [])}\nfiltered  = {ed.get('filtered', [])}",
        language="text",
    )

    verdict = trace.verdict.value if trace.verdict else "—"
    st.markdown(
        f"**Verdict:** `{verdict}`"
        + (f"   ·   **route:** `{trace.route}`" if trace.route else "")
    )

    st.markdown("**Audit chain**")
    chain = "  ◀  ".join(f"#{r.n} {r.hash}" for r in trace.audit_rows)
    st.code(f"{chain}     verify ✓", language="text")


# ── WELCOME screen ────────────────────────────────────────────────────────────
def render_welcome() -> None:
    theme.header_band(ADVISOR_IDENTITY)
    st.markdown(
        """
        <div class="nw-welcome">
          <h2>Stock Briefing</h2>
          <p class="lead">Get up to speed on a stock in minutes — before a client conversation.</p>
          <p>📈 <b>Time-stamped quote</b> &nbsp;·&nbsp; 📄 <b>key points from recent SEC filings</b>
          &nbsp;·&nbsp; 🔗 <b>every fact linked to its source</b>.</p>
          <p>✅ Delivered with citations, or ⤴ routed for human review — never a guess. &nbsp;
          🛡️ No advice, no non-public info, no stale price as live. &nbsp; 🧾 Every decision audited.</p>
          <p class="lead">Useful for you. Defensible for compliance.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([2, 3, 2])
    with mid:
        if st.button(
            "Enter the Stock Briefing  ›", type="primary", width="stretch", key="enter"
        ):
            st.session_state.entered = True
            st.rerun()


# ── app ───────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="Northwind — Stock Briefing", page_icon="📊", layout="wide"
    )
    theme.inject_css()
    ss = st.session_state
    ss.setdefault("entered", False)
    ss.setdefault("surface", "advisor")
    ss.setdefault("entitlements", [])
    ss.setdefault("result", None)

    if not ss.entered:
        render_welcome()
    elif ss.surface == "operator":
        render_operator()
    else:
        render_advisor()


main()
