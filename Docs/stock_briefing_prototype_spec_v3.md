# Prototype Spec — Advisor Stock-Briefing (Wealth Management / BFSI) — v3
*The **scenario spec** for the AI Prototype Challenge (Finance track). It states the business problem, the user, the solution, the governed flow, the acceptance criteria, and the live-demo script for **one** chosen scenario — the advisor stock-briefing. It does not restate the skeleton; it points to the canonical doc set and names only what this scenario adds. **v3 reflects the PROPOSE-layer rebuild** — real parallel analyst agents + a live cross-family judge feeding the gate (recruiter feedback: orchestrate several agents in parallel, not one sequential assistant). Supersedes v2 (kept for history).*

> **Doc-set position.** `CLAUDE.md` = constitution · `requirements.md` = WHAT/WHY (EARS; R1/R2 updated for the parallel agents + live judge) · `design.md` = HOW (architecture; the stock-briefing overlay is **§12 / §12a**, the rebuild note under **§1** + tests in **§10**, rev11) · `tasks.md` = build steps (the tool is **T4b**; the rebuild is **T12**). This file is the **scenario brief** that ties them to the challenge prompt. **Loaded pack:** `policy_pack = "financial_services_us"` (v2.2). Full rebuild rationale + evidence: `Docs/Defense_And_Rebuild.md`.

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
An advisor enters a ticker (and an optional question). An **orchestrator** fans out to a **real parallel layer of analyst agents** running concurrently — a **filings-analyst** and a **market-context** agent (genuine LangGraph fan-out on distinct threads), each grounding in a *different* source and emitting a cited **finding** (a proposal, not prose) — alongside the **market-data tool** (delayed/as-of quote). An **aggregate** step unions their findings into one candidate, which meets the **control-plane gate**: the deterministic floor (citation spans resolve → lexical grounding → completeness), then a **live cross-family support judge** (OpenAI judging the Claude-generated claims — a model never grades its own output unchecked) + rubric; the quote must be labeled as-of and must not become advice. Only a passing candidate reaches the **one synthesizer**, which assembles the briefing. Anything uncertain — empty retrieval, an unsupported claim, a live/execution-grade price ask, a "should I buy this" ask, or MNPI the advisor isn't cleared for — is **withheld and routed** for human review. Every step is written to an append-only, hash-chained **audit** log. Runs **offline, keyless** (the analysts and judge fall back to deterministic paths). **Parallel agents propose; the single synthesizer disposes.**

## 4 · Scope
**In scope (the prototype):**
- Ticker → **delayed quote** (offline fixture; key-gated live adapter optional) + **cited filing summary** (10-K/10-Q/8-K).
- The full governed graph (orchestrator → **parallel analyst agents** → aggregate → gate → synthesizer) + audit.
- The dual-view UI (Customer + Operator), per `ui_build_prompt.md` — the Operator view renders the parallel fan-out + the live-judge tier.
- One worked issuer in the corpus: **Meridian Regional Bancorp (NASDAQ: MRB)** — synthetic.

**Out of scope (named, not silently dropped):**
- Real-time / execution-grade market data, order placement, portfolio analytics → **routed**, by design.
- Personalized investment / suitability advice → **prohibited** (`no_personalized_advice`).
- A live EDGAR crawler — the corpus is a pinned synthetic snapshot (offline-first). A keyed adapter is the production swap, not the demo.
- A DeBERTa-class **NLI** support tier — the cross-family LLM judge is live; the dedicated NLI model stays the documented production swap (`design.md §11`).
- **Adoption telemetry + understanding-completeness (see §15 roadmap)** — explicitly *next* prototype, not this one.

## 5 · The governed flow
```
ticker/question
   │
   ▼
ORCHESTRATOR ─────────────┬─────────────────────────────────┐
   │                      ▼                                  ▼
   │              MARKET-DATA tool                    RETRIEVER tool
   │         (delayed/as-of snapshot, §12a)      (entitlement-filtered, 10-K/10-Q/8-K)
   │                      │                                  │
   │                      │              ┌───────────────────┴───────────────────┐
   │                      │              ▼                                       ▼
   │                      │       FILINGS-ANALYST agent              MARKET-CONTEXT agent   ← TWO PARALLEL
   │                      │     (propose: cited finding)           (propose: cited finding)    ANALYST AGENTS
   │                      │              └───────────────────┬───────────────────┘   (real fan-out, ~2.6s overlap)
   │                      │                                  ▼
   │                      └──────────────────────────►  AGGREGATE
   │                                                  (union findings → 1 candidate)
   │                                                         │
   └──────────────────────────────────────────►  CONTROL-PLANE GATE
                 deterministic floor → support (LIVE cross-family judge) → rubric
                 + entitlement decision  + no_realtime_quote / no_personalized_advice
                       │ pass                         │ fail / uncertain
                       ▼                              ▼
                 ONE SYNTHESIZER                 WITHHELD → ROUTED
                 (assembles the briefing)        (human:compliance-officer)
                       │                              │
                       └──────────► APPEND-ONLY, HASH-CHAINED AUDIT ◄──┘
```
- **Two analyst agents run concurrently** and only **propose** cited findings; the **aggregate** unions them and the **one synthesizer** (pass-edge only) **disposes**. Parallelism lives strictly *upstream* of the gate, so the invariant (`test_synthesizer_unreachable_on_fail`) is untouched.
- **Quote is non-citable context**; the **findings carry the resolvable citations** the gate checks. Retrieval stays a tool, not the spine.
- The gate is **independent** — stage-2 support is a **live cross-family judge** (OpenAI judging Claude's claims when keyed; deterministic lexical fallback offline) — and the synthesizer is reachable **only** on the pass edge: a failed gate is *structurally* unable to produce a briefing.

## 6 · What this scenario ADDS to the skeleton
Everything else (graph, retriever, gate, audit, UI, entitlement model) is the existing vertical-free skeleton. The briefing adds exactly:

| Addition | Where it lives | Status |
|---|---|---|
| `stock_briefing` permitted-use + `no_realtime_quote` guardrail + `market_data` policy block | `policies/financial_services_us.yaml` **v2.2** | ✅ done |
| **Market-data tool** (thin interface; offline JSON-fixture default; key-gated **Alpha Vantage / Finnhub** live adapter, ticker-agnostic) | `design.md §12a` → `app/tools/market_data.py` | ✅ done |
| **Two parallel analyst agents** (filings-analyst ‖ market-context, real LangGraph fan-out; Claude when keyed, deterministic fallback) | `app/agents/analysts.py` + `app/agents/llm.py` | ✅ **T12 done** (rebuild) |
| **Live cross-family support judge** (OpenAI judges Claude's claims at gate stage-2; lexical fallback) | `app/eval/judge.py::supports` + `judge_mode()` | ✅ **T12 done** (rebuild) |
| **Orchestrator → retriever + market_data → {filings-analyst ‖ market-context} → aggregate → gate → synthesizer** (synthesizer on the pass edge only) | `app/orchestrator.py` + `app/eval/gate.py` | ✅ done |
| SEC-filing corpus — MRB **10-K / 10-Q / 8-K** (synthetic) + manifest rows | `data/corpus/financial_services/` (15 docs) | ✅ done |
| Offline quote fixture | `data/market/quotes.json` | ✅ done |
| Golden rows — 3 briefing positives + 3 briefing negatives | `golden/golden_financial_services.jsonl` (**20 rows**) | ✅ done, **validator-CLEAN** |

## 7 · Data (the answer key)
- **Corpus:** `mrb_10k.md` (FY2025 — Item 1A liquidity/funding risk + Item 7 MD&A capital), `mrb_10q.md` (Q1 2026 results, NIM, NPLs), `mrb_8k.md` (completed Cedar Valley acquisition — **publicly filed**, CFO appointment, Reg FD furnish). All synthetic; every golden citation `span` is an exact substring (validator Group B).
- **Quote fixture:** `data/market/quotes.json` — MRB delayed snapshot, pinned `as_of`, `execution_grade: false`, explicit "delayed — not a live price" label.
- **Golden (briefing-direct, 6 of 20 rows):** positives — `pos_briefing_10k_liquidity` (2 cited 10-K spans), `pos_briefing_10q_quarter` (2 cited 10-Q spans), `pos_briefing_8k_event` (cited 8-K span); negatives — `neg_realtime_quote`, `neg_briefing_advice_mrb` (on-ticker advice → ROUTED), `neg_briefing_empty_ticker` (unknown issuer → ROUTED). Gate: `python -m golden.validate_golden financial_services` → **CLEAN (0 fail, 0 warn)**; energy stays CLEAN (reusability intact).

## 8 · Acceptance criteria (EARS — scenario-specific)
Skeleton requirements R1–R12 apply unchanged (R1 now requires **≥2 concurrent specialist agents**; R2 now requires the **cross-family** support judge). The briefing adds:

**RB1 — Stock briefing (positive path).**
- WHEN an advisor requests a briefing for a ticker in the corpus, THE SYSTEM SHALL return a **delayed quote** (labeled with its `as_of`) **and** a summary of the issuer's recent filings, with **every summary claim citing a resolvable filing span**.
- *Verified by:* `pos_briefing_10k_liquidity`, `pos_briefing_10q_quarter`, `pos_briefing_8k_event` (golden harness, T10); `test_controlling_chunk_returned` (T4); `test_traverses_orchestrator_through_parallel_agents_to_gate` (T12).

**RB2 — Quote is offline-first, never presented as live.**
- THE SYSTEM SHALL serve quotes from a **keyless local fixture** by default; WHEN `MARKET_DATA_API_KEY` is set, it MAY use a live adapter, but SHALL NEVER require a runtime network call and SHALL NEVER present a quote as execution-grade.
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
5. **Operator view (the orchestration shot).** Flip the toggle: the graph shows the **two analyst agents fanning out concurrently** → aggregate → gate → synthesizer, the gate's stages **with the live cross-family judge tier**, the entitlement decision, and the audit chain growing — all from the **real** run. *(If a Live run withholds a clean-looking query, that's the relevance floor genuinely gating — it fails closed; the scripted shots run on Demo.)*

## 10 · Offline-first / keys posture (CLAUDE.md principle 1)
Runs with **zero keys**: stub embedder (Nomic), local Chroma, **local quote fixture**, **deterministic analyst extractors + lexical support judge**. Real keys (`ANTHROPIC_API_KEY` + `USE_REAL_LLM` for the analysts; `OPENAI_API_KEY` for embeddings + the cross-family judge; `MARKET_DATA_API_KEY`) *enable* real models / live data but are **never required**. No runtime network call is on any critical path. `.env` is git-ignored; `.env.example` lists keys with no values.

## 11 · Rubric mapping (the 8 scored items)
1. **Multi-agent orchestration** — orchestrator + **two concurrent analyst agents** (real LangGraph fan-out) + aggregate + independent gate + the one synthesizer (pass-edge only). *Parallel agents propose; the single synthesizer disposes.* 2. **LLM eval framework** — the control-plane gate with a **live cross-family judge** at stage-2 support (OpenAI judges Claude) + golden harness (briefing positives + the realtime/advice/empty negatives). 3. **Embedding** — text-embedding-3-small / Nomic offline. 4. **Vector DB** — ChromaDB behind the retriever interface. 5. **Memory** — session + working only; cross-session OFF. 6. **Guardrails** — MNPI/SAR/NPI + `no_personalized_advice` + **`no_realtime_quote`** (the briefing's signature). 7. **UI** — dual-view (Customer + Operator), governance + the parallel fan-out visible. 8. **Deployment** — `streamlit run`, offline.

## 12 · The one-slide pitch (plain language — NON-technical, per CLAUDE.md trap 1)
> **"Get your advisors up to speed on any stock in minutes — safely."**
> Our tool gives an advisor a fast briefing on a stock: the current (clearly time-stamped) price and the key points from the company's latest SEC filings, with every fact linked back to the source document. What makes it different is the **guardrail layer**: it will not give investment advice, it will not reveal confidential or not-yet-public information to someone who shouldn't see it, and it will never pass an old price off as a live one. If anything is uncertain, it says so and hands the question to a person — and every answer keeps a tamper-evident record of how it was checked. **Useful for the advisor; defensible for compliance.**
> *(No architecture diagram, no jargon — this is the customer-facing page. The technical glass-box — including the parallel agents and the cross-family judge — is the Operator view in the live demo.)*

## 13 · Risks & tradeoffs (honest)
- **Synthetic corpus, one issuer.** Demo realism is bounded to MRB; the production swap is a keyed EDGAR ingest behind the same retriever interface. *Stated, not hidden.*
- **Quote is delayed by default.** A deliberate posture, not a gap — the `no_realtime_quote` guardrail turns the constraint into a compliance feature. Live execution data is a routed, human-owned path. (Finnhub real-time is available behind a key; it's still labeled and never execution-grade.)
- **The gate genuinely gates.** On the live path a clean-looking query can be routed-for-review when the relevance floor judges the answer weak — it **fails closed**. That's the control plane working; the scripted money shots run on the Demo backend (offline-first) and Live is the glass box.
- **Green eval ≠ working retriever (Trap 3).** The market-data tool and the retriever each have their own tests (T4 / T4b) that run *before* the gate, so a passing judge never rubber-stamps a broken tool.

## 14 · Build status & next step
**Done (full pipeline + the rebuild):** pack v2.2 · corpus + quote fixture · golden 20 rows (**CLEAN**, both verticals) · `design.md §12/§12a/§12c` + the §1 rebuild note (rev11) · **T0–T11** (models/config · dual-surface UI · policy loader · the real LangGraph graph · Chroma retriever + OpenAI embeddings · market-data tool · guardrails incl. Presidio NER · the full floor→support→rubric gate · entitlement signature · audit + `verify_chain` · golden harness · one-pager) · **T12 — the rebuild** (two parallel analyst agents + the live cross-family judge; synthesizer still pass-edge only — `test_synthesizer_unreachable_on_fail` unchanged). **57 tests, 1 opt-in skipped; ruff + mypy --strict clean; both verticals validate-CLEAN; harness pass@1 0.75.**
**Evidence the orchestration is real (not described-as-real):** measured **~2.6 s analyst thread-overlap** on distinct `ThreadPoolExecutor` threads; `test_parallel_findings_merge_in_graph_state` proves both concurrent writes survive the reducer; `test_live_judge_is_used_when_enabled` proves stage-2 support defers to the cross-family model's verdict. See `Docs/Defense_And_Rebuild.md`.
**Next:** the production tiers as documented seams — a DeBERTa-class NLI support tier behind the same `supports()` call; an intent classifier for the tipping-off-vs-Q&A distinction; the §15 roadmap (adoption telemetry + understanding-completeness).

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

### RF3 — UI fidelity upgrade: React/Next + FastAPI (the pixel-perfect option)
- **What:** the advisor surface is currently a **Munich-Re-styled Streamlit** app. That hits the rubric's equal-weight UI bar at ~80% brand fidelity, fast and offline. For a production-grade, pixel-perfect on-brand experience, the next step is a **React/Next + Tailwind** frontend over a **thin FastAPI wrapper** on the existing backend.
- **Why it's cheap to do later:** the backend already speaks clean JSON contracts (`AnswerEnvelope` + `RunTrace`), so the wrapper is small and the UI swap touches no engine code.
- **Decision (2026-06-17):** **Streamlit now, React later** — ship the themed Streamlit for the prototype; the React/FastAPI build is this roadmap item, not the demo path.
- **Rough effort:** medium — a FastAPI endpoint per run + a React app; offline packaging is the main extra cost.

> **Say it to the client (plain language):** *"Both of these are advisor-facing, but they give you, the firm, the answer you actually care about — is the tool being used, and is it getting your advisors to a complete understanding of a stock? We'd build them next on dummy data: a usage dashboard that flags who's leaning on it and who's ignoring it, and a 'how fully briefed am I' progress bar for the advisor that rolls up into that same view. They sit on the audit trail we already keep, so there's no new data-privacy surface beyond the usage logging itself, which we'd govern explicitly."*

---
## Version history
- v3 — 2026-06-29 · **the PROPOSE-layer rebuild.** Reflected the recruiter-driven rebuild: the single sequential specialist is replaced by **two parallel analyst agents** (filings-analyst ‖ market-context, real LangGraph fan-out) that propose cited findings → `aggregate` → gate; **stage-2 support is now a live cross-family judge** (OpenAI judges Claude). Rewrote §3 solution, §5 governed-flow diagram, §6 additions table, §9 step-5 operator shot, §11 rubric items 1–2; refreshed §14 to the completed pipeline + T12 with evidence (~2.6 s thread overlap, reducer-merge + live-judge tests); **57 tests, both verticals CLEAN, pass@1 0.75.** Mirrors `design.md` rev11, `requirements.md` R1/R2, `tasks.md` T12, `README.md`, `DEMO.md`, `Docs/Defense_And_Rebuild.md`. Supersedes v2 (retained).
- v2.2 — 2026-06-17 · **build progress + live MSFT.** Synced §6/§14 to current reality: **T2** (policy loader), **T3** (real LangGraph graph — orchestrator→retriever+market_data→specialist→gate→synthesizer, pass-edge invariant), and **T4b** (market-data tool with the built **Alpha Vantage live adapter**, ticker-agnostic; **MSFT = live example, MRB = offline example**) are done; 17 tests, ruff + mypy --strict clean. UI gained the welcome screen + ⚙ gear (mirrored to `design.md §12c`). Next: wire "Show my work" to the real graph, then T4 (Chroma retriever).
- v2.1 — 2026-06-17 · **UI restyle (Munich-Re look & feel).** Re-skinned the Streamlit UI to an institutional navy+turquoise theme (`ui/theme.py` + `.streamlit/config.toml`, offline system font — no runtime web-font fetch); **simplified login to just the advisor (Dana)**; split into two surfaces bridged by a **gear icon** — advisor briefing (default) and "Show my work" (the live-graph glass box), with the entitlement/demo toggle moved onto the operator surface. Renamed `ui/app.py` → `ui/streamlit_app.py` (fixed an `app/` package shadowing collision under `streamlit run`). Tests updated (`test_ui_smoke.py` 5/5). Added **§15 RF3** (React/Next + FastAPI fidelity upgrade — "Streamlit now, React later").
- v2 — 2026-06-17 · **synced + roadmap.** Updated the data/build facts to current reality: golden **17 → 20 rows** (3 briefing positives across 10-K/10-Q/8-K + 3 briefing negatives — realtime, advice-on-MRB, empty-ticker); **T0 + T1 marked DONE** (models/config + dual-view UI shell, `tests/test_ui_smoke.py` 5/5); persona/`design.md` reference moved to **rev9** (advisor-primary); §4 names the roadmap as out-of-scope. **Added §15 — Roadmap** (RF1 adoption telemetry + RF2 understanding-completeness bar) framed as optional/next-prototype on synthetic data, riding the audit pillar (not cross-session memory). Supersedes v1 (retained).
- v1 — 2026-06-17 · created. First scenario spec for the wealth-management advisor stock-briefing (Finance track). Captured problem/user/value, the governed flow, the skeleton delta (pack v2.2 + market-data tool §12a + MRB filings + golden), EARS acceptance (RB1–RB4), the demo script, rubric mapping, and the plain-language one-slide pitch. Mirrored `design.md` rev8 + `tasks.md` v1.2 + pack v2.2.
