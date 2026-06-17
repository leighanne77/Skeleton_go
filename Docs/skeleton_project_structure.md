# Skeleton project structure — the on-disk shape of the spec-driven build

*Reference for the VS Code workspace. Goal: a layout you can open on screen and explain in one breath — code in one place, the Policies pillar as a clean data folder, the spec-driven set at the root where Claude Code reads it, reference prose out of the code root. This tree is the on-disk form of `design.md §9` (the canonical build order).*

## Status — what's already settled
The three early fixes are done: `policies/` exists (`_base.yaml` + five vertical packs), `load_pack.py` sits at the root and reads `./policies/`, and `.env.example` is committed beside the gitignored `.env`. What's new since: the **spec-driven set** (`CLAUDE.md`, `requirements.md`, `design.md`, `tasks.md`, `KNOWN_ISSUES.md`) lives at the root so Claude Code **auto-loads `CLAUDE.md`** and reads the rest by name, and a **`.claude/settings.json`** denies the build agent read access to `.env` and other secrets.

## Recommended layout

```
governed-agent-skeleton/
├─ .claude/
│  └─ settings.json           # permission rules: DENY read on .env / *.key / *.pem / secrets/; ask on rm, git push
├─ .env                       # real config + keys (GITIGNORED — the agent is denied read access)
├─ .env.example               # committed template: same keys, no secrets (the config CONTRACT)
├─ .gitignore                 # .env, data/chroma/, __pycache__, *.pyc
│
├─ CLAUDE.md                  # auto-loaded constitution: principles, invariants, forbidden lists, rubric map
├─ requirements.md            # EARS user stories R1–R13 (8 rubric items + governance R9–R12 + R13 energy)
├─ design.md                  # the HOW — topology, models, build order §9 (SOURCE OF TRUTH for this tree)
├─ tasks.md                   # ordered, individually-testable build steps T0–T11
├─ KNOWN_ISSUES.md            # preventable bugs, by task (read alongside CLAUDE.md)
│
├─ README.md                  # how to run + the 8-scored-item map
├─ requirements.txt           # pinned deps (offline-first, clean provenance per §1)
├─ requirements-dev.txt       # ruff, mypy, pytest
├─ run.py                     # entrypoint: builds the graph, launches the UI
│
├─ app/                       # the governed-agent skeleton (the spine)
│  ├─ __init__.py             # marks app/ as a package (imports resolve)
│  ├─ config.py               # pydantic-settings: reads .env once (provider, model, backend, dims) + stub path
│  ├─ models.py               # Pydantic v2 models + StrEnums (Citation, Claim, AnswerEnvelope, AuditRecord, …)
│  ├─ policy.py               # thin wrapper over load_pack() — the ONE seam to the Policies pillar
│  ├─ orchestrator.py         # plans + routes (the supervisor)
│  ├─ agents/                 # the SWAPPABLE worker layer
│  │  ├─ retriever.py         #   retrieval-as-a-TOOL (not the spine)
│  │  ├─ specialist_a.py
│  │  ├─ specialist_b.py
│  │  └─ synthesizer.py       #   writes the answer in ONE place, ONLY on the gate's pass edge
│  ├─ guardrails.py           # deterministic hard rules (PII via Presidio, schema, permitted-use)
│  ├─ eval/                   # the control plane's points engine
│  │  ├─ gate.py              #   CONTROL-PLANE GATE: deterministic floor → stage-2 support → rubric judge
│  │  ├─ judge.py             #   cross-family LLM-judge (+ NLI hook for prod)
│  │  └─ harness.py           #   loads golden_<vertical>.jsonl, runs the eval, prints the report
│  ├─ memory.py               # 3 tiers: session · working (= audit record) · cross-session OFF
│  └─ audit.py                # hash-chained JSONL writer + verify_chain() (the tamper demo)
│
├─ policies/                  # ← THE POLICIES PILLAR (data, one file per regime)
│  ├─ _base.yaml              #   common PII + injection + citation + audit + withhold baseline
│  ├─ financial_services_us.yaml  # ← THE DEMO VERTICAL (BFSI — v2.1, validator-CLEAN)
│  ├─ energy_utilities_us.yaml    #   the reusability proof (v2.1, also validator-CLEAN)
│  ├─ insurance_us.yaml
│  ├─ life_sciences_us.yaml
│  └─ manufacturing_iot_us.yaml
│
├─ load_pack.py               # deep-merge _base + chosen overlay → one dict (POLICIES_DIR = ./policies)
│
├─ data/
│  ├─ corpus/                 #   pinned source docs, one folder per vertical (each with manifest.jsonl)
│  │  ├─ financial_services/  #     ← demo corpus: Reg BI/FINRA/BSA + MNPI/SAR/NPI + manifest.jsonl (12 docs)
│  │  └─ energy/              #     reusability-proof corpus: NERC CIP + CEII/BCSI/OT + manifest.jsonl (13 docs)
│  └─ chroma/                 #   persisted Chroma (gitignored; ANONYMIZED_TELEMETRY=False)
│
├─ golden/                    # ← per-vertical eval sets + the reusable validator (the T0.5 gate)
│  ├─ validate_golden.py      #   `python -m golden.validate_golden <vertical>` → CLEAN gate (ONE script, all verticals)
│  ├─ __init__.py
│  ├─ golden_financial_services.jsonl   #   demo (14 rows) — CLEAN
│  ├─ golden_energy.jsonl               #   reusability proof (13 rows) — CLEAN
│  └─ retired/                #   pre-corpus golden snapshots (history)
│
├─ ui/
│  └─ app.py                  #   Streamlit — built FIRST; identity banner + DELIVERED / ROUTED-FOR-REVIEW
│
├─ tests/                     #   negative tests · chain-break · retrieval-determinism · BOTH-principals
│
└─ docs/                      #   reference prose, NOT code
   ├─ policies_README.md
   ├─ spec_remember_*.md      #   per-vertical "things to remember" notes
   ├─ ui_build_prompt.md
   ├─ perficient_cheat_sheet_plus_faq_v3.html
   └─ (build checklist · full plan)
```

## Why this shape (the one-breath explanation)

- **The spec-driven set sits at the root on purpose.** Claude Code auto-loads `CLAUDE.md`; `design.md`/`tasks.md`/`requirements.md`/`KNOWN_ISSUES.md` are read by name. Rule config + context management + validation coverage are what govern output quality — putting them where the agent reads them is the point, not decoration.
- **`app/` is the skeleton, and it maps 1:1 to the eight scored items** — orchestration (`orchestrator` + `agents/`), eval (`eval/`), embeddings/vector DB (`retriever.py` + `config.py`), memory (`memory.py`), guardrails (`guardrails.py`), audit (`audit.py`), UI (`ui/`), deployment (`.env` + `run.py`). A folder per rubric line.
- **`policies/` is a separate data folder on purpose.** It's the *Policies* pillar of PACE — rules as data, swapped by the `POLICY_PACK` switch, with the same *Controls* (`guardrails.py`, `eval/`, `audit.py`) underneath. The folder boundary *is* the data-plane / control-plane split made visible on disk.
- **The control-plane gate is `app/eval/gate.py`, not an agent.** The workers in `agents/` (retriever, two specialists, synthesizer) are swappable; the gate is the independent control node the synthesizer is reachable through only on the pass edge. (There is no `verifier.py` — that was the old name for this.)
- **`golden/` and `data/` are pinned snapshots** — reproducibility is a scored expectation; versioned corpus + eval set (not generated live) is the defensible posture.
- **`docs/` keeps prose out of the code root** so the thing you screen-share reads as an engineered system, not a folder of mixed notes.

## `.env` & secrets — the VS Code setup

You'll run this in VS Code with a real `.env`, so make the config flow explicit *and* governed:

- **`.env` (gitignored, real keys)** — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (embeddings), `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` (optional tracing), plus non-secret switches: `LLM_PROVIDER`/`LLM_MODEL`, `EMBED_MODEL`/`EMBED_DIM`, `VECTOR_BACKEND` (`chroma`|`pgvector`)/`PG_TABLE`, the `USE_REAL_LLM` / `USE_REAL_EMBED` stub-vs-real toggles, and `MAX_LLM_CALLS_PER_RUN` / `…_PER_SESSION` / `MAX_LLM_TOKENS_PER_RUN` / `MAX_EMBED_CALLS_PER_RUN` cost caps. This is what makes the live demo run on cloud inference; `USE_REAL_*=false` flips to the keyless stub path.
- **`.env.example` (committed)** — the same keys with empty/placeholder values. It's the *contract*: an architect sees exactly what the system needs without seeing a secret.
- **`app/config.py` (pydantic-settings) reads `.env` once** and hands typed config to the rest of the app — nothing else touches env directly. Keys absent → the stub path runs. That's the "zero-keys-to-run, real when keyed" line you can say out loud.
- **`.claude/settings.json` denies the agent reading `.env`** (and `*.key` / `*.pem` / `secrets/`). On camera this is a small, real governance signal: the build agent itself can't read your keys — it mirrors the entitlement story the product sells.
- **`.gitignore` excludes `.env`** and `data/chroma/`.

**One honest caution to say out loud if asked:** with a live `.env`, the demo uses cloud inference (Claude + OpenAI embeddings), so it isn't *literally* offline during the recording. The *architecture* stays offline-capable — flip to the stub/local path (local Llama, Nomic embeddings, no keys) with no code change. That's the portability claim; don't overclaim "offline" while the keys are live.

## Loader seam (unchanged, still true)
- `load_pack.py` stays importable from `app/policy.py` (`from load_pack import load_pack`) so nothing else in the skeleton reads YAML directly — one seam for policies.
- `POLICIES_DIR = Path(__file__).parent / "policies"` resolves correctly with `load_pack.py` at the root and `policies/` beside it.

---

## Version history
v3 — 2026-06-17 · changed: **refocused the tree onto the BFSI demo** — `financial_services_us.yaml` is now the demo vertical (energy = the reusability proof); expanded `data/corpus/` to the per-vertical layout (`financial_services/` + `energy/`, each with `manifest.jsonl`); replaced the single `golden.jsonl` with the real `golden/` contents — `validate_golden.py` (the reusable T0.5 CLEAN gate), `__init__.py`, `golden_financial_services.jsonl`, `golden_energy.jsonl`, `retired/`; fixed pack count (five vertical packs) and the harness golden filename.
v2 — 2026-06-16 · changed: aligned the tree to `design.md §9` and current reality — added the spec-driven set at the root (`CLAUDE.md` / `requirements.md` / `design.md` / `tasks.md` / `KNOWN_ISSUES.md`), `.claude/settings.json` (secrets-deny), `app/models.py`, and `requirements-dev.txt`; removed the retired `agents/verifier.py` (the control-plane gate is `app/eval/gate.py`) and the retired `docs/prototype_spec_TEMPLATE.md`; replaced the stale "fix these three things first" screenshot section with a settled-status note; **expanded the `.env`/secrets section for the VS Code setup** (pydantic-settings config flow, `.claude` secrets-deny, and the offline-capable-vs-live-keys caution). Filename kept (referenced by `design.md §9`); version in this footer.
v1 — 2026-06-16 · created: target skeleton layout with the Policies pillar as a clean data folder.
