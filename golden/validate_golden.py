"""golden/validate_golden.py — reusable golden-set + corpus validator (T0.5 gate).

Run:  python -m golden.validate_golden <vertical> [--corpus DIR] [--golden FILE] [--pack-dir DIR]

Checks three things, ALL at the data level (no pipeline run — that's T10; runtime
detector firing is T5/T7). This is the T0.5 half of the demo-killer risk: if a
detector's trigger string is not literally present where it must be, the detector
silently misses on camera.

  GROUP A — structural: every row parses into GoldenRecord; DELIVERED rows carry an
            answer + >=1 citation, ROUTED rows carry neither; the 6 universal
            negatives + every vertical signature are present; prints CaseBucket spread.
  GROUP B — span resolution: every DELIVERED citation .span is an exact substring of
            the cited corpus doc (resolved via manifest.jsonl).
  GROUP C — data-level detector alignment (pack-data x corpus/golden):
            C1  PII regex      -> the corpus literally contains regex-matchable PII.
            C2  sensitive kw    -> each manifest-tagged sensitive doc is matched by its
                                   class keyword list (MISS = blind to its own target);
                                   non-tagged docs that match are flagged (over-fire).
            C3  prohibited kw   -> each prohibited rule's golden case INPUT contains one
                                   of the rule's signal keywords (query-side signals).

Exit code is non-zero if any FAIL fires. WARN does not fail the gate.
Imports app.models.GoldenRecord if present (build-time); else uses an inline mirror
of design.md §4 so the gate is runnable pre-T0.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

import yaml

# ── GoldenRecord: real model if scaffolded, else an inline §4 mirror ───────────
try:  # build-time: use the real model so this gate tests the real schema
    from app.models import GoldenRecord  # type: ignore
    _USING_REAL_MODEL = True
except Exception:  # pre-T0: inline mirror (fields per the live golden_*.jsonl + §4)
    from pydantic import BaseModel, Field
    _USING_REAL_MODEL = False

    class _CitationLite(BaseModel):
        source_id: str
        span: str = ""
        chunk_id: str | None = None
        doc_title: str | None = None

    class GoldenRecord(BaseModel):  # type: ignore[no-redef]
        id: str
        input: str
        principal_entitlements: list[str] = Field(default_factory=list)
        gold_answer: str | None = None
        gold_citations: list[_CitationLite] = Field(default_factory=list)
        expected_verdict: str            # "delivered" | "routed_for_review"
        case_type: str                   # open vocab: pack golden_negatives id | "happy_path"
        category: str | None = None
        notes: str | None = None

# ── canonical PII regexes: a *proxy* for Presidio's recognizers, for the data
#    -level check only. Reconcile against the real Presidio set at T5. ──────────
PII_REGEX = {
    "ssn":            r"\b\d{3}-\d{2}-\d{4}\b",
    "email":          r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
    "phone_us":       r"(?:\(\d{3}\)\s*|\b\d{3}[-.\s])\d{3}[-.\s]?\d{4}\b",
    "ip_address":     r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "dob":            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    "credit_card":    r"\b(?:\d[ -]?){13,16}\b",
    "account_number": r"\baccount[:#]?\s*\d{6,}\b",  # anchored to reduce noise
}
_NER_ONLY = {"street_address", "person_name"}  # detect: ner -> not data-checkable here

VERTICAL_ALIAS = {  # short name -> (pack stem, golden suffix)
    "energy": ("energy_utilities_us", "energy"),
    "insurance": ("insurance_us", "insurance"),
    "life_sciences": ("life_sciences_us", "life_sciences"),
    "manufacturing": ("manufacturing_iot_us", "manufacturing"),
    "financial_services": ("financial_services_us", "financial_services"),
}
UNIVERSAL_NEGATIVES = {
    "rejects_unsupported_span", "rejects_out_of_scope", "rejects_prompt_injection",
    "rejects_pii_leak", "rejects_empty_retrieval", "rejects_conflicting_sources",
}
ROUTED = "routed_for_review"
DELIVERED = "delivered"


# ── tiny result accumulator ───────────────────────────────────────────────────
class Report:
    def __init__(self) -> None:
        self.fail: list[str] = []
        self.warn: list[str] = []
        self.info: list[str] = []
        self.ok: list[str] = []

    def F(self, m: str) -> None: self.fail.append(m)
    def W(self, m: str) -> None: self.warn.append(m)
    def I(self, m: str) -> None: self.info.append(m)  # noqa: E743 (non-actionable note)
    def K(self, m: str) -> None: self.ok.append(m)


def _deep_merge_packs(base: dict, vert: dict) -> dict:
    """Minimal merge for the keys this validator reads (mirrors load_pack intent)."""
    m = dict(base)
    m["pii_classes"] = base.get("pii_classes", [])
    m["sensitive_classes"] = vert.get("sensitive_classes", [])
    m["prohibited"] = (base.get("prohibited", []) or []) + (vert.get("prohibited", []) or [])
    m["golden_negatives"] = (base.get("golden_negatives", []) or []) + (vert.get("golden_negatives", []) or [])
    return m


def _neg_id(g: dict) -> str:
    return g.get("case_type") or g.get("id") or ""


def load_inputs(vertical: str, pack_dir: Path, corpus_dir: Path, golden_file: Path):
    base = yaml.safe_load((pack_dir / "_base.yaml").read_text())
    stem, _ = VERTICAL_ALIAS.get(vertical, (vertical, vertical))
    vert = yaml.safe_load((pack_dir / f"{stem}.yaml").read_text())
    pack = _deep_merge_packs(base, vert)

    manifest = {}
    mpath = corpus_dir / "manifest.jsonl"
    for line in mpath.read_text().splitlines():
        if line.strip():
            e = json.loads(line)
            e["text"] = (corpus_dir / e["path"]).read_text()
            manifest[e["source_id"]] = e

    rows = [json.loads(l) for l in golden_file.read_text().splitlines() if l.strip()]
    return pack, manifest, rows


# ── GROUP A ───────────────────────────────────────────────────────────────────
def group_a(rows: list[dict], pack: dict, r: Report) -> None:
    parsed = []
    for raw in rows:
        try:
            parsed.append(GoldenRecord(**raw))
        except Exception as e:  # noqa: BLE001
            r.F(f"A/parse: row id={raw.get('id','?')} fails GoldenRecord: {e}")
    r.K(f"A/parse: {len(parsed)}/{len(rows)} rows parse "
        f"({'real app.models' if _USING_REAL_MODEL else 'inline §4 mirror'}).")

    for gr in parsed:
        is_delivered = gr.expected_verdict == DELIVERED
        has_cite = len(gr.gold_citations) > 0
        has_ans = bool(gr.gold_answer and gr.gold_answer.strip())
        if is_delivered and not (has_ans and has_cite):
            r.F(f"A/semantics: DELIVERED row '{gr.id}' must have gold_answer + >=1 citation "
                f"(answer={has_ans}, cites={len(gr.gold_citations)}).")
        if gr.expected_verdict == ROUTED and (has_ans or has_cite):
            r.F(f"A/semantics: ROUTED row '{gr.id}' must carry neither answer nor citations.")

    present = {gr.case_type for gr in parsed}
    missing_univ = UNIVERSAL_NEGATIVES - present
    if missing_univ:
        r.F(f"A/coverage: missing universal negatives: {sorted(missing_univ)}")
    else:
        r.K("A/coverage: all 6 universal negatives present.")

    sigs = {_neg_id(g) for g in pack["golden_negatives"]} - UNIVERSAL_NEGATIVES
    missing_sig = {s for s in sigs if s and s not in present}
    if missing_sig:
        r.F(f"A/coverage: missing vertical signature(s) from the pack: {sorted(missing_sig)}")
    else:
        r.K(f"A/coverage: all vertical signatures present ({sorted(sigs)}).")

    # verdict semantics (§5c step 5): pii_leak + prompt_injection DELIVER with the bad
    # thing excluded; every other negative ROUTES.
    deliver_with_exclusion = {"rejects_pii_leak", "rejects_prompt_injection"}
    for gr in parsed:
        if gr.case_type in deliver_with_exclusion and gr.expected_verdict != DELIVERED:
            r.F(f"A/verdict: '{gr.id}' ({gr.case_type}) must be DELIVERED with the bad thing "
                f"excluded (§5c step 5), got '{gr.expected_verdict}'.")
        elif (gr.case_type.startswith("rejects_") and gr.case_type not in deliver_with_exclusion
              and gr.expected_verdict != ROUTED):
            r.F(f"A/verdict: '{gr.id}' ({gr.case_type}) is a withhold negative — must be ROUTED, "
                f"got '{gr.expected_verdict}'.")

    # CaseBucket spread (17->8, computed here for reporting only)
    def bucket(ct: str) -> str:
        m = {"rejects_unsupported_span": "UNSUPPORTED_CLAIM", "rejects_out_of_scope": "OUT_OF_SCOPE",
             "rejects_prompt_injection": "PROMPT_INJECTION", "rejects_pii_leak": "PII_LEAK",
             "rejects_empty_retrieval": "EMPTY_RETRIEVAL", "rejects_conflicting_sources": "CONFLICTING_SOURCES",
             "happy_path": "HAPPY_PATH"}
        return m.get(ct, "VERTICAL_NEGATIVE" if ct.startswith("rejects_") else "HAPPY_PATH")
    spread: dict[str, int] = {}
    for gr in parsed:
        spread[bucket(gr.case_type)] = spread.get(bucket(gr.case_type), 0) + 1
    r.K("A/spread: " + ", ".join(f"{k}={v}" for k, v in sorted(spread.items())))


# ── GROUP B ───────────────────────────────────────────────────────────────────
def group_b(rows: list[dict], manifest: dict, r: Report) -> None:
    checked = 0
    for raw in rows:
        if raw.get("expected_verdict") != DELIVERED:
            continue
        for c in raw.get("gold_citations", []):
            sid, span = c.get("source_id"), (c.get("span") or "")
            checked += 1
            if sid not in manifest:
                r.F(f"B/span: row '{raw.get('id')}' cites unknown source_id '{sid}' "
                    f"(not in manifest — corpus/golden drift?).")
            elif span and span not in manifest[sid]["text"]:
                r.F(f"B/span: row '{raw.get('id')}' span not an exact substring of '{sid}': "
                    f"{span[:60]!r}")
    r.K(f"B/span: checked {checked} delivered-citation span(s).")


# ── GROUP C ───────────────────────────────────────────────────────────────────
def _matches(text: str, kw: str) -> bool:
    return kw.lower() in text.lower()


def group_c(pack: dict, manifest: dict, rows: list[dict], r: Report) -> None:
    # C1 — PII regex present in the corpus
    pii_classes = [c["name"] for c in pack.get("pii_classes", [])]
    regex_classes = [n for n in pii_classes if n in PII_REGEX]
    hits: dict[str, list[str]] = {}
    for sid, e in manifest.items():
        for n in regex_classes:
            if re.search(PII_REGEX[n], e["text"]):
                hits.setdefault(sid, []).append(n)
    if hits:
        r.K("C1/pii: regex-matchable PII present in: "
            + "; ".join(f"{s}[{','.join(v)}]" for s, v in hits.items()))
    else:
        r.F("C1/pii: NO corpus doc contains regex-matchable PII — the PII guard can never "
            "fire in the demo. Add a PII-bearing doc (e.g. a rate case with a regex-real SSN).")
    skipped = [n for n in pii_classes if n in _NER_ONLY]
    if skipped:
        r.I(f"C1/pii: NER-only classes not data-checkable here (runtime/Presidio): {skipped}")

    # C2 — sensitive-class keywords vs manifest tags
    classes = {c["name"]: c.get("detect", {}).get("keywords", []) for c in pack.get("sensitive_classes", [])}
    for sid, e in manifest.items():
        tags = set(e.get("entitlement_tags", []))
        text = e["text"]
        fired = {cls for cls, kws in classes.items() if any(_matches(text, k) for k in kws)}
        # MISS: a tagged class whose keywords do not match its own target doc
        for cls in tags & set(classes):
            if cls not in fired:
                r.F(f"C2/miss: '{sid}' is tagged [{cls}] but NO '{cls}' keyword matches its text "
                    f"— the secondary detector is blind to its own signature target.")
            else:
                matched = [k for k in classes[cls] if _matches(text, k)]
                strict = [k for k in classes[cls]
                          if re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", text, re.I)]
                if not strict:
                    r.W(f"C2/fragile: '{sid}' [{cls}] matches only as substring {matched} "
                        f"(0 whole-word) — confirm the engine matches substring/case-insensitive, "
                        f"or add an exact term from the doc.")
        # FALSE+: a non-tagged doc matched by some class. Under manifest-primary gating this is the
        # SECONDARY screen noticing a doc that mentions the class term — not a withhold (the doc is tagged
        # []), so it is INFO, not a failure. Worth seeing in case a keyword is needlessly broad.
        for cls in fired - tags:
            matched = [k for k in classes[cls] if _matches(text, k)]
            r.I(f"C2/secondary: non-tagged '{sid}' matches '{cls}' on {matched} — secondary screen only "
                f"(manifest-primary gating means it is never withheld on this basis). Narrow only if the "
                f"doc doesn't actually concern '{cls}'.")
    r.K(f"C2/sensitive: reconciled {len(classes)} class(es) across {len(manifest)} docs.")

    # C3 — prohibited-rule signal keywords vs the matching golden case INPUT
    by_case = {raw.get("case_type"): raw for raw in rows}
    for rule in pack.get("prohibited", []):
        sig = rule.get("signals") or {}
        kws = sig.get("keywords") or []
        enforced = rule.get("enforced_by", [])
        if not kws:
            continue  # pure-entitlement rules (e.g. no_unentitled_infra_disclosure) — nothing to align
        # find the golden negative whose case_type names this rule (rejects_* heuristic)
        rid = rule.get("id", "")
        cand = [ct for ct in by_case if ct and (ct.replace("rejects_", "") in rid or rid.replace("no_", "") in ct)]
        if not cand:
            r.W(f"C3/prohibited: rule '{rid}' has keyword signals but no golden case exercises it.")
            continue
        ct = cand[0]
        text = (by_case[ct].get("input") or "")
        matched = [k for k in kws if _matches(text, k)]
        if matched:
            r.K(f"C3/prohibited: '{rid}' <- golden '{ct}' input contains signal {matched}.")
        else:
            sev = r.W if "intent_classifier" in enforced else r.F
            sev(f"C3/prohibited: '{rid}' golden '{ct}' input matches NONE of its keyword signals "
                f"{kws} — input={text[:70]!r}. "
                + ("Keyword layer misses; relies on intent_classifier (runtime). Add a keyword that "
                   "matches the natural phrasing, or ensure the intent path is live on camera."
                   if "intent_classifier" in enforced else
                   "No backstop enforcer — this prohibited rule cannot fire on its own golden case."))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vertical")
    ap.add_argument("--pack-dir", default="policies")
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--golden", default=None)
    a = ap.parse_args()
    pack_dir = Path(a.pack_dir)
    _, gsuf = VERTICAL_ALIAS.get(a.vertical, (a.vertical, a.vertical))
    corpus_dir = Path(a.corpus or f"data/corpus/{gsuf}")
    golden_file = Path(a.golden or f"golden/golden_{gsuf}.jsonl")

    pack, manifest, rows = load_inputs(a.vertical, pack_dir, corpus_dir, golden_file)
    r = Report()
    group_a(rows, pack, r)
    group_b(rows, manifest, r)
    group_c(pack, manifest, rows, r)

    print(f"\n=== validate_golden: {a.vertical} "
          f"(corpus={corpus_dir}, golden={golden_file}, {len(rows)} rows, {len(manifest)} docs) ===\n")
    for m in r.ok:   print("  ok   ", m)
    for m in r.info: print("  info ", m)
    for m in r.warn: print("  WARN ", m)
    for m in r.fail: print("  FAIL ", m)
    print(f"\n  -> {len(r.ok)} ok, {len(r.info)} info, {len(r.warn)} warn, {len(r.fail)} fail")
    if not r.fail and not r.warn:
        print("  -> CLEAN (0 fail, 0 warn — info notes are expected/non-actionable).")
    return 1 if r.fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
