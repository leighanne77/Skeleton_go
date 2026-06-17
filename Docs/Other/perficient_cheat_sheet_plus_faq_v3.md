# Walk-in cheat sheet — Perficient prototype
*One glance, in the room. Everything ladders to one claim.*

> **THE CLAIM:** I can ship **defensible agentic systems in regulated industries.**
> **DEFENSIBLE =** guardrails + eval-against-goal + **auditability**. That trio is the moat — the part frontier models can't commoditize per client.

**Posture.** One reusable **governed-agent skeleton**; the scenario is just a skin. Topology = **orchestrator-workers + evaluator-optimizer gate** (a supervisor). *Deliberately not a swarm — in a regulated setting, predictable, auditable control flow beats emergent autonomy.*

**First move (before any code).** Write the **spec + golden-set needs** on screen. Define "correct" = **faithfulness** (grounded) **and task-success** (what was asked). → *"The gate thresholds, the checks that fire, and the eval are all undefined until 'correct' is defined. Everything's downstream of this."*

**Scenario pick (don't go cold).** Default **insurance** — the quick win: mirrors Perficient's *published* broker-quote case, proves the whole skeleton in one sitting. Speak to **energy & utilities + life sciences** as the *durable* play (audit legally continuous · OT/physical complexity · buyers pay for trust). Why the assurance subscription stays with Perficient → **independent attestation**, like a financial audit: independence you can't self-provide.

---

### The 8 scored items — locked answer + the phrase that pays

| # | Item | Locked answer | Say it |
|---|---|---|---|
| **1** | Multi-agent orchestration *(heaviest)* | Orchestrator → retriever (a **tool**) → 2 specialists → **independent control-plane gate** → synthesizer. Runtime routing + bounded retry. | *"Multi-agent because there's an independent control-plane gate — not one model grading itself."* |
| **2** | Eval framework | LangFuse + offline harness vs a golden set. **Two gates: faithfulness + task-success.** Then calibrate the judge. | *"I evaluate against a defined target — and I evaluate the evaluator."* |
| **3** | Embedding | **OpenAI text-embedding-3-small** — real semantic embedder (fixes "fee" vs "fees"). Pre-embed + cache; only the query is live. | *"Cached offline; the only live call is the query embedding."* |
| **4** | Vector DB | **ChromaDB** (keyless, local, deterministic on screen) → **pgvector** in prod. | *"In prod the vectors live next to the entitlement and audit tables, one access model."* |
| **5** | Memory | 3 tiers: session state · agent working memory (**= the audit record**) · **no cross-session, by design**. | *"Corpus retrieval isn't memory; cross-session is off because persisted user memory is regulated data."* |
| **6** | Guardrails | Deterministic hard rules (PII, schema, permitted-use), **guard-first**, distinct from eval. | *"Guardrails decide what's allowed; the eval decides whether it met the goal."* |
| **7** | UI | **Built first.** Plain-language; identity banner; visible **deliver / routed-for-review** states. | *"Built first, not bolted on — weighted equal to the backend."* |
| **8** | Deployment | Local / offline, **zero keys**. Not scored; prod path spoken, not built. | *"Nothing in the room depends on a live service."* |

---

### Locked stack (one line)
Claude (primary) · OpenAI **text-embedding-3-small** (Nomic = keyless alt) · **ChromaDB** → pgvector · **LangFuse** · **hash-chained JSONL** audit (tamper-**evident**) · identity **stubbed on purpose** · demo co = **Northwind** · Python · Groq (voice).

### The eval gate, in one breath
Deterministic floor (schema → citation-span **existence** → lexical grounding → completeness) → **stage-2 support: the span must *entail* the claim** (LLM-judge for the build; **dedicated NLI** is the prod design) → rubric judge (faithfulness + relevance, **every reported dimension gates**). Runtime: **pass → deliver · fail+retries → bounded self-correct · exhausted → withhold + escalate (HITL).**

### Killer lines
- *"I deliberately did not build a swarm — predictable, auditable control flow beats emergent autonomy."*
- *"And I evaluate the evaluator — so a green eval isn't just the judge agreeing with itself."*
- *"Tamper-evident, not tamper-proof."* (never claim tamper-proof)
- *"I build the hooks compliance plugs into; I don't fake the compliance itself."* (HIPAA/GDPR named, not built)
- *"Same skeleton, three philosophies — durable (Rolls-Royce), fast (Formula One: the customer's cloud — Google / AWS, a stack I shipped on at Nielsen / Azure, Perficient's Microsoft Inner Circle), portable (junkyard FOSS). The control plane is the part that's mine on any stack."*

### EQT layer (once the build has earned the room)
EQT funds AI → **Perficient is how the bet reaches enterprises** → the defensible part is governed agentic delivery → *"That's design, scale, and commercial in one hire."*

### Why the control plane (the survival logic)
Why I lean so hard on the control plane: what Perficient actually sells is **the ongoing assurance that the system is still correct and compliant as the world moves underneath it.** The **customer can't credibly self-attest** (no independence) and the **hyperscaler won't do it per-client** (conflict of interest + the economics don't pencil) — so the recurring-assurance layer **stays with Perficient.** That's the multi-agent-system-ops *subscription*: the build is one-time, but the assurance renews as models, regulations, and data keep moving.

![Why the recurring-assurance / control plane stays with Perficient — a three-actor Venn: Customer (owns the problem + data, can't self-attest) · Hyperscaler (owns the data plane, conflicted + won't do per-client) · Perficient (independent, per-client, regulation-current)](p_control_plane_venn.svg)

---

### Traps that lose points
UI bolted on at the end · a choice you can't explain live · jargon you can't unpack · a one-pager that's still technical · picking the scenario cold · low-code that hides the governance layer · **adversarial-nation tooling** (Milvus/Qdrant/Qwen…) · **claiming "tamper-proof"** · **trusting a green eval over an untested retriever**.

### The final deliverable
One plain-language **one-pager** to a non-technical, made-up customer. No diagrams. Never let it drift technical.

---

---

> The section below is the **full FAQ** merged in — the crisp spoken answer for each of the eight scored items, each with its prototype diagram. Use the cheat sheet above to walk in; drop into the matching FAQ answer if an architect probes.

## FAQ — one-liners for the eight scored items (with diagrams)
*Crisp spoken answers in case an architect asks. Q1–8 are the eight scored items (Q1 first because multi-agent orchestration is the heaviest-weighted). Q9 is the scenario-choice rationale. Each has a spoken version; the substance to fall back on is in the build plan. Q1–6 each carry a diagram of how the item works **in this prototype**, with any production choice moved to sit beneath the diagram (Q7–8 are not diagrammed). The SVGs live alongside this file.*

---

**1. Multi-agent orchestration — is this genuine orchestration, or a linear pipeline with one brain?**
I'll explain why these agents exist — separation of concerns, and the control-plane gate as an *independent* check that can't be the same LLM grading itself (the reasoning model isn't its own judge) — and where real orchestration shows: delegation, parallel specialists, the gate as a control-flow branch, and bounded retries.

![Multi-agent orchestration topology — orchestrator routes to a retriever-tool and two specialists, an independent control-plane gate decides, pass delivers / fail retries / exhausted withholds](faq1_orchestration.svg)

*One probe to be ready for, since you'd be inviting it: the known failure mode of evaluator-optimizer is that it becomes circular when the evaluator can't reliably distinguish good output from bad. That's exactly the risk your calibration + cross-family independent judge + deterministic floor already answer — so if an architect pushes on "isn't the evaluator just grading itself?", you walk straight into your "I evaluate the evaluator" line. The pattern name sets up your strongest material.*

**An option I'm deliberately *not* taking (be ready to name it):** *Deep Agents is the ready-made harness — I'd reach for it for long-horizon planning on top of LangGraph.* For this governed prototype I'm not using it: a batteries-included, "trust-the-LLM-to-plan" harness is the wrong default when every step has to be gated and auditable, so I keep the control flow explicit and compose the governed graph myself. Naming it shows I know the shortcut exists and chose the governed path on purpose — not that I missed it.

**2. LLM eval framework / orchestration — how do you evaluate, and against what?**
LangFuse for tracing plus an offline harness against a golden set. I evaluate against a defined target — the task-specific success criteria written before I build — on two gates: faithfulness (is it true/grounded) and task-success (is it what was asked). The eval is a gate, not a log: on fail it withholds and escalates. And I evaluate the evaluator — I calibrate each gate against the golden set — so a green eval isn't just the judge agreeing with itself.

![Eval gate — candidate answer flows through a deterministic floor, then support/entailment, then a rubric judge; all-pass delivers, any-fail withholds; two gating axes and judge calibration shown](faq2_eval_gate.svg)

**3. Embedding model — why this one?**
OpenAI text-embedding-3-small — the cost/latency floor for the retrieval quality I need: cheap and fast enough to embed the whole corpus offline and cache it, so the only live call is the query, with accuracy that holds up on regulated Q&A. Dimension-configurable, -large on standby if a scenario's semantics are subtle, clean US provenance. (Deliberate, not a default: a hash or keyword embedder breaks on morphology like "fee" vs "fees" — a real semantic embedder is the cheapest fix that's actually correct.)

![Embedding flow — corpus embedded offline with text-embedding-3-small and cached in Chroma; at demo time only the query is embedded live with the same model and version, then searches the cache](faq3_embedding.svg)

**4. Vector database — why this one?**
Chroma for the build — keyless, local, zero-setup, so it runs fully offline and I can show *deterministic* retrieval on screen. Chosen for the demo constraints — no keys, reproducible retrieval — not habit. (Milvus and Qdrant are excluded on provenance.)

![Vector database — ChromaDB in the prototype: in-process, keyless, local, persisted; deterministic retrieval on screen via a score-then-chunk_id tie-break](faq4_vector_db.svg)

**In production:** pgvector on Postgres, so the vectors live next to the entitlement and audit tables under one access model instead of in a separate service.

**5. Memory — how is it handled?**
Three deliberately-scoped tiers. Session/conversational state (thread-scoped short-term memory — kept local, bounded, the "it remembers what I just asked" layer); agent working memory (the shared graph state the agents read and write — which is also what the audit log records); and cross-session memory, which is deliberately *none* in the prototype, because persisted user memory in a regulated setting is regulated data (retention, PII, right-to-erasure, audit all attach). Memory is entitlement-scoped and audited like retrieval — a remembered fact from a regulated conversation is regulated data. And corpus retrieval isn't memory: that's RAG, not the agent remembering.

![Memory — three tiers: session/conversational state (short-term), agent working memory (the shared graph state, which is the audit record), and cross-session memory deliberately off; corpus retrieval is not memory](faq5_memory.svg)

**6. Guardrails — what are they, exactly?**
Deterministic hard rules that run before and around the LLM — PII/secret redaction, output schema/format, prohibited-content and permitted-use checks — kept deliberately separate from eval-against-goal: guardrails decide what's *allowed*, the eval decides whether the answer *met the goal*. Both gate; guard-first so it fails fast and cheap.

![Guardrails — deterministic hard rules (PII redaction, schema, prohibited content, permitted-use) run first; allowed flows to eval-against-goal, blocked is redacted/refused; guardrails decide what's allowed, eval decides if it met the goal](faq6_guardrails.svg)

**7. User-facing UI — what does the user actually see?**
Built first, not bolted on — it's weighted equal to the backend. A non-technical user gets plain-language answers, an identity banner (who they're signed in as), and the gate outcome made visible: a clean answer when it passes, a "routed for human review" state when it's withheld. The final deliverable is a plain-language one-pager, no diagrams.

**8. Deployment — local or cloud?**
Local, offline-first for the demo — zero keys to run, so nothing depends on a live service in the room. It's explicitly not scored, so I don't over-invest; if asked, the production path is the all-cloud perimeter (Vertex + AlloyDB under VPC-SC, or the equivalent AWS/Azure skeleton), but I keep that spoken, not built.

**9. Scenario choice — why these scenarios? Why insurance, and where would you take it?**
*(Spoken):* "Insurance is the quick win — fast, credible, and it mirrors Perficient's own published broker-quote case, so I can prove the whole governed skeleton in one sitting. But the *durable* version lives where the work doesn't end and the crowd can't reach: energy & utilities and life sciences — where the audit is legally continuous, the OT or physical complexity is the barrier competitors can't vault, and the buyer pays for trust, not just cost."

*(Substance to fall back on):* The filter is three properties — (a) perpetual mandatory governance, so recurring assurance is structural rather than an upsell; (b) physical / OT / experiential complexity, so platforms can't commoditize it; (c) a buyer who isn't margin-squeezed, so pricing power holds. Insurance fails two of the three as a *durable* business — it's a margin-pressured industry and the repeatable-extraction task is finite and crowdable — which is why it's the demo, not the destination. Energy & utilities (rate-base economics, NERC CIP audited continuously, OT integration) and life sciences (FDA/GxP, pharmacovigilance that never ends) pass all three. And the recurring-assurance subscription stays with Perficient rather than getting insourced because it's an **independent-attestation** business modeled on financial audit: independence you can't self-provide (SR 11-7 / EU AI Act conformity), a cross-client benchmark no single client can build, centrally-maintained regulation-current policy packs, and — for the mid-market that is Perficient's actual lane — insourcing economics that never pencil out. (Full argument: `perficient_survivability_strategy_v3.md`.)

---

---

## Version history
v3 — 2026-06-16 · changed: (1) renamed "verifier" → **control plane** throughout (incl. the orchestration diagram label and the phrase-that-pays); (2) added a **"Why the control plane (the survival logic)"** section + the **three-actor Venn** (`p_control_plane_venn.svg`) — customer can't self-attest, hyperscaler won't per-client, so recurring assurance stays with Perficient.
v2 — 2026-06-16 · changed: removed the "Three judgment calls (be ready)" section (MCP / policy packs / Deep Agents) per request — those points live in the build checklist and FAQ; the merged walk-in reference stays leaner.
v1 — 2026-06-16 · created: merged the walk-in cheat sheet (v2) and the FAQ (v3) into a single HTML reference, cheat sheet first then the full FAQ; all six FAQ diagrams (orchestration, eval gate, embedding, vector DB, memory, guardrails) embedded.
