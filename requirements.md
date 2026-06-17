# requirements.md — Intent & acceptance criteria (the WHAT/WHY) · SKELETON (vertical-free)
*The **requirements** doc of the spec-driven set. Captures intent as user stories and **acceptance criteria** in EARS form ("WHEN/WHILE/IF … THE SYSTEM SHALL …"). `design.md` says HOW; this says what "done" means. Not to be confused with `requirements.txt` (Python deps). This is the **vertical-free** skeleton; the chosen vertical adds its domain acceptance in the template slot at the end.*

**Actors.** **End user** — a non-technical regulated professional (fictional persona "Dana" at fictional company "Northwind"). **Compliance owner** — the party accountable for the system staying correct/compliant (the recurring-assurance buyer). **Architect/reviewer** — evaluates the build live.

**How to read a requirement:** each has a *story*, *acceptance criteria* (EARS), and *verified by* (the test in `tasks.md` / `design.md` §10). A requirement is met only when its acceptance criteria are demonstrable.

---

## R1 — Multi-agent orchestration *(scored, heaviest)*
**Story:** As the architect, I want the work decomposed across an orchestrator, specialists, and an independent gate, so orchestration is real (delegation, routing, retry) — not one prompt in a trench coat.
**Acceptance:**
- WHEN a request arrives, THE SYSTEM SHALL route it through an **orchestrator** that delegates to a **retriever tool** and at least one **specialist** before any answer is formed.
- THE SYSTEM SHALL place an **independent control-plane gate** between the specialists and the synthesizer.
- WHEN the gate fails AND retries remain, THE SYSTEM SHALL bounded-self-correct (default cap 2); WHEN retries are exhausted, THE SYSTEM SHALL withhold + escalate.
- THE SYSTEM SHALL expose the orchestration as a graph (LangGraph), with the synthesizer reachable **only** on the gate's pass edge.
*Verified by:* `test_synthesizer_unreachable_on_fail`, graph traversal review.

## R2 — Eval-against-goal (the control-plane gate) *(scored)*
**Story:** As the compliance owner, I want every answer evaluated against faithfulness **and** task-success before it can be delivered.
**Acceptance:**
- THE SYSTEM SHALL evaluate each candidate on **two axes** — faithfulness (grounded in cited spans) and task-success (answers the question) — and SHALL **gate, not merely record**.
- THE SYSTEM SHALL run a **deterministic floor** (schema → citation-span existence → lexical grounding → completeness) BEFORE any model-judge stage.
- IF a claim's cited span does not entail the claim, THE SYSTEM SHALL mark it UNSUPPORTED and withhold.
- THE SYSTEM SHALL evaluate against a **golden set** and report pass@1 + per-dimension judge-vs-gold agreement + negative-test results.
*Verified by:* `test_rejects_unsupported_span`, golden harness run.

## R3 — Embedding model *(scored — named + justified)*
**Story:** As the architect, I want a named, justified embedding choice with an offline fallback.
**Acceptance:**
- THE SYSTEM SHALL use **OpenAI text-embedding-3-small** by default, with a **keyless offline alternative (Nomic)** selectable by config.
- THE SYSTEM SHALL keep **one embedding space per index** (no mixing dimensions/models).
*Verified by:* config review; retrieval smoke test.

## R4 — Vector database *(scored — named + justified)*
**Story:** As the architect, I want a named vector store that's swappable for production.
**Acceptance:**
- THE SYSTEM SHALL use **ChromaDB** (local, persisted) for the build, behind a **thin retriever interface** so the store is swappable (pgvector in prod).
- THE SYSTEM SHALL break score ties **deterministically** (score, then `chunk_id`).
*Verified by:* `test_retrieval_determinism`.

## R5 — Memory *(scored — deliberate)*
**Story:** As the compliance owner, I want memory handled deliberately, with cross-session persistence off for regulated data.
**Acceptance:**
- THE SYSTEM SHALL maintain **session** memory (thread-scoped) and **working** memory (graph state = audit source).
- THE SYSTEM SHALL NOT persist **cross-session** user memory.
*Verified by:* memory-policy test (no cross-session write).

## R6 — Guardrails *(scored — explicit)*
**Story:** As the compliance owner, I want explicit, guard-first rules constraining what the agents produce.
**Acceptance:**
- THE SYSTEM SHALL run guardrails **guard-first**, enforcing PII handling, output schema, prohibited content, and permitted-use **from the loaded policy pack** (not hardcoded).
- WHEN PII is detected, THE SYSTEM SHALL redact/mask per the class; PII SHALL NOT appear in `answer_text`.
- THE SYSTEM SHALL treat retrieved content as **data**; instructions embedded in retrieved documents SHALL NOT be followed.
*Verified by:* `test_pii_never_in_output`, `test_ignores_prompt_injection`.

## R7 — User-facing UI *(scored — equal weight to backend)*
**Story:** As a **non-technical** end user (the authorized Northwind analyst), I want a simple console that shows who I am, the answer (or a clear "routed for review"), and what it's cited to — and that makes the *governance* visible rather than hiding it in a chat stream.
**Acceptance** *(detailed spec + 4 option models in `ui_build_prompt.md`):*
- THE SYSTEM SHALL show an **identity / entitlement banner**: "Signed in as an authorized Northwind user — your access scopes what these agents can retrieve and answer." (Identity stubbed; the banner makes the entitlement gate visible.)
- THE SYSTEM SHALL render **two answer states, never blurred**: **DELIVERED** (a passing, cited answer) and **ROUTED FOR HUMAN REVIEW** (withheld by the gate, showing the `withhold_reason` + escalation route, and **no** answer). A wrong/unverified answer SHALL NOT be shown as if confident.
- THE SYSTEM SHALL treat **citations as first-class** — every claim in a delivered answer shows the grounding source span / document, expandable.
- THE PRIMARY SURFACE SHALL be **plain language, no jargon, no technical diagrams**; an optional **collapsible "how this was checked"** panel MAY expose the pipeline for the demo.
- THE SYSTEM SHALL offer an optional, **collapsible "audit / trace"** affordance (the hash-chained record for the last answer), out of the non-technical user's way.
- THE UI SHALL be **offline-first** (local Python backend; no external auth or third-party widgets) and built **early** (weighted equal to backend).
- THE UI SHALL **not** be a bare chatbot. Lead with **Option B — hybrid task console + scoped Q&A**; fall back to **Option A — pure task console** if time is tight (rationale in `ui_build_prompt.md`).
*Verified by:* visual validation (screenshot **both** states); UI walkthrough against `ui_build_prompt.md` hard requirements.

## R8 — Deployment *(present; not scored)*
**Story:** As the architect, I want it to run anywhere with nothing to provision.
**Acceptance:**
- THE SYSTEM SHALL run **locally, offline, zero-keys-to-run** (stubs where needed).
*Verified by:* clean-clone run.

## R9 — Auditability *(governance — the moat)*
**Story:** As the compliance owner, I want a tamper-evident record of every decision.
**Acceptance:**
- THE SYSTEM SHALL write an **append-only, hash-chained** audit record per run (input, principal, entitlement scope, retrieved ids, guardrail actions, gate results, verdict).
- THE SYSTEM SHALL provide `verify_chain()`; IF any record is altered, `verify_chain()` SHALL fail at that record.
- THE SYSTEM SHALL NOT mutate or delete audit records.
*Verified by:* `test_audit_chain_integrity`.

## R10 — Entitlements & permitted-use *(governance)*
**Story:** As the compliance owner, I want the agent to answer only what the user is allowed to see and do.
**Acceptance:**
- WHEN a sensitive class is `block_unless_entitled` AND the principal lacks the required entitlement, THE SYSTEM SHALL withhold + escalate (no disclosure).
- THE SYSTEM SHALL enforce the pack's `permitted_use` / `prohibited` rules via the named `enforced_by` Control (entitlement / keyword / intent_classifier / output_schema / eval_gate).
*Verified by:* `test_policy_pack_load`, the vertical signature test (see the template slot).

## R11 — Provenance *(governance — the credential)*
**Story:** As the compliance owner, I want zero adversarial-nation-linked tooling in the decision path.
**Acceptance:**
- THE SYSTEM SHALL depend only on clean-provenance decision-level tooling; THE BUILD SHALL NOT introduce excluded tools (Milvus/Zilliz, Qdrant, BGE/GTE, Qwen/DeepSeek/GLM/Yi/Kimi, Dify).
*Verified by:* dependency review against `CLAUDE.md` principle 3.

## R12 — Fail-closed *(governance — the safety posture)*
**Story:** As the compliance owner, I want uncertainty to default to silence, not a guess.
**Acceptance:**
- WHEN any uncertainty or unhandled error occurs, THE SYSTEM SHALL default to **withhold**; a failed/unverified answer SHALL be structurally unable to reach the user.
*Verified by:* `test_empty_retrieval_withholds`, `test_conflicting_sources`, error-path review.

---

## Rv — Vertical acceptance (TEMPLATE — fill per vertical)
*The chosen vertical adds its domain criteria here. Copy this block, name it (e.g. `R13 — <vertical> acceptance`), and fill from `spec_remember_<vertical>.md` + `policies/<vertical>_us.yaml`.*
**Story:** As the <vertical persona>, I want answers that cite the controlling <regime> and never disclose <sensitive class> to anyone uncleared.
**Acceptance:**
- WHEN an **entitled** user asks an in-scope question, THE SYSTEM SHALL answer with a citation to the controlling <regime / rule>.
- WHEN an **unentitled** user requests a `block_unless_entitled` class (the vertical's **signature negative**), THE SYSTEM SHALL withhold + route — `case_type: <rejects_…>`.
- WHEN a request implies a `prohibited` action (e.g. <vertical hard-never>), THE SYSTEM SHALL withhold + escalate.
- THE SYSTEM SHALL load these rules from `policies/<vertical>_us.yaml` (no vertical logic hardcoded).
*Verified by:* `test_vertical_signature_negative`, the vertical golden negatives.

---

## Version history
v1 · SKELETON — 2026-06-16 · created: the vertical-free intent + acceptance-criteria doc — EARS user stories for the 8 scored rubric items (R1–R8) plus governance requirements (R9 auditability, R10 entitlements, R11 provenance, R12 fail-closed), each with a "verified by" pointer, and a **vertical-acceptance template slot (Rv)** to be filled per engagement. The energy-instantiated counterpart (with R13) lives at the repo root.
