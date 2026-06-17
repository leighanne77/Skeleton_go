# If I have more time for the Prototype
*The production upgrades I'd speak to — and, for each, the exact steps to add it to the skeleton. These are deliberately **not** built in the 2.5-hour session; they're the "what I'd do with more time" answers, each grounded in a concrete change to the repo. Skeleton paths refer to the layout in `skeleton_project_structure.md` (`app/eval/`, `app/agents/`, `app/audit.py`, `golden/`, `policies/`, `.env` / `app/config.py`).*

---

## a. Overall — the stage-2 NLI support tier (production design)
Stage-2 support runs as an **LLM-judge in the build** (fastest, already in the stack — it lives in `app/eval/gate.py`, calling `app/eval/judge.py`). The production upgrade I'd speak to — and what I'd spend the extra time building — is to turn that one function into a **dedicated, tiered NLI support check**. Everything below (b–g) upgrades that single seam; (h) is the other production upgrade I'd reach for.

*Where it plugs in:* `app/eval/gate.py` already does deterministic floor → **stage-2 support** → rubric judge. Only the stage-2 support call changes.

---

## b. ☐ Swap in a dedicated NLI support tier
A small encoder-based NLI classifier (DeBERTa-style; provenance-check the checkpoint). Entailment / neutral / contradiction + confidence; local, keyless, reproducible, cheap per claim, logs a discrete label+score = clean audit record.

**Steps to add it to the skeleton:**
1. Create `app/eval/nli.py`. Add `load_nli()` that loads a small local NLI checkpoint (DeBERTa-v3-MNLI class — the DeBERTa architecture is Microsoft-origin/clean, but provenance-check the *specific* fine-tuned checkpoint per §1) onto **CPU**, cached at module load.
2. Expose `nli_entail(premise: str, hypothesis: str) -> tuple[str, float]` → `("entailment"|"neutral"|"contradiction", confidence)`.
3. Make it reproducible/offline: pin the exact checkpoint + revision hash in `requirements.txt` (or a `models/MODELCARD.md`), download once into a local `models/` dir, so the run stays **keyless**.
4. Add `STAGE2_BACKEND=llm|nli` to `.env` and `app/config.py` (default `llm` for the demo profile, `nli` for the prod profile).
5. In `app/eval/gate.py`, branch the stage-2 support call on `STAGE2_BACKEND`: `nli` → `app/eval/nli.py`; else the existing `app/eval/judge.py`.
6. In `app/audit.py`, log per claim `{claim, premise, label, score, backend}` — the discrete verdict is the auditable record.

---

## c. ☐ Nail input construction (makes or breaks it)
Decompose the answer into atomic single-sentence claims; premise = the cited span expanded to its surrounding sentence; hypothesis = the atomic claim.

**Steps to add it to the skeleton:**
1. Create `app/eval/claims.py`.
2. `atomize(answer) -> list[str]`: sentence-split the answer into atomic single-sentence claims (start with a sentence splitter; upgrade to clause-splitting when one sentence carries two claims — NLI degrades on multi-claim paragraphs).
3. `expand_span(citation, corpus) -> str`: return the cited chunk **plus its neighbouring sentence(s)** as the premise (enough context for entailment).
4. In `gate.py` stage-2: for each `claim` in `atomize(answer)`, build `(premise = expand_span(cite, corpus), hypothesis = claim)` and pass each pair to the support check.

---

## d. ☐ Decision logic per claim
Entailment ≥ threshold → supported · contradiction → hard fail (the "not covered" vs "covered" polarity case) · neutral → unsupported. Pass stage 2 only if every claim passes; a failing claim names itself for the repair loop.

**Steps to add it to the skeleton:**
1. In `gate.py`, implement the per-claim verdict: `score ≥ τ` & `entailment` → **supported**; `contradiction` → **hard fail** (short-circuit the whole answer — the polarity case); `neutral` → **unsupported**.
2. Stage-2 passes **only if every claim is supported**.
3. On any failing claim, attach `{claim_text, verdict, premise}` to the failure reason returned to the orchestrator — so the claim **names itself** for the bounded self-correct loop.
4. Keep the existing runtime wiring: fail-with-retries → self-correct → exhausted → **withhold + escalate (HITL)**.

---

## e. ☐ Calibrate
Tune the entailment threshold per domain against the golden set; run the `rejects_unsupported_span` negative test (literally an NLI contradiction/neutral case).

**Steps to add it to the skeleton:**
1. Add jargon / polarity / neutral cases to `golden/golden.jsonl` with hand-verified per-claim `expected_verdict`.
2. Add `app/eval/calibrate.py` (or extend `app/eval/harness.py`) to **sweep τ** over the golden set and report per-domain agreement; pick τ **per domain** and store it as `entailment_threshold` in the vertical's `policies/<vertical>.yaml` (so the threshold is part of the loaded policy pack) or in `app/config.py`.
3. Keep the `rejects_unsupported_span` negative test green — it's an NLI contradiction/neutral case by construction.

---

## f. ☐ Handle the known weaknesses
Domain/legal/financial jargon → FEVER-style fact-verification model or fine-tune on domain pairs (LLM-judge as backstop) · long premises → window the span · multi-hop claims → decompose further or route to the judge · numeric/temporal (deductibles, dates, $) → deterministic numeric checks (NLI is weak there).

**Steps to add it to the skeleton:**
1. **Jargon:** add a `support_model` config in `app/config.py`; swap the generic MNLI checkpoint for a **FEVER-style fact-verification** checkpoint (claim-vs-evidence, closer to the citation task) or fine-tune on domain pairs. Route any claim with `score < τ_conf` to `app/eval/judge.py` as the backstop.
2. **Long premises:** in `expand_span` (`app/eval/claims.py`), window the span to a max-token budget around the citation.
3. **Multi-hop claims:** in `atomize`/`gate.py`, if a claim needs several spans, decompose further or route it to the judge.
4. **Numeric/temporal:** add `app/eval/checks_numeric.py` with deterministic comparisons (deductibles, dates, $) and run it **in the deterministic floor, before NLI** — NLI is weak on numbers, so don't let it judge them.

> **Say it:** *"Yes, I bake the domain's jargon and its hard negatives into the golden set — that's how I measure and calibrate it. But the golden set detects the failure; the handling is in the tier — a domain-tuned support model with the judge as the backstop for the cases it's unsure on."*

---

## g. ☐ Build it as a tier, not a swap
Deterministic numeric/format → dedicated NLI (cheap, handles most) → LLM-judge backstop only for the ambiguous + multi-hop residue. Deterministic-first, judge-last.

**Steps to add it to the skeleton:**
1. In `gate.py`, order stage-2 as a **cascade**: (i) deterministic numeric/format (`checks_numeric.py`) → (ii) dedicated NLI (`nli.py`) for entailment, handles most → (iii) LLM-judge (`judge.py`) backstop only for low-confidence + multi-hop residue.
2. **Route by confidence:** NLI decides a claim when `score ≥ τ_conf`; otherwise that single claim escalates to the judge. Log **which tier decided each claim** in `app/audit.py`.
3. Deterministic-first, judge-last — the same posture as the rest of the gate.

> **Say it:** *"For the prototype I run stage-2 support as an LLM-judge — fastest to stand up and already in the stack. In production I'd move it to a dedicated NLI tier: small, local, reproducible, cheap per claim, with a discrete auditable verdict — and keep the judge as the backstop for the ambiguous and multi-hop cases."*

---

## h. ☐ Identity in prod
Entitlement-filtered retrieval (the **HP $40B exchange** model) — the agent only retrieves what the user is entitled to see.

**Steps to add it to the skeleton:**
1. In `app/agents/retriever.py`, add an `entitlements` parameter (derived from the authenticated principal) and **filter the index query by entitlement at retrieval time** — the agent can only retrieve what the user is cleared to see.
2. **Demo seam:** stub the principal in `ui/app.py` (the identity banner) and pass a stubbed `entitlements` set into the retriever, so the seam exists on screen even though identity is stubbed.
3. **Production store:** keep entitlement scope on the vector rows (metadata) or in a join table so the filter is a SQL `WHERE` clause — this is exactly why **pgvector-in-Postgres** is the production default: entitlements (and the audit log) live **beside** the vectors, under one access model.
4. In `app/audit.py`, record the **entitlement scope used for each retrieval** (who asked, what scope, what was returned) — entitlement is auditable like everything else.

> **Say it:** *"Identity is stubbed in the demo, but the seam is real — retrieval is entitlement-filtered, so in production the agent only ever sees what the asker is cleared for, and that scope is in the audit record."*

---

## Version history
v2 — 2026-06-16 · changed: added the **jargon say-it** to item f ("I bake the domain's jargon and hard negatives into the golden set — the golden set detects, the tier handles, judge as backstop").
v1 — 2026-06-16 · created: extracted the stage-2 NLI support-tier production design (a–g) and the identity-in-production answer (h) out of the build checklist into a standalone "if I have more time" doc, and added **exact skeleton steps** to each item (file-by-file: `app/eval/nli.py`, `claims.py`, `checks_numeric.py`, `calibrate.py`, gate cascade, retriever entitlements, audit logging).
