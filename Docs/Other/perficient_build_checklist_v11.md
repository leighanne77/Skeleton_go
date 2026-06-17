# Build checklist — what to do, part by part
*Actionable do-list. Pre-room homework, then the in-room order of operations, one block per part. Each part ends with the line to say.*

> **Skeleton-only means:** have the persona, doc types, policy packs, and stack mapping ready — *don't* pre-embed a full corpus or build a golden set for it. If energy & utilities comes up on the day, you stand the skeleton up on the same governed spine; if it doesn't, you still have the spoken answer for "where would you take this beyond insurance?"

---

## Phase 0 — pre-room homework (done before the session)
- [ ] Build the reusable governed-agent **skeleton**; be able to explain every line on screen.
- [ ] Pre-embed the default corpora (OpenAI text-embedding-3) and **cache** the vectors.
- [ ] Build golden sets per pre-staged corpus; **calibrate** judge + stage-2 support per-dimension with negative tests.
- [ ] Wire the **tamper-evident audit log**; rehearse the tamper → chain-break demo.
- [ ] Make the **eval report runnable on screen**; rehearse narrating a real miss out loud.
- [ ] Pre-stage **2–3 scenarios + a default**: insurance contract-intelligence (SPINF), healthcare/life-sciences (EQT portfolio), fintech (SEC/FINRA). Keep one non-corpus pattern in your back pocket.
- [ ] **Skeleton-only pre-stage for the durable verticals** (energy & utilities first — see the block below). These are the "doesn't-end, can't-be-crowded" plays; prep them as *skeletons*, not full corpora.
- [ ] **Pre-stage the policy packs** (skeleton-only — see the "Policy packs" section): US defaults (HIPAA / SEC-FINRA+SR 11-7 / NAIC / state privacy), energy & utilities, life sciences, with the EU AI Act / GDPR overlay on the shelf. Load the matching one by parameter in the room.
- [ ] Rehearse the **8 FAQ one-liners** cold; rehearse the evaluator-optimizer "isn't it grading itself?" probe → walk into "I evaluate the evaluator."

---

## Scenario skeletons — durable verticals (skeleton-only pre-stage)
*The "doesn't-end, can't-be-crowded" verticals — energy/utilities, life sciences, etc. Pre-stage each as a **skeleton** (persona + doc types + policy packs + the swappable domain layer), **not** a full pre-built corpus. Enough to spin up fast in the room and to speak to where the **durable, recurring** version of the architecture lives — the work that doesn't evaporate once the repeatable tasks are automated, and that competitors can't all crowd into.*

### Energy & utilities *(do this one)*
- [ ] **Persona** — a NERC CIP compliance / grid-operations analyst at an investor-owned utility, buried in compliance evidence and changing standards.
- [ ] **Use case** — a governed decision agent over regulated documents: NERC CIP compliance-evidence Q&A + gap-flagging, or a FERC / state-PUC filing assistant. Same spine: extract → decide → **cite the standard** → gate → audit → escalate.
- [ ] **Doc types** — NERC CIP standards + evidence, FERC orders, interconnection agreements, OT asset inventories, rate-case / regulatory filings.
- [ ] **Policy packs (load these)** — **NERC CIP** (bulk-electric-system cybersecurity), **FERC** (reliability + market regulation), **IEC 62443** + **NIST SP 800-82** (OT/ICS security), state **PUC** rules, and **US state privacy** (CCPA-class) for the retail/customer-data side. Default to the strictest applicable; same Controls underneath, different rules on top.
- [ ] **Why it's the durable play** — audit is *legally continuous* (recurring-assurance is structural, not an upsell), OT/physical complexity is the barrier competitors can't vault, and rate-base buyers pay for trust, not just cost. It resists the three failure modes insurance doesn't: margin-race, task-ends, everyone-crowds-in.

---

## Policy packs — pre-stage these (skeleton-only)

**Should you pre-load policies? Yes — but as *skeleton* packs, not a compliance program.** A "pack" here is a short, named list of the concrete rules the guardrails and eval actually check against for a regime (permitted-use, PII/PHI handling, citation/evidence requirements, prohibited outputs, retention) — **not** built compliance. Pre-staging means: when you lock the scenario in the room, you **load the matching pack with a parameter** instead of inventing rules live. Default to the **strictest applicable** pack; same **Controls** underneath, different rules on top — which is exactly why **Policies** is its own configurable pillar.

**How to pre-stage (concrete):**
- [ ] A `policies/` folder, **one file per regime**, each enumerating the rules the gate enforces.
- [ ] A **`policy_pack` parameter** on the run — the spec step (§1) picks which pack(s) to load. One flip, not a rebuild.
- [ ] **Default = the US pack the scenario implies**; keep **EU AI Act / GDPR** on the shelf as the strictest-bar overlay (owner-aligned with EQT; clears most others).

**The packs to have ready (these now exist as real files — `policies/` + `load_pack.py`):**
- [ ] **`_base.yaml`** — inherited by every pack: common PII classes + injection guard + citation/output defaults + audit defaults + the withhold baseline. (PII protection is structural, not per-vertical.)
- [ ] **`insurance_us.yaml`** *(the quick-win scenario)* — NAIC AI bulletin / MDL-668 / UTPA · GLBA (NPI) · state DOI; adds `protected_class` (block-in-decision) + `fairness_check`.
- [ ] **`energy_utilities_us.yaml`** *(durable)* — NERC CIP · FERC · IEC 62443 · NIST SP 800-82 · state PUC · state privacy; adds `ceii` / `bcsi` / `ot_asset` (block-unless-entitled).
- [ ] **`life_sciences_us.yaml`** *(durable)* — HIPAA · 21 CFR Part 11 · GxP · HITRUST; adds `phi` / `trial_subject` / `adverse_event`.
- [ ] **`manufacturing_iot_us.yaml`** — IEC 62443 · NIST 800-82 / CSF / NISTIR 8259 · EAR; adds `trade_secret` / `export_controlled` / `ot_asset`.
- [ ] **Cross-industry US defaults** also live as rules you can cite: HIPAA · SEC/FINRA + SR 11-7 · NAIC · US state privacy.
- [ ] **EU overlay (on the shelf):** **EU AI Act / GDPR** — switch on if the deployment touches the EU.
- [ ] **`load_pack("insurance_us")`** deep-merges `_base` + the overlay into one dict (tested); the guardrail / eval / audit modules read fields off it. Swap the pack, not the engine.

> **The "faithful ≠ compliant" demo beat (insurance):** a ZIP-as-protected-class-proxy decline is *grounded*, so a faithfulness-only gate passes it — and ships a proxy-discrimination violation. With `insurance_us` loaded, the same input is **withheld + escalated**, and the negative golden case flips fail→pass. That's the policy pack changing a visible outcome — not just hygiene. (Per-vertical signature negatives are in the `spec_remember_<vertical>.md` notes.)

> **Say it:** *"I pre-stage the policy packs as skeletons and load them by parameter — default to the strictest US regime the scenario implies, with the EU AI Act on the shelf as the high-water overlay. The Controls stay the same; only the rules on top change."*

---

## In the room — order of operations

### 0 · Pick the scenario (don't go cold)
- [ ] Choose from the menu offered on the day; **default to insurance contract-intelligence** unless another plays better. **Insurance is the quick win** — fast, credible, mirrors Perficient's published broker-quote case, and proves the skeleton in one sitting. Lead with it; the durable verticals (energy & utilities, life sciences) are what you *speak to* as where the recurring, un-crowdable version compounds. (Quick win earns the room; durable play shows you see past 2030.)
- [ ] Restate it in one sentence so the architect hears you frame it.

### 1 · Spec + golden-set needs — **FIRST, before any code**
**A · Write the spec (define "correct"):**
- [ ] One-sentence task definition (input → output).
- [ ] Define "correct" on the two gating axes — **faithfulness** + **task-success** — as testable assertions, not adjectives.
- [ ] List the **guardrail constraints** (PII, output schema/format, prohibited content, permitted-use).
- [ ] Enumerate the **failure modes** to catch → each becomes a `case_type`.
- [ ] State the **withhold/escalate policy** (the exact conditions to refuse + route to a human).
- [ ] Set the **thresholds** you'll be judged against (pass@1, entailment/support, judge-vs-gold agreement per dimension).

**B · Define the golden-set:**
- [ ] Per-example fields: `input` · `gold_answer` · `gold_citations` · `expected_verdict` · `case_type`.
- [ ] **Coverage, not volume** — ~20–40 cases, with the negatives: unsupported-claim, out-of-scope, prompt-injection, PII. One good negative > ten happy paths.
- [ ] **Build a jargon-heavy slice** — the domain's terms of art *and their hard negatives* (e.g. "subrogation," "coinsurance vs. copay," "not covered" vs "covered"). The golden set **detects** the jargon weakness and calibrates the threshold against it; the **handling** is the tier (a domain-tuned support model + the judge as backstop). *(See item f in `If I have more time for the Prototype_v2.md`.)*
- [ ] Edge cases: ambiguous query, empty/no-hit retrieval, conflicting sources.
- [ ] **Bootstrap with Claude → hand-verify every label** (never ship unchecked labels; the gold set stays independent of the judge).

**C · Tools:** `golden.jsonl` (one record/line) · a Pydantic model for the record · LangFuse Datasets (or Promptfoo/DeepEval) · the corpus pinned to a snapshot.

> **Say it:** *"I write the spec and the golden set first, because the thresholds, the checks, and the eval are all undefined until 'correct' is defined."*

### 2 · UI — **build it first** (weighted equal to the backend)
- [ ] Plain-language surface for a **non-technical** user.
- [ ] **Identity banner** — "signed in as an authorized Northwind user; your access scopes what these agents can retrieve."
- [ ] Governance-visible states: **deliver** (passing answer) and **routed for human review** (withheld).

> **Say it:** *"Identity is stubbed here, but in production it's the gate on who-can-ask and what-each-agent-can-see."*

> **Say it (why not a chatbot):** *"I didn't default to a chatbot — for a non-technical regulated user the win is making the gate visible, so I lead with a task console plus a scoped question box: every answer shows whether it was delivered or routed for review, what it's cited to, and that it's audited."*

### 3 · The skeleton (the spine)
- [ ] **Orchestrator** plans the task and routes.
- [ ] **Retrieval is a tool, not the spine** (so the skeleton absorbs a non-document scenario).
- [ ] **Two specialist agents** — the swappable domain layer.
- [ ] **Control-plane gate (eval-gate)** — independent (can't be the model grading itself).
- [ ] **Synthesizer** writes the user-facing answer in **exactly one place**, reachable only after the gate passes (a failed answer structurally can't reach the user).

### 4 · Embeddings + vector DB
- [ ] **OpenAI text-embedding-3-small**; embed the query with the **same model + version** as the corpus.
- [ ] **ChromaDB** local, persisted; add a **tie-break** in the store query (score, then `source_id`/`chunk_id`) so retrieval is deterministic on screen.

### 5 · Memory — three tiers, deliberate
- [ ] **Tier 1 — session/conversational state** (thread-scoped, bounded; summarize older turns, but keep summaries traceable to source).
- [ ] **Tier 2 — agent working memory** (the shared graph state the agents read/write — **this is what the audit log records**).
- [ ] **Tier 3 — cross-session memory: OFF by design.** Say why: persisted user memory in a regulated setting is regulated data (retention, PII, right-to-erasure, audit).
- [ ] Tie-back: memory is **entitlement-scoped and audited like retrieval**; corpus retrieval is **not** memory.

### 6 · Guardrails
- [ ] Deterministic hard rules: **PII/secret redaction · output schema/format · prohibited content · permitted-use.**
- [ ] **Guard-first** so it fails fast — kept distinct from eval-against-goal.

### 7 · Eval gate (the points engine)
- [ ] **Deterministic floor:** schema validation → **citation-span existence** → lexical grounding → completeness (+ retrieval-sufficiency → withhold if nothing relevant).
- [ ] **Stage-2 support:** the cited span must **entail** the claim — decompose into atomic claims, check each. (LLM-judge for the build; **dedicated NLI** is the production design to speak to.)
- [ ] **Rubric judge:** faithfulness + answer-relevance; **every reported dimension must gate** (no cosmetic scores).
- [ ] **Composition:** deterministic = hard gates (fail fast); support + rubric = graded thresholds. Overall pass = all deterministic AND stage-2 support AND every rubric dim ≥ threshold.
- [ ] **Runtime:** pass → deliver · fail with retries left → bounded self-correct (failure reason as feedback) · exhausted → **withhold + escalate (HITL)**. Hard attempt cap.
- [ ] **Calibrate** per-dimension vs the golden set + negative tests (`rejects_unsupported_span`).

### 8 · Audit trail
- [ ] **Hash-chained, append-only** log; record every decision (candidate, checks, pass/fail, deliver/withhold).
- [ ] **Demo beat:** edit one record → re-run chain verification → show it break at that record.
- [ ] Say **"tamper-evident, not tamper-proof"** (prod = WORM (Write Once, Read Many) storage + external timestamp anchoring).

### 9 · Run the eval on screen (demo beat)
- [ ] Put the report up: **pass@1 / functional accuracy**, **per-dimension judge-vs-gold agreement**, **negative-test results**.
- [ ] **Narrate a real miss** — a failed case or a low agreement number. Showing your own failures reads as credibility.

### 10 · The one-pager (final deliverable)
- [ ] One slide / one-pager to a **non-technical, made-up customer**: plain language, **no technical diagrams**.
- [ ] Draft against the chosen scenario; **never let it drift technical**.

---

## Demo-day rehearsal — before the recorded demo beats
*The last-mile execution gate. Bug-prevention detail lives in `KNOWN_ISSUES.md` (Top 10); this is what to rehearse on the day.*
- [ ] **The signature negative must fire on the demo doc** — test **both principals** (entitled → delivered + cited; unentitled → withheld + routed). A missed keyword = a **CEII disclosure on camera**. *(KNOWN_ISSUES T7)*
- [ ] **Latency** — parallelize / cache; **rehearse the pacing** so a 40s query doesn't read as a hang (spinner + a sentence of narration over the wait). *(KNOWN_ISSUES: cross-cutting Latency; T1)*
- [ ] **Gate determinism between rehearsal and recording** — pick demo questions that sit **clearly inside or outside the thresholds, never on the boundary**. *(KNOWN_ISSUES T6 / T4)*

---

## If asked / time permits

### Production path — same skeleton, three philosophies (versatility, dialed to the customer)
*Deliberately **extreme** archetypes — they exist to show range. The point isn't that one is "right"; it's that the **same governed skeleton** ports onto whatever the customer optimizes for, and I pick by **their** constraints, not my habits. The control plane (= PACE) **stays mine on every one** — only the data plane underneath changes.*

- [ ] **Rolls-Royce — durable** *(cost-no-object, built for decades).* **When:** a regulated, high-stakes, long-lived core (underwriting, claims, clinical) where the customer optimizes for correctness, security, and longevity — not unit cost. Best-of-everything + confidential compute end-to-end.
  > *Say it:* "When the asset is core and long-lived, every layer is the most capable, most secure version — durable execution, confidential compute, regulator-grade immutable audit — because the cost of being wrong dwarfs the cost of the build."

  **What the Rolls-Royce stack looks like (unlimited money, no legacy tech):**

  | Layer | Rolls-Royce build |
  |---|---|
  | Orchestration | LangGraph **+ Temporal** (durable, replayable, crash-proof long-running execution) + a real control plane |
  | Reasoning LLM | **Claude Opus (flagship)** + a **cross-family judge** (different vendor) for independent eval; provisioned throughput, provider redundancy |
  | Embeddings | **text-embedding-3-large** or **Voyage-3-large**, domain-tuned and re-embedded |
  | Vector store | **AlloyDB AI + ScaNN** (or enterprise Pinecone / Weaviate) — one transactional, replicated, CMEK store |
  | Eval | LangFuse enterprise + a **dedicated NLI judge** (DeBERTa-class) + cross-family LLM-judge + continuous online eval + golden-set regression in CI |
  | Memory | **all three tiers, governed** — long-term store ON with entitlement-scoping, retention, and right-to-erasure tooling |
  | Guardrails | layered: deterministic + **NeMo Guardrails** + a policy engine in the control plane |
  | Audit | **WORM storage + external timestamp anchoring** (RFC-3161 TSA / transparency log) — regulator-grade immutable |
  | Identity | full enterprise IAM + entitlement-filtered retrieval + **workload identity (SPIFFE/SPIRE)** + pre-dispatch approvals |
  | Confidential compute | **TEE everywhere** — confidential VMs (Intel TDX / AMD SEV-SNP) + **confidential GPUs (NVIDIA H100/H200 CC)**, attestation-gated key release |
  | Deployment | multi-region HA + DR; sovereign-cloud or on-prem option |

  *Why it lasts:* every layer is the most capable and most secure version, redundant and confidential end-to-end. *The catch:* highest cost, longest build — only justified when the asset is a core, long-lived regulated system. **The control plane is still mine** — it's just the most hardened version of it.

  **Who at Perficient's client base wants it:** a global systemically-important bank or a top-5 health payer/pharma building a *core, long-lived decisioning system* — claims/underwriting, clinical, or a GxP submission platform. Being wrong is catastrophic, a regulator audits it for years, and unit cost is a rounding error against that risk. (Maps to Perficient's regulated-trio depth: healthcare/financial-services/insurance.)

- [ ] **Formula One — fast** *(fastest time to revenue, on the customer's cloud).* **When:** the customer wants value in weeks and already lives on a cloud, so I lean fully into that cloud's managed agent platform — fast because **the platform already built the control plane** (I *configure, not code*). Trade: lock-in. Match their cloud:
  - [ ] **All-Google (GCP).** *Say it:* "All-Google lets me collapse the stack into a single IAM/CMEK/VPC-SC perimeter and make the A2A compliance agent real on Agent Engine — and I can drop the standalone vector DB by either letting Gemini ground over Vertex AI Search, or folding vectors into AlloyDB. For regulated, I keep AlloyDB so the audit trail and span-level verification stay in one governed store."
  - [ ] **AWS.** *Say it:* "On AWS it works because the managed pieces map one-to-one onto my skeleton: Bedrock runs Claude natively, AgentCore is the managed agent runtime, Knowledge Bases is managed RAG (I can drop the vector DB), Bedrock Guardrails + Evaluations cover the gate, CloudTrail/CloudWatch + KMS + PrivateLink give audit and perimeter, and Nitro Enclaves handle confidential compute — control plane kept on top. **And I was in an AWS shop at Nielsen/Gracenote, so I'm fluent in this stack, not just naming it.**"
  - [ ] **Microsoft (Azure) — *most on-brand for Perficient.*** *Say it:* "Azure is the one that compounds with Perficient's own **Microsoft AI Business Solutions Inner Circle** position. It works because Foundry Agent Service / Copilot Studio is the runtime, Claude runs via Foundry, Azure AI Search is managed RAG, Foundry Evaluations is the eval, **Entra Agent ID** gives each agent its own identity, and **Microsoft Purview** is the governance/audit spine — control plane kept on top. So the same governed skeleton lands *inside the alliance Perficient already sells through.*"

  **What the "Microsoft Formula One" stack looks like (Azure-native — the on-brand one):**

  | Layer | Microsoft Formula One build |
  |---|---|
  | Orchestration / runtime | **Azure AI Foundry — Foundry Agent Service / Copilot Studio** (the platform *is* the control plane; configure, not code) |
  | Reasoning LLM | **Claude via Foundry** (Azure OpenAI also available) |
  | Retrieval / RAG | **Azure AI Search** (managed RAG — can drop the standalone vector DB) |
  | Embeddings | Azure OpenAI embeddings |
  | Eval | **Foundry Evaluations** (+ keep my golden-set harness on top) |
  | Memory | Foundry agent/thread state; long-term via the governed store |
  | Guardrails | **Azure AI Content Safety** + Purview policy |
  | Audit / governance | **Microsoft Purview** + Azure Monitor — *plus my hash-chained control plane on top* |
  | Identity | **Entra Agent ID** (per-agent identity) + entitlement-filtered retrieval |
  | Confidential compute | Azure confidential VMs |
  | Deployment | Azure region(s); fast because the platform already built the control plane |

  *Why it's fast:* Foundry owns the data plane, so I configure rather than code. *The catch:* lock-in — the perimeter is Microsoft's. **The control plane (guardrails + eval-against-goal + tamper-evident audit) stays mine on top.**

  **Who at Perficient's client base wants it:** an enterprise that's already a **Microsoft shop** (M365 + Dynamics + Azure + Copilot) and wants a governed agent *live this quarter* — e.g., a regional insurer or health system standardized on Azure. This is the **most on-brand** option: it lands inside the alliance Perficient already sells through, so it's the likeliest real engagement.

- [ ] **Junkyard — portable** *(extreme portability + cost-consciousness).* **When:** startups, air-gapped/edge, cost-sensitive, or "must run anywhere, no keys." All FOSS + clean-provenance (no adversarial-nation tooling, §1); runs on a laptop or one VM.
  > *Say it:* "When it has to run anywhere with no keys, I go all-FOSS clean-provenance and **decompose**: most production value is deterministic workflow (rule → classifier → ML → single LLM call → agent), agency reserved for the ambiguous seams. The prototype proves I *can* orchestrate agents; production uses the cheapest tool that's correct — control plane still mine."

  **What the Junkyard stack looks like (all FOSS, clean provenance, runs anywhere):**

  | Layer | Junkyard build |
  |---|---|
  | Orchestration | LangGraph (OSS); for batch, **Airflow / Prefect / Dagster**; **Temporal OSS** for durability |
  | LLM | self-hosted open weights — **Llama (Meta)** or **Mistral (France)** via **vLLM / Ollama / llama.cpp**, quantized (GGUF). *Excluded: Qwen / DeepSeek / GLM / Yi / Kimi — China, §1.* Burst to a hosted open-router only on demand |
  | Embeddings | **Nomic Embed (US)** / **all-MiniLM (DE)** / **Snowflake Arctic (US)**, on CPU. *Excluded: BGE / GTE — China* |
  | Vector store | **LanceDB** (embedded) / **pgvector** / **FAISS** / **sqlite-vec** / **DuckDB-VSS** — file-based, zero ops. Small corpus → skip it (BM25 or long-context) |
  | Eval | **Promptfoo / DeepEval** + LangFuse self-hosted — keyless, local; deterministic checks do most of the work |
  | Memory | **SQLite checkpointer** — file-based, zero infra |
  | Guardrails | deterministic Python + **Guardrails AI / Presidio** (PII) |
  | Audit | the **hash-chained JSONL** you already built — portable, append-only; optional Merkle log |
  | Identity / policy | **Keycloak** + **OPA (Open Policy Agent)**; JWT |
  | Confidential (optional) | **Gramine** on SGX — or trust your host |
  | Deployment | **Docker Compose** on a laptop / single VM / air-gapped. Zero-keys-to-run |

  *The radical idea:* in production you often **don't need a multi-agent system** — decompose to the ladder **rule > classifier > ML model > single LLM call > agent**, climb only when the cheaper rung is wrong, and reserve agency for the seams. *Why it survives:* runs anywhere, near-zero marginal cost, no lock-in, no foreign-adversary tooling. *The catch:* you operate and assure it yourself — which is exactly where **the control plane (mine in every version)** earns its keep.

  **Who at Perficient's client base wants it:** a **sovereignty-sensitive, air-gapped, or edge** deployment — an OT/edge system in a utility substation with no cloud connectivity, a defense-adjacent customer who can't send data off-prem, or a cost-sensitive startup that needs it to "run anywhere with no keys." The clean-provenance posture (§1) is a selling point here, not just a constraint.

- [ ] **The constant across all three:** the **control plane — guardrails + eval-against-goal + tamper-evident audit (= PACE)** — never gets outsourced to the stack. Only the data plane swaps. *(This is the real answer to "what would you do differently in production?")*

> **Why I lean so hard on the control plane (the survival logic):** what Perficient actually sells is *the ongoing assurance that the system is still correct and compliant as the world moves underneath it.* The **customer can't credibly self-attest** (no independence) and the **hyperscaler won't do it per-client** (conflict of interest + the economics don't pencil) — so the recurring-assurance layer **stays with Perficient.**

![Why the recurring-assurance / control plane stays with Perficient — a three-actor Venn: Customer (owns the problem + data, can't self-attest) · Hyperscaler (owns the data plane, conflicted + won't do per-client) · Perficient (independent, per-client, regulation-current)](p_control_plane_venn.svg)

> **Production default (most builds):** whatever the archetype, for most production deployments I **replace ChromaDB with pgvector on Postgres**, so the vectors live next to the entitlement and audit tables under **one access model** instead of in a separate service. Chroma is the prototype's keyless/offline choice; pgvector is the governed-store default in production.

### For production — embeddings & vector DB options
**a · Embeddings — options, and the multimodal case.**
- [ ] **Text (default):** OpenAI **text-embedding-3-small** → **-large** for subtler semantics; **Nomic** (keyless/offline); **Voyage-3** / **Cohere Embed v3** for stronger retrieval. All clean-provenance (§1); excluded: BGE/GTE.
- [ ] **Multimodal (when the corpus has images/audio):** for *cross-modal* search (text query → image hit) you need **one model that puts both modalities in the same space** — **CLIP** / **SigLIP**, **Cohere multimodal**, **Voyage multimodal**, **Nomic Embed Vision**, or managed **Vertex / Titan multimodal**. **Audio → transcribe first** (Groq/Whisper) and embed the *transcript*, so the citation stays a citable text span.
- [ ] **Metadata filtering matters *more* for multimodal:** you keep a **separate index per embedding space** (can't compare different models/dims), and you filter by modality + source + entitlement — which favors a metadata-rich store (another reason pgvector/Weaviate fit).

**b · Vector DB — options, why we keep what we've got, and when we'd switch.**
- [ ] **Keep ChromaDB for the build** — keyless, local, deterministic on screen.
- [ ] **pgvector on Postgres = the production default** — vectors beside entitlement + audit tables, one access model, SQL/metadata filters; **AlloyDB + ScaNN** for scale or hybrid entitlement-filtered search.
- [ ] **Switch to Pinecone when:** the customer wants a **fully-managed, serverless, horizontally-scaling** vector service and doesn't want to operate Postgres — large corpora / high QPS with minimal ops.
- [ ] **Weaviate when:** native **hybrid (vector + keyword)** search is the priority, self-hosted or managed.
- [ ] **LanceDB / FAISS / sqlite-vec when:** embedded, offline, file-based (the Junkyard / air-gapped case).
- [ ] **Excluded (§1):** Milvus/Zilliz (China), Qdrant (Russia).

### Tools — using vs. deliberately not using
- [ ] **Deep Agents — deliberately not using:** the ready-made LangChain harness on LangGraph — I'd reach for it on long-horizon planning, but a "trust-the-LLM-to-plan" harness is the wrong default when every step has to be **gated and auditable**, so I keep control flow explicit. Naming it shows the shortcut was a choice, not a miss.
- [ ] **MCP — using, but scoped:** name the open standard (Linux-Foundation-governed; what the Microsoft/Salesforce control planes speak). **In the demo, in-process SDK MCP only — not external servers:** the Claude Agent SDK wraps your own Python functions as in-process MCP tools (`create_sdk_mcp_server`) — the retriever, the citation-verifier, the audit-writer — **no separate process, no keys, fully offline.** Satisfies "use MCP" without breaking the zero-keys / explain-everything-on-screen posture.

### Other on-call answers
- [ ] **EQT layer:** the four beats → *"design, scale, and commercial in one hire."*

> **Moved to its own doc:** the **stage-2 NLI support tier** (the production eval upgrade) and the **identity-in-production** detail now live in `If I have more time for the Prototype.md`, each with the exact steps to add it to the skeleton. Speak to them from there.

---

## Don't (the traps)
UI last · a choice you can't explain · jargon you can't unpack · a technical one-pager · picking cold · low-code that hides governance · **adversarial-nation tooling** · **claiming "tamper-proof"** · **trusting a green eval over an untested retriever**.

---

## Version history
v11 — 2026-06-16 · changed: switched the Demo-day rehearsal block's `KNOWN_ISSUES` cross-references from volatile `#`-rank numbers to stable `T`-task IDs (T7 / cross-cutting Latency + T1 / T6 + T4), so a future Top-guard renumber can't drift them. No content change to the three rehearsal items.
v10 — 2026-06-16 · changed: added a **"Demo-day rehearsal — before the recorded demo beats"** section after §10 — the three on-camera execution guards (signature negative must fire / test both principals → no CEII disclosure on camera; latency pacing so a 40s query doesn't read as a hang; gate determinism → pick boundary-safe demo questions), each cross-referenced to the `KNOWN_ISSUES.md` Top 10.
v9 — 2026-06-16 · changed: (1) **terminology** — renamed the "verifier" to the **control plane** throughout the body (the eval-gate node is now "control-plane gate"; "citation-verifier" tool name kept); (2) added the **control-plane survival narrative** + a **three-actor Venn** (`p_control_plane_venn.svg` — Customer can't self-attest, hyperscaler won't per-client, so recurring assurance stays with Perficient) after the "constant across all three" line; (3) added a **jargon-heavy golden-dataset** checkbox to §1B (golden set detects, the tier handles); (4) added a **"For production — embeddings & vector DB options"** subsection (text + multimodal embeddings, metadata-filtering note, vector-DB options with when-to-switch-to-Pinecone/Weaviate/LanceDB).
v8 — 2026-06-16 · changed: (1) **moved Deep Agents** out of "Other on-call answers" into a new **"Tools — using vs. deliberately not using"** subsection (alongside the scoped-MCP note); (2) added a second **UI say-it line** ("I didn't default to a chatbot…") to §2; (3) in the production path, added **who-wants-it customer profiles** for Rolls-Royce / Microsoft-Formula-One / Junkyard, a dedicated **Microsoft Formula One stack table** (Azure-native, the on-brand one), and a **production-default note** (replace ChromaDB → pgvector on Postgres for most builds, vectors beside the entitlement/audit tables); (4) **moved out** the stage-2 NLI support tier and the identity-in-production detail to the new `If I have more time for the Prototype.md` (with a pointer left behind).
v7 — 2026-06-16 · changed: (1) added the **Rolls-Royce stack table** (unlimited-money / no-legacy: Temporal, Claude Opus + cross-family judge, -large/Voyage embeddings, AlloyDB+ScaNN, NLI judge + CI regression, all-three-tiers governed memory, NeMo + policy engine, WORM + RFC-3161 anchoring, SPIFFE/SPIRE, TEE + confidential GPUs) under the production path; (2) added the **Junkyard stack table** (all-FOSS clean-provenance: LangGraph/Temporal-OSS, self-hosted Llama/Mistral, Nomic/MiniLM/Arctic, LanceDB/FAISS/sqlite-vec, Promptfoo/DeepEval, SQLite checkpointer, Presidio, Keycloak+OPA, Gramine, Docker Compose) with the decompose-to-the-cheapest-correct-tool note; (3) **alignment fixes** — added the **Deep Agents "deliberately not using"** on-call answer (was in the FAQ/cheat-sheet/plan but missing here), and rewrote the **policy-pack list** to point to the real built files (`_base` + insurance/energy/life-sci/**manufacturing**, `load_pack.py`, inherited PII, the faithful≠compliant insurance worked example, pointer to the `spec_remember_*` notes).
v6 — 2026-06-16 · changed: (1) expanded the "If asked / time permits" production path into three archetype blocks with say-it lines — Rolls-Royce (durable), Formula One (fast, with All-Google / AWS / Microsoft sub-lines: the All-Google quote, the AWS "I was in an AWS shop at Nielsen" + why-it-works, the Microsoft Inner-Circle tie + why-it-works), junkyard (portable) — each tied to what the end customer optimizes for, verifier-stays-mine constant; (2) added a "stage-2 NLI support tier" checklist of what I'd build with more time on the eval; (3) expanded the MCP line with the in-process SDK MCP detail (`create_sdk_mcp_server`, no process/keys, offline); (4) added a "Policy packs — pre-stage these (skeleton-only)" section (US defaults / energy & utilities / life sciences / EU overlay, loaded by `policy_pack` parameter) + a Phase 0 pre-stage bullet.
v5 — 2026-06-16 · changed: spelled out the WORM acronym in §8 — "WORM (Write Once, Read Many) storage."
v4 — 2026-06-16 · changed: moved the "Skeleton-only means…" note to the very top of the doc (above Phase 0) as a standing callout, and removed the duplicate copy from the energy & utilities section.
v3 — 2026-06-16 · changed: locked the "insurance = quick win, durable verticals = the compounding play" framing on the in-room scenario-pick line — lead with insurance (fast, credible, mirrors the published broker-quote case, proves the skeleton), speak to energy/utilities + life sciences as where the recurring, un-crowdable version lives. — lead with insurance (fast, credible, mirrors the published broker-quote case, proves the skeleton), speak to energy/utilities + life sciences as where the recurring, un-crowdable version lives.
v2 — 2026-06-16 · changed: added a "Scenario skeletons — durable verticals (skeleton-only pre-stage)" section with **energy & utilities** fully specified (persona, use case, doc types, **policy packs: NERC CIP / FERC / IEC 62443 / NIST SP 800-82 / state PUC / state privacy**, and the durable-play rationale); flagged it as skeleton-only (persona + doc types + policy packs + stack mapping, no full corpus build); updated the Phase 0 pre-stage line to point to it. with **energy & utilities** fully specified (persona, use case, doc types, **policy packs: NERC CIP / FERC / IEC 62443 / NIST SP 800-82 / state PUC / state privacy**, and the durable-play rationale); flagged it as skeleton-only (persona + doc types + policy packs + stack mapping, no full corpus build); updated the Phase 0 pre-stage line to point to it.
v1 — 2026-06-16 · created: part-by-part build checklist (Phase 0 homework → in-room order of operations → if-asked → traps).
