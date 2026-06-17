# KNOWN_ISSUES.md — preventable bugs (by build task)
*Read alongside `CLAUDE.md`. These are the failure modes this architecture invites. **Before marking any task in `tasks.md` done, check its guards here.** Each entry: the trap → the guard → what catches it.*

---

## Top guards — stack-ranked (likelihood × blast radius)
*The full per-task list below is the working reference; this is the triage. 🔴 = demo-killer, 🟡 = will-bite-at-build.*

| # | Guard | Task | Why it ranks here |
|---|---|---|---|
| 🔴 1 | **Test BOTH principals** — `test_entitled_user_gets_ceii` + the unentitled withhold; verify the detector fires on the exact demo doc | T7 | The on-camera money shot. A missed keyword = a CEII disclosure on the recording, or a blanket censor that blocks the entitled analyst too. |
| 🔴 2 | **`@st.cache_resource` the graph + Chroma client; wire the toggle to re-invoke** | T1 | Toggle-no-op kills the entitled/unentitled flip; rebuild-on-keystroke makes the demo crawl. |
| 🔴 3 | **Chroma `ANONYMIZED_TELEMETRY=False` + lazy client init** | T4/T0 | A live network call that breaks the zero-keys/offline claim you're selling. |
| 🔴 4 | **Deterministic retrieval order — sort by `(score, chunk_id)`** | T4 | Flaky test, and the demo behaves differently in rehearsal vs recording. |
| 🟡 5 | **Canonical audit serialization** — `model_dump(mode="json")`, `sort_keys=True`, `default=str` | T9 | `verify_chain()` flakes nondeterministically; the tamper-demo is part of the pitch. |
| 🟡 6 | **LangGraph list reducers + attempt cap + `recursion_limit`** | T3 | Parallel-state clobber throws at build; unbounded retry = `GraphRecursionError`/runaway cost. |
| 🟡 7 | **Mock the judge in unit tests; assert cross-family ≠ same-model** | T6 | Judge nondeterminism flakes CI; in stub mode the separation silently collapses to self-grading. |
| 🟡 8 | **Tune base PII regexes against the corpus** (don't redact CIP/standard numbers) | T5 | `\b\d{8,17}\b` eats requirement numbers/dates → garbled answers + broken citations. |
| 🟡 9 | **`python -m spacy download en_core_web_sm` in setup** | T0 | Instant Presidio crash; trivial to prevent, easy to forget. |

**Everything below this is hygiene-tier or only bites under specific conditions** (Pydantic-vs-`TypedDict` state, override-vs-append merge, single-writer audit, `thread_id` scoping, dependency pinning, latency pacing) — keep them, but don't sweat them until they surface at their task.

---

## Cross-cutting (applies to the whole build)
- **Offline-first leaks.** Hidden network calls break the zero-keys/offline claim: Chroma telemetry, LangFuse, HuggingFace/spaCy model downloads, and LLM clients instantiated at import. **Guard:** set `ANONYMIZED_TELEMETRY=False`; lazy-init all model clients (never at module top); pre-download spaCy/NLI models in setup; gate any LangFuse call behind a config flag.
- **AI-built-code drift.** Claude Code may "helpfully" collapse the two specialists into one, make retrieval the spine, write the answer in two places, or let a failed gate reach the synthesizer. **Guard:** the invariants in `CLAUDE.md` + the negative tests — *run* them, and read *why* each passes.
- **Dependency churn.** `langchain`/`langgraph`/`chromadb` APIs move fast; `>=` floors let a breaking newer version in. **Guard:** start loose, **pin a lockfile once green** (T11).
- **Latency.** Orchestrator → 2 specialists → guardrails → 3-stage gate → (retry) → synthesizer is many sequential LLM calls; a query can take 30–60s+. **Guard:** parallelize the safe parts, cache, and don't demo questions that sit on the threshold boundary.

---

## T0 — Scaffold + config
- **spaCy model missing** → Presidio crashes at runtime. **Guard:** `python -m spacy download en_core_web_sm` in setup; assert it loads.
- **Eager client init breaks zero-keys.** **Guard:** read config via `pydantic-settings`; construct Anthropic/OpenAI/Chroma clients lazily; provide a true stub path when keys are absent.
- **Telemetry env.** **Guard:** `ANONYMIZED_TELEMETRY=False` in `.env.example` / config.

## T1 — UI
- **Streamlit reruns top-to-bottom every interaction** → the graph + Chroma client get rebuilt (and re-embed) on every keystroke. **Guard:** `@st.cache_resource` the client and the compiled graph; never build them at module top.
- **The entitled/unentitled toggle no-ops.** If the principal is read once at load, flipping the banner doesn't re-invoke. **Guard:** the toggle must re-run the pipeline with the new `Principal`.
- **Silent hang.** A 40s pipeline with no feedback reads as a crash. **Guard:** wrap in `st.status`/spinner.
- **States blurred.** **Guard:** render DELIVERED vs ROUTED visually distinct (color/icon/layout), not just different text.

## T2 — Policy loader
- **Pack completeness regression.** The v2 packs are adopted in `policies/`; the standing guard is the assertion, not a reminder. **Guard:** `test_policy_pack_load` asserts the loaded merged pack exposes `entitlements`, `golden_negatives`, and the base PII rules — so a future pack edit can't quietly drop them.
- **`handling` vs `action`.** The v2.1 schema uses `handling` on `sensitive_classes`. **Guard:** the engine reads `handling`, never `.action`.
- **Entitlement-string mismatch.** `ceii_cleared` vs `ceii-cleared` silently blocks everyone or no one. **Guard:** centralize entitlement IDs in one constant/enum used by both pack and principal.
- **Override vs append.** Deep-merge *concatenates* base+vertical lists; a vertical can't override a base rule, and same-`id` rules duplicate. **Guard:** keep ids unique; only append.

## T3 — Graph (LangGraph)
- **Parallel nodes clobber shared state** → "can receive only one value per step," or a lost write. **Guard:** annotate list fields with a reducer (`Annotated[list, operator.add]`); don't let two nodes write the same scalar key.
- **Unbounded retry** → `GraphRecursionError` / runaway cost. **Guard:** increment *and* check `attempts`; set a `recursion_limit`.
- **Synthesizer reachable on fail.** **Guard:** wire it only to the gate's pass edge; `test_synthesizer_unreachable_on_fail` must exercise a forced fail.
- **Pydantic state friction.** A Pydantic `BaseModel` graph state can fight partial updates. **Guard:** if updates "don't take," consider `TypedDict` state.

## T4 — Retriever / embeddings / Chroma  ⚠️ DEMO-CRITICAL
- **"Determinism" that isn't.** HNSW is approximate; ties aren't ordered → `test_retrieval_determinism` flakes. **Guard:** sort top-k by `(score, chunk_id)` explicitly; pin the collection.
- **Embedding-dim mismatch.** 1536-dim ↔ 768-dim against one collection = error. **Guard:** one collection per embedding model; rebuild on switch.
- **Chroma telemetry** = a live network call. **Guard:** `ANONYMIZED_TELEMETRY=False`.
- **Citation-span false negatives.** A paraphrased span fails an exact-match check → good answers withheld. **Guard:** decide exact vs normalized span matching up front.

## T5 — Guardrails / PII
- **Greedy PII regexes on a numbers-heavy corpus.** `\b\d{8,17}\b` redacts CIP numbers, dates, IDs → garbled answers + broken citations. **Guard:** tune the base regexes against the actual corpus; verify they don't eat standard/requirement numbers.
- **Redaction breaks the cited span.** **Guard:** redact in the *output*, preserve the retrieved span the gate checks against (order of operations).
- **Starter keyword detectors miss real content.** **Guard:** verify the vertical's `sensitive_classes` keywords actually fire on your corpus's wording (see T7).
- **Injection screen scope.** **Guard:** screen *retrieved* content (and the query) as data; never follow embedded instructions.

## T6 — Control-plane gate  (calibration)
- **Judge nondeterminism flakes tests.** **Guard:** mock the judge with fixtures in unit tests; live LLM-judge only in the harness.
- **Cross-family separation collapses in stub mode** → a model grades itself. **Guard:** assert judge family ≠ generator family (or skip+flag in stub mode).
- **Threshold miscalibration** → everything routes (looks broken) or nothing routes (looks fake). **Guard:** calibrate entailment/rubric against the golden set before the demo.
- **Numbers slip through entailment.** **Guard:** run a deterministic numeric/temporal check *before* the LLM-judge.

## T7 — Entitlement enforcement  ⚠️ DEMO-CRITICAL (the money shot)
- **Can't tell a real gate from a keyword censor.** **Guard:** test BOTH principals — `test_vertical_signature_negative` (unentitled → withheld) **and** `test_entitled_user_gets_<class>` (entitled → delivered, cited). If only the first exists, a blanket censor that also blocks the entitled analyst passes — and your demo flip looks broken.
- **Detector misses the demo doc.** If the keyword list doesn't match the synthetic D8 wording, the unentitled user gets the CEII answer on camera. **Guard:** assert the detector fires on the *exact* corpus doc; test the unentitled path hardest.
- **Opaque withhold.** **Guard:** the routed state names *why* in plain language ("infrastructure-sensitive / not entitled — routed").

## T8 — Memory
- **Session bleed across users.** **Guard:** scope the checkpointer by `thread_id`; don't reuse a thread across principals.
- **Cross-session persistence creeping back** via a persistent checkpointer. **Guard:** assert no cross-session write (tier-3 off).

## T9 — Audit (hash-chain)
- **Non-canonical serialization** → `verify_chain()` fails nondeterministically (dict key order, float/datetime/enum formatting). **Guard:** `json.dumps(record.model_dump(mode="json"), sort_keys=True, default=str)`; freeze it.
- **Logging a live reference**, not a snapshot → every record reflects the *final* state. **Guard:** deep-copy the state slice at write time.
- **Concurrent appends corrupt the chain.** **Guard:** single-writer append.

## T10 — Golden set + harness
- **Golden set written to your assumption, not the gate's behavior.** **Guard:** refine it against what the gate actually does (calibration loop).
- **Positives need the corpus.** The YAML gives you the negatives' structure; `gold_answer`/`gold_citations` for positives need the corpus + hand-verify.

## T11 — Validation + one-pager
- **False-green negatives.** A negative passing for the *wrong* reason (out-of-scope refusal masquerading as an entitlement block). **Guard:** read *why* each negative passes.
- **Unpinned deps.** **Guard:** pin the lockfile now that it's green.
- **4-step validation** per `CLAUDE.md`: lint → tests → runtime → visual.

---

## Demo-day rehearsal (run-of-show — actions, not bugs)
*Bug-prevention lives in the Top 10; this is what to actually rehearse. Most of it points back to the 🔴 rows.*
- **Dry-run the entitled → unentitled flip** (Top 10 #2/#3) until it's one clean toggle on screen — this is the moment the whole pitch turns on.
- **Pick boundary-safe demo questions** — clearly in-scope or clearly blocked, never on the threshold edge — so the gate behaves identically in rehearsal and on camera (Top 10 #5).
- **Pace for latency** — a 40s pipeline needs a spinner + a sentence of narration so it doesn't read as a hang; parallelize/cache first.
- **Have the audit tamper-demo loaded** — run `verify_chain()`, alter a record, show it fail (Top 10 #6).

---

## Version history
v3 — 2026-06-16 · changed: retired Top-guard #1 ("adopt the `_v2` packs before any run") — the packs are adopted, so the surviving guard is now a `test_policy_pack_load` assertion (entitlements + golden_negatives present), not a remember-to-adopt warning; renumbered the table to 9 rows and dropped the hard "10" from the heading; removed the **⚠️ DEMO-CRITICAL** tag from the T2 section.
v2 — 2026-06-16 · changed: added a **stack-ranked Top 10** (likelihood × blast radius, 🔴 demo-killer / 🟡 will-bite-at-build) at the head for triage; kept the full per-task list below as the working reference and tagged the long tail as hygiene-tier; **reframed the redundant "Demo-day top 3" into a distinct run-of-show rehearsal checklist** that points back to the Top 10 rather than re-listing them.
v1 — 2026-06-16 · created: preventable-bug guards for the governed-agent build, organized by `tasks.md` task (T0–T11) plus cross-cutting (offline leaks, AI-build drift, dependency churn, latency) and a demo-day top-3. Read alongside `CLAUDE.md`; check the matching task's guards before marking it done.
