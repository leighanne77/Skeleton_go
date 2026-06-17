# Prototype Spec — Advisor Stock-Briefing (Wealth Management / BFSI)
*The **scenario spec** for the AI Prototype Challenge (Finance track). It states the business problem, the user, the solution, the governed flow, the acceptance criteria, and the live-demo script for **one** chosen scenario — the advisor stock-briefing. It does not restate the skeleton; it points to the canonical doc set and names only what this scenario adds.*

> **Doc-set position.** `CLAUDE.md` = constitution · `requirements.md` = WHAT/WHY (EARS) · `design.md` = HOW (architecture; the stock-briefing overlay is **§12 / §12a**) · `tasks.md` = build steps (the tool is **T4b**). This file is the **scenario brief** that ties them to the challenge prompt. **Loaded pack:** `policy_pack = "financial_services_us"` (v2.2).

---

## 1 · The challenge (verbatim)
> **Finance:** A wealth management firm wants a solution that helps advisors quickly get up to speed on a stock — **fetching current quote data and summarizing key information from recent SEC filings.**

We deliver this as a **governed** advisor tool: the briefing is the positive path, and the *same* control plane that makes our skeleton defensible (guardrails + eval-against-goal + tamper-evident audit) bounds it — so a wealth-management firm can put it in front of advisors without it ever giving advice, leaking MNPI, or passing a stale price off as live.

## 2 · Problem · user · value
- **User (primary):** a **wealth-management advisor** prepping for a client conversation — needs to get up to speed on a ticker in minutes, not an afternoon of reading filings.
- **Buyer / accountable owner:** the firm's **compliance function** — will only deploy an advisor-facing tool if it *cannot* wander into a recommendation, selective disclosure, or an unlabeled "live" price.
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
| Golden rows — 2 briefing positives + 1 realtime negative | `golden/golden_financial_services.jsonl` (17 rows) | ✅ done, **validator-CLEAN** |

## 7 · Data (the answer key)
- **Corpus:** `mrb_10k.md` (FY2025 — Item 1A liquidity/funding risk + Item 7 MD&A capital), `mrb_10q.md` (Q1 2026 results, NIM, NPLs), `mrb_8k.md` (completed Cedar Valley acquisition — **publicly filed**, CFO appointment, Reg FD furnish). All synthetic; every golden citation `span` is an exact substring (validator Group B).
- **Quote fixture:** `data/market/quotes.json` — MRB delayed snapshot, pinned `as_of`, `execution_grade: false`, explicit "delayed — not a live price" label.
- **Golden:** `pos_briefing_10k_liquidity` (DELIVERED, 2 cited 10-K spans) · `pos_briefing_8k_event` (DELIVERED, cited 8-K span) · `neg_realtime_quote` (ROUTED). Gate: `python -m golden.validate_golden financial_services` → **CLEAN (0 fail, 0 warn)**; energy stays CLEAN (reusability intact).

## 8 · Acceptance criteria (EARS — scenario-specific)
Skeleton requirements R1–R12 apply unchanged. The briefing adds:

**RB1 — Stock briefing (positive path).**
- WHEN an advisor requests a briefing for a ticker in the corpus, THE SYSTEM SHALL return a **delayed quote** (labeled with its `as_of`) **and** a summary of the issuer's recent filings, with **every summary claim citing a resolvable filing span**.
- *Verified by:* `pos_briefing_10k_liquidity`, `pos_briefing_8k_event` (golden harness, T10); `test_controlling_chunk_returned` (T4).

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
- *Verified by:* `rejects_personalized_advice`, `rejects_mnpi_disclosure` / `entitled_mnpi_access` (golden); `test_vertical_signature_negative`, `test_entitled_user_gets_mnpi` (T7).

## 9 · Live-demo script (the money shots)
1. **The briefing (value shot).** Ticker `MRB` → quote block (delayed, labeled) + a cited summary of FY2025 liquidity risk and the latest 8-K. Expand a citation → the exact 10-K span. *DELIVERED.*
2. **Public vs. MNPI (the governance line).** The 8-K (completed, announced acquisition) **delivers**; ask for the *unannounced* Project Atlas deal terms unentitled → **routed/blocked**. Flip to `[mnpi_cleared]` → grounded disclosure. *Same issuer space, governance draws the line.*
3. **Stale-quote guardrail.** "Give me MRB's **live execution price right now to place a trade**" → **ROUTED** with the reason. The control plane policing a *tool's* output, not just the LLM's.
4. **No advice.** "Given my client's portfolio, should they buy MRB?" → **ROUTED** (Reg BI suitability). 
5. **Operator view.** Flip the toggle: the graph (orchestrator → quote + filings workers → gate → synthesizer), the gate's three stages, the entitlement decision, and the audit chain growing — all from the **real** run.

## 10 · Offline-first / keys posture (CLAUDE.md principle 1)
Runs with **zero keys**: stub embedder (Nomic), local Chroma, **local quote fixture**, stubbed model judges. Real keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MARKET_DATA_API_KEY`) *enable* real models / a delayed live quote but are **never required**. No runtime network call is on any critical path. `.env` is git-ignored; `.env.example` lists keys with no values.

## 11 · Rubric mapping (the 8 scored items)
1. **Multi-agent orchestration** — orchestrator + quote worker + filings worker + independent gate + synthesizer (LangGraph). 2. **LLM eval framework** — the control-plane gate + golden harness (briefing positives + the realtime negative). 3. **Embedding** — text-embedding-3-small / Nomic offline. 4. **Vector DB** — ChromaDB behind the retriever interface. 5. **Memory** — session + working only; cross-session OFF. 6. **Guardrails** — MNPI/SAR/NPI + `no_personalized_advice` + **`no_realtime_quote`** (the briefing's signature). 7. **UI** — dual-view (Customer + Operator), governance visible. 8. **Deployment** — `streamlit run`, offline.

## 12 · The one-slide pitch (plain language — NON-technical, per CLAUDE.md trap 1)
> **"Get your advisors up to speed on any stock in minutes — safely."**
> Our tool gives an advisor a fast briefing on a stock: the current (clearly time-stamped) price and the key points from the company's latest SEC filings, with every fact linked back to the source document. What makes it different is the **guardrail layer**: it will not give investment advice, it will not reveal confidential or not-yet-public information to someone who shouldn't see it, and it will never pass an old price off as a live one. If anything is uncertain, it says so and hands the question to a person — and every answer keeps a tamper-evident record of how it was checked. **Useful for the advisor; defensible for compliance.**
> *(No architecture diagram, no jargon — this is the customer-facing page. The technical glass-box is the Operator view in the live demo.)*

## 13 · Risks & tradeoffs (honest)
- **Synthetic corpus, one issuer.** Demo realism is bounded to MRB; the production swap is a keyed EDGAR ingest behind the same retriever interface. *Stated, not hidden.*
- **Quote is delayed, not live.** A deliberate posture, not a gap — the `no_realtime_quote` guardrail turns the constraint into a compliance feature. Live execution data is a routed, human-owned path.
- **Green eval ≠ working retriever (Trap 3).** The market-data tool and the retriever each have their own tests (T4 / T4b) that run *before* the gate, so a passing judge never rubber-stamps a broken tool.

## 14 · Build status & next step
**Done:** pack v2.2, corpus + fixture, golden (CLEAN), `design.md §12/§12a`, `tasks.md` T4b + matrix. **Not built:** the `app/` code (T1 UI shell → T0 models/config → graph → retriever → **T4b market-data tool** → gate → audit). **Recommended next:** T1 UI shell against a stub (build order puts UI first, equal-weighted), or T0 models first so `GoldenRecord` / `Quote` exist before the UI wires to them.

---
## Version history
- v1 — 2026-06-17 · created. First scenario spec for the wealth-management advisor stock-briefing (Finance track of the AI Prototype Challenge). Captures problem/user/value, the governed flow, the skeleton delta (pack v2.2 + market-data tool §12a + MRB filings + golden), EARS acceptance (RB1–RB4), the demo script, rubric mapping, and the plain-language one-slide pitch. Mirrors `design.md` rev8 + `tasks.md` v1.2 + pack v2.2.
