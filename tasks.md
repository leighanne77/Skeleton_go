# tasks.md — Ordered build (the steps) · SKELETON (vertical-free)
*The **tasks** doc of the spec-driven set. Each task is discrete, ordered, and individually testable, cites the requirement it satisfies (`requirements.md`) and the design section it implements (`design.md`), and carries its own acceptance check. **Vertical-free** — load a vertical by setting `policy_pack` (the energy-instantiated counterpart lives at the repo root).*

> **Kick off in Plan Mode.** Decompose before coding; the usual clarifying questions (stack / persistence / scope) are already answered in `design.md` and `CLAUDE.md` — confirm against them, don't re-ask. **First, pick the vertical** (`policy_pack`) and fill `design.md` §12 + `requirements.md` Rv.
>
> **Validation gate for EVERY task (a task isn't done without evidence):**
> **1. Compile + lint** — build runs, `ruff` + `mypy --strict app/` clean · **2. Tests** — this task's tests pass, existing stay green · **3. Runtime** — launch the app, watch the console · **4. Visual** — screenshot the UI where relevant.

---

## T0 — Scaffold + config
Create the tree from `skeleton_project_structure.md`: `.env.example`, `.gitignore` (incl. `.env`, `data/chroma/`), `requirements.txt` + `requirements-dev.txt`, `app/config.py` (pydantic-settings), `app/models.py` (Pydantic v2 models **+ the StrEnums from design §3 at the top of the same file — no separate `enums.py`**), `app/__init__.py`. Move `policies/` in (with `load_pack.py`).
- **Satisfies:** R8, R11 · **Design:** §2, §3, §4
- **Acceptance:** `python -c "import app"` succeeds; ruff + mypy clean; `.env.example` committed with no values; `.env` gitignored.

## T0.5 — Golden dataset + synthetic corpus (define "correct")
*The "first move" before the feature build: author the eval **answer key** as DATA — no pipeline run yet (running it is T10). Defines what "correct" means, so the gate thresholds, the checks that fire, and the eval are all downstream of this.* Build a pinned **synthetic** `data/corpus/energy/` (~10–14 docs per design §12 doc types — CIP excerpts, compliance-evidence with a gap, FERC order, interconnection agreement, the **OT/relay-settings inventory** that is the CEII/OT signature target, a BCSI doc, state-PUC rule, a rate-case excerpt carrying base-PII, an **injection-laced** doc), each with a stable `source_id`/`doc_title` + `entitlement_tags`. Then `golden/golden_energy.jsonl` — one `GoldenRecord` per line, **Claude-bootstrapped + hand-verified**: happy-path positives (DELIVERED, `gold_answer` + `gold_citations` to real corpus spans) + the 6 base `golden_negatives` + the 3 energy signatures (`rejects_unentitled_ceii`, `rejects_ot_command`, `rejects_realtime_grid_op`).
- **Satisfies:** R2 (the golden-set artifact) · **Design:** §4 (`GoldenRecord`), §5, §12 · **Source:** the packs' `golden_negatives` (negatives) + the corpus (positives)
- **Acceptance:** every line parses into the T0 `GoldenRecord` model; corpus pinned + readable; the signature negative present; coverage spans the `CaseBucket` categories. **The T0.5 gate is `python -m golden.validate_golden <vertical>` → must print CLEAN (0 fail, 0 warn).** Run it for **both** the demo vertical and the reusability-proof vertical — `financial_services` *and* `energy` — both must be CLEAN. *(Positives are **hand-verified** against the corpus — never Claude-graded-by-Claude. Running the set against the pipeline is T10.)*
- **Recipe — follow `design.md §5c` (the reusable method).** The non-obvious moves that make it good: ① **corpus-first** — author docs + positives together so every citation `span` is an **exact substring** of a corpus doc (+ a `manifest.jsonl`); ② **one doc per trap** — an injection-laced doc, a PII doc, a **conflict pair**, the `block_unless_entitled` target, an evidence doc with a **gap**; ③ the **entitled/unentitled pair** — same query, `principal_entitlements: []` routes vs `[<cleared>]` delivers; ④ **verdict semantics** — `pii_leak`/`prompt_injection` are DELIVERED-with-it-excluded, the rest route; ⑤ **synthetic-but-regex-real** values so guards fire; ⑥ **validate** with the reusable `golden/validate_golden.py` (`python -m golden.validate_golden <vertical>` — one script, all verticals; **not** a per-vertical script) → CLEAN is the T0.5 gate. **Two verticals are already authored and validator-CLEAN — `data/corpus/financial_services/` + `golden/golden_financial_services.jsonl` (the BFSI demo; now also carries the stock-briefing corpus — MRB 10-K/10-Q/8-K + `data/market/quotes.json` — and its positives + the `rejects_realtime_quote` negative) and `data/corpus/energy/` + `golden/golden_energy.jsonl` (the reusability proof). Same skeleton, same validator, two greens = the reusable-framework evidence; copy either as the worked template.**

## T1 — UI shell FIRST (against a stub backend)
Build `ui/app.py` (Streamlit) **from `ui_build_prompt.md`** — lead with **Option B (hybrid: structured task console + scoped Q&A)**; fall back to **Option A (pure task console)** if time is tight. **Not a bare chatbot.** Hard requirements: identity/entitlement banner ("authorized Northwind user — your access scopes what these agents can retrieve and answer"); the **two never-blurred states** DELIVERED (answer + expandable citations) and ROUTED FOR HUMAN REVIEW (shows `withhold_reason` + route, no answer); first-class expandable citations; plain-language surface + a collapsible "how this was checked" panel; a collapsible "audit / trace" affordance (hash-chained record for the last answer). **Build it as TWO views of the same run via a toggle: a Customer view (plain, default) and an Operator view (glass box: the orchestration graph with per-node status, the gate stages, the entitlement decision, and the audit chain).** The Operator view reads from the run trace / gate result / audit log — driven by the **real** run once the graph exists (T3+); against the T1 stub it renders a canned trace. **Never mock the graph.** **Render it post-run — recolor a fixed topology (orchestrator→retriever→specialists→gate→synthesizer) from the captured `RunTrace`; no live animation / no `st.fragment` streaming** (that's a stretch goal only). See `ui_build_prompt.md` → "Operator view — build it post-run." Wire to a stub returning a canned `AnswerEnvelope` (+ canned trace) of each type.
- **Satisfies:** R7 (+ R1 orchestration-legibility via the Operator view) · **Design:** §1, §5, §5b · **Spec:** `ui_build_prompt.md`
- **Acceptance:** app launches; **both** answer states render; citations expand; audit panel toggles; **the Customer/Operator toggle switches views of the same run**, and the Operator view shows the orchestration graph with per-node status + the gate stages (from the run trace, not mocked); **visual** screenshots of DELIVERED *and* ROUTED (Customer view) plus the graph/gate (Operator view). *(UI is weighted equal to backend — do not defer.)*
- **Say it:** *"I didn't default to a chatbot — for a non-technical regulated user the win is making the gate visible: a task console plus a scoped question box, where every answer shows whether it was delivered or routed, what it's cited to, and that it's audited. Same app, two views of the same run: I flip one toggle and you watch the graph form and the gate decide, live."*

## T2 — Policy loader (load the chosen vertical)
Wire `app/policy.py` over `load_pack.py`; load the chosen `policy_pack` (deep-merges `_base`).
- **Satisfies:** R6, R10 · **Design:** §4, §12
- **Acceptance:** `test_policy_pack_load` — merged pack exposes base PII + the vertical's `sensitive_classes`; base universal `prohibited`/`golden_negatives` concatenated with the vertical's; vertical `thresholds` override base.

## T3 — Skeleton graph (orchestrator + specialists + stub gate)
Build `app/orchestrator.py` + `app/agents/*` in LangGraph: orchestrator delegates to the retriever tool + ≥1 specialist; a **stub** gate for now; **one** synthesizer wired **only** to the gate's pass edge.
- **Satisfies:** R1 · **Design:** §1
- **Acceptance:** a request traverses orchestrator → retriever → specialist → gate(stub) → synthesizer; `test_synthesizer_unreachable_on_fail` (a forced fail cannot reach the synthesizer).

## T4 — Retriever tool + embeddings + Chroma (ingest the corpus)
Implement the retriever behind a thin interface; embeddings = text-embedding-3-small (Nomic fallback by config); ChromaDB persisted under `data/chroma/`. Ingest the chosen vertical's corpus under `data/corpus/<vertical>/` (pinned snapshot; synthetic where sensitive). Deterministic tie-break: score, then `chunk_id`.
- **Satisfies:** R3, R4 · **Design:** §2, §12
- **Acceptance:** `test_retrieval_determinism`; `test_controlling_chunk_returned` — an in-scope query returns the controlling-source chunk; corpus embedded and queryable. **Retrieval is tested on its own here so a green eval is never trusted over an untested retriever (Trap 3): determinism + controlling-chunk-returned run *before* the gate, and T6's deterministic floor checks citation-span existence + lexical grounding + empty-retrieval-withholds *before* the judge can rubber-stamp anything.**

## T4b — Market-data tool (the stock-briefing quote source) — BFSI only
Build `app/tools/market_data.py`: a `MarketDataTool` behind a thin interface (sibling to the retriever) with a deterministic offline **stub** backend reading `data/market/quotes.json` (default, keyless, pinned `as_of`) and a key-gated **live** delayed-quote adapter (`MARKET_DATA_API_KEY`; never execution-grade, no runtime call required). Returns a Pydantic `Quote`. Wire the **quote worker** + **filings-summarizer worker** into the graph (T3) — both feed the one synthesizer; the quote is non-citable context, the filing summary carries the gate-checked citations. The `no_realtime_quote` guardrail (as-of label + no-advice; live/trade-now routes) is enforced at T5/T6 from the pack.
- **Satisfies:** R3 (retrieval-is-a-tool, second instance) · the BFSI stock-briefing use case · **Design:** §2, §12a
- **Acceptance:** `test_quote_tool_offline_deterministic` (stub returns an identical `Quote` across runs, keyless); `test_stale_quote_labeled` (every quote carries `as_of` + `execution_grade=False` + the delayed label); `test_realtime_quote_routes` (a live / execution-grade / trade-now ask → withheld + routed via `rejects_realtime_quote`). **Tested on its own (Trap 3): a tool the briefing depends on is never trusted on a green eval alone.**

## T5 — Guardrails (Presidio + policy classes), guard-first
Build `app/guardrails.py`: Presidio PII (base regex/NER classes) + the pack's `sensitive_classes` detectors (keyword + optional intent-classifier) + injection screen. Guard-first ordering.
- **Satisfies:** R6 · **Design:** §6, §7
- **Acceptance:** `test_pii_never_in_output`; `test_ignores_prompt_injection` (an instruction embedded in a retrieved doc is not followed).

## T6 — Control-plane gate (deterministic floor → support → rubric)
Build `app/eval/gate.py` + `judge.py`: deterministic floor (schema → citation-span existence → lexical grounding → completeness) → **stage-2 support** (cross-family LLM-judge: span must entail claim) → **rubric judge** (faithfulness + relevance, every dim gates). Runtime: pass → deliver / fail+retries → bounded self-correct / exhausted → withhold + escalate.
- **Satisfies:** R2, R12 · **Design:** §1, §6
- **Acceptance:** `test_rejects_unsupported_span`, `test_empty_retrieval_withholds`, `test_conflicting_sources`.

## T7 — Entitlement enforcement (the vertical signature)
Enforce `block_unless_entitled` against `principal.entitlements` in retrieval/guardrail; wire the vertical's `prohibited` rules to their `enforced_by` Controls; route withholds → the pack's escalation route.
- **Satisfies:** R10 · **Design:** §7, §12
- **Acceptance:** `test_vertical_signature_negative` — an **unentitled** user's request for a `block_unless_entitled` class is **withheld + routed** (the vertical's `rejects_…` case), never a grounded disclosure. **`test_entitled_user_gets_<class>` — the ENTITLED half of the money shot: the *same* query with the matching entitlement (`[mnpi_cleared]` / `[sar_cleared]` / `[ceii_cleared]`) returns a grounded, cited disclosure (proves the gate is entitlement-scoped, not a blanket block).** **`test_detector_data_alignment` — the validator's C1–C3 run as a test: every `block_unless_entitled` class's detector fires on its manifest-tagged corpus doc, and the PII regex matches the PII doc (catches a pack that drifts out of sync with the corpus).**

## T8 — Memory wiring
Session memory via the LangGraph checkpointer; working memory = `AgentState`; cross-session **off**.
- **Satisfies:** R5 · **Design:** §4
- **Acceptance:** session continuity within a thread; no cross-session write (memory-policy test).

## T9 — Audit (hash-chained JSONL + verify_chain)
Build `app/audit.py`: append-only `audit_log.jsonl`, each record `hash = sha256(prev_hash + canonical(payload))`, recording entitlement scope + gate results + verdict. Add `verify_chain()`.
- **Satisfies:** R9 · **Design:** §4
- **Acceptance:** `test_audit_chain_integrity` — tamper one record → `verify_chain()` fails at that record; log is never mutated/deleted.

## T10 — Golden harness (run the already-authored set)
The golden set + corpus were authored at **T0.5**; this task is the **runner + calibration loop**. Build `app/eval/harness.py` to run `golden/golden_<vertical>.jsonl` through the full pipeline and print pass@1 / per-dimension judge-vs-gold agreement / negative-test results, bucketed by `CaseBucket`. Then **calibrate** the golden set against what the gate actually does (refine labels/thresholds — the KNOWN_ISSUES T10 guard).
- **Satisfies:** R2 · **Design:** §5, §12 · **Consumes:** the T0.5 `golden_energy.jsonl` + `data/corpus/energy/`
- **Acceptance:** harness runs end-to-end; all signature negatives pass; positives meet the vertical thresholds.

## T11 — Full validation + customer one-pager
Run the 4-step validation across the whole suite. Produce the **plain-language one-pager** for a non-technical customer (no diagrams, no jargon) explaining how the agent solves their problem.
- **Satisfies:** all (esp. R7) · **Design:** §8
- **Acceptance:** ruff + mypy clean; full `tests/` green; app runtime-verified; UI visually validated (both states); one-pager passes the "would a non-technical buyer get it?" read.

## T12 — Rebuild: real parallel analyst agents + live cross-family judge
Replace the single sequential specialist with **two concurrent analyst agents** feeding the gate (recruiter feedback: orchestrate several agents in parallel). Build `app/agents/analysts.py` (`filings-analyst` ‖ `market-context`, each scoped to a different source, each emitting a cited `Finding`) + `app/agents/llm.py` (cross-family clients: Claude generator, OpenAI judge — gated on `USE_REAL_LLM` + key, fail-soft to deterministic). Add a reducer field `AgentState.findings` (`Annotated[list, operator.add]`) so the parallel nodes write concurrently; wire `orchestrate → {retrieve, market_data} → {filings_analyst ‖ market_context} → aggregate → gate` in `app/orchestrator.py`. Upgrade `app/eval/judge.py::supports` to call the **live cross-family OpenAI judge** when keyed (lexical fallback) + expose `judge_mode()`. **Keep the invariant:** ONE synthesizer on the gate's conditional pass edge — parallelism strictly upstream — so `test_synthesizer_unreachable_on_fail` is unchanged. Update the operator glass-box (analyst nodes + aggregate + live-judge tier) + the stub topology.
- **Satisfies:** R1 (multi-agent, heaviest) + R2 (cross-family judge) · **Design:** §1 topology + rebuild note, §10 · **Doc:** `Docs/Defense_And_Rebuild.md`
- **Acceptance:** `test_traverses_orchestrator_through_parallel_agents_to_gate`, `test_each_analyst_emits_a_grounded_finding`, `test_analysts_diversify_across_sources`, `test_live_judge_is_used_when_enabled` pass; `test_synthesizer_unreachable_on_fail` still passes; analyst thread-overlap empirically confirmed (~2.6 s); conftest forces both LLM families off (hermetic); full suite green (57 passed, 1 skipped); ruff + mypy --strict clean.

---

## Test → requirement map (the acceptance matrix)
| Test | Requirement | Task |
|---|---|---|
| `test_policy_pack_load` | R6, R10 | T2 |
| `test_golden_set_validates` (validate_golden CLEAN, both verticals) | R2 | T0.5 |
| `test_retrieval_determinism` | R3, R4 | T4 |
| `test_controlling_chunk_returned` | R3, R4 | T4 |
| `test_quote_tool_offline_deterministic` (BFSI) | R3 | T4b |
| `test_stale_quote_labeled` (BFSI) | R6 | T4b |
| `test_realtime_quote_routes` (BFSI) | R10 | T4b |
| `test_pii_never_in_output` | R6 | T5 |
| `test_ignores_prompt_injection` | R6 | T5 |
| `test_rejects_unsupported_span` | R2 | T6 |
| `test_empty_retrieval_withholds` | R12 | T6 |
| `test_conflicting_sources` | R12 | T6 |
| `test_synthesizer_unreachable_on_fail` | R1 | T3 |
| `test_traverses_orchestrator_through_parallel_agents_to_gate` | R1 | T12 |
| `test_each_analyst_emits_a_grounded_finding` | R1 | T12 |
| `test_analysts_diversify_across_sources` | R1 | T12 |
| `test_live_judge_is_used_when_enabled` | R2 | T12 |
| `test_vertical_signature_negative` | R10 (+ vertical Rv) | T7 |
| `test_entitled_user_gets_<class>` | R10 (+ vertical Rv) | T7 |
| `test_detector_data_alignment` | R6, R10 | T7 |
| `test_audit_chain_integrity` | R9 | T9 |

---

## Version history
v1.3 · SKELETON — 2026-06-29 · added **T12 — rebuild: real parallel analyst agents + live cross-family judge** (recruiter feedback: orchestrate several agents in parallel, not one sequential assistant). Two concurrent analyst agents (`filings-analyst` ‖ `market-context`) propose cited findings → `aggregate` → gate; the single synthesizer stays on the pass edge (invariant intact). Stage-2 support is now a live cross-family OpenAI judge (lexical fallback). Four new tests added to the acceptance matrix (`test_traverses_orchestrator_through_parallel_agents_to_gate`, `test_each_analyst_emits_a_grounded_finding`, `test_analysts_diversify_across_sources`, `test_live_judge_is_used_when_enabled`). Mirrors `design.md` rev11, `requirements.md` R1/R2, `Docs/Defense_And_Rebuild.md`.
v1.2 · SKELETON — 2026-06-17 · added **T4b — market-data tool** (the BFSI stock-briefing quote source: offline JSON-fixture default + key-gated delayed-quote live adapter, `no_realtime_quote` guardrail, quote-worker + filings-summarizer-worker) with three tool-level tests added to the acceptance matrix (`test_quote_tool_offline_deterministic`, `test_stale_quote_labeled`, `test_realtime_quote_routes`). T0.5's financial_services data now also carries the briefing corpus (MRB 10-K/10-Q/8-K) + golden rows (17, CLEAN). Mirrors `design.md §12/§12a` + pack v2.2.
v1.1 · SKELETON — 2026-06-16 · changed: **moved the golden *data* early** — inserted **T0.5 (Golden dataset + synthetic corpus)** between T0 and T1 to "define correct" before the feature build (negatives derive from the packs; positives hand-verified vs a synthetic corpus); **slimmed T10** from "golden set + harness" to **"Golden harness"** (runs the already-authored T0.5 set + calibration). Rest of the order (T1 UI → T9) unchanged. Mirrors `CLAUDE.md` / `design.md §9`.
v3 · SKELETON — 2026-06-17 · **T1 now builds the dual-mode UI** — a Customer/Operator toggle over the same run: Customer view (plain, default) + Operator view (glass box: orchestration graph with per-node status, gate stages, entitlement decision, audit chain), driven by the real run trace (never mocked); acceptance + say-it + R1-legibility updated.

v2 · SKELETON — 2026-06-17 · named **`validate_golden <vertical>` → CLEAN as the T0.5 gate** (run for both `financial_services` + `energy`); fixed recipe wording (one reusable validator, not per-vertical); added **`test_controlling_chunk_returned`** (T4), **`test_entitled_user_gets_<class>`** + **`test_detector_data_alignment`** (T7), **`test_golden_set_validates`** (T0.5) to acceptance + the matrix; baked the untested-retriever trap-prevention note into T4/T6.

v1 · SKELETON — 2026-06-16 · created: the vertical-free ordered build doc — 12 discrete, individually-testable tasks (T0–T11), each citing its requirement + design section + acceptance check, with the 4-step validation gate (compile/lint → tests → runtime → visual) per task; T1 (UI) carries the `ui_build_prompt.md` requirements + say-it line. Vertical specifics (which pack, which corpus, which signature negatives) are parameters filled at build time. The energy-instantiated counterpart lives at the repo root.
