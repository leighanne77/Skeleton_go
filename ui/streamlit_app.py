"""ui/app.py — the governed stock-briefing UI (Streamlit). Built FIRST (T1).

Option B (hybrid): a structured task console + a scoped Q&A box — NOT a bare chatbot.
Two views of the SAME run via one toggle:
  • Customer view (default) — plain language; the two never-blurred states
    (DELIVERED / ROUTED FOR HUMAN REVIEW); first-class citations; a delayed quote
    block; collapsible "how this was checked" + "audit".
  • Operator view — a glass box: the fixed orchestration graph recolored by the run
    trace, the gate stages, the entitlement decision, and the audit chain.

At T1 the backend is `ui.stub_backend` (canned, real-shaped). Swap `run()` for the
real governed graph at T3+ — this file does not change.

Launch:  streamlit run ui/streamlit_app.py   (or: python run.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import AnswerEnvelope, NodeStatus, RunTrace, Verdict  # noqa: E402
from load_pack import load_pack  # noqa: E402
from ui import stub_backend  # noqa: E402

POLICY_PACK = "financial_services_us"

# ── node status → graphviz fill ──────────────────────────────────────────────
_FILL = {
    NodeStatus.DONE: "#cde5cd",
    NodeStatus.WITHHELD: "#ffe0a3",
    NodeStatus.FAILED: "#f5b7b1",
    NodeStatus.UNREACHABLE: "#dcdcdc",
    NodeStatus.PENDING: "#ffffff",
    NodeStatus.SKIPPED: "#ececec",
}
_LABELS = {
    "orchestrator": "Orchestrator",
    "retriever": "Retriever (tool)",
    "market_data": "Market-data (tool)",
    "specialist": "Filings specialist",
    "gate": "Control-plane GATE",
    "synthesizer": "Synthesizer",
}
_EDGES = [
    ("orchestrator", "retriever"),
    ("orchestrator", "market_data"),
    ("retriever", "specialist"),
    ("specialist", "gate"),
    ("market_data", "gate"),
    ("gate", "synthesizer"),
]


@st.cache_data(show_spinner=False)
def _pack_entitlements() -> list[str]:
    pack = load_pack(POLICY_PACK)
    return [e["id"] for e in pack.get("entitlements", [])]


def _badge(status: NodeStatus) -> str:
    return {
        NodeStatus.DONE: "✓",
        NodeStatus.WITHHELD: "⤴",
        NodeStatus.FAILED: "✗",
        NodeStatus.UNREACHABLE: "⃠",
        NodeStatus.PENDING: "·",
        NodeStatus.SKIPPED: "–",
    }[status]


def _dot(trace: RunTrace) -> str:
    by_id = {n.id: n for n in trace.nodes}
    lines = [
        "digraph G {",
        "  rankdir=LR;",
        '  node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=11];',
    ]
    for nid in stub_backend.FIXED_TOPOLOGY:
        n = by_id.get(nid)
        status = n.status if n else NodeStatus.PENDING
        label = _LABELS[nid] + (f"\\n{_badge(status)} {status.value}" if n else "")
        lines.append(f'  {nid} [label="{label}" fillcolor="{_FILL[status]}"];')
    for a, b in _EDGES:
        lines.append(f"  {a} -> {b};")
    lines.append("}")
    return "\n".join(lines)


# ── Customer view ─────────────────────────────────────────────────────────────
def _render_customer(env: AnswerEnvelope) -> None:
    if env.status == Verdict.DELIVERED:
        st.success("✓  DELIVERED", icon="✅")
        if env.quote is not None:
            q = env.quote
            c1, c2, c3 = st.columns([1, 1, 3])
            c1.metric(
                f"{q.symbol}",
                f"${q.last:,.2f}",
                f"{q.change_pct:+.2f}%" if q.change_pct is not None else None,
            )
            c2.caption(f"{q.exchange or ''} · {q.currency or ''}")
            c3.warning(f"🕒 {q.label}", icon="🕒")
        st.markdown(f"#### Briefing\n{env.answer_text}")
        if env.citations:
            st.markdown("**Sources**")
            for i, c in enumerate(env.citations, 1):
                with st.expander(f"▸ Source {i}: {c.doc_title}"):
                    st.markdown(f"> {c.span}")
                    st.caption(f"`{c.source_id}` · chunk `{c.chunk_id}`")
    else:
        st.warning("⤴  ROUTED FOR HUMAN REVIEW", icon="⚠️")
        st.markdown(
            "This needs a cleared reviewer. It's been **sent to your compliance team** "
            "and was **not answered here** — by design, an uncertain or out-of-bounds "
            "request is withheld rather than guessed."
        )
        reasons = ", ".join(r.value for r in env.withhold_reason) or "policy gate"
        st.caption(f"Why: **{reasons}**")

    with st.expander("🔎 How this was checked"):
        if env.status == Verdict.DELIVERED:
            st.markdown(
                "- Retrieved the controlling filing spans and **grounded every claim** in them\n"
                "- An **independent gate** confirmed each claim is supported by its citation\n"
                "- Checked your **entitlements** — nothing here required a clearance you don't hold\n"
                "- The delayed quote is **labeled as-of** and is never presented as a live price"
            )
        else:
            st.markdown(
                "- The **control-plane gate** withheld this before it could reach you\n"
                "- A failed/uncertain/out-of-bounds answer is **structurally unable** to be delivered\n"
                "- It was routed to a human reviewer and the decision was **audited**"
            )

    with st.expander("🧾 View audit (hash-chained)"):
        st.caption(f"Audit reference: `{env.audit_ref}`")
        st.caption(
            "Append-only, tamper-evident. Full chain shown in the Operator view."
        )


# ── Operator view ─────────────────────────────────────────────────────────────
def _render_operator(
    env: AnswerEnvelope, trace: RunTrace, query: str, entitlements: list[str]
) -> None:
    st.caption(f'RUN  q="{query}"   principal={entitlements or "[]"}')
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


# ── app ───────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="Northwind — Stock Briefing", page_icon="📊", layout="wide"
    )

    head_l, head_r = st.columns([3, 1])
    head_l.title("📊 Stock Briefing — Northwind Securities")
    mode = head_r.radio(
        "View", ["Customer", "Operator"], horizontal=True, label_visibility="collapsed"
    )

    entitlements: list[str] = st.session_state.get("entitlements", [])
    scope = (
        ", ".join(entitlements) if entitlements else "none (standard advisor access)"
    )
    st.info(
        f"**Signed in as Dana — an authorized Northwind advisor.** Your access scopes what these "
        f"agents can retrieve and answer.  **Your access:** {scope}.",
        icon="🪪",
    )

    with st.sidebar:
        st.header("Get up to speed on a stock")
        labels = [lbl for lbl, _ in stub_backend.PRESETS]
        pick = st.selectbox("Pick a task", labels, index=0)
        preset_q = dict(stub_backend.PRESETS)[pick]
        typed = st.text_input(
            "…or ask your own",
            placeholder="e.g. Summarize MRB's latest 10-K liquidity risk",
        )
        st.divider()
        st.caption("Demo control — principal entitlements")
        st.multiselect(
            "Entitlements (flip to see the gate change)",
            options=_pack_entitlements(),
            default=entitlements,
            key="entitlements",
            help="Dana the advisor holds none by default. Add mnpi_cleared to see the same MNPI query deliver instead of route.",
        )
        run_clicked = st.button("▶  Run briefing", type="primary", width="stretch")

    if run_clicked:
        query = typed.strip() or preset_q
        env, trace, scenario = stub_backend.run(
            query, st.session_state.get("entitlements", [])
        )
        st.session_state["result"] = (env, trace, query, scenario)

    if "result" not in st.session_state:
        st.markdown(
            "👈 Pick a task or ask a question in the sidebar, then **Run briefing**.\n\n"
            "Every answer is **gated before it reaches you**: it's either **DELIVERED** with "
            "citations, or **ROUTED FOR HUMAN REVIEW** — never a confident guess."
        )
        return

    env, trace, query, _scenario = st.session_state["result"]
    if mode == "Customer":
        _render_customer(env)
    else:
        _render_operator(env, trace, query, st.session_state.get("entitlements", []))


main()
