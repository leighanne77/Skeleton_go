# Prototype Interview — Unified Build Plan

## Rubric self-audit — can I get the points?

A glance at where the eight scored items stand. **✓** locked · **◐** needs one more thing · **—** not scored. All scored items now have an answer on paper; #8 is the only **—** because deployment isn't scored. The remaining work is *building and rehearsing*, not deciding.

| # | Scored item | Points? | What clinches it |
|---|---|---|---|
| 1 | Multi-agent orchestration — *heaviest lens* | ✓ | Named pattern (orchestrator-workers + evaluator-optimizer gate), genuinely multi-agent (independent verifier), agentic (runtime routing/retry), deliberately not a swarm. |
| 2 | LLM eval framework / orchestration | ✓ | Eval against a defined target; faithfulness + task-success both gate; calibrate the judge against the golden set. |
| 3 | Embedding model | ✓ | OpenAI text-embedding-3-small, named with a cost/latency/quality justification. |
| 4 | Vector database | ✓ | Chroma (build) → pgvector (prod), named and justified. |
| 5 | Memory | ✓ | Three deliberately-scoped tiers: session state · agent working memory · no cross-session memory by design — entitlement-scoped and audited like retrieval. |
| 6 | Guardrails | ✓ | Deterministic hard rules (PII, schema, permitted-use), guard-first, distinct from eval. |
| 7 | User-facing UI | ✓ | Built first, plain-language, governance-visible states (deliver / routed-for-review) + identity banner. |
| 8 | Deployment | — | Local / offline-first, zero keys; cloud path spoken if asked. Explicitly not scored. |

**It's a supervisor topology — orchestrator-workers — with an evaluator-optimizer gate.**

![Agent infrastructure — our framing](agent_infrastructure_our_framing.svg)

It's an orchestrator-workers topology with an evaluator-optimizer gate. Multi-agent because there are independent, specialized agents plus an independent verifier — not one model doing everything. Agentic because routing and the retry-or-withhold decision are made at runtime, not hard-coded. **I deliberately did not build a swarm: in a regulated setting, predictable, auditable control flow beats emergent autonomy.**

*One governed perimeter wraps everything. Evaluation is pulled out of the harness into its own **Assurance** gate. Observability and **Auditability** are split — auditability is the moat. Identity scopes retrieval. Runtime flows harness → assurance.*

> **This governed perimeter is the *technical half* of Perficient's PACE in code.** **Policies** = the compliance boundary and permitted-use rules (HIPAA/GDPR, data contracts). **Controls** = the technical guardrails, eval-against-goal, monitoring, and tamper-evident audit — most of the perimeter. The other two PACE pillars are *organizational*, around the system: **Advocacy** = enterprise adoption and stakeholder buy-in; **Enablement** = the training, tools, and workflows teams use — surfacing here as the plain-language UI. The framework (LangGraph/LangFuse) is the data plane; PACE is the control plane on top — and that's the part that isn't commoditized.

> **Note — HIPAA and EU data-privacy (GDPR) are *not built* in the prototype; they're named as the production overlay, and here's why.** The demo runs offline on synthetic data (Northwind), with no real PHI or personal data — so those obligations don't legally attach to it. And compliance isn't a code feature you bolt on in 2.5 hours: it's an organizational + infrastructural program (BAAs with vendors, data-residency/region controls, DPAs, data-subject-rights tooling, retention schedules, a formal compliance review). What the prototype *does* show is the **architecture compliance plugs into** — entitlement-scoped retrieval, the withhold gate, and the tamper-evident audit trail are exactly the hooks HIPAA/GDPR attach to. So the honest line is: **"I build the hooks compliance plugs into; I don't fake the compliance itself."** That's the same discipline as stubbing identity on purpose — name the production layer, don't pretend the demo is it.

**BLUF.** The session is ~2.5 hours, live and recorded, with an architect in the room. The scenario is chosen on the day from a few cross-industry options, so the thing actually being tested is architecture, not domain knowledge — every scored item is scenario-independent. The winning posture is **one reusable governed-agent skeleton** plus pre-room homework that can't be done live. Walk in with all eight scored items pre-answered and the skeleton already built and explainable. Every choice ladders back to one claim: *I can ship defensible agentic systems in regulated industries.*

## First move in the room (before any code)
Once you've picked the scenario, the first thing you do on screen is **write the spec and the golden-dataset needs** — define what "correct" means for this task and what the labeled set has to contain. Everything downstream (gate thresholds, which checks fire, the eval) is undefined until that exists. Doing this first sequences the build correctly *and* signals that you work spec-first and eval-first — the most senior-reading habit you can show. (Distinct from your pre-staged golden sets; those cover your default scenarios, this covers whatever the menu actually hands you.)

### How to do it (spec-first, eval-first)

**A · Write the spec (define "correct" before anything else).**
1. **One-sentence task definition** — input → output. ("Given a 100-page composite quote, extract the 80+ named fields into a structured record with a citation per field.")
2. **Define "correct" on the two gating axes** — *faithfulness* (every claim grounded in a retrieved span) **and** *task-success* (the output is what was actually asked, in the right shape). Both gate. Write the success criteria as testable assertions, not adjectives.
3. **List the guardrail constraints** — PII handling, output schema/format, prohibited content, permitted-use. These are hard rules, separate from the eval.
4. **Enumerate the failure modes to catch** — hallucinated field, citation that doesn't support its claim, wrong outcome, out-of-scope ask, policy violation. Each one becomes a `case_type`.
5. **State the withhold/escalate policy** — the exact conditions under which the system must *refuse and route to a human* rather than answer (e.g., unsupported claim, empty retrieval, low judge confidence).
6. **Set the thresholds you'll be judged against** — target pass@1 / functional accuracy, the entailment/support threshold, and the judge-vs-gold agreement you'll accept per dimension. (You can tune these later, but name them now so the eval has a target.)

**B · Define the golden-dataset needs (what the labeled set must contain).**
1. **Per-example fields:** `input` (query + the retrievable context/corpus), `gold_answer` (or gold outcome/record), `gold_citations` (which source spans support each claim), `expected_verdict` (deliver vs withhold), and a `case_type` label.
2. **Coverage, not volume** — a few positives per `case_type` **plus** the negatives: an unsupported-claim case the gate must *reject* (`rejects_unsupported_span`), an out-of-scope case it must *withhold*, a prompt-injection/adversarial case, a PII case. One good negative is worth ten happy-path passes.
3. **Edge cases** — ambiguous query, empty/!no-hit retrieval, conflicting sources.
4. **Size for the room** — ~20–40 well-chosen cases is plenty for a 2.5-hour build; quality and adversarial coverage beat size. Say that out loud — it reads as judgment, not corner-cutting.
5. **Labeling method** — you're the domain expert in the room, so hand-label fast; or bootstrap candidates with an LLM and hand-verify. Either way, *you* own the gold labels.
6. **Bootstrap with Claude, then hand-verify** — concretely: have Claude draft candidate labels over the pinned corpus (one record per case: `input` → `gold_answer` → `gold_citations` → `expected_verdict` → `case_type`), then *you* read and correct every one before it's gold. It's the fast path to a usable set in a 2.5-hour build — but never ship Claude's labels unchecked. The gold set is the answer key the eval grades against; if Claude both writes the key and is later graded by it, that's the student grading their own exam. Say that out loud — "Claude-bootstrapped, hand-verified" reads as judgment, and it keeps the gold set independent of the judge.

**C · Tools to pull in (keep it keyless/local where you can).**
1. **A `golden.jsonl` file** — plain, version-controlled, one record per line. The lowest-friction system of record.
2. **A Pydantic model** for the gold record — enforce the schema so a malformed case fails loudly, not silently.
3. **LangFuse Datasets** — register `golden.jsonl` as a LangFuse dataset and run the offline harness against it (this is also the on-screen eval report later). Keyless alternatives if you'd rather: **Promptfoo** or **DeepEval**.
4. **The corpus itself** — the documents the system retrieves over, pinned to a fixed snapshot so the golden set is reproducible.

**The sequencing line to say:** *"I write the spec and the golden set first, because the gate thresholds, the checks that fire, and the eval are all undefined until 'correct' is defined. Everything else is downstream of this."*

## Locked decisions & requirements

- **Vector DB — prototype: ChromaDB**; **backup: LanceDB**.
- **Vector DB — production: Weaviate** *or* **pgvector on Postgres** — lead with pgvector (you live in Postgres day-to-day, and it's the governance story: embeddings in the client's own governed DB).
- **Embedding model: OpenAI text-embedding-3** (clean-provenance US; real semantic embedder, so morphology/synonymy work — kills the "fees vs fee" miss). **Would also consider: Nomic** (local, keyless, open-weight, clean) — the sovereignty-friendly option if a fully offline / zero-keys build is wanted. Pre-embed the corpus offline and cache vectors in Chroma; the only live call at demo-time is embedding the query.
- **Eval framework: LangFuse**.
- **Stage-2 support: LLM-as-judge for the build** (fastest to stand up in 2.5h; you already have the model in the stack). **Dedicated NLI is the production design** — documented below as the answer to "what would you build with more time."
- **Audit trail is tamper-evident, not tamper-proof.**
- **Reproducible eval is a requirement.**
- LLM = Claude (primary); voice/STT where relevant = Groq; language = Python.
- **Caveat on the framework + eval tooling (say it before they do).** LangGraph and LangFuse are libraries — the *data plane* where agents run and get traced. They do **not** govern risky actions before they hit production: policy enforcement, pre-dispatch approvals, and audit *across* agents are a separate **control plane** (a recognized, fast-emerging category in 2026). That gap — policy, approvals, cross-agent audit — is exactly the governance/assurance layer, i.e. the moat, and it's what I architect on top, not something the framework hands me. **This maps onto the *technical half* of Perficient's PACE**: the control plane is **Policies** (the compliance boundary) + **Controls** (guardrails, eval, monitoring, audit) made operational in code. PACE's other two pillars — **Advocacy** (adoption/buy-in) and **Enablement** (training, tools, workflows) — are organizational and live around the system, not in the framework.

---

## The format (what the recruiter said)

- ~2.5 hours, live and recorded. An architect asks questions, watches how you communicate, and helps if you get stuck.
- You pick one scenario from a few cross-industry options offered on the day.
- No environment, keys, or tools provided — bring your own stack.
- Use AI to plan and build rather than hand-code, but you must be able to explain everything on screen.
- Final deliverable: one slide / one-pager to a non-technical, made-up customer. Plain language, no technical diagrams.
- Deployment (local or cloud) is explicitly not scored against you.

## The spine: one reusable skeleton

Orchestrator plans the task and routes across specialist agents that work over a retrieval-grounded corpus, a verifier gates the output, and a thin surface delivers a plain-language result to a non-technical user. Two design rules keep it from reading as a generic RAG demo:

- **Retrieval is a tool, not the spine.** The orchestrator calls retrieval as one tool among others — this lets the same skeleton absorb a non-document scenario instead of breaking.
- **Produce a candidate, then commit it.** The user-facing answer is written in exactly one place, reachable only after the gate passes. A failed answer structurally cannot reach the user.

---

## The eight scored items, pre-answered

### 1. Multi-agent orchestration — the top lens
Frame the whole build this way. Topology: orchestrator → retriever (a tool) → two specialist agents (swappable domain layer) → verifier/eval-gate → synthesizer/deliver. Genuinely multi-agent but finishable and explainable in 2.5 hours. The verifier earns the most points per unit effort — it carries eval, guardrails, and the audit trail at once.

*Worth knowing — Deep Agents (LangChain's `deepagents`, built on LangGraph).* A "batteries-included" harness that bundles a planning tool, sub-agent delegation, virtual file-system memory, and per-file permission rules out of the box — useful if a chosen scenario is genuinely **long-horizon** (multi-step research/synthesis where the agent must plan, decompose, and remember across a long run). Two honest caveats keep it on-brand: (a) it's a **"trust the LLM" harness** — its own docs say to enforce boundaries at the tool/sandbox level, not by expecting the model to self-police — which is exactly the emergent autonomy I deliberately *constrain* with an explicit supervisor and a deterministic gate; so reach for it only where the task needs it, not by default. (b) It **composes** with my skeleton: any LangGraph `CompiledStateGraph` can be dropped in as a Deep Agents sub-agent, so my governed graph can sit *inside* a Deep Agent if a scenario ever wants the planning layer. Clean provenance (LangChain, US; default examples even run on Claude). The line: *"Deep Agents is the ready-made harness; I'd use it for long-horizon planning, but I keep control flow explicit and gated for auditability — and my governed graph plugs in as a sub-agent either way."*

### 2. LLM eval framework / orchestration — show eval against the goal, not vibes

**[GET POINTS — scored item #2]** Two things to say out loud; both are points on the rubric.

**Make "the goal" an explicit, written artifact — not implied.** Before any code, write down *the goal = the task-specific success criteria for this scenario* — what a correct answer must contain, must not contain, and must cite. The eval then measures distance to *that*, not generic quality. Stating it is the difference between "I evaluate" and "I evaluate against a target."
> **Phrase that pays:** "I evaluate against a defined target."

**Evaluate on two axes — and keep "evaluate the evaluator" as a *separate* point.** The eval measures both *is it true* (faithfulness / grounding) and *is it what was asked* (task-success); both gate. Distinct from that, you also check the judge itself, by calibrating each gate against the golden set.
> **Phrase that pays (the eval):** "I'm evaluating against the goal, not just policing hallucination — faithfulness and task-success are two separate gates."
> **Phrase that pays (the evaluator):** "And I evaluate the evaluator itself — I calibrate each gate against a golden set, per-dimension agreement plus negative tests — so a green eval isn't just the judge agreeing with itself."

*(Why these are split: the two gating evals check the **answer** on two axes; "evaluate the evaluator" is the calibration step that checks the **judge**. Folding them into one sentence — "I evaluate the evaluator by using two gating evals" — is the kind of imprecision an architect catches, because the two gates don't check the judge, they check the answer.)*

Framework locked: **LangFuse** — tracing for the runtime path plus the offline harness against the golden set. Two pieces:
- **Runtime gate** — eval is a branch point, not a terminal logger. Pass → deliver; fail with attempts left → bounded self-correction with the failure reason as feedback; fail exhausted → withhold and escalate to human review. Hard attempt cap.
- **Offline harness (LangFuse)** — system run against the labeled set, aggregate pass rate.

**Hybrid gate — not judge-only.** Two layers catching different failure classes: a pure judge gate is circular, a pure deterministic gate can't see meaning.

**Deterministic floor (rule-based, no model).** No labels, works on any corpus — the scenario-agnostic floor. Pass the retrieved span *text* into the gate, not just `source_id` labels:
- *Schema validation* — output is an object with `answer`, a `citations` array, and `confidence`; each citation has `source_id`, `claim`, `span`. Fails on missing key, wrong type, or empty citations while the answer makes claims.
- *Citation-span existence (stage 1)* — each `span` is found in the chunk named by its `source_id` (exact/normalized fuzzy). Fails on a span not in its chunk — fabricated/mis-attributed citation. The live-demo check.
- *Lexical grounding (stage 1.5)* — per cited sentence, token overlap with its span ≥ a **low** threshold; catches decorative/off-topic citations, fails fast. Lexical not semantic — can't see polarity, can wrongly reject paraphrase; a coarse pre-filter (consider routing low-overlap to stage 2 rather than hard-failing).
- *Completeness — task-shape dependent (carry both):* structured task → deterministic required-field checklist; open-ended query → query-key-term coverage and/or fold into the judge's relevance. Covering the terms ≠ answering correctly — a floor, not a guarantee.
- (Retrieval-sufficiency: nothing relevant retrieved → "not enough evidence" → withhold, not confabulate.)

**The seam the floor can't close: existence is not support.** A model can cite a *real* span and hang a claim on it the span doesn't make — and existence, even lexical overlap, pass it. The highest-stakes regulated failure: *looks grounded, isn't.* So the citation check is **per claim, in stages**: existence (stage 1) → lexical grounding (stage 1.5) → **support (stage 2): the span must *entail* the claim.** Decompose into atomic claims, check each independently. Existence alone never passes a claim.

**Rubric layer (LLM-as-judge, structured).** Named dimensions, scored with reasons:
- *Faithfulness* — backstop above stage-2 support: does the answer's overall meaning follow from the sources.
- *Answer relevance / goal completion* — did it answer the actual question.
- **Every reported dimension must gate.** A dimension scored but not in the pass predicate is cosmetic — the recorder-vs-gate bug one level down. If you report it, it gates.

**Composition.** Deterministic checks are hard gates — any failure = fail, run first and fail fast. Support and rubric checks graded — each clears a threshold. Overall pass = all deterministic pass AND stage-2 support clears AND every rubric dimension ≥ threshold. The failed check is the reason feeding the repair loop and the audit log.

**Calibration is per-dimension, with negative tests.** Measure `faithfulness_agreement` and `relevance_agreement` separately against the golden set; add negative tests that assert the gate *rejects* bad inputs (`rejects_unsupported_span`). Each `case_type` becomes a positive-and-negative assertion. A negative assertion is worth more than ten happy-path passes.

**Run the eval and show the results — a demo beat.** Don't just *have* an eval; run the offline harness on screen and put the report up (LangFuse makes it visible). The senior move is to narrate the misses rather than hide them — point at a **functional-accuracy miss** (a golden case where the system produced the wrong outcome) and at the **judge-vs-gold agreement** number (how often the LLM-judge matched the human labels), per dimension. Surfacing where your own system is weak — a low agreement on one dimension, a failed case — reads as credibility, not weakness; an architect trusts the person who shows their failures. The report should put up: **pass@1 / functional accuracy** on the golden set, **per-dimension judge-vs-gold agreement** (faithfulness, relevance), and the **negative-test results** (`rejects_unsupported_span` and the other `case_type` assertions). That turns "I evaluated against the goal" from a claim into something on the screen — and it's a clean way to demonstrate the "Evaluation" pillar directly.

> **The right thing to build.** Deterministic floor (schema + existence + lexical grounding + completeness) + per-claim support via the LLM-judge + faithfulness/relevance (both gating), calibrated per-dimension in LangFuse with negative tests. Small enough to finish and explain in 2.5 hours, complete enough to be demonstrable and defensible.

### 3. Embedding model — locked: OpenAI text-embedding-3 (Nomic considered)
**OpenAI text-embedding-3** — clean (US), strong, trivial to integrate, real semantic embedder, so morphology/synonymy work (fixes the retrieval-miss class of bug a hash embedder causes). Trade-off: keyed/networked, so pre-embed the corpus offline and cache; the one live call is the query embedding. **Nomic** is the considered alternative — local, keyless, open-weight, clean — the pick if you want a fully offline / zero-keys build and want the sovereignty story to be airtight. BGE/GTE excluded under §1.

*Refresh / consistency (the thing to remember).* No periodic refresh is needed for the build — the corpus is static and pre-embedded. The real guard is **model consistency**: embed the query with the *same* model and version as the corpus, or the vectors aren't comparable and retrieval quietly returns garbage (don't mix `-small` and `-large`, or swap providers, between corpus and query). Re-embed if you change the corpus or the chunking during prep (cache invalidation). For production this becomes a real re-index policy: re-embed changed documents incrementally, and re-embed the **whole** corpus on any embedding-model-version change — that's a migration, and the embedding version is part of the lineage/audit record. (The All-Google option's in-DB `embedding()` simplifies this — embeddings are regenerated in the database via SQL, where the data already lives.)

### 4. Vector database — ChromaDB (prototype), LanceDB backup, pgvector/Weaviate production
- **Prototype primary: ChromaDB** — in-process, zero-config, persists locally, explainable; offline-first.
- **Prototype backup: LanceDB** — embedded, on-disk, clean drop-in.
- **Production: Weaviate** (clean, native hybrid search) *or* **pgvector on Postgres** — lead with pgvector: you work in Postgres daily and it's the governance story (embeddings in the client's governed DB; Cloud SQL + pgvector/HNSW, then AlloyDB + ScaNN for scale or entitlement-filtered hybrid search). Store behind a thin swappable interface = a deployment choice, not an architecture commitment.
- Excluded under §1: Milvus/Zilliz (China), Qdrant (Russia).

### 5. Memory — handled deliberately (positive design, three tiers)
Lead with the senior framing, then *immediately* give the positive design — the framing alone reads as defining memory away.

**Corpus retrieval is not memory.** RAG over the document store is *retrieval*, not the agent remembering anything. Say that — then give the three deliberately-scoped tiers (LangGraph house terms in parentheses):

- **1 · Session / conversational state** *(short-term memory — thread-scoped, persisted by the checkpointer).* The running turn history within one session. Policy, stated: stored **locally**, scoped to the session/thread, and bounded — keep the last N turns verbatim, summarize older turns past a token budget. This is the memory a non-technical user actually feels ("it remembers what I just asked"). Regulated caveat worth saying out loud: a summary is a *lossy transform of regulated data*, so it stays traceable to its source turns — I don't silently compress away a material fact.
  > **Phrase that pays (context limits / long conversations):** "I summarize older turns past a budget, but a summary is a lossy transform of regulated data, so it stays traceable to source — I never let a lossy compression become the system of record."
- **2 · Agent working memory** *(the shared graph state / channels passed between nodes).* The orchestration's scratchpad: what each specialist writes, what the verifier reads, what the synthesizer composes. This is the memory that makes the system genuinely *multi-agent* rather than a series of stateless calls — so it doubles as evidence for item #1. And the state transitions the agents write here are exactly what the audit log captures: **the working memory's evolution is the audit record** — memory and auditability are the same mechanism.
- **3 · Long-term / cross-session memory** *(long-term memory — a cross-thread store).* The deliberate choice: **none in the prototype, by design.** The one-line reason turns the absence into a governance decision: *in a regulated setting, persisted user memory is regulated data — retention, PII, right-to-erasure, and audit all attach to it, and I won't stub that casually.* I can also say what it *would* take if a scenario demanded it: an entitlement-scoped, retention-bounded, auditable store with named compliance owners — a design decision, not a checkbox. (I don't bolt on a memory product either; tiers 1–2 are native to the orchestration, and any memory tool would be provenance-vetted per §1.)

**One precision that reads *more* senior, not less:** tiers 1 and 2 usually aren't separate stores — the conversation history and the inter-agent scratchpad both live in the **same thread-scoped graph state**. So: one short-term state holding two roles (user-facing conversation vs. inter-agent working memory), plus a deliberately-absent long-term store. "Same mechanism, different roles" pre-empts the architect who says "those are both just the graph state."

**"Keep it local" has a clean rationale.** The store is in-process / a local DB — consistent with offline-first and zero-keys-to-run. And critically: **memory is subject to the same entitlements and audit as retrieval** — a remembered fact from a regulated conversation is regulated data, so it's PII-screened, entitlement-scoped, and auditable like everything else. That one sentence ties memory back to the identity and auditability pillars and separates this from candidates who treat memory as a vector-store afterthought.

### 6. Guardrails — explicit rules constraining output
Distinct from eval-against-goal: guardrails are hard rules (PII, format/schema, prohibited content, permitted-use); eval is whether the answer met the goal. Both gate; deterministic-guard-first so it fails fast. Provenance-check any guardrails library. *(PACE: the guardrail is a **Control** — a technical guardrail enforced at runtime; the rule it encodes is a **Policy**.)*

### 7. User-facing UI — weighted equal to the backend
Build it first. Non-technical user. Use the UI to make governance visible: the deliver state for passing answers, a "routed for human review" state when an answer is withheld.

**Surface the identity gate.** Open the UI with a short authorization banner — e.g. "Welcome — you're signed in as an authorized Northwind user. Your access scopes what these agents can retrieve and answer." That one line makes the Identity pillar visible on screen and sets up the spoken point: **"identity is stubbed here, but in production it's the gate on who-can-ask and what-each-agent-can-see"** — which turns a demo shortcut into a deliberate, defensible scoping decision rather than a missing feature. (Northwind is the fictional demo company — a deliberately sector-neutral, clearly-fictional name that works whether the scenario is insurance, life sciences, or fintech; chosen instead of "Ironclad," which is a real, prominent AI-contracts company that would collide with a contracts/insurance scenario.)

### 8. Deployment — not scored either way
Local default. Don't over-invest; spend time on the seven scored items.

---

## Backup skeleton — "All-Google (Almost)"

A second, pre-decided skeleton to walk in with — use it when the scenario is defense / dual-use / sovereignty-heavy, where "data never leaves Google + Assured Workloads" is the winning story. It deliberately inverts the §6 thesaurus rule (where ADK/Gemini is "cite, don't build on" because you're Claude-primary): here you *do* build on Google, on purpose, because the whole pitch is a single governed perimeter. It's also a direct replay of your Pythia work (ADK + A2A on Vertex), so it's not borrowed vocabulary.

| Layer | Primary skeleton (what we're building) | All-Google (Almost) | Trade-off |
| :-- | :-- | :-- | :-- |
| **Orchestration** | LangGraph supervisor (self-hosted graph) | ADK agents + A2A inter-agent calls on **Vertex AI Agent Engine** (managed runtime, no self-hosted graph) | Managed runtime + genuinely networked multi-agent (A2A) — but you trade graph-level control for Google's runtime |
| **Reasoning** | Claude (primary) | **Gemini** on Vertex AI | One vendor; you lose Claude's strengths and the cross-family judging split |
| **Compliance specialist** | an in-process LangGraph node — a specialist/verifier you write | a **real standalone ADK agent** with an Agent Card, reached over A2A | Becomes a network-discoverable agent (strong on the orchestration rubric — real A2A, not an in-process function) — at the cost of more infra to stand up |
| **Retrieval / grounding** | Chroma → pgvector | **Vertex AI Search / RAG Engine**, or Gemini grounding, or AlloyDB/BigQuery | Less infra (managed) — but you trust Google's chunking unless you keep your own store |
| **Embeddings** | OpenAI text-embedding-3 | **gemini-embedding-001**, or in-DB `embedding()` (AlloyDB `google_ml_integration`) | One vendor; in-DB embeddings mean vectors never leave the database — but Gemini embeddings tie you to Vertex |
| **Eval / judge** | custom harness + LangFuse | custom harness **+ Vertex AI Gen AI Evaluation Service** for judge/calibration | Managed judge/calibration alongside your harness — less control than rolling it all yourself |
| **Observability** | LangFuse | **Cloud Trace + Cloud Logging** (Agent Engine emits spans natively) | Native spans, no extra tool — but Google-native, less portable |
| **Audit trail** | hash-chained `audit_log.jsonl` | hash-chain kept **in AlloyDB**, plus BigQuery append-only / `pgaudit` + CMEK | Platform tamper-resistance *and* your demonstrable hash-chain — but see the correction below; these are complementary, not a swap |
| **Governance perimeter** | custom app-layer | **VPC-SC + CMEK + IAM + Assured Workloads** — one perimeter, data never leaves Google | The dual-use/defense story in one perimeter — at the cost of full Google lock-in |

**Two corrections to the mapping, so you can defend it:**
- *Audit trail isn't a straight swap.* `pgaudit` and BigQuery append-only give *platform-level* tamper-resistance and action logging — that is **not** the same thing as your *application-level* hash-chain, which is what you demo (edit a record, watch the chain break) and what gives span-level tamper-evidence. For regulated, **keep the hash-chain inside AlloyDB**; `pgaudit` + append-only + CMEK is the complementary perimeter layer around it, not a replacement for it.
- *The compliance specialist gets more "real."* In the primary skeleton it's a node you call in-process; in All-Google it's a published ADK agent (Agent Card + A2A), so the compliance check is a genuine inter-agent call. That reads strongly on the orchestration rubric — just be ready for the infra cost of standing up a second deployed agent.

**The line for the room:** *"All-Google lets me collapse the stack into a single IAM/CMEK/VPC-SC perimeter and make the A2A compliance agent real on Agent Engine — and I can drop the standalone vector DB by either letting Gemini ground over Vertex AI Search, or folding vectors into AlloyDB. For regulated, I keep AlloyDB so the audit trail and span-level verification stay in one governed store."*

### Can you skip the vector DB? Four ways, ranked for this use case
1. **Long-context, no retrieval at all.** A ~5–10 policy-doc corpus fits trivially in Gemini's 1M-token window — stuff all policy into the system context and let Gemini answer with citations. For a demo this size a vector DB is genuinely optional; simplest possible thing.
2. **Vertex AI Search (managed retrieval).** Upload docs to a data store; Google handles chunking, embedding, indexing, and retrieval, returning grounded answers with citations. You skip running any vector DB — it's a managed grounding service, not infra you operate.
3. **Gemini grounding** pointed at a Vertex AI Search data store (or Google Search) — citations come back as a first-class field of the response.
4. **Reuse a database you already have.** BigQuery `VECTOR_SEARCH` (leans on your Nielsen/Gracenote BQ depth) or AlloyDB with `embedding()` + ScaNN. Not skipping a vector store — skipping a *dedicated* one; search lives in the warehouse/OLTP DB you already run.

**The catch — and it's the interesting part.** Skipping retrieval partially undercuts the verifier you just built. The citation-span check works by comparing the answer's claims against the specific spans that were *retrieved*. Go long-context (option 1) and there's no discrete "retrieved set" — every doc is in context, so "did this citation resolve to a retrieved span" degrades to "is it anywhere in the corpus," a weaker grounding guarantee. Options 2–3 give the spans back in the grounding metadata, so the verifier still works — but you're now trusting Google's chunking instead of controlling it.

**So the real trade:** managed grounding (Vertex AI Search) buys less infra and a clean one-vendor governance story; a DB you control (AlloyDB/pgvector) keeps the single transactional, CMEK-encrypted, IAM-governed store **plus** the span-level audit your verifier depends on. For a regulated assistant that's the whole pitch — so the recommendation is:

**All-Google, but keep AlloyDB as the store.** Gemini + ADK/A2A + Agent Engine for the agent layer; AlloyDB AI (in-DB embeddings, ScaNN, `pgaudit`, CMEK) as the one store for vectors + policy metadata + the hash-chained audit. You still "skip the dedicated vector DB" (it's just your operational DB), data never leaves the VPC (the confidential-computing angle), and the citation-span verifier keeps its retrieved spans.

---

## Stage-2 support — build choice and the production design

**For the build: LLM-as-judge.** In the time given, stage-2 support (does the span entail the claim) runs as an LLM-judge call rather than a separate model — fastest to stand up, and the model's already in the stack. Note for the room: you have OpenAI in the stack for embeddings, so running the *judge* on an OpenAI model while Claude generates the answer is a deliberate **cross-family** choice — a different model judging than the one that generated reduces self-preference/self-grading bias. (Either family works; the point is to be able to say why you split them.)

**What I'd build with more time: a dedicated NLI support tier.** This is the production answer to speak to — not built in the session, but designed:

- *The model.* A small encoder-based NLI classifier (DeBERTa-style; Microsoft-origin architecture is clean — provenance-check the specific fine-tuned checkpoint). It outputs entailment / neutral / contradiction with a confidence score. Runs locally, keyless, reproducible — which is exactly why it's the better production fit: no sampling, cheap per claim at scale, and it logs a discrete label + score per claim, which is a clean audit record.
- *Input construction (the part that makes or breaks it).* Decompose the answer into atomic, single-sentence claims first — NLI models are trained on sentence pairs and degrade on multi-claim paragraphs. Premise = the cited span, expanded to its surrounding sentence for enough context; hypothesis = the atomic claim.
- *Decision logic.* Per claim: entailment ≥ threshold → supported; contradiction → hard fail (the polarity case, "not covered" vs "covered"); neutral → unsupported (the span doesn't address the claim — the savings-text-for-fees case). The answer passes stage 2 only if every claim passes; a failing claim names itself for the repair loop.
- *Calibration.* Measure against the golden set, tune the entailment threshold for the domain, and run the `rejects_unsupported_span` negative test — this is literally an NLI contradiction/neutral case.
- *Known weaknesses and how the design handles them.* Generic NLI is brittle on domain/legal/financial jargon → use a FEVER-style fact-verification model (claim-vs-evidence, closer to the citation task than generic MNLI), or fine-tune on domain pairs, and keep the LLM-judge as a backstop for low-confidence verdicts. Long premises → window the span. Multi-hop claims (need several spans) → decompose further or route to the judge. Numeric/temporal claims (deductibles, dates, dollar amounts) → deterministic numeric checks or the judge, since NLI is weak there.
- *The ideal architecture.* A tiered support check: deterministic numeric/format checks → dedicated NLI for entailment (cheap, deterministic, handles most cases) → LLM-judge backstop only for the ambiguous and multi-hop residue. Deterministic-first, judge-last — the same posture as the rest of the gate.

**The line for the room:** *"For the prototype I run stage-2 support as an LLM-judge — fastest to stand up and already in the stack. In production I'd move it to a dedicated NLI tier: small, local, reproducible, cheap per claim, with a discrete auditable verdict — and keep the judge as the backstop for the ambiguous and multi-hop cases."*

---

## Reproducibility (requirement)
A reproducible eval is part of "defensible." Pin every controllable source of nondeterminism in the offline harness:
- **Deterministic retrieval** — ANN search returns ties in arbitrary order. Add a tie-break in the store query (sort by score, then a stable key like `source_id`/`chunk_id`). Same query → same chunks, same order, every run.
- **Judge temperature 0 + fixed seeds** where exposed.
- **Eval retrieval separately from generation** — recall@k against the known-relevant chunks. A retrieval miss is caught before generation, instead of hiding behind a fluent answer.

## Retrieval can be the silent failure
The worst case is a green eval over a broken retriever — every layer looks fine while the system is wrong, because the failure is upstream. Worked example: a hash embedder buckets "fees" and "fee" separately, "tell me about fees" retrieves nothing relevant, and the agent answers from unrelated savings-interest text; a naive eval passes it. Defenses, mostly already in the plan:
- A **real embedder** (OpenAI text-embedding-3, or Nomic if offline) so morphology/synonymy work — not a hash/toy embedder.
- **Retrieval eval (recall@k)** as its own check.
- **Gating relevance + per-claim support** — both independently catch fees-answered-from-savings-text.
- **Golden-set cases for vague and morphological-variant queries** with expected behavior (retrieve the right chunk, or abstain).

The line for the room: *a passing eval over a broken retriever is false confidence — test retrieval in isolation before you trust the gate.*

---

## The audit trail — tamper-evident by design
The verifier writes an audit record of every decision (candidate, checks run, pass/fail, deliver-or-withhold). Make it **tamper-evident**: a hash-chained append-only log where each record carries a hash of the prior record, so editing any record breaks the chain downstream and a verifier pass detects exactly where it snaps.

**The demo beat.** Edit one record, re-run the chain verification, show it fail at that record. Deterministic, no model — it *shows* the auditability claim instead of asserting it.

**Requirement — say it precisely.** **Tamper-evident, not tamper-proof.** A hash chain detects tampering; it doesn't stop someone with full write control from recomputing downstream hashes. Production path: WORM / append-only storage + external timestamp anchoring. Claiming "tamper-proof" is the only way this backfires. *(PACE: the audit trail is the **Controls** layer's evidence — the proof an auditor or a Perficient PACE review actually consumes.)*

## HITL framing — the eval is load-bearing
*In a regulated setting an unverifiable answer is a liability, so the gate routes it to accountable human review instead of shipping it.* That's "Adversarial Safety & Liability Mitigation" + "Human-in-the-Loop (HITL) Workflows" from the résumé, stated as architecture. Narrate the escalate branch in those words — it converts an architecture decision into a credential, and distinguishes a real HITL design (the eval *withholds*) from a cosmetic one. *(PACE: the withhold-and-escalate path is a **Control** — a risk control that routes an unverifiable answer to accountable human review. Advocacy and Enablement are the organizational pillars around it, not this code path.)*

## Identity & entitlements — the governance pillar (don't under-sell it)
"Who's allowed" spans three things: the end-user's identity (who's asking), the agent/workload identity (which agent is acting, under what least-privilege scope), and entitlements/RBAC (what data each user or agent may see or touch). This isn't a gap in your experience — it's the **HP $40B channel data exchange** almost exactly (entitlements, RBAC, data contracts, permitted-use), and the all-Google skeleton's IAM is the cloud-native form. Say it as a first-class pillar, not a footnote. *(PACE: identity/entitlements are **Controls** — the access spine the whole control plane sits on.)*

- **In the prototype:** identity is stubbed (a demo doesn't need real SSO). The move is to *say so deliberately* — "identity is stubbed here, but in production it's the gate on who-can-ask and what-each-agent-can-see" — and surface it in the UI via the authorization banner (item 7). A stub you name on purpose reads as scoping discipline; a stub you hide reads as a missing feature.
- **The production form is entitlement-filtered retrieval:** an agent only retrieves over data the asking user is entitled to see, so the answer can't be grounded in documents they're not permitted to access. That's the HP entitlements model applied to RAG, and AlloyDB's entitlement-filtered hybrid search is the all-Google version. It also ties identity straight to the verifier — the retrieved set the citation checks run against is already scoped by the user's permissions.

---

## Building the golden (eval) set — when and how
Labeled reference data — inputs paired with known-correct outputs/judgments. Triple duty: drives the offline harness (LangFuse), calibrates the judge, calibrates stage-2 support. Pre-room homework for your defaults; for the day's actual scenario, written first thing in the room.

**When.** After you lock the scenario and task definition, before you tune thresholds or calibrate. Early enough to drive development.

**Format: structured JSON, citation-first** — the same shape the schema, existence, lexical, and support checks operate on (the Pythia pattern, and a real proof point). Happy-path:

```json
{
  "id": "ins-0007",
  "case_type": "happy_path",
  "input": "Does this policy cover flood damage to a finished basement?",
  "retrieved": ["policy_42#chunk_3", "policy_42#chunk_8"],
  "expected": {
    "verdict": "answerable",
    "answer": "No — flood damage is excluded under the water-damage exclusion.",
    "citations": [
      { "claim": "Flood damage is excluded", "source_id": "policy_42#chunk_3", "span": "loss caused by flood ... is not covered" }
    ]
  }
}
```

Insufficient-evidence hard case (correct behavior is to refuse → withhold/escalate):

```json
{
  "id": "ins-0019",
  "case_type": "insufficient_evidence",
  "input": "What is the deductible for wildfire smoke damage?",
  "retrieved": ["policy_42#chunk_3"],
  "expected": { "verdict": "insufficient_evidence", "answer": null, "citations": [] }
}
```

**What's usually used to make it.** Representative source docs; hand-authored references (20–50 is plenty); model-bootstrapped then human-curated (curation non-negotiable); real historical known-good outcomes if available. **Seed hard cases** by `case_type`: `happy_path`, `insufficient_evidence`, `out_of_scope`, `hallucination_bait` (fabricated citation — stage-1 failure), `unsupported_claim` (real span, wrong claim — stage-2 failure), and vague/morphological-variant queries. The mix matters more than the count.

**Common helpers.** RAGAS / LlamaIndex / DeepEval test-set generators, LangFuse datasets. Provenance-check before adopting any.

---

## Final deliverable: the customer one-pager
One slide / one-pager to a non-technical, made-up customer explaining how their problem is solved. Plain language, no technical diagrams. Draft against the chosen scenario; never let it drift technical.

## Pre-room homework
- Build the reusable skeleton; explain every line on screen.
- Pre-embed the default corpora (OpenAI text-embedding-3) and cache vectors.
- Build golden sets per pre-staged corpus; calibrate judge + support per-dimension with negative tests.
- Wire the tamper-evident audit log; rehearse the tamper → chain-break demo.
- Have the eval report runnable on screen (pass@1 / functional accuracy, per-dimension judge-vs-gold agreement, negative tests); rehearse narrating a real miss out loud.
- Nail the memory story (three-way distinction).
- Pre-stage 2–3 scenarios with a default: insurance contract intelligence (SPINF), healthcare / life sciences (EQT portfolio), fintech with SEC/FINRA framing. Keep one non-corpus pattern in your back pocket.

## Traps that lose points
UI bolted on at the end · a choice you can't explain live · jargon you can't unpack · a one-pager that's still technical · picking the scenario cold · building on low-code that hides the governance layer · adversarial-nation-linked tooling · claiming "tamper-proof" when it's tamper-evident · trusting a green eval over an untested retriever.

## Open decisions
All major stack and gate decisions are now locked. The dedicated-NLI support tier is the documented production upgrade to speak to, not a build task for the session.

---

## FAQ — one-liners to have ready

Moved to its own file: **`perficient_faq_v1.md`** — crisp spoken answers for the eight scored items (Q1 = multi-agent orchestration, the heaviest) plus Q9, the scenario-choice rationale (insurance quick win vs. the durable energy/utilities + life-sciences play, and why the assurance subscription stays with Perficient).

---

## Two judgment calls worth pre-answering

### Should I use any Anthropic MCPs — including for the golden set?
Short answer: **MCP is the integration standard to *name*, and the Claude Agent SDK's in-process MCP is the only flavor worth *running* in the recorded demo. Nothing about MCP builds the golden set — Claude does that.**

- **What MCP is now (say it right).** MCP (Model Context Protocol) is an open standard — **governed by the Linux Foundation since Dec 2025**, not just an Anthropic project — and it's natively supported by **Salesforce Agentforce and Microsoft**. So "I expose tools and data as MCP servers" is the *portable, standard-compliant* integration story, and it's literally how you'd plug a governed agent into Perficient's Microsoft/Salesforce control planes. Naming it reads current and on-brand.
- **What to actually run in the room: in-process SDK MCP, not external servers.** The Claude Agent SDK lets you wrap your own Python functions as **in-process MCP tools** (`create_sdk_mcp_server`) — your retriever, the citation-verifier, the audit-writer — with **no separate process, no keys, fully offline**. That satisfies "use MCP" without breaking the zero-keys / explain-everything-on-screen posture. The SDK's **hooks** are deterministic points in the agent loop — the same guardrail-boundary concept as ADK callbacks / LangGraph interrupts (already in the thesaurus).
- **MCP = a governance surface, not just plumbing.** MCP tools require **explicit permission before Claude can call them**, and MCP 2.4 added per-tool consent + audit logs. That's tool-boundary enforcement baked into the standard — name it, and connect it to the **lethal trifecta** risk (private-data access + untrusted content + an exfiltration path) that any MCP tool surface introduces. That ties MCP straight to your moat.
- **Don't** bolt *external/networked* MCP servers onto the demo — live dependencies, keys, and things you can't explain on screen. And every MCP server is in scope for the §1 provenance rule: the registry has ~9,400 servers, most unvetted — Anthropic's reference servers (filesystem, fetch, git) are clean; audit anything third-party.
- **The golden set, specifically:** there is no "golden-dataset MCP." The leverage is **Claude itself** — use it to *bootstrap candidate labels* (generate input → expected-output → citation triples), then **hand-verify** (you own the labels), and use Claude as the **cross-family LLM-judge** tier. That's where the AI helps; MCP isn't part of it.

**One-liner for the room:** *"I expose tools as MCP because it's the open standard the control planes speak — but in the demo it's in-process and keyless, and the golden set is Claude-bootstrapped then hand-verified, not an MCP thing."*

### Should the policies default to EU-friendly, since EQT owns Perficient?
**Don't hardcode EU — make the policy set a *parameter*, default it to the strictest applicable bar (often the EU AI Act / GDPR), and say why.** The reasoning is the senior-reading part:
- **The client sets the regime, not the owner.** Perficient is ~95% US revenue; most clients are bound by **HIPAA, SEC/FINRA, NAIC, and US state privacy laws** — not GDPR. Imposing GDPR on a US-only insurance scenario would be a category error. EQT being European doesn't change which law binds a given client.
- **But designing *to* the EU bar is smart and owner-aligned.** The EU AI Act is the strictest regime, so building to it is a **high-water-mark** strategy — clear EU and you've largely cleared the rest — *and* it's aligned with a European owner whose own portfolio carries EU AI Act exposure. EU-readiness is a portfolio-level selling point for EQT.
- **So architect Policies as a swappable policy pack.** This is exactly why **Policies is its own pillar and the perimeter is configurable** (see the two-plane graphic): a HIPAA pack, a GDPR pack, a SEC/FINRA pack — same Controls underneath, different rules on top. Default to the strictest, parameterize the rest.
- **Ship the US packs as the standing default set — EU as the high-water overlay.** Because Perficient is ~95% US, the policy packs you actually load by default are the **US regimes — HIPAA (healthcare), SEC/FINRA + SR 11-7 (financial services), NAIC (insurance), and US state privacy (CCPA-class).** Keep an **EU AI Act / GDPR** pack on the shelf as the strictest-bar overlay you can switch on (owner-aligned, and the high-water mark that clears most others). Framing for the room: *the US packs adhere by default because that's who the clients are; the EU pack is there "just in case" the deployment touches the EU — one parameter flip, not a rebuild.*
- **Add a sector pack per durable vertical.** Beyond the cross-industry US packs, each regulated vertical loads its own sector pack — same Controls underneath, different rules on top. For **energy & utilities** (the durable skeleton): **NERC CIP** (bulk-electric-system cybersecurity), **FERC** (reliability + market regulation), **IEC 62443** + **NIST SP 800-82** (OT/ICS security), state **PUC** rules, and **US state privacy** (CCPA-class) on the retail/customer-data side. (Life sciences would load FDA / GxP / HITRUST; the pattern generalizes.)

**One-liner for the room:** *"I default the policy layer to the strictest applicable standard — often the EU AI Act, which is owner-aligned and a clean high-water mark — but I keep the regime configurable, because the client's jurisdiction sets which one binds, and Perficient is mostly US."*

---

## Taking this into production

The prototype is one governed skeleton — **orchestrator-workers + evaluator-optimizer gate + verifier + tamper-evident audit + entitlement-scoped retrieval**. Productionizing it is a *stack choice*, not a redesign: the topology and the verifier stay constant; the substrate changes to fit what the customer values. Three archetypes, by what the customer is optimizing for.

**The constant across all three.** The **verifier** — guardrails + eval-against-goal + tamper-evident audit, i.e. the **control plane / PACE layer** — is the part that never gets outsourced to the stack. Every variant below swaps the *data plane*; the *control plane stays yours*. (See `agent_infrastructure_two_plane.svg`.) Claude stays the primary reasoning model in all three — it runs on every major cloud (Bedrock / Vertex / Foundry), so the brain is portable even when the perimeter isn't.

### 1 · The Rolls-Royce — cost-no-object, built for decades and hard miles
*When to pick it:* a regulated, high-stakes, long-lived core system (underwriting, claims, clinical). The customer cares about correctness, security, and longevity — not unit cost. Expensive up front; compounds value over years and takes hard regulated miles.

| Layer | Prototype | Rolls-Royce |
|---|---|---|
| Orchestration | LangGraph | LangGraph + **Temporal** (durable, replayable, crash-proof long-running execution) + a real control plane |
| Reasoning LLM | Claude | **Claude Opus (flagship)** primary + a **cross-family judge** (different vendor) for independent eval; provisioned throughput, provider redundancy |
| Embeddings | text-embedding-3-small | **text-embedding-3-large** or **Voyage-3-large**, domain-tuned and re-embedded |
| Vector store | Chroma | **AlloyDB AI + ScaNN** (or enterprise Pinecone/Weaviate) — one transactional, replicated, CMEK store |
| Eval | LangFuse | LangFuse enterprise + a **dedicated NLI judge** (DeBERTa-class) + cross-family LLM-judge + continuous online eval + golden-set regression in CI |
| Memory | tiers 1–2; tier-3 off | **all three tiers, governed** — long-term store ON with entitlement-scoping, retention, and right-to-erasure tooling |
| Guardrails | deterministic-first | layered: deterministic + **NeMo Guardrails** + a policy engine in the control plane |
| Audit | hash-chained JSONL | **WORM storage + external timestamp anchoring** (RFC-3161 TSA / transparency log) — regulator-grade immutable |
| Identity | stubbed | full enterprise IAM + entitlement-filtered retrieval + **workload identity (SPIFFE/SPIRE)** + pre-dispatch approvals |
| Confidential compute | — | **TEE everywhere** — confidential VMs (Intel TDX / AMD SEV-SNP) + **confidential GPUs (NVIDIA H100/H200 CC)**, attestation-gated key release; removes the operator from the trust boundary |
| Deployment | local | multi-region HA + DR; sovereign-cloud or on-prem option |

*Why it lasts:* every layer is the most capable and most secure version, with redundancy and confidential compute end-to-end. *The catch:* highest cost and longest build — only justified when the asset is core and long-lived.

### 2 · The Formula One car (with the best pit crew) — fastest time to revenue
*When to pick it:* the customer wants value in weeks, already lives on a cloud, and wants you to lean fully into that cloud's managed agent platform. It's fastest because **the platform already built the control plane** — you *configure, not code*. The honest trade is the data-plane/control-plane one: maximum speed, at the cost of portability/lock-in.

Match the customer's cloud:

- **GCP → near-all-Google** (see `GOOGLE_STACK.md`): ADK + A2A on Vertex Agent Engine · Gemini *or Claude on Vertex* · Vertex AI Search **or** AlloyDB AI (drop the standalone vector DB) · gemini-embedding-001 · Vertex Gen AI Evaluation · Cloud Trace/Logging · VPC-SC + CMEK + IAM. **Keep the verifier.**
- **AWS → AWS-native**: Amazon Bedrock (**Claude native on Bedrock**) + Bedrock **AgentCore** (managed agent runtime) · Bedrock **Knowledge Bases** (managed RAG — drop the vector DB) over OpenSearch Serverless / Aurora pgvector · Bedrock **Guardrails** · Bedrock **Evaluations** · CloudTrail + CloudWatch · IAM + PrivateLink + KMS · **Nitro Enclaves** (confidential). **Keep the verifier.** *(A stack I'm fluent in, not just naming — Nielsen/Gracenote ran on AWS.)*
- **Azure / Microsoft → Azure-native** *(most on-brand for Perficient — Microsoft Inner Circle)*: Azure AI Foundry + Foundry Agent Service / Copilot Studio · Azure OpenAI + **Claude via Foundry** · Azure AI Search (managed RAG) · Foundry Evaluations · **Entra Agent ID** (agent identity) · **Microsoft Purview** (governance/audit) · Azure confidential VMs. **Keep the verifier.**
- **Salesforce-centric → Agentforce** *(Perficient's published anchor)*: Agentforce + Data Cloud + MuleSoft, with the **prototype's verifier wrapped around Agentforce as the external assurance layer** — literally the governed version of Perficient's own insurance-quote case.

**The three cloud-native skeletons, layer by layer.** Same topology every time — orchestrator-workers + gate + verifier; only the substrate changes. Microsoft sits as a full equal next to Google and AWS (and is the most on-brand for Perficient — Microsoft Inner Circle):

| Layer | Google (GCP) | AWS | Microsoft (Azure) |
|---|---|---|---|
| Orchestration / runtime | ADK + A2A on **Vertex Agent Engine** | Bedrock **AgentCore** | **Foundry Agent Service** / Copilot Studio |
| Reasoning LLM | Gemini *or* **Claude on Vertex** | **Claude native on Bedrock** | Azure OpenAI + **Claude via Foundry** |
| Retrieval / RAG | Vertex AI Search *or* AlloyDB AI (drop the vector DB) | Bedrock **Knowledge Bases** over OpenSearch / Aurora pgvector | **Azure AI Search** (managed RAG) |
| Embeddings | gemini-embedding-001 | Titan / Cohere on Bedrock | Azure OpenAI embeddings |
| Eval | Vertex Gen AI Evaluation | Bedrock **Evaluations** | **Foundry Evaluations** |
| Guardrails | Model Armor + built-in safety | Bedrock **Guardrails** | Azure AI Content Safety + Purview policy |
| Identity | IAM + workload identity | IAM + PrivateLink | **Entra Agent ID** (agent identity) |
| Governance / audit | Cloud Trace/Logging · VPC-SC · CMEK | CloudTrail · CloudWatch · KMS | **Microsoft Purview** + Azure Monitor |
| Confidential compute | Confidential VMs / Assured Workloads | **Nitro Enclaves** | Azure confidential VMs |
| **The verifier** | **stays yours** | **stays yours** | **stays yours** |

The bottom row is the whole point: the platform owns the data plane, but the verifier (guardrails + eval-against-goal + tamper-evident audit = the PACE control plane) is the part Perficient builds and keeps, on whichever cloud the client already lives on.

**Regulated overlays — compose onto any of the above:**
- *Healthcare (HIPAA/HITRUST):* BAA-covered services, PHI de-identification, Health Data Services / HealthLake / Healthcare API.
- *Financial services (SEC/FINRA, SR 11-7):* model inventory + validation (ModelOp-class), immutable audit, explainability, data residency.
- *Insurance (NAIC):* the above + fairness testing (Holistic-AI-class).
- *Government (FedRAMP):* AWS GovCloud / Azure Government / Google Assured Workloads.

*Why it's fast:* the cloud's managed agent platform **is** the control plane, and Claude stays the brain on all three. *The catch:* portability drops — the perimeter is the vendor's. Name it as a deliberate trade, not an accident.

### 3 · The junkyard car that runs — extreme portability + cost-consciousness
*When to pick it:* startups, air-gapped/edge, cost-sensitive, or "must run anywhere with no keys." Everything free/open and **clean-provenance** (no China/Russia tooling, per §1); runs on a laptop or a single VM.

| Layer | Junkyard build (all FOSS, clean provenance) |
|---|---|
| Orchestration | LangGraph (OSS); for batch, **Airflow / Prefect / Dagster**; **Temporal OSS** for durability |
| LLM | self-hosted open weights — **Llama (Meta)** or **Mistral (France)** via **vLLM / Ollama / llama.cpp**, quantized (GGUF). *Excluded: Qwen / DeepSeek / GLM / Yi / Kimi — China, §1.* Burst to a hosted open-router only on demand |
| Embeddings | **Nomic Embed (US)** / **all-MiniLM (TU Darmstadt, DE)** / **Snowflake Arctic (US)**, on CPU. *Excluded: BGE / GTE — China* |
| Vector store | **LanceDB** (embedded) / **pgvector** / **FAISS** / **sqlite-vec** / **DuckDB-VSS** — file-based, zero ops. At small corpus, skip it (BM25 or long-context) |
| Eval | **Promptfoo / DeepEval** + LangFuse self-hosted — keyless, local; deterministic checks do most of the work |
| Memory | **SQLite checkpointer** — file-based, zero infra |
| Guardrails | deterministic Python + **Guardrails AI / Presidio** (PII) |
| Audit | the **hash-chained JSONL** you already built — portable, append-only; optional Merkle log |
| Identity / policy | **Keycloak** + **OPA (Open Policy Agent)**; JWT |
| Confidential (optional) | **Gramine** on SGX — or trust your host |
| Deployment | **Docker Compose** on a laptop / single VM / air-gapped. Zero-keys-to-run |

**The radical idea — you often don't need a multi-agent system in production.** The prototype proves you *can* orchestrate agents; production should use the **cheapest tool that's correct**. So decompose:
- Push the high-volume work into **deterministic ML pipelines / batch jobs** (extraction, classification, embedding, retrieval, scoring) on Airflow/Prefect/Ray/Spark — cacheable, parallel, testable, cheap, and far more auditable than an agent loop. No LLM where a rule or a classifier is correct.
- Reserve **agency for the seams** — the ambiguous last mile, synthesis, the human-facing assembly. **Agents assemble the outputs of deterministic pipelines "at the end,"** instead of driving every step.
- The discipline, stated as a ladder: **rule > classifier > ML model > single LLM call > agent** — climb only when the cheaper rung is wrong. (This is the Anthropic *workflow-vs-agent* line taken to its production conclusion: most production value is workflows; agents are the garnish, not the entrée.)

*Why it survives:* runs anywhere, near-zero marginal cost, no lock-in, no foreign-adversary tooling. *The catch:* you operate and assure it yourself — which is exactly where the verifier (yours in every version) earns its keep.

---

**The line for the room.** Same skeleton, three philosophies — **durable** (Rolls-Royce), **fast** (Formula One), **portable** (junkyard). What never changes is the governed control plane / PACE layer and the verifier. That's the part that's *yours* — on any stack, at any price point — and it's the real answer to "what would you do differently in production?"

---

## What EQT needs from Perficient — and where I fit

The ownership logic in four beats, ending in the one-hire pitch. This is the "why I understand your business" layer to surface once the build has earned the room's trust. *(Anchored to the EQT × Perficient thesis — align, don't reinvent.)*

1. **EQT is pouring capital into AI.** The EU deep-tech / Scaleup Europe fund, a dedicated **AI-infrastructure strategy**, Value Creation Days built around AI integration, and **Motherbrain** run in-house since 2016. AI is an explicit value-creation theme across the portfolio — funded conviction, not a side bet.

2. **In the EQT portfolio, Perficient is how that bet actually reaches enterprises.** Motherbrain Labs can *advise* a portfolio company on AI; it can't *build and ship* it across hundreds of them. Perficient is the applied-AI-**delivery engine** that turns the thesis into deployed systems inside EQT's regulated holdings — that delivery capacity is exactly what an applied-AI-services business is *for*.

3. **The defensible part is governed, regulated-grade agentic delivery — and that's three layers in one hire.**
   > *(spoken, ~20 sec)* "I build the governed, regulated-grade agentic systems that are the defensible part of that — and I can land them across the India and LatAm delivery base, because I've lived in Hyderabad and run those teams for years. That's design, scale, and commercial in one hire."

4. **Perficient's survivable lane stays open.** Even as hyperscalers squeeze into owning the generic **"control plane" for multi-agent systems**, Perficient's durable lane is to be the **regulated-vertical SI that delivers, governs, integrates, and customizes those control planes for Global-2000 clients.** The platforms can own the commodity control plane; the per-client governed integration in regulated verticals — entitlements, eval-against-goal, audit, the policy packs that bind *this* client — does not commoditize. That lane *is* the verifier / PACE layer this entire prototype is built around. (Full treatment: `Perficient_2026-2030_v2.md`, Part 0 swing-factors + Part 3 control-plane strategy.)

---

## Version history

v27 — 2026-06-16 · changed: (1) converted the 16 checkbox items in the "First move in the room" section to grouped **numbered lists** (A 1–6, B 1–6, C 1–4) and renamed the sub-heading from "How to do it — a checklist" to "How to do it (spec-first, eval-first)" — the detailed plan now uses numbered lists, not checklists (the short build checklist keeps the checkbox format); (2) added the Nielsen/Gracenote AWS-shop credibility note to the AWS production bullet to align with the build checklist's say-it line. Otherwise confirmed alignment with `perficient_build_checklist_v6.md` (three production archetypes, the stack, the eval gate, policy packs, stage-2 NLI, in-process MCP).

v26 — 2026-06-16 · changed: (1) extracted the FAQ section into its own file (`perficient_faq_v1.md`) and left a pointer; (2) mirrored the energy & utilities **sector policy pack** (NERC CIP / FERC / IEC 62443 / NIST SP 800-82 / state PUC / state privacy) into the policy catalogue, with a note that each durable vertical loads its own sector pack (life sciences → FDA / GxP / HITRUST).

v25 — 2026-06-16 · changed: (1) added an explicit golden-set checklist item — "Bootstrap with Claude, then hand-verify" (Claude drafts candidate labels over the pinned corpus; you correct every one; never ship unchecked labels, since the gold set must stay independent of the judge); (2) added a "ship the US packs (HIPAA / SEC-FINRA / NAIC / state) as the standing default, EU as the high-water overlay" bullet to the policy section; (3) added a Deep Agents note to §1 orchestration (LangChain's `deepagents` on LangGraph — useful for long-horizon planning, but a "trust the LLM" harness to use sparingly; the governed graph composes in as a sub-agent); (4) added a three-column cloud-native skeleton table (Google / AWS / Microsoft, layer by layer, verifier-stays-yours row) so Microsoft sits as a full equal in the production section; (5) added a "What EQT needs from Perficient — and where I fit" section after the production section (four beats + the one-hire spoken line + the survivable-lane framing). — "Bootstrap with Claude, then hand-verify" (Claude drafts candidate labels over the pinned corpus; you correct every one; never ship unchecked labels, since the gold set must stay independent of the judge); (2) added a "ship the US packs (HIPAA / SEC-FINRA / NAIC / state) as the standing default, EU as the high-water overlay" bullet to the policy section; (3) added a Deep Agents note to §1 orchestration (LangChain's `deepagents` on LangGraph — useful for long-horizon planning, but a "trust the LLM" harness to use sparingly; the governed graph composes in as a sub-agent); (4) added a three-column cloud-native skeleton table (Google / AWS / Microsoft, layer by layer, verifier-stays-yours row) so Microsoft sits as a full equal in the production section; (5) added a "What EQT needs from Perficient — and where I fit" section after the production section (four beats + the one-hire spoken line + the survivable-lane framing).

v24 — 2026-06-16 · changed: added a "Two judgment calls" section — (1) Anthropic MCP guidance (MCP is the Linux-Foundation open standard to *name*; run only in-process keyless SDK MCP in the demo; MCP as a governance/permission surface tied to the lethal trifecta; the golden set is Claude-bootstrapped + hand-verified, not an MCP thing) and (2) EU-policy guidance (don't hardcode EU; parameterize Policies, default to the strictest/EU-AI-Act bar as an owner-aligned high-water mark, since the client's jurisdiction binds, not the owner). — (1) Anthropic MCP guidance (MCP is the Linux-Foundation open standard to *name*; run only in-process keyless SDK MCP in the demo; MCP as a governance/permission surface tied to the lethal trifecta; the golden set is Claude-bootstrapped + hand-verified, not an MCP thing) and (2) EU-policy guidance (don't hardcode EU; parameterize Policies, default to the strictest/EU-AI-Act bar as an owner-aligned high-water mark, since the client's jurisdiction binds, not the owner).

v23 — 2026-06-16 · changed: reconciled the PACE mapping to the corrected definitions (Policies = the compliance boundary/permitted-use; Controls = guardrails + eval + monitoring + audit; Advocacy + Enablement are the organizational pillars *around* the system, with Enablement surfacing as the UI) — fixed the PACE-in-code map, the control-plane caveat, the guardrails tag, and the HITL tag (withhold is a Control, not Advocacy/Enablement); added a checklist under "first move" for writing the spec + golden-dataset needs (define "correct," what the labeled set contains, tools to pull in); added a note that HIPAA/EU-GDPR are named-not-built production overlays and why.

v22 — 2026-06-16 · changed: added a closing "Taking this into production" section with three skeleton stacks mapping the prototype onto production — the Rolls-Royce (cost-no-object, best-of-everything + confidential compute, built for decades), the Formula One car (fastest time to revenue via the customer's cloud — GCP/AWS/Azure/Salesforce variants + regulated overlays), and the junkyard car (extreme portability, FOSS clean-provenance, plus the "you don't always need a multi-agent system — decompose into ML workflows and let agents assemble at the end" decomposition). The verifier/control plane stays constant across all three.

v21 — 2026-06-16 · changed: added the summary/lossy-transform "phrase that pays" to the memory section; wove Perficient **PACE** through the plan in several places — a consolidated PACE-in-code map under the graphic, plus tags on guardrails (Policies/Controls), identity (Controls), the audit trail (Controls evidence), HITL (Advocacy/Enablement), and the control-plane caveat (the control plane *is* PACE made operational).

v20 — 2026-06-16 · changed: added a caveat to the locked decisions on the LangGraph/LangFuse tool choice — they're the data plane (run + trace), not the control plane; policy, approvals, and cross-agent audit before risky actions hit production are a separate, emerging category and exactly the governance/assurance layer (the moat) I architect on top.

v19 — 2026-06-16 · changed: built out Memory (#5) as a positive three-tier design — session/conversational state (short-term, thread-scoped), agent working memory (shared graph state = the audit record), and deliberately-no cross-session memory (regulated-data governance call); mapped tiers to LangGraph short-term/long-term vocab; added the "same mechanism, different roles" precision and the memory-is-entitlement-scoped-and-audited tie. Replaced the FAQ #5 placeholder with the locked one-liner; flipped rubric rows #1 and #5 to ✓ and updated the self-audit intro (all scored items now answered on paper).

v18 — 2026-06-16 · changed: added an evaluator-optimizer probe-readiness note under FAQ #1 — the circular-evaluator failure mode and how calibration + cross-family judge + deterministic floor answer it, bridging to the "I evaluate the evaluator" line.

v17 — 2026-06-16 · changed: added the architecture-defense paragraph under the graphic (orchestrator-workers + evaluator-optimizer; why it's multi-agent and agentic, not a pipeline), ending with the bolded "deliberately did not build a swarm — predictable, auditable control flow beats emergent autonomy" line.

v16 — 2026-06-16 · changed: added the architecture tagline above the graphic — "It's a supervisor topology — orchestrator-workers — with an evaluator-optimizer gate." — naming the canonical pattern so item #1 lands in an architect's mental model.

v15 — 2026-06-16 · changed: added a "Rubric self-audit" table at the very top (below the title, above the graphic) — the eight scored items with a ✓ / ◐ / — status and a one-line "what clinches it" for each; flags #1 (prove genuinely multi-agent) and #5 (memory design) as the two still needing work.

v14 — 2026-06-16 · changed: expanded the FAQ to cover all eight scored items (added crisp one-liners for eval, UI, and deployment; memory still deferred); added two "[GET POINTS]" goal-setting notes to eval item #2 — making the goal an explicit written artifact ("I evaluate against a defined target") and the two-axis faithfulness/task-success framing, with "evaluate the evaluator" corrected to a separate calibration point rather than conflated with the two gates.

v13 — 2026-06-16 · changed: dropped "Mutual" from the demo company name (reads too financial-sector; the scenario could be life sciences) — now just Northwind, sector-neutral; added a FAQ section of architect-facing one-liners (Q1 multi-agent orchestration first as heaviest-weighted; embedding, vector DB, and guardrails answered; memory one-liner deferred until the memory design is locked).

v12 — 2026-06-16 · changed: added the upgraded agent-infrastructure graphic at the top of the document (evaluation lifted out of the harness into the Assurance gate; observability/auditability split with auditability badged the moat; identity→retrieval tie; runtime arrow; color legend), referenced as a sibling SVG asset.

v11 — 2026-06-16 · changed: set the demo company to Northwind (replacing the [DEMO CO] placeholder); moved the version-history block from the top of the document to this section at the end.

v10 — 2026-06-16 · changed: added Identity & entitlements as a governance pillar (HP tie + entitlement-filtered retrieval + the "stubbed here, gate in production" line); added a UI welcome banner that surfaces the authorized Northwind user to make the identity gate visible.

v9 — 2026-06-16 · changed: made running the offline eval and showing the results an explicit demo beat — narrate functional-accuracy misses and per-dimension judge-vs-gold agreement on screen, surfacing your own failures as a credibility signal.

v8 — 2026-06-16 · changed: added an embedding refresh/consistency note (model-consistency guard for the build, re-index policy for production); added the backup "All-Google (Almost)" skeleton — current-vs-Google comparison chart, the scripted line, and the "can you skip the vector DB" analysis with the regulated conclusion (keep AlloyDB).

v7 — 2026-06-16 · changed: added Nomic as a considered embedding alternative; resolved the stage-2 support decision — LLM-as-judge for the build, dedicated NLI documented as the production design to speak to; open-decisions list now effectively closed.

v1–v6 — earlier iterations: established the reusable skeleton, the candidate-vs-committed eval gate, the hybrid gate (deterministic floor + per-claim support + judge), the golden-set design, the tamper-evident audit trail, and the locked stack (ChromaDB, LangFuse, OpenAI embeddings).
