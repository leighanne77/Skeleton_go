# _FIXES_APPLIED.md — corrections to the Skeleton Pre-Build workspace
*2026-06-16 · applied to the uploaded `Skeleton_Pre-Build.zip` snapshot.*

## Blocking (fixed)
1. **Adopted the enriched v2 policy packs.** `_base`, `energy_utilities_us`, `insurance_us`, `life_sciences_us`, `manufacturing_iot_us` were v1 (no `entitlements`/`golden_negatives`/`thresholds`/`enforced_by`). Replaced with the v2 schema; `financial_services_us` was already v2. Verified via `load_pack.py`: energy now loads `entitlements=True`, `golden_negatives=9`, `thresholds=True`, `sensitive_classes=3`. `test_policy_pack_load` will pass.
2. **Added `.gitignore`** (excludes `.env`, `.DS_Store`, `data/chroma/`, `__pycache__/`, caches). The real `.env` was sitting next to no gitignore.
3. **Renamed `Policies/` → `policies/`** to match `load_pack.py` (`POLICIES_DIR = ./policies`). Worked on macOS (case-insensitive) but would `FileNotFoundError` on Linux/CI.

## Governance scaffolding (added)
4. **`.env.example`** — committed contract mirroring the real key set (`LLM_PROVIDER`/`LLM_MODEL`/`USE_REAL_LLM`, `EMBED_MODEL`/`EMBED_DIM`/`USE_REAL_EMBED`, `VECTOR_BACKEND`/`PG_TABLE`, `LANGFUSE_*`, `MAX_*` caps), no secret values.
5. **`.claude/settings.json`** — deny-read on `.env`/`*.key`/`*.pem`/`secrets/`; ask on `rm`/`git push`/`git reset`; allow the build/test commands. The on-camera "the agent can't read my keys" signal.

## Spec set (synced to session-latest for coherence)
6. **`KNOWN_ISSUES.md`** → v3: removed the retired "adopt the v2 packs before any run" Top-guard row (now adopted), renumbered to 9.
7. **`tasks.md`** → session-latest: T2/T4/T7 acceptance strengthened (entitlements+golden_negatives assertion, telemetry-off + `(score,chunk_id)` determinism, both-principals test); stale adopt-warning removed.
8. **`CLAUDE.md`** + **`design.md`** → added the `KNOWN_ISSUES.md` pointer (doc-set list + validation step / companions line) so Claude Code actually loads it.

## Housekeeping
9. Moved `policies_README.md` → `Docs/`; moved the stale `perficient_walk_in_cheat_sheet_v2.html` → `Docs/Other/` (superseded by `cheat_sheet_plus_faq_v3`).
10. De-duplicated `spec_remember_*.md` — kept the newer root copies (with v2 bindings), consolidated into `Draft specs/`, removed the older duplicates.
11. Build checklist `v10` → `v11` (stable `T`-task cross-refs) in `Docs/Other/`.
12. Removed `.DS_Store` clutter. Placed the updated `skeleton_project_structure.md` (real `.env` keys) in `Docs/`.

## Deliberately NOT changed
- **Your real `.env` is not in this folder** — kept out on purpose so your secret isn't sitting in a generated zip. Copy your local `.env` back in (it's gitignored).
- **`requirements.md`** left as your snapshot (differs slightly from the outputs lineage; no targeted fix needed). Flag if you want it synced too.
- No `app/`, `ui/`, `tests/`, `data/`, `golden/` — those are the in-room build, not pre-build.

## Update — requirements.txt (2026-06-16, later)
- Replaced the zip's older `requirements.txt` with the newer uploaded version, then **capped the fast-movers to current majors**: `langgraph>=1,<2`, `chromadb>=1,<2`, `langfuse>=4,<5` (each shipped a breaking major since the old `>=0.x` floors; Langfuse v4 is an OpenTelemetry rewrite). `langchain-core` left to resolve transitively under langgraph. Header corrected to "five verticals"; `USE_REAL_EMBED` comments aligned to `true/false`; added "pre-bake the venv / don't pip torch on camera" + "keep Langfuse behind a flag" notes. Freeze a lockfile once green (T11).

## Update — T0.5 golden data + corpus seed (2026-06-16, later)
- Added **T0.5** (golden data, before the UI) to `tasks.md` + `design §9` (step 1.5) + a "golden set first" principle to `CLAUDE.md`; renamed T10 to "run + report"; T4 fills positive citations. No T1–T11 renumber.
- Generated the seed: `data/corpus/energy/D8_substation_ceii.md` (CEII trap doc — contains every `ceii`/`ot_asset` detector keyword), companions D1/D2/D3 (CIP evidence w/ PII + 3yr retention; FERC summary w/ 7yr retention → conflict; ops bulletin w/ planted injection), and `golden/golden_energy.jsonl` (9 negatives + 2 positive stubs; validated GoldenRecord-shaped; signature `rejects_unentitled_ceii` present). All corpus docs are SYNTHETIC/fictional.

## Update — principal_entitlements on GoldenRecord (2026-06-16, later)
- Added optional `principal_entitlements: list[str] = []` to `GoldenRecord` (design §4) — `[]` = baseline/unentitled. Lets one `input` be scored under different principals, so the entitlement signature case is expressible from the golden set (not only a pytest). Noted in §12 + T0.5; the T10 harness builds each `Principal` from this field.
- `golden_energy.jsonl` now 12 rows: field present on every row; added `pos_entitled_ceii` (the entitled pair of `neg_unentitled_ceii`) — same input, `["ceii_cleared","ot_cleared"]` → delivered+cited (positive stub).
