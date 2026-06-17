# Prototype Spec — Advisor Stock-Briefing (Wealth Management / BFSI) — v2
*The **scenario spec** for the AI Prototype Challenge (Finance track). It states the business problem, the user, the solution, the governed flow, the acceptance criteria, and the live-demo script for **one** chosen scenario — the advisor stock-briefing. It does not restate the skeleton; it points to the canonical doc set and names only what this scenario adds. v2 syncs the data/build facts and adds the §15 roadmap. Supersedes v1 (kept for history).*

> **Doc-set position.** `CLAUDE.md` = constitution · `requirements.md` = WHAT/WHY (EARS) · `design.md` = HOW (architecture; the stock-briefing overlay is **§12 / §12a**, persona at rev9) · `tasks.md` = build steps (the tool is **T4b**). This file is the **scenario brief** that ties them to the challenge prompt. **Loaded pack:** `policy_pack = "financial_services_us"` (v2.2).

---

## 1 · The challenge (verbatim)
> **Finance:** A wealth management firm wants a solution that helps advisors quickly get up to speed on a stock — **fetching current quote data and summarizing key information from recent SEC filings.**

We deliver this as a **governed** advisor tool: the briefing is the positive path, and the *same* control plane that makes our skeleton defensible (guardrails + eval-against-goal + tamper-evident audit) bounds it — so a wealth-management firm can put it in front of advisors without it ever giving advice, leaking MNPI, or passing a stale price off as live.

## 2 · Problem · user · value
- **User (primary):** **Dana, a wealth-management advisor** prepping for a client conversation — needs to get up to speed on a ticker in minutes, not an afternoon of reading filings. Not a governance specialist; the surface stays plain-language and the control plane rides underneath.
- **Buyer / accountable owner:** the firm's **compliance function** — will only deploy an advisor-facing tool if it *cannot* wander into a recommendation, selective disclosure, or an unlabeled "live" price; runs the compliance-Q&A path and receives anything the gate routes.
- **Job to be done:** "Give me a fast, trustworthy briefing on this stock — the current quote and the key points from its recent SEC filings — that I can rely on and that won't get me (or the firm) in trouble."
- **Why it lands for the role:** forward-deployed work = turn an ambiguous ask into a working, *defensible* solution fast. The briefing is useful; the governance is why it ships in a regulated firm. BFSI is the JD's named market.

## 3 · The solution (one paragraph)
An advisor enters a ticker (and an optional question). An **orchestrator** fans out to two specialist workers — a **quote worker** (delayed/as-of snapshot via the market-data tool) and a **filings-summarizer worker** (retrieval over the issuer's recent 10-K / 10-Q / 8-K). Their outputs meet at the **control-plane gate**: the filing summary must pass the deterministic floor (citation spans resolve → lexical grounding → completeness) then the cross-family support + rubric judge; the quote must be labeled as-of and must not become advice. Only a passing candidate reaches the **one synthesizer**, which assembles the briefing. Anything uncertain — empty retrieval, an unsupported claim, a live/execution-grade price ask, a "should I buy this" ask, or MNPI the advisor isn't cleared for — is **withheld and routed** for human review. Every step is written to an append-only, hash-chained **audit** log. Runs **offline, keyless**.

## 4 · Scope
**In scope (the prototype):**
- Ticker → **delayed quote** (offline fixture; key-gated live adapter optional) + **cited filing summary** (10-K/10-Q/8-K).
- The full governed graph (orchestrator → workers → gate → synthesizer) + audit.
- The dual-view UI (Customer + Operator), per `ui_build_prompt.md`.
- One worked issuer in the corpus: **Meridian Regional Bancorp (NASDAQ: MRB)** — synthetic.

**Out of scope (named, not silently dropped):**
- Real-time / execution-grade market data, order placement, portfolio analytics → **routed**, by design.
- Personalized investment / suitability advice → **prohibited** (`no_personalized_advice`).
- A live EDGAR crawler — the corpus is a pinned synthetic snapshot (offline-first). A keyed adapter is the production swap, not the demo.
- **Adoption telemetry + understanding-completeness (see §15 roadmap)** — explicitly *next* prototype, not this one.

## 5 · The governed flow
```
ticker/question
   │
   ▼
ORCHESTRATOR ──────────────┬───────────────────────────┐
   │                       ▼                            ▼
   │              QUOTE WORKER                 FILINGS-SUMMARIZER WORKER
   │         (market-data tool, §12a)        (retriever tool over 10-K/10-Q/8-K)
   │         delayed/as-of snapshot          cited spans from the corpus
   │                       │                            │
   └──────────► CONTROL-PLANE GATE ◄─────────────────────┘
                 deterministic floor → support (cross-family) → rubric judge
                 + entitlement decision  + no_realtime_quote / no_personalized_advice
                       │ pass                         │ fail / uncertain
                       ▼                              ▼
                 ONE SYNTHESIZER                 WITHHELD → ROUTED
                 (assembles the briefing)        (human:compliance-officer)
                       │                              │
                       └──────────► APPEND-ONLY, HASH-CHAINED AUDIT ◄──┘
```
- **Quote is non-citable context**; the **filing summary carries the resolvable citations** the gate checks. Retrieval stays a tool, not the spine.
- The gate is **independent** (cross-family judge for stage-2 support) and the synthesizer is reachable **only** on the pass edge — a failed gate is *structurally* unable to produce a briefing.

## 6 · What this scenario ADDS to the skeleton
Everything else (graph, retriever, gate, audit, UI, entitlement model) is the existing vertical-free skeleton. The briefing adds exactly:

| Addition | Where it lives | Status |
|---|---|---|
| `stock_briefing` permitted-use + `no_realtime_quote` guardrail + `market_data` policy block | `policies/financial_services_us.yaml` **v2.2** | ✅ done |
| **Market-data tool** (thin interface; offline JSON-fixture default; key-gated delayed-quote live adapter) | `design.md §12a`; build = **T4b** → `app/tools/market_data.py` | spec ✅ / code ⏳ |
| **Quote worker** + **filings-summarizer worker** | graph (T3) + T4b | ⏳ |
| SEC-filing corpus — MRB **10-K / 10-Q / 8-K** (synthetic) + manifest rows | `data/corpus/financial_services/` (15 docs) | ✅ done |
| Offline quote fixture | `data/market/quotes.json` | ✅ done |
| Golden rows — 3 briefing positives + 3 briefing negatives | `golden/golden_financial_services.jsonl` (**20 rows**) | ✅ done, **validator-CLEAN** |

## 7 · Data (the answer key)
- **Corpus:** `mrb_10k.md` (FY2025 — Item 1A liquidity/funding risk + Item 7 MD&A capital), `mrb_10q.md` (Q1 2026 results, NIM, NPLs), `mrb_8k.md` (completed Cedar Valley acquisition — **publicly filed**, CFO appointment, Reg FD furnish). All synthetic; every golden citation `span` is an exact substring (validator Group B).
- **Quote fixture:** `data/market/quotes.json` — MRB delayed snapshot, pinned `as_of`, `execution_grade: false`, explicit "delayed — not a live price" label.
- **Golden (briefing-direct, 6 of 20 rows):** positives — `pos_briefing_10k_liquidity` (2 cited 10-K spans), `pos_briefing_10q_quarter` (2 cited 10-Q spans), `pos_briefing_8k_event` (cited 8-K span); negatives — `neg_realtime_quote`, `neg_briefing_advice_mrb` (on-ticker advice → ROUTED), `neg_briefing_empty_ticker` (unknown issuer → ROUTED). Gate: `python -m golden.validate_golden financial_services` → **CLEAN (0 fail, 0 warn)**; energy stays CLEAN (reusability intact).

## 8 · Acceptance criteria (EARS — scenario-specific)
Skeleton requirements R1–R12 apply unchanged. The briefing adds:

**RB1 — Stock briefing (positive path).**
- WHEN an advisor requests a briefing for a ticker in the corpus, THE SYSTEM SHALL return a **delayed quote** (labeled with its `as_of`) **and** a summary of the issuer's recent filings, with **every summary claim citing a resolvable filing span**.
- *Verified by:* `pos_briefing_10k_liquidity`, `pos_briefing_10q_quarter`, `pos_briefing_8k_event` (golden harness, T10); `test_controlling_chunk_returned` (T4).

**RB2 — Quote is offline-first, never presented as live.**
- THE SYSTEM SHALL serve quotes from a **keyless local fixture** by default; WHEN `MARKET_DATA_API_KEY` is set, it MAY use a **delayed** live adapter, but SHALL NEVER require a runtime network call and SHALL NEVER present a quote as execution-grade.
- WHEN a quote is shown, THE SYSTEM SHALL display its `as_of` timestamp and a "delayed — not a live execution price" label.
- *Verified by:* `test_quote_tool_offline_deterministic`, `test_stale_quote_labeled` (T4b).

**RB3 — Real-time / trade-now is withheld.**
- IF the advisor requests a **live / real-time / execution-grade** price or a **trade-now** action, THE SYSTEM SHALL withhold + route (`rejects_realtime_quote`), never improvise a live price.
- *Verified by:* `test_realtime_quote_routes` (T4b); `neg_realtime_quote` (golden).

**RB4 — The briefing cannot become advice, and cannot leak MNPI.**
- THE SYSTEM SHALL withhold + route any **personalized recommendation / suitability** ask (`no_personalized_advice`) and SHALL gate **MNPI** behind `mnpi_cleared` — even within a briefing.
- WHEN a filing event is **publicly disclosed** (the 8-K), THE SYSTEM SHALL deliver it; WHEN equivalent information is **unannounced** (`mnpi_dealbook`), THE SYSTEM SHALL block it unless the principal is entitled.
- *Verified by:* `rejects_personalized_advice`, `neg_briefing_advice_mrb`, `rejects_mnpi_disclosure` / `entitled_mnpi_access` (golden); `test_vertical_signature_negative`, `test_entitled_user_gets_mnpi` (T7).

## 9 · Live-demo script (the money shots)
1. **The briefing (value shot).** Ticker `MRB` → quote block (delayed, labeled) + a cited summary of FY2025 liquidity risk and the latest 8-K. Expand a citation → the exact 10-K span. *DELIVERED.*
2. **Public vs. MNPI (the governance line).** The 8-K (completed, announced acquisition) **delivers**; ask for the *unannounced* Project Atlas deal terms unentitled → **routed/blocked**. Flip to `[mnpi_cleared]` → grounded disclosure. *Same issuer space, governance draws the line.*
3. **Stale-quote guardrail.** "Give me MRB's **live execution price right now to place a trade**" → **ROUTED** with the reason. The control plane policing a *tool's* output, not just the LLM's.
4. **No advice.** "Prepping an MRB briefing — should I buy MRB for my client?" → **ROUTED** (Reg BI suitability).
5. **Operator view.** Flip the toggle: the graph (orchestrator → quote + filings workers → gate → synthesizer), the gate's stages, the entitlement decision, and the audit chain growing — all from the **real** run.

## 10 · Offline-first / keys posture (CLAUDE.md principle 1)
Runs with **zero keys**: stub embedder (Nomic), local Chroma, **local quote fixture**, stubbed model judges. Real keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MARKET_DATA_API_KEY`) *enable* real models / a delayed live quote but are **never required**. No runtime network call is on any critical path. `.env` is git-ignored; `.env.example` lists keys with no values.

## 11 · Rubric mapping (the 8 scored items)
1. **Multi-agent orchestration** — orchestrator + quote worker + filings worker + independent gate + synthesizer (LangGraph). 2. **LLM eval framework** — the control-plane gate + golden harness (briefing positives + the realtime/advice/empty negatives). 3. **Embedding** — text-embedding-3-small / Nomic offline. 4. **Vector DB** — ChromaDB behind the retriever interface. 5. **Memory** — session + working only; cross-session OFF. 6. **Guardrails** — MNPI/SAR/NPI + `no_personalized_advice` + **`no_realtime_quote`** (the briefing's signature). 7. **UI** — dual-view (Customer + Operator), governance visible. 8. **Deployment** — `streamlit run`, offline.

## 12 · The one-slide pitch (plain language — NON-technical, per CLAUDE.md trap 1)
> **"Get your advisors up to speed on any stock in minutes — safely."**
> Our tool gives an advisor a fast briefing on a stock: the current (clearly time-stamped) price and the key points from the company's latest SEC filings, with every fact linked back to the source document. What makes it different is the **guardrail layer**: it will not give investment advice, it will not reveal confidential or not-yet-public information to someone who shouldn't see it, and it will never pass an old price off as a live one. If anything is uncertain, it says so and hands the question to a person — and every answer keeps a tamper-evident record of how it was checked. **Useful for the advisor; defensible for compliance.**
> *(No architecture diagram, no jargon — this is the customer-facing page. The technical glass-box is the Operator view in the live demo.)*

## 13 · Risks & tradeoffs (honest)
- **Synthetic corpus, one issuer.** Demo realism is bounded to MRB; the production swap is a keyed EDGAR ingest behind the same retriever interface. *Stated, not hidden.*
- **Quote is delayed, not live.** A deliberate posture, not a gap — the `no_realtime_quote` guardrail turns the constraint into a compliance feature. Live execution data is a routed, human-owned path.
- **Green eval ≠ working retriever (Trap 3).** The market-data tool and the retriever each have their own tests (T4 / T4b) that run *before* the gate, so a passing judge never rubber-stamps a broken tool.

## 14 · Build status & next step
**Done:** pack v2.2 · corpus + quote fixture · golden 20 rows (**CLEAN**, both verticals) · `design.md §12/§12a` (rev9) · `tasks.md` T4b + matrix · **T0** (`app/models.py` incl. `Quote`/`RunTrace`, `app/config.py`; ruff + mypy --strict clean) · **T1** (the dual-view Streamlit UI against a stub backend; `tests/test_ui_smoke.py` 5/5 — both verdict states + Operator view + the MNPI entitlement flip render).
**Not built yet:** T2 policy-loader wrapper → **T3** governed graph (orchestrator → workers → stub gate → synthesizer; `test_synthesizer_unreachable_on_fail`) → **T4** retriever + **T4b** market-data tool → T5 guardrails → T6 gate → T7 entitlement → T9 audit → T10 golden harness.
**Recommended next:** T2 then T3 (stand up the real graph so the UI's Operator view reads a real `RunTrace` instead of the canned one).

## 15 · Roadmap — optional, next-prototype features (advisor-facing → employer outcome)
*Not in this prototype. Two features the firm can be told are **on the roadmap**, buildable next on **synthetic / dummy data**, keyless. Both are advisor-facing, but they exist to answer the employer's real question: **"Is this tool driving the outcome — are advisors using it to get up to speed, or is the tool being ignored?"** They extend our **eval-against-goal** pillar from answer-level correctness to **outcome-level adoption**.*

> **Architecture honesty (why these don't break the constitution).** Both ride the **existing audit pillar** — every run already writes an append-only, hash-chained record. Usage/completeness reporting is a **read-model over that audit trail**, i.e. observability, **not** cross-session agent memory (which stays **OFF** — the agent never uses prior sessions to shape an answer). Telemetry informs *humans about the tool*, never the *model about the user*.

### RF1 — Adoption & usage telemetry ("is the tool being used as expected?")
- **What:** each briefing run emits a usage event — advisor id, ticker, timestamp, verdict (delivered/routed), which filings surfaced, time-on-task. An **employer / compliance dashboard** rolls these up: adoption rate, **active vs. dormant advisors**, top tickers, the delivered-vs-routed mix, and — the headline the client asked for — a flag on advisors **not** using it ("the stock-education tool is being ignored").
- **Data (prototype):** synthetic / dummy advisor + usage logs — no real employee PII.
- **Architecture fit:** a read-model over the **append-only audit log** we already emit; keyless, offline. No new memory, no new external service.
- **Value:** turns "is it working?" into a number and ties adoption to the outcome (advisors actually getting up to speed).
- **Governance note (do it right):** employee-usage telemetry has its own governance — advisor transparency, retention limits, proportionality — and the reporting itself is audited. Flagged as a design consideration, not an afterthought.
- **Rough effort:** small — a usage-event emitter on the run + a Streamlit "Adoption" view seeded with synthetic data.

### RF2 — "Understanding completeness" progress bar (advisor-facing)
- **What:** an advisor-facing progress indicator showing **how complete their picture of the stock is** — a coverage checklist over the canonical briefing components: quote ✓ · 10-K risk factors ✓ · latest quarter (10-Q) ◻ · recent 8-K events ◻ · (extensible: peers, key ratios). A bar that nudges the advisor toward "fully briefed."
- **The idea:** define "complete understanding" as a **coverage rubric** over the briefing components — this is **eval-against-goal made user-visible**: the goal is a complete brief, the bar is progress toward it.
- **Employer benefit:** completeness scores roll up into RF1's report ("average completeness 78%"; "advisor X stops at the quote, never opens the filings") — directly answering whether the tool delivers the intended outcome.
- **Architecture fit:** a small completeness scorer over which components the advisor actually viewed/ran (data already present in the run trace + RF1 usage events) + a progress component in the Customer view. Canned/synthetic first.
- **Rough effort:** small–medium — a coverage model + a UI progress element.

> **Say it to the client (plain language):** *"Both of these are advisor-facing, but they give you, the firm, the answer you actually care about — is the tool being used, and is it getting your advisors to a complete understanding of a stock? We'd build them next on dummy data: a usage dashboard that flags who's leaning on it and who's ignoring it, and a 'how fully briefed am I' progress bar for the advisor that rolls up into that same view. They sit on the audit trail we already keep, so there's no new data-privacy surface beyond the usage logging itself, which we'd govern explicitly."*

---
## Version history
- v2 — 2026-06-17 · **synced + roadmap.** Updated the data/build facts to current reality: golden **17 → 20 rows** (3 briefing positives across 10-K/10-Q/8-K + 3 briefing negatives — realtime, advice-on-MRB, empty-ticker); **T0 + T1 marked DONE** (models/config + dual-view UI shell, `tests/test_ui_smoke.py` 5/5); persona/`design.md` reference moved to **rev9** (advisor-primary); §4 names the roadmap as out-of-scope. **Added §15 — Roadmap** (RF1 adoption telemetry + RF2 understanding-completeness bar) framed as optional/next-prototype on synthetic data, riding the audit pillar (not cross-session memory). Supersedes v1 (retained).
- v1 — 2026-06-17 · created. First scenario spec for the wealth-management advisor stock-briefing (Finance track). Captured problem/user/value, the governed flow, the skeleton delta (pack v2.2 + market-data tool §12a + MRB filings + golden), EARS acceptance (RB1–RB4), the demo script, rubric mapping, and the plain-language one-slide pitch. Mirrored `design.md` rev8 + `tasks.md` v1.2 + pack v2.2.
