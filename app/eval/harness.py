"""app/eval/harness.py — run the golden set through the full pipeline (T10).

Runs each GoldenRecord's `input` through the REAL graph (app.orchestrator.run) under
its `principal_entitlements`, and compares the actual verdict to the gold
`expected_verdict`. Reports pass@1 overall and per CaseBucket, and lists mismatches
for calibration. This is the eval-against-goal scoreboard: the golden set authored at
T0.5, graded against what the gate actually does.

    python -m app.eval.harness financial_services

Note: validate_golden (T0.5) checks the answer key as DATA; this RUNS it through the
pipeline (T10). Differences are expected where the skeleton is intentionally partial
(e.g., advice/SAR signatures depend on the intent-classifier tier, not yet built) —
those are the calibration targets, surfaced as mismatches here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from app.models import GoldenRecord
from app.orchestrator import run

VERTICAL_PACK = {
    "financial_services": "financial_services_us",
    "energy": "energy_utilities_us",
}
_BUCKET = {
    "rejects_unsupported_span": "UNSUPPORTED_CLAIM",
    "rejects_out_of_scope": "OUT_OF_SCOPE",
    "rejects_prompt_injection": "PROMPT_INJECTION",
    "rejects_pii_leak": "PII_LEAK",
    "rejects_empty_retrieval": "EMPTY_RETRIEVAL",
    "rejects_conflicting_sources": "CONFLICTING_SOURCES",
    "happy_path": "HAPPY_PATH",
}


def _bucket(case_type: str) -> str:
    if case_type in _BUCKET:
        return _BUCKET[case_type]
    return "VERTICAL_NEGATIVE" if case_type.startswith("rejects_") else "HAPPY_PATH"


def run_golden(vertical: str, golden_file: str | None = None) -> dict[str, object]:
    pack = VERTICAL_PACK.get(vertical, f"{vertical}_us")
    path = Path(golden_file or f"golden/golden_{vertical}.jsonl")
    rows = [
        GoldenRecord(**json.loads(ln))
        for ln in path.read_text().splitlines()
        if ln.strip()
    ]

    per_bucket: dict[str, list[bool]] = {}
    mismatches: list[tuple[str, str, str, str]] = []
    for r in rows:
        env, _trace = run(r.input, r.principal_entitlements or [], policy_pack=pack)
        ok = env.status == r.expected_verdict
        per_bucket.setdefault(_bucket(r.case_type), []).append(ok)
        if not ok:
            mismatches.append(
                (r.id, r.case_type, r.expected_verdict.value, env.status.value)
            )

    passed = sum(1 for b in per_bucket.values() for x in b if x)
    total = len(rows)
    return {
        "vertical": vertical,
        "total": total,
        "passed": passed,
        "pass_at_1": round(passed / total, 3) if total else 0.0,
        "per_bucket": {k: (sum(v), len(v)) for k, v in sorted(per_bucket.items())},
        "mismatches": mismatches,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vertical")
    ap.add_argument("--golden", default=None)
    a = ap.parse_args()
    rep = run_golden(a.vertical, a.golden)

    per_bucket = cast("dict[str, tuple[int, int]]", rep["per_bucket"])
    mismatches = cast("list[tuple[str, str, str, str]]", rep["mismatches"])
    print(f"\n=== golden harness: {rep['vertical']} ({rep['total']} rows) ===\n")
    print(f"  pass@1: {rep['passed']}/{rep['total']}  ({rep['pass_at_1']})\n")
    print("  per CaseBucket (passed/total):")
    for bucket, (p, t) in per_bucket.items():
        print(f"    {bucket:20} {p}/{t}")
    if mismatches:
        print("\n  mismatches (id · case_type · gold → actual):")
        for mid, ct, gold, actual in mismatches:
            print(f"    {mid:28} {ct:28} {gold} → {actual}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
