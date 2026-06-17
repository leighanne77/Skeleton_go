# tasks.md — Ordered build (the steps)
*The **tasks** doc of the spec-driven set. Each task is discrete, ordered, and individually testable, cites the requirement it satisfies (`requirements.md`) and the design section it implements (`design.md`), and carries its own acceptance check. Instantiated for the **Energy & Utilities** demo (`policy_pack = "energy_utilities_us"`).*

> **Kick off in Plan Mode.** Decompose before coding; the usual clarifying questions (stack / persistence / scope) are already answered in `design.md` and `CLAUDE.md` — confirm against them, don't re-ask.
>
> **Validation gate for EVERY task (a task isn't done without evidence):**
> **1. Compile + lint** — build runs, `ruff` + `mypy --strict app/` clean · **2. Tests** — this task's tests pass, existing stay green · **3. Runtime** — launch the app, watch the console · **4. Visual** — screenshot the UI where relevant.
>
> **Before marking any task done, clear its guards in `KNOWN_ISSUES.md`** (preventable bugs, by task).

---

## T0 — Scaffold + config
Create the tree from `skeleton_project_structure.md`: `.env.example`, `.gitignore` (incl. `.env`, `data/chroma/`), `requirements.txt` + `requirements-dev.txt`, `app/config.py` (pydantic-settings), `app/__init__.py`, `app/models.py` (StrEnums from design §3 at the **top of models.py**, then the Pydantic models — **no separate `enums.py`**). Move `policies/` in (with `load_pack.py`) and the `_v2` packs adopted (replacing v1) + `financial_services_us.yaml`.
- **Satisfies:** R8, R11 · **Design:** §2, §3, §4
- **Acceptance:** `python -c "import app"` succeeds; ruff + mypy clean; `.env.example` committed with no values; `.env` gitignored.

## T0.5 — Golden data + corpus seed (the acceptance target, before the UI)
Author the golden set **before any UI/backend** so every later task has a target to validate against (spec-driven, tests-first). No pipeline needed — negatives are pack-derived; positives are stubbed until the corpus is indexed (T4).
- Build **`data/corpus/energy/D8_substation_ceii.md`** (the CEII/OT trap doc) + a small companion seed (D1 CIP evidence, D2 FERC summary, D3 ops bulletin with a planted injection). D8's wording must contain the energy pack's `ceii`/`ot_asset` detector keywords so the detector fires.
- Seed **`golden/golden_energy.jsonl`**: the 9 negatives (6 universal + `rejects_unentitled_ceii` / `rejects_ot_command` / `rejects_realtime_grid_op`) + positive stubs (`expected_verdict: delivered`; citations filled at T4). The signature case is a **pair sharing one input** — `neg_unentitled_ceii` (`principal_entitlements: []`) and `pos_entitled_ceii` (`["ceii_cleared","ot_cleared"]`); the T10 harness builds each `Principal` from `principal_entitlements`.
- **Satisfies:** R2 (eval target) · **Design:** §3 (`GoldenRecord`), §12 (energy golden set)
- **Acceptance:** `golden_energy.jsonl` parses and every row is `GoldenRecord`-shaped; the `rejects_unentitled_ceii` row is present; D8 contains the `ceii`/`ot_asset` detector keywords verbatim. *(KNOWN_ISSUES T7 — the exact-wording guard now has a home.)*

## T1 — UI shell FIRST (against a stub backend)
Build `ui/app.py` (Streamlit) **from `ui_build_prompt.md`** — lead with **Option B (hybrid: structured task console + scoped Q&A)**; fall back to **Option A (pure task console)** if time is tight. **Not a bare chatbot.** Hard requirements: identity/entitlement banner ("authorized Northwind user — your access scopes what these agents can retrieve and answer"); the **two never-blurred states** DELIVERED (answer + expandable citations) and ROUTED FOR HUMAN REVIEW (shows `withhold_reason` + route, no answer); first-class expandable citations; plain-language surface + a collapsible "how this was checked" panel; a collapsible "audit / trace" affordance (hash-chained record for the last answer). Wire to a stub returning a canned `AnswerEnvelope` of each type.
- **Satisfies:** R7 · **Design:** §1, §5, §5b · **Spec:** `ui_build_prompt.md`
- **Energy tie-in:** the **ROUTED state is how the CEII signature negative reads on screen** — an unentitled user's request for substation protection-relay settings shows "routed for human review" with the entitlement reason, never a grounded CEII disclosure. Build the UI so that case is unmissable.
- **Acceptance:** app launches; **both** states render; citations expand; audit panel toggles; **visual** screenshots of DELIVERED *and* the unentitled-CEII ROUTED state. *(UI is weighted equal to backend — do not defer.)*
- **Say it:** *"I didn't default to a chatbot — for a non-technical regulated user the win is making the gate visible: a task console plus a scoped question box, where every answer shows whether it was delivered or routed, what it's cited to, and that it's audited."*

## T2 — Policy loader (load energy)
Wire `app/policy.py` over `load_pack.py`; load `policy_pack = "energy_utilities_us"` (deep-merges `_base`).
- **Satisfies:** R6, R10 · **Design:** §4, §12
- **Acceptance:** `test_policy_pack_load` — merged pack exposes base PII + `ceii`/`bcsi`/`ot_asset`; **7 prohibited** (4 universal + 3 energy) and **9 golden_negatives** (6 universal + 3 energy) present; energy `thresholds` override base; **assert `entitlements` + `golden_negatives` load** (regression guard). Engine reads `handling`, never `action`. *(KNOWN_ISSUES T2)*

## T3 — Skeleton graph (orchestrator + specialists + stub gate)
Build `app/orchestrator.py` + `app/agents/*` in LangGraph: orchestrator delegates to the retriever tool + ≥1 specialist; a **stub** gate for now; **one** synthesizer wired **only** to the gate's pass edge.
- **Satisfies:** R1 · **Design:** §1
- **Acceptance:** a request traverses orchestrator → retriever → specialist → gate(stub) → synthesizer; `test_synthesizer_unreachable_on_fail` (a forced fail cannot reach the synthesizer).

## T4 — Retriever tool + embeddings + Chroma (ingest energy corpus)
Implement the retriever behind a thin interface; embeddings = text-embedding-3-small (Nomic fallback by config); ChromaDB persisted under `data/chroma/`. Ingest `data/corpus/energy/` (NERC CIP standards/evidence, FERC orders, OT inventories, filings — synthetic where sensitive). Deterministic tie-break: score, then `chunk_id`.
- **Satisfies:** R3, R4, R13 · **Design:** §2, §12
- **Acceptance:** `test_retrieval_determinism`; energy corpus embedded and queryable; CIP-evidence query returns the controlling-standard chunk. Set `ANONYMIZED_TELEMETRY=False` (offline); sort top-k by `(score, chunk_id)`; one Chroma collection per embedding model. *(KNOWN_ISSUES T4)* Now that the corpus is indexed, verify/fill the positive `gold_citations` in `golden_energy.jsonl`.

## T5 — Guardrails (Presidio + policy classes), guard-first
Build `app/guardrails.py`: Presidio PII (base regex/NER classes) + the pack's `sensitive_classes` detectors (keyword + optional intent-classifier) + injection screen. Guard-first ordering.
- **Satisfies:** R6 · **Design:** §6, §7
- **Acceptance:** `test_pii_never_in_output`; `test_ignores_prompt_injection` (instruction embedded in an energy doc is not followed).

## T6 — Control-plane gate (deterministic floor → support → rubric)
Build `app/eval/gate.py` + `judge.py`: deterministic floor (schema → citation-span existence → lexical grounding → completeness) → **stage-2 support** (cross-family LLM-judge: span must entail claim) → **rubric judge** (faithfulness + relevance, every dim gates). Runtime: pass → deliver / fail+retries → bounded self-correct / exhausted → withhold + escalate.
- **Satisfies:** R2, R12 · **Design:** §1, §6
- **Acceptance:** `test_rejects_unsupported_span`, `test_empty_retrieval_withholds`, `test_conflicting_sources`.

## T7 — Entitlement enforcement (the energy signature)
Enforce `block_unless_entitled` against `principal.entitlements` in retrieval/guardrail; wire the energy `prohibited` rules (`no_ot_commands`, `no_unentitled_infra_disclosure`, `no_realtime_grid_ops`) to their `enforced_by` Controls; route withholds → `human:grid-compliance-reviewer`.
- **Satisfies:** R10, R13 · **Design:** §7, §12
- **Acceptance:** `test_vertical_signature_negative` — **unentitled user asks for substation protection-relay settings → withheld + routed** (`rejects_unentitled_ceii`); plus `rejects_ot_command`, `rejects_realtime_grid_op`. ⚠️ **Also `test_entitled_user_gets_ceii`** (entitled → delivered + cited) — proves it's an entitlement gate, not a blanket censor; verify the detector fires on the exact D8 wording. *(KNOWN_ISSUES T7)*

## T8 — Memory wiring
Session memory via the LangGraph checkpointer; working memory = `AgentState`; cross-session **off**.
- **Satisfies:** R5 · **Design:** §4
- **Acceptance:** session continuity within a thread; no cross-session write (memory-policy test).

## T9 — Audit (hash-chained JSONL + verify_chain)
Build `app/audit.py`: append-only `audit_log.jsonl`, each record `hash = sha256(prev_hash + canonical(payload))`, recording entitlement scope + gate results + verdict. Add `verify_chain()`.
- **Satisfies:** R9 · **Design:** §4
- **Acceptance:** `test_audit_chain_integrity` — tamper one record → `verify_chain()` fails at that record; log is never mutated/deleted.

## T10 — Golden harness: run + report (consumes the T0.5 seed)
Build `golden/golden_energy.jsonl`: happy-path CIP-evidence Q&A (DELIVERED, cited) + the 6 universal negatives + the 3 energy signature negatives. (Negatives derive from the pack's `golden_negatives`; positive gold answers/citations need the corpus + **hand-verify**.) Build `app/eval/harness.py` to run it and print pass@1 / per-dimension agreement / negative results.
- **Satisfies:** R2, R13 · **Design:** §5, §12
- **Acceptance:** harness runs end-to-end; all signature negatives pass; positives meet the energy thresholds.

## T11 — Full validation + customer one-pager
Run the 4-step validation across the whole suite. Produce the **plain-language one-pager** for a non-technical energy customer (no diagrams, no jargon) explaining how the agent solves their problem.
- **Satisfies:** all (esp. R7) · **Design:** §8
- **Acceptance:** ruff + mypy clean; full `tests/` green; app runtime-verified; UI visually validated (both states); one-pager passes the "would a non-technical buyer get it?" read.

---

## Test → requirement map (the acceptance matrix)
| Test | Requirement | Task |
|---|---|---|
| `test_policy_pack_load` | R6, R10 | T2 |
| `test_retrieval_determinism` | R3, R4 | T4 |
| `test_pii_never_in_output` | R6 | T5 |
| `test_ignores_prompt_injection` | R6 | T5 |
| `test_rejects_unsupported_span` | R2 | T6 |
| `test_empty_retrieval_withholds` | R12 | T6 |
| `test_conflicting_sources` | R12 | T6 |
| `test_synthesizer_unreachable_on_fail` | R1 | T3 |
| `test_vertical_signature_negative` (energy) | R10, R13 | T7 |
| `test_audit_chain_integrity` | R9 | T9 |

---

## Version history
v3 — 2026-06-16 · changed: added **T0.5 — Golden data + corpus seed** between T0 and T1 (spec-driven: author the golden set before the UI); renamed T10 to the run+report harness that consumes the T0.5 seed; T4 now verifies/fills positive citations. No renumber of T1–T11 (T-refs preserved).
v2 — 2026-06-16 · changed: **T2 acceptance** — removed the stale "adopt the `_v2` packs first" warning (the packs are adopted in `policies/`); the surviving guard is now stated as a `test_policy_pack_load` regression assertion (`entitlements` + `golden_negatives` load), alongside the existing "engine reads `handling`, never `action`."
v1 — 2026-06-16 · created: the ordered build doc of the spec-driven set — exploded `design.md` §9 into 12 discrete, individually-testable tasks (T0–T11), each citing its requirement + design section + acceptance check, with the blog's 4-step validation gate (compile/lint → tests → runtime → visual) applied per task; instantiated for the Energy & Utilities demo (energy corpus, `energy_utilities_us` pack, energy golden negatives incl. `rejects_unentitled_ceii`); added a test → requirement acceptance matrix. · then enriched **T1 (UI)** from `ui_build_prompt.md` — option choice (hybrid B, fallback A), the hard requirements, the say-it line, and the energy CEII-as-ROUTED-state tie-in.
