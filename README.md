# Governed Advisor Stock-Briefing (BFSI)

A **governed decision agent over regulated documents**: it helps a wealth-management
advisor get up to speed on a stock — a clearly time-stamped **quote** plus the key
points from the issuer's recent **SEC filings** — where **every answer is gated
before it can reach the user**. The build is evidence for one claim: *defensible
agentic systems in regulated industries* = **guardrails + eval-against-goal +
tamper-evident audit**.

The skeleton is **vertical-free**; a vertical is loaded at runtime via a `policy_pack`.
The worked demo is **financial services (BFSI, US)**, and the same skeleton is proven
on a second vertical (energy & utilities) — two `validate_golden`-CLEAN verticals on
one codebase is the reusable-framework evidence.

---

## What makes it different

Most "ask the docs" demos hide the governance. Here the **control plane is the
product**:

- **Two never-blurred states.** Every answer is either **DELIVERED** (with resolvable
  citations) or **ROUTED FOR HUMAN REVIEW** — never a confident guess.
- **The synthesizer is reachable only on the gate's pass edge.** A failed/uncertain
  answer is *structurally* unable to reach the user (enforced by a LangGraph
  conditional edge; see `test_synthesizer_unreachable_on_fail`).
- **Entitlement-scoped retrieval.** A document tagged `[mnpi]` is invisible to an
  advisor who lacks `mnpi_cleared`. Flip the clearance and the *same* query goes from
  ROUTED to DELIVERED.
- **Policy is data.** Rules live in `policies/*.yaml` and are read at runtime — never
  hardcoded in the engine. Swap the pack to change verticals.
- **Offline-first, zero-keys-to-run.** The whole thing runs keyless with deterministic
  stubs; real keys *enable* real models/data but are never required.

---

## The governed flow

```
ticker / question
        │
        ▼
 ORCHESTRATOR ───────────┬──────────────────────────┐
        │                ▼                           ▼
        │        RETRIEVER (tool)            MARKET-DATA (tool)
        │   embeddings + Chroma,            delayed/real-time quote,
        │   entitlement-filtered            never execution-grade
        │                │                           │
        └────────► CONTROL-PLANE GATE ◄──────────────┘
                    deterministic floor → support → rubric
                         │ pass                    │ fail / uncertain
                         ▼                          ▼
                   ONE SYNTHESIZER           WITHHELD → ROUTED
                   (writes the answer)       (human:compliance-officer)
                         │                          │
                         └──────► APPEND-ONLY, HASH-CHAINED AUDIT ◄──┘
```

Retrieval is a **tool, not the spine**; the quote is non-citable context; the filing
summary carries the resolvable citations the gate checks.

---

## Quick start

```bash
# Python 3.11+ required (uses enum.StrEnum). Create a venv:
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Run the UI (Streamlit) — works keyless with stubs:
python run.py                 # → streamlit run ui/streamlit_app.py
# open http://localhost:8501
```

In the app: **Enter the Stock Briefing** → run a quick task or pick a top-50 ticker.
Use the **⚙ gear** (bottom-right) to open **"Show my work"** — the orchestration graph
recolored by the real run, the gate stages, the entitlement decision, and the audit
chain. The reviewer entitlement toggle lives there (flip `mnpi_cleared` and re-run).

### Two surfaces, one run
- **Advisor briefing** (default) — plain-language; the two verdict states; the quote
  card; first-class citations.
- **Show my work** — the operator glass box, plus an **engine toggle**: *Demo*
  (scripted scenarios incl. the guardrail money-shots) vs *Live graph* (the real
  `app.orchestrator` LangGraph run).

---

## Configuration (all optional — keyless by default)

Config is read once from `.env` via `app/config.py` (pydantic-settings). The build
agent is denied read access to `.env`; `.env.example` is the committed contract.

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` + `USE_REAL_EMBED=true` | Real retrieval — **OpenAI `text-embedding-3-small`** + Chroma (else deterministic keyword fallback) |
| `MARKET_DATA_API_KEY` + `USE_REAL_MARKET_DATA=true` | Live quotes (else offline fixture) |
| `MARKET_DATA_PROVIDER` | `finnhub` (free **real-time** US quotes) or `alpha_vantage` (free **delayed EOD**; intraday is premium) |
| `USE_REAL_MARKET_DATA=true` (no key) | also enables the **SEC EDGAR** filings pull (free, US-gov) for live tickers |
| `USE_PRESIDIO_NER=true` | name/address PII redaction via **Presidio + spaCy** (`python -m spacy download en_core_web_sm`); regex PII always on |
| `ANTHROPIC_API_KEY` + `USE_REAL_LLM=true` | Real reasoning LLM (Claude); cross-family judge on OpenAI |

> **Live prices:** free key at finnhub.io → `MARKET_DATA_PROVIDER=finnhub`,
> `MARKET_DATA_API_KEY=<token>`, `USE_REAL_MARKET_DATA=true`, restart. Quotes are always
> labeled and **never execution-grade** — a trade-now / execution ask routes to a human.

---

## Layout

```
app/
  models.py        Pydantic v2 schemas + StrEnums (one source of truth)
  config.py        typed config from .env (keyless-by-default)
  policy.py        the ONE seam over load_pack (policy = data)
  orchestrator.py  the LangGraph supervisor graph (rubric item 1)
  guardrails.py    guard-first: regex + Presidio NER PII · injection · prohibited/entitlement
  memory.py        deliberate memory policy (session/working on; cross-session OFF)
  audit.py         append-only, hash-chained, verifiable audit log
  agents/
    retriever.py   retrieval-as-a-tool: OpenAI embeddings + Chroma / keyword fallback
    embeddings.py  the embedding-model seam (text-embedding-3-small)
    synthesizer.py specialist (top-K cited spans) + synthesizer (finalize, pass-edge only)
  eval/
    gate.py        the control-plane gate (floor → stage-2 support → rubric, fail-closed)
    judge.py       support/relevance/conflict (deterministic; LLM/NLI tier behind the calls)
    harness.py     runs the golden answer key through the pipeline → pass@1 + mismatches
  tools/
    market_data.py quote tool — fixture / Alpha Vantage / Finnhub, ticker-agnostic
    edgar.py       SEC EDGAR — recent filings list + extractive cited summary
ui/
  streamlit_app.py the two-surface UI (advisor briefing + Show my work)
  theme.py         Munich-Re-inspired design system (offline system fonts)
  stub_backend.py  canned, real-shaped scenarios for the demo
policies/          _base.yaml + per-vertical packs (financial_services_us, energy_…)
data/corpus/       synthetic corpus per vertical (+ manifest.jsonl)
data/market/       offline quote fixture
golden/            golden eval set + validate_golden.py (the "define correct" gate)
tests/             pytest suite (hermetic — forces keyword/offline paths)
Docs/one_pager.md  the plain-language, non-technical customer page
```

---

## Validate & test

```bash
# Golden-set gate — must print CLEAN (0 fail, 0 warn) for both verticals:
python -m golden.validate_golden financial_services
python -m golden.validate_golden energy

# Test suite (hermetic — no network/API calls):
pytest -q                       # 49 passing, 1 skipped (opt-in semantic)
RUN_EMBED_TESTS=1 pytest tests/test_retriever.py   # exercises the real OpenAI+Chroma path

# Eval scoreboard — run the golden answer key through the real pipeline:
python -m app.eval.harness financial_services      # pass@1 + per-bucket + mismatches

# Lint + types (must pass):
ruff check app/ ui/ tests/
mypy --strict app/
```

---

## Build status

**Complete (T0–T11).** models/config · dual-surface UI · policy loader · governed
LangGraph graph (pass-edge invariant) · retriever (OpenAI embeddings + Chroma, keyword
fallback) · market-data tool (fixture + Alpha Vantage + Finnhub) · SEC-EDGAR filings
pull + extractive cited summary · **guardrails** (regex + **Presidio NER** PII +
injection deliver-with-exclusion + prohibited/entitlement enforcement, guard-first) ·
**full gate cascade** (floor → support → rubric) · entitlement signature · memory
policy (cross-session OFF) · **hash-chained audit** · golden harness + calibration ·
final validation + the plain-language one-pager (`Docs/one_pager.md`).

**The three-pillar moat is real:** guardrails ✓ · eval-against-goal ✓ · tamper-evident audit ✓.

**Production tiers (documented seams, swap-in behind the same calls):** the
cross-family LLM / NLI judge for stage-2 support + strict rubric; an intent classifier
for the tipping-off-vs-Q&A and out-of-scope distinctions; Presidio NER for name/address
PII. The deterministic defaults keep the suite hermetic and the demo keyless.

**Quality:** ruff + `mypy --strict` clean; **49 tests** (1 opt-in skipped); both
verticals `validate_golden`-CLEAN; golden harness **pass@1 0.75** (all positives
deliver; vertical signatures pass).

---

## Documents

- `CLAUDE.md` — the project constitution (constraints + invariants)
- `requirements.md` — intent + acceptance criteria (EARS)
- `design.md` — architecture (the BFSI overlay is §12 / §12a / §12c)
- `tasks.md` — ordered build steps
- `Docs/stock_briefing_prototype_spec_v2.md` — the scenario brief (problem → solution → demo → roadmap)

---

*Offline-capable by design. With live keys the demo uses cloud inference (Claude +
OpenAI embeddings + a market-data provider); flip the `USE_REAL_*` toggles off to run
the keyless local path with no code change.*
