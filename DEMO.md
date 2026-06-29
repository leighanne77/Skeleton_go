# 🎬 Live Demo Script — Governed Advisor Stock-Briefing

**Open:** http://localhost:8501  ·  start it with `python run.py` (keyless works; add keys
for live data — see `README.md` → Configuration).

**Audience framing:** *"An advisor getting up to speed on a stock — where every answer
is governed before it reaches them."*

**Two setup notes**
- Keep **⚙ Show my work → engine = Demo** for the scripted shots (the polished path).
  Flip to **Live graph** only if a technical reviewer wants to watch the real
  LangGraph run.
- There are **three inputs**: a typed question, the **demo-scenario** dropdown (2nd),
  and the **live top-50 stock picker** (3rd). The scripted shots use the 2nd; the live
  quote uses the 3rd.

**The through-line to repeat:** *guardrails + eval-against-goal + tamper-evident audit*
— every shot maps to one of those three.

---

## 0 · The welcome (10 sec)
Land on the welcome card → read the one line *"Useful for you. Defensible for
compliance."* → click **Enter the Stock Briefing**.

## 1 · The value shot — a real briefing (45 sec)
**Demo-scenario dropdown → "📊 Brief me on MRB — liquidity risk (10-K)" → Run.**
- **Say:** "Quote, plus the key points from the 10-K, and every fact links to the source."
- **Show:** ✓ DELIVERED · the quote card (labeled *delayed*) · expand a **Source** → the
  exact 10-K span.

## 2 · The governance line — public vs. MNPI (60 sec) ⭐ *the strongest shot*
- Run **"🗂️ MRB — latest 8-K event"** → **DELIVERED** (it's *public*).
- Run **"🔒 Project Atlas pre-announcement deal terms"** → **⤴ ROUTED** — *"the same
  issuer, but this is material non-public info; the advisor isn't cleared, so it's
  withheld."*
- Click **⚙** → in **Reviewer control** add **`mnpi_cleared`** → **Re-run** → now
  **DELIVERED** with the dealbook cited.
- **Say:** "Same question, one entitlement flipped — that's the visible difference
  between *faithful* and *entitled*."

## 3 · The guardrail policing a tool (20 sec)
Run **"⛔ Live price right now to place a trade"** → **ROUTED.**
- **Say:** "It won't pass a delayed price off as a live execution price — the control
  plane polices the *tool's* output, not just the model."

## 4 · The escalation example (20 sec)
Run **"⚠️ Escalation example — Should I buy this for my client?"** → **ROUTED to a human
compliance reviewer.**
- **Say:** "An advisor can't get a buy/sell recommendation out of it — Reg BI
  suitability is a human's call."

## 5 · Live data — real-time quote + real SEC filings (30 sec)
**Third dropdown → pick MSFT → Run** (wait for the spinner). Feel free to vary the
ticker live (AAPL, NVDA, JPM…) — Finnhub's free tier is 60 calls/min, so no throttling.
- **Show:** the **real-time quote** (labeled *"Real-time market quote via Finnhub —
  informational, not an execution price"*) + **Recent SEC filings (EDGAR)** with live
  sec.gov links + **cited highlights** from the latest filing.
- **Say:** "Live price *and* live filings — MSFT is just an example; the tool is
  ticker-agnostic across the top 50. Still labeled informational, and a trade-now ask
  still routes — real-time doesn't mean execution-grade."

## 6 · Show my work — the glass box (30 sec) — *for the technical reviewer*
Click the spinning **⚙** → the **orchestration graph** recolored by the real run · the
**two parallel analyst agents** (filings-analyst ‖ market-context) fanning out · the
**gate stages** (with the live cross-family judge tier) · the **entitlement decision** ·
the **verifiable audit chain**.
- **Say:** "Nothing here is a slide — it's a read-out of the actual run. Two analyst
  agents run *concurrently* and propose; the gate adjudicates their findings; the one
  synthesizer is reachable *only* on the gate's pass edge. Parallel agents propose, the
  single writer disposes."
- **If a Live run withholds a clean-looking query, pre-empt it:** "That's the gate doing
  its job, not a glitch — on the live path the relevance floor genuinely withheld a
  weak answer and routed it for review. It fails *closed*. The scripted shots run on
  Demo so the narrative stays tight; Live is here to prove the gate really gates."

## 7 · The closer (15 sec)
End on **`Docs/one_pager.md`** — the plain-language page with no jargon:
> *"Useful for the advisor. Defensible for compliance."*

---

## ⚠️ Two things to know live
- **Live data is on (Finnhub + EDGAR).** Quotes are **real-time** (Finnhub, 60/min — no
  throttling); SEC filings pull live from EDGAR. If the network ever hiccups, the quote
  **fails soft** to a clearly-labeled fixture rather than erroring. Run it with:
  `USE_REAL_MARKET_DATA=true MARKET_DATA_PROVIDER=finnhub MARKET_DATA_API_KEY=<token>`.
  *(Alpha Vantage is the alternative provider — free but delayed/EOD and rate-limited.)*
- **Keep the engine on Demo** for the scripted money shots; the Live-graph engine runs
  the real pipeline (great for the glass box, but the canned scenarios are the polished
  narrative).

## The eight rubric items, one line each (if asked)
1. **Orchestration** — LangGraph supervisor → retriever + market-data → **two parallel
   analyst agents** (real fan-out) → aggregate → gate → synthesizer (pass-edge only).
2. **LLM eval** — control-plane gate (floor → support → rubric), with a **live
   cross-family judge** (OpenAI judging Claude) at stage-2 support + the golden harness
   scoreboard.
3. **Embeddings** — OpenAI `text-embedding-3-small` (keyless Nomic/keyword fallback).
4. **Vector DB** — ChromaDB behind a thin retriever interface.
5. **Memory** — session + working only; cross-session **OFF** by design.
6. **Guardrails** — regex + Presidio NER PII · injection deliver-with-exclusion ·
   prohibited/entitlement enforcement.
7. **UI** — two surfaces (advisor briefing + Show my work), governance visible.
8. **Deployment** — `python run.py`, offline-capable.
