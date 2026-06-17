# UI build prompt — governed-agent prototype
*Paste this into your AI builder (Claude / v0 / etc.) to generate the UI. It states the constraints, asks for **several options**, and forces the governance states to be visible. Companion analysis ("do we need a chat UI?") is below the prompt.*

---

## The prompt (copy from here)

> You are building the **user-facing UI for a governed multi-agent assistant** used in a regulated industry (**banking & financial services** / insurance / energy / life sciences / manufacturing — keep it sector-neutral; the **loaded demo is BFSI**). The end user is **non-technical** (a **wealth-management advisor**, persona name "Dana" at a fictional company "Northwind Securities", getting up to speed on a stock for a client meeting — a delayed quote + a cited summary of the issuer's recent SEC filings). She is not a governance specialist, so the surface must be plain-language and the control plane has to ride underneath — enforced, but not in her face. *(The firm's compliance function is the secondary persona: the accountable owner who runs the compliance-Q&A path and receives anything the gate routes.)* This UI is **weighted equal to the backend**, so it must be legible, plain-language, and make the *governance* visible — it is not a generic chatbot. **Ship the UI as TWO modes of the same app, switched by one toggle: (1) a Customer view — plain-language, for the non-technical end user; and (2) an Operator view — a glass box that shows the orchestration graph forming and the control-plane gate working, for the technical reviewer (the interviewing architect). Same run, same backend events; default to the Customer view and flip to Operator to narrate *how* it works.**
>
> **Hard requirements (every option must satisfy these):**
> 1. **Identity banner** at the top: "Signed in as an authorized Northwind user — your access scopes what these agents can retrieve and answer." (Identity is stubbed; the banner makes the gate visible. The displayed scopes are the **loaded pack's entitlements** — for the BFSI demo, `mnpi_cleared` / `sar_cleared`; the same banner would show `ceii_cleared` / `ot_cleared` under the energy pack. Don't hardcode them — read from the pack. **Dana the advisor holds *neither* clearance**, which is exactly why a briefing that brushes against MNPI or a SAR routes for review — the banner makes that scoping visible before she even asks.)
> 2. **Two explicit answer states, never blurred:** a **DELIVERED** state (a passing, cited answer) and a **ROUTED FOR HUMAN REVIEW** state (the answer was withheld by the gate). A wrong answer must never be shown as if confident.
> 3. **Citations are first-class** — every claim in a delivered answer shows the source span / document it's grounded in, clickable or expandable.
> 4. **Plain language, no jargon, no technical diagrams** in the surface the user reads. (The internal pipeline can be shown in a separate, collapsible "how this was checked" panel for the demo, but the primary surface stays plain.)
> 5. **Offline-first / zero-keys** friendly: assume the backend is a local Python process; don't require external auth or third-party widgets.
> 6. An optional, collapsible **"audit / trace"** affordance for the demo (show the hash-chained record for the last answer) — present but out of the non-technical user's way.
> 7. **Two modes, one app, one run (required):**
>    - **Customer view (default)** — everything in requirements 1–6: plain language, the two answer states, citations, identity banner. No graph, no internals.
>    - **Operator view (toggle)** — a *glass box* for the technical reviewer: the **orchestration graph** (orchestrator → retriever-tool → specialists → control-plane gate → synthesizer) with each node's **status** (done / failed / withheld / unreachable) from the run trace (**rendered post-run** — see the build note below; live streaming is an optional stretch); the **gate's stages** (deterministic floor → support/entailment → rubric judge) with a pass/fail per stage; the retrieved chunks + scores; the **entitlement decision** (which sensitive classes were filtered for this principal); and the **audit chain** growing one row per step.
>    - **Same backend, same events.** The Operator view is a *read-out of the actual execution* — driven by the LangGraph run state / callbacks, the eval-gate result object, and the audit log you already emit. **Never mock the graph or fake node states.** If a node or stage isn't wired to a real run, don't show it — you must be able to explain everything on screen. The toggle changes the *view*, never the run.
>
> **Deliverable:** propose **3–4 distinct UI options** (not just restyles — genuinely different interaction models), each with: a short description, an ASCII/wireframe sketch, what it's best at, what it trades off, and how it surfaces the two answer states + citations + identity. Then **recommend one** for a 2.5-hour live demo with a non-technical persona, and justify the pick. Keep the stack simple (Streamlit or Gradio for speed; React only if a richer layout earns it).
>
> **The four options to cover (at minimum)** — these define the **Customer view's** interaction model; the **Operator view is the same glass-box overlay** on top of whichever you choose:
> - **Option A — Structured task console.** The user performs the task directly (e.g. upload a document → see extracted fields / answer in a structured panel with citations + a clear DELIVERED / ROUTED banner). No open chat box. Best at making the governed pipeline legible and keeping the demo on-rails.
> - **Option B — Hybrid: task panel + constrained Q&A.** The structured task console, plus a *scoped* question box ("ask about this document") that only accepts in-scope questions. Combines directness with conversational follow-up while staying bounded.
> - **Option C — Guided wizard / stepper.** A step-by-step flow (select task → confirm scope/identity → run → review result → deliver-or-escalate). Best for a non-technical user who benefits from rails and for showing each governance checkpoint as a discrete step.
> - **Option D — Conversational with a governance rail.** A chat interface, but every assistant turn carries a visible verdict chip (delivered / withheld), inline citations, and a side "governance rail" showing what the guardrails/eval did. Familiar, but must be engineered so the gate states aren't lost in the chat flow.
>
> For each option, explicitly answer: *does this make guardrails + eval-against-goal + audit visible to a non-technical user, or does it hide them?*

---

## The two modes — wireframes

**Customer view (default).** Plain language; the verdict and its sources are the whole story.

```
 [ ●Customer view | Operator view ]            <- one toggle, top-right
┌──────────────────────────────────────────────────┐
│ Signed in as an authorized Northwind user          │  identity / entitlement banner
│ Your access: mnpi_cleared, sar_cleared             │  (read from the loaded pack)
├──────────────────────────────────────────────────┤
│ Ask or pick a task ▸                               │
│ [ Are there open Reg BI supervision gaps for Q1? ] │
├──────────────────────────────────────────────────┤
│  ✓ DELIVERED                                       │  never-blurred verdict
│  Rep R-119's recommendations weren't reviewed      │
│  within the 30-day window — an open supervision    │
│  gap against the Reg BI Care Obligation.           │
│   ▸ Source: Supervision Log Q1 2026      [view]    │  first-class citations
│   ▸ Source: Reg BI Care Obligation        [view]   │
│   [ view audit ]   (collapsed)                     │
└──────────────────────────────────────────────────┘

  ...and when the gate withholds, the same surface, unmistakably different:
┌──────────────────────────────────────────────────┐
│  ⤴ ROUTED FOR HUMAN REVIEW                         │
│  This needs a cleared reviewer. Sent to your       │
│  compliance team — not answered here.              │
└──────────────────────────────────────────────────┘
```

**Operator view (toggle).** The *same run*, opened up — the graph forms and the gate decides, live.

```
 [ Customer view | ●Operator view ]

 RUN  q="What are the Project Atlas deal terms?"   principal=[ ]   (unentitled)

   orchestrator ●done
      └▶ retriever (tool) ●done    3 chunks   top = mnpi_dealbook  0.88
      └▶ specialist: compliance ●done
             ▼
   control-plane gate ●WITHHELD
      ├ deterministic floor    ✓ schema  ✓ span-exists  ✓ grounded
      ├ entitlement check      ✗ mnpi requires mnpi_cleared — principal has none
      └ verdict: ROUTED_FOR_REVIEW   route = human:compliance-reviewer
   synthesizer ⃠ unreachable (gate did not pass)

   audit chain   #41 hash=9c2f… ◀ #42 hash=a17b…   verify ✓
```

*The entitled run (`principal=[mnpi_cleared]`) shows the same graph, the gate passing, the synthesizer reachable, and a DELIVERED verdict — flipping that one input on screen is the money shot.* Both modes render from the **same** `AnswerEnvelope` + run trace + audit log; the Operator view adds no new backend, only a new read-out.

### Operator view — build it post-run, not as a live animation (do this)

**Default approach.** Render the Operator view **once, after the run finishes**, from a captured trace object. The graph topology is **fixed** — orchestrator → retriever-tool → specialists → control-plane gate → synthesizer — so you do **not** need dynamic graph layout or real-time streaming. You draw the known nodes and **recolor them** from the trace. This is the cheap, robust build that survives Streamlit's rerun model and an architect's questions.

**Why not live animation.** Streamlit reruns top-to-bottom on every interaction, so true node-by-node "lighting up" needs `st.fragment` / streaming / placeholder-mutation gymnastics that eat the build time you owe to the eval gate and guardrails. Post-run rendering gives ~95% of the "watch the graph form" effect for a fraction of the cost and risk. (Streamed step-by-step is a **stretch goal at the end**, never the plan.)

**How (concrete, Streamlit):**
1. Have the backend return, alongside the `AnswerEnvelope`, a small **`RunTrace`** the UI just displays — e.g.:
   ```
   RunTrace = {
     "nodes": [ {"id":"orchestrator","status":"done"},
                {"id":"retriever","status":"done","detail":"3 chunks, top=mnpi_dealbook 0.88"},
                {"id":"specialist_compliance","status":"done"},
                {"id":"gate","status":"withheld"},
                {"id":"synthesizer","status":"unreachable"} ],
     "gate_stages": [ {"name":"deterministic_floor","pass":true, "detail":"schema, span-exists, grounded"},
                      {"name":"entitlement","pass":false,"detail":"mnpi requires mnpi_cleared — principal has none"} ],
     "entitlement_decision": {"filtered":["mnpi"], "principal":[]},
     "verdict":"routed_for_review", "route":"human:compliance-reviewer",
     "audit_rows": [ {"n":41,"hash":"9c2f…"}, {"n":42,"hash":"a17b…"} ]
   }
   ```
   Populate it from the LangGraph run (final state / per-node callbacks), the gate result object, and the audit log — **the data already exists**; you're only shaping it for display. Compute nothing new for the UI.
2. **Render the fixed graph, colored by status.** Two cheap options, pick one:
   - `st.graphviz_chart` with a DOT string where each node's `fillcolor` = status (done = green, withheld/failed = amber/red, unreachable = grey). Edges are constant. ~15 lines.
   - Plain layout: a row of node "cards" (`st.columns`), each with a status badge (✓ / ✗ / ⃠) + its one-line `detail`. Even cheaper, no graphviz dependency.
3. Below the graph: the **gate stages** as a ✓/✗ checklist (+ detail per stage), the **entitlement decision** line, and the **audit chain** rows (`n`, `hash`, verify ✓) — all read straight from `RunTrace`.
4. The **toggle** just swaps which block renders (Customer surface vs the `RunTrace` block) over the **same** `st.session_state` run — no re-execution.

**Still real, not mocked.** Post-run ≠ fake: every node status, gate stage, and audit row comes from the execution that just ran. You give up the per-step *animation*, not the *truth* of it. Against the T1 stub (before the real graph exists), render a **canned `RunTrace`** of each verdict type; swap to the real one at T3+.

**DON'T:** build a bespoke graph-animation engine, pull in a heavy JS graph library, or reach for `st.fragment`/streaming just to make nodes light up one-by-one. Fixed-topology + post-run recolor is the move.

> **Say it:** *"The graph view renders from the real run trace after it completes — I color a fixed topology by what actually happened, so it's honest and cheap. I didn't burn the session animating it; that time went to the gate and the guardrails."*

## Do we need a chat-based interface? (the analysis)

**Short answer: no — and a bare chatbox is often the *weaker* choice here.** Chat is one valid option, not a requirement. The rubric rewards a UI that makes governance legible to a non-technical user; a raw chat window tends to *hide* the very things you're being scored on.

**Why chat is tempting:** the document-QA use case is naturally conversational, chat is familiar to non-technical users, it's fast to build, and it shows session memory ("it remembers what I just asked").

**Why chat can hurt you:**
- **It hides the gate.** Delivered vs. routed-for-review is the heart of the governance story; in a chat stream those states blur into "messages." A structured surface puts the verdict front and center.
- **It invites off-spec input.** An open box lets the user (or the architect) wander outside the task, which makes guardrails/eval harder to demo cleanly and risks a wandering 2.5 hours. A task-shaped UI constrains input to what the spec covers.
- **Citations and audit get buried.** In a task console they're first-class panels; in chat they're easy to lose.

**The recommendation:** lead with **Option B (hybrid)** — a structured task console (upload/select → cited result → DELIVERED / ROUTED banner → "view audit") *plus* a scoped Q&A box for follow-ups. It gets the legibility of a task UI and the natural feel of chat, while keeping the gate, citations, identity, and audit visible. If time is tight, fall back to **Option A** (pure task console) — it's the fastest to make governance-legible. Reserve **Option D** (chat with a governance rail) only if the chosen scenario is genuinely conversational *and* you've engineered the verdict/citation rail so the gate never disappears.

**The two-mode move (why it scores double).** The same Option-B app ships with an Operator toggle that shows the orchestration graph forming and the gate deciding, driven by the real run. One build satisfies *two* rubric items: the **non-technical UI** (Customer view, the default) *and* **multi-agent orchestration + eval-against-goal made legible** (Operator view — the heaviest lens). Keep it cheap: the Operator view reads from the LangGraph state, the gate result object, and the audit log you already produce — not a bespoke animation engine. Default to Customer; flip to Operator the moment the architect asks *how* it works.

> **Say it (two modes):** *"Same app, two views of the same run. The customer sees plain language — delivered or routed, and what it's cited to. I flip one toggle and you watch the graph form and the gate decide, live, on the real execution — that's the orchestration and the eval-against-goal, not a slide."*

> **Say it:** *"I didn't default to a chatbot — for a non-technical regulated user the win is making the gate visible, so I lead with a task console plus a scoped question box: every answer shows whether it was delivered or routed for review, what it's cited to, and that it's audited."*