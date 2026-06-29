# A note on the rebuild

Thank you for the candid feedback — that I'd been working through a single AI assistant
rather than orchestrating several in parallel, which is the working pattern you need at
the Lead level. It was the right critique, and I want to be straight with you about both
the original decision and what I did with the note.

## What I'd originally built, and why

The first version collapsed answer-writing to a **single synthesizer reachable only on
the gate's pass edge**. That wasn't an accident — it was a deliberate bet on the thesis
the brief argued: *I can ship defensible agentic systems in regulated industries.* With
exactly one writer to fence off, "a bad answer cannot reach the user" becomes a property
of the graph, not a promise about prompts — there's a test (`test_synthesizer_unreachable_on_fail`)
that holds precisely because there's one writer. The governance trio underneath it —
entitlement-scoped retrieval, a fail-closed gate, a hash-chained audit log — is genuinely
built, and it's the strongest part of the repo.

## The honest part

Optimizing that hard for *defensible* spent the architecture budget on the rubric item
weighted **least** and starved the one weighted **first** — multi-agent orchestration.
Worse, the materials described the starved part as if it were rich: an "orchestrator-workers"
topology that in truth ran a single sequential specialist, and a "cross-family judge"
that was actually a deterministic lexical stub wearing the language of a second reasoning
model. You caught exactly the right thread.

## The fix — and why it's *not* a retreat from the governance spine

The insight that unlocked it: I'd been treating "real parallel agents" and "one-writer
governance" as competing for the same time-box. They aren't. The resolution is one line:

> **Parallel agents *propose*. The single synthesizer *disposes* — after the gate.**

Parallelism lives strictly *upstream* of the gate. So I rebuilt the propose layer as a
**genuine LangGraph fan-out**: two analyst agents — a **filings-analyst** and a
**market-context** agent — now run concurrently, each grounding in a different source and
emitting a cited *finding* (a proposal, not prose). An aggregate node unions their
findings into the one candidate the gate adjudicates. And the **cross-family judge is now
live** — a different-family model (OpenAI) actually judging the Claude-generated claims at
the gate's stage-2 support, with the deterministic check as the keyless fallback.

Crucially, the one synthesizer stays on the gate's pass edge, and the invariant test
passes **unchanged**. Multi-agent orchestration and defensibility stopped competing and
became the *same* demo: the gate now adjudicates several concurrent agents, which makes
the governance story stronger, not traded away.

## How I made sure it's real, not described-as-real

I held myself to the standard your feedback implied — evidence, not adjectives:

- **The concurrency is real.** I instrumented both analyst calls in the production graph;
  their execution intervals **overlap by ~2.6 seconds on distinct worker threads** — they
  genuinely run at the same time, not sequentially relabeled.
- **The cross-family judge is real.** A keyed run shows the gate reporting
  `support judge: cross-family LLM (openai)`, and a test proves `supports()` defers to the
  model's verdict (it can override a lexically-passing claim to *not supported*) while
  failing soft to the deterministic check offline.
- **The spine is intact.** `test_synthesizer_unreachable_on_fail` still passes; the whole
  suite is **55 passed, 1 skipped**, with `ruff` and `mypy --strict` clean.
- **It still runs keyless.** Offline-first holds — the analysts and the judge both fall
  back to deterministic paths, so the system runs with zero keys.

One detail I'm proud of rather than hiding: on the live path, a clean-looking "summarize
the 10-K" query was *routed for review* because the relevance floor genuinely judged the
answer too weak. That's the control plane doing its job — it fails **closed**. I'd rather
show you a system that withholds honestly than one that always says yes.

If it's useful, the full reasoning and decision log is in `Docs/Defense_And_Rebuild.md`,
the architecture note is in `design.md`, and the glass-box view in the UI is a read-out of
the actual run — you can watch the two agents fan out and the gate adjudicate them live.

Thank you again for the push. It made the work better.

— Leigh Anne
