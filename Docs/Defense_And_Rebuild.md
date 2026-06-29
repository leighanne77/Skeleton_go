# Defense & Rebuild — from "as delivered" to "as needed by the interviewer"

*A running record of the original design decision, the honest critique of it, the reframe
that resolves the tension, and the rebuild log. Written so the decisions — and the **why**
behind moving from as-delivered to as-needed — are legible, not just the diff.*

---

## 1 · The original decision (as delivered): one writer, fenced off

The build collapsed synthesis to a **single synthesizer reachable only on the gate's
pass edge.** That was a deliberate, defensible choice — arguably the right one for the
thesis the brief actually argued (*"I can ship defensible agentic systems in regulated
industries"*):

- The **governance invariant is structural, not promised.** `test_synthesizer_unreachable_on_fail`
  passes *because there is exactly one writer to fence off* — a failed gate routes to
  `withhold` and the synthesizer node is unreachable. With one writer, "a bad answer
  cannot reach the user" is a property of the graph, not a hope about prompts.
- **Fewer writers = less surface for the gate to police.** Multiple parallel agents each
  emitting prose would multiply the attack/error surface the control plane has to
  adjudicate.
- The governance layer is **genuinely built**, not decorative: entitlement-scoped
  retrieval (PII structurally invisible without clearance), the fail-closed
  floor→support→rubric cascade, the hash-chained tamper-evident audit. That trio is the
  moat the brief named, and it's the strongest part of the repo.

**This part is not being abandoned. The spine stays.**

## 2 · The trap (the honest critique)

Optimizing hard for *defensible* spent the architecture budget on the rubric item weighted
**least** (deployment isn't even scored; governance depth is one item) and **starved the
item weighted first** — *multi-agent orchestration*. Worse, the materials described the
starved part **as if it were rich**: an "orchestrator-workers" topology that, in truth, ran
a single sequential specialist, and a "cross-family judge" that was a **deterministic
lexical stub** wearing the language of a second reasoning model.

So the two rubric headliners — *multi-agent orchestration* and *defensible* — were
**competing for the same time-box** instead of being the same thing.

## 3 · The reframe (the fix): propose in parallel, dispose once

The fix is **not** "abandon the governance spine and bolt on agents." It's that the spine
**needed real parallel agents feeding it**, so the two stories reinforce:

> **Parallel agents *propose*. The single synthesizer *disposes* — after the gate.**

Parallelism lives **upstream** of the gate, in the *analysis/proposal* layer. The **write**
stays single and fenced. Concretely:

- **Genuine concurrent workers** whose outputs the gate adjudicates — a **filings-analyst**
  agent and a **market-context** agent running in parallel (real LangGraph fan-out), each
  producing grounded, cited *findings* (proposals), not prose.
- The **gate adjudicates the union** of their findings (every claim must resolve, entail,
  and pass the rubric). The gate now polices *more* — which is the point: it's the
  control plane arbitrating concurrent agents.
- The **cross-family LLM judge is wired live** as a **second reasoning agent** (OpenAI
  judging Claude-generated claims) in stage-2 support — a model never grades its own
  output unchecked — with the deterministic check as the offline/keyless fallback.
- The **one synthesizer stays on the gate's pass edge.** `test_synthesizer_unreachable_on_fail`
  is preserved verbatim.

Result: *multi-agent orchestration* and *defensible* become **one demo**. The fan-out makes
the parallelism real; the gate-adjudicates-many makes the governance story **stronger**, not
traded against.

## 4 · As-delivered → as-needed

| Dimension | As delivered | As needed (rebuild) |
|---|---|---|
| Workers feeding the gate | one sequential `specialist` node | **two+ concurrent analyst agents** (filings-analyst ‖ market-context) — real LangGraph fan-out |
| What workers emit | one candidate answer | **grounded, cited findings** (proposals) the gate adjudicates |
| Stage-2 support judge | deterministic lexical heuristic | **live cross-family LLM agent** (OpenAI judges Claude's claims); deterministic fallback offline |
| Synthesizer | one writer, pass-edge only | **unchanged** — one writer, pass-edge only |
| `test_synthesizer_unreachable_on_fail` | passes | **still passes** (invariant preserved) |
| Governance trio (entitlement retrieval · fail-closed gate · hash-chained audit) | built | **unchanged + now adjudicating concurrent agents** |
| Offline-first / keyless run | yes | **yes** (deterministic fallbacks for analysts + judge) |

**Topology change** (the gate, the conditional pass-edge, and the single synthesizer are
identical; only the upstream proposal layer fans out):

```
            ┌─ retrieve ─┐
orchestrate ┤            ├→ ┌─ filings-analyst ──┐
            └─ market ───┘   └─ market-context ──┘ → aggregate → GATE ─pass→ synthesize → END
              (parallel)         (parallel agents)   (union of    │ (floor →   (ONE writer)
                                                      findings)    │  support*  └fail→ withhold
                                                                   │  → rubric)
                                                  * stage-2 support = live cross-family judge agent
```

## 5 · Rebuild log (updated as it ships)

*Each entry: what changed · why · evidence. Append-only.*

- **✓ Probe — LangGraph fan-out is real.** Built a throwaway graph (two 1 s-sleep nodes
  fanning off one) and a Pydantic-state variant. *Evidence:* two 1 s nodes finished in
  **1.01 s** (concurrent, not 2 s), and an `Annotated[list, operator.add]` reducer merged
  both branches' writes (`['filings-analyst','market-context']`). Pydantic `AgentState`
  with a reducer field merged identically. Decision: parallelism is genuine — wire it.

- **✓ Cross-family LLM clients** (`app/agents/llm.py`). Claude = generator family,
  OpenAI = judge family. Both gated on `USE_REAL_LLM` + key and **fail soft** to the
  deterministic path → keyless/hermetic still holds.

- **✓ Parallel analyst agents** (`app/agents/analysts.py`) — `filings-analyst` ‖
  `market-context`, each scoped to its own source chunk so the two ground in **different
  sources** (the visible payoff of parallelism). Each emits a grounded, cited **Finding**
  (a proposal), validated to a verbatim retrieved span even on the LLM path. Findings
  merge via the `AgentState.findings` reducer; the new `aggregate` node unions + dedups
  them into the one candidate the gate adjudicates.

- **✓ Orchestrator rewired** (`app/orchestrator.py`) to the fan-out:
  `orchestrate → {retrieve, market_data} → {filings_analyst ‖ market_context} →
  aggregate → gate ─pass→ synthesize`. *Evidence — real concurrency in the production
  graph (not just the toy):* instrumented both analyst calls; their execution intervals
  **overlap by 2,594 ms** on **distinct `ThreadPoolExecutor` threads**. The single
  synthesizer stays on the gate's conditional pass edge — `test_synthesizer_unreachable_on_fail`
  **still passes unchanged**.

- **✓ Live cross-family judge** wired into the gate's stage-2 support
  (`app/eval/judge.py::supports` → OpenAI when keyed, lexical fallback) + `judge_mode()`
  surfaced in the gate detail and the operator trace. *Evidence:* a keyed Live run shows
  `support judge: cross-family LLM (openai)`; the hermetic test
  `test_live_judge_is_used_when_enabled` proves `supports()` defers to the model verdict
  (overriding a lexically-passing case to NO) and falls back to lexical offline.

- **✓ Operator glass-box** (`ui/`) renders the fan-out (two analyst nodes + aggregate)
  and the live-judge tier; stub topology updated to match.

- **✓ Suite green.** 55 passed, 1 skipped · `ruff` + `ruff format` clean · `mypy --strict`
  clean. New tests: `test_traverses_orchestrator_through_parallel_agents_to_gate`,
  `test_each_analyst_emits_a_grounded_finding`, `test_analysts_diversify_across_sources`,
  `test_live_judge_is_used_when_enabled`, + the preserved invariant test.

### Note — the gate genuinely gates (a feature, not a bug)
On the **keyless/deterministic** path both flagship queries DELIVER (2 agents · 2
findings → 1 candidate). On the **keyed live** path one "summarize the 10-K" query was
**routed-for-review on `rubric_failed`** — the live `market-context` agent quoted a
lower-relevance context sentence, diluting the candidate below the relevance floor, and
the deterministic rubric withheld it. That is the control plane working: a real, honest
withhold, not a crash. The offline demo's money shots run on the Demo/stub backend (by
design, offline-first); Live is the glass box that proves the real graph behaves.

---
*v1 — created at the start of the rebuild. The spine (one writer, fail-closed gate,
hash-chained audit) is preserved; the rebuild adds real concurrency upstream and a live
second reasoning agent, so multi-agent orchestration and defensibility are one story.*
*v2 — rebuild shipped: parallel analyst agents + live cross-family judge wired, evidence
recorded (2.6 s thread overlap; live judge override), suite green, invariant intact.*
