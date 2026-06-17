"""app/guardrails.py — guard-first input/output screening (rubric item 6).

Pack-driven, deterministic, keyless:
  • PII (pack `pii_classes`, regex) → redact/mask per `handling`. The NER-only classes
    (street_address / person_name) are handled by **Presidio + spaCy** when
    `USE_PRESIDIO_NER=true` (keyless/offline once the model is installed:
    `python -m spacy download en_core_web_sm`); off by default, and the regex pass
    always runs so the skeleton degrades gracefully without the model.
  • Injection screen — instruction-injection markers in retrieved/untrusted content are
    flagged and never followed (retrieved content is data, never commands).
  • Sensitive-class keyword screen (pack `sensitive_classes`) — a secondary signal; the
    PRIMARY entitlement gate is manifest tags at retrieval time (see retriever.py).

Guard-first: PII is stripped before any text reaches the user; injection is flagged
before any retrieved instruction could be acted on.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.models import GuardrailResult
from app.policy import get_pack

# pack NER `entity` → Presidio entity type (spaCy has no ADDRESS; LOCATION is the proxy)
_NER_ENTITY = {"PERSON": "PERSON", "ADDRESS": "LOCATION"}

# Instruction-injection markers (case-insensitive). Treat any hit as data to ignore.
_INJECTION = re.compile(
    r"\b(ignore|disregard|forget|override)\b[^.]{0,40}\b"
    r"(above|previous|prior|earlier|all)\b[^.]{0,30}\b(instruction|prompt|context|rule)s?\b"
    r"|\b(system\s+prompt|you\s+are\s+now|new\s+instructions?\s*:)\b",
    re.IGNORECASE,
)
_MASK = "•"


def scan_injection(text: str) -> bool:
    return bool(_INJECTION.search(text))


def _mask(s: str) -> str:
    return s[:2] + _MASK * max(len(s) - 4, 1) + s[-2:] if len(s) > 4 else _MASK * len(s)


def redact_pii(
    text: str, pack_name: str | None = None
) -> tuple[str, list[dict[str, object]]]:
    pack = get_pack(pack_name or get_settings().policy_pack)
    actions: list[dict[str, object]] = []
    out = text
    for c in pack.get("pii_classes", []):
        if c.get("detect") != "regex" or not c.get("pattern"):
            continue
        name, handling, pattern = (
            str(c["name"]),
            str(c.get("handling", "redact")),
            str(c["pattern"]),
        )

        def repl(m: re.Match[str], h: str = handling, n: str = name) -> str:
            return _mask(m.group(0)) if h == "mask" else f"[{n.upper()} REDACTED]"

        out, n = re.subn(pattern, repl, out)
        if n:
            actions.append({"class": name, "action": handling, "count": n})
    return out, actions


@lru_cache(maxsize=1)
def _ner_engine() -> Any:
    """Presidio analyzer on a small spaCy model (en_core_web_sm). Cached; returns None
    if Presidio or the model isn't installed (so the regex pass still runs offline)."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        provider = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }
        )
        return AnalyzerEngine(
            nlp_engine=provider.create_engine(), supported_languages=["en"]
        )
    except Exception:  # noqa: BLE001 — missing presidio/model → NER unavailable, regex still works
        return None


def redact_ner(
    text: str, pack_name: str | None = None
) -> tuple[str, list[dict[str, object]]]:
    """Redact NER PII (the pack's `detect: ner` classes — name/address) via Presidio.
    No-op (returns text unchanged) if the engine is unavailable."""
    engine = _ner_engine()
    if engine is None:
        return text, []
    pack = get_pack(pack_name or get_settings().policy_pack)
    entities = [
        _NER_ENTITY.get(str(c.get("entity")), str(c.get("entity")))
        for c in pack.get("pii_classes", [])
        if c.get("detect") == "ner" and c.get("entity")
    ]
    if not entities:
        return text, []
    results = [
        r
        for r in engine.analyze(text=text, entities=entities, language="en")
        if r.score >= 0.4
    ]
    actions: list[dict[str, object]] = []
    out = text
    for r in sorted(
        results, key=lambda x: x.start, reverse=True
    ):  # end→start preserves offsets
        out = out[: r.start] + f"[{r.entity_type} REDACTED]" + out[r.end :]
        actions.append(
            {
                "class": r.entity_type.lower(),
                "action": "redact",
                "score": round(r.score, 2),
            }
        )
    return out, actions


def detect_sensitive(text: str, pack_name: str | None = None) -> list[str]:
    pack = get_pack(pack_name or get_settings().policy_pack)
    low = text.lower()
    hits: list[str] = []
    for c in pack.get("sensitive_classes", []):
        keywords = c.get("detect", {}).get("keywords", [])
        if any(str(k).lower() in low for k in keywords):
            hits.append(str(c["name"]))
    return hits


def query_violations(
    query: str, entitlements: list[str], pack_name: str | None = None
) -> list[str]:
    """Input-side enforcement (pack-driven): a query that trips a prohibited rule's
    keyword signal, or targets a `block_unless_entitled` class the principal isn't
    cleared for, must be routed to a human — regardless of what retrieval finds.

    Catches the BFSI signatures from the pack as DATA: no_personalized_advice,
    no_realtime_quote, MNPI/SAR tipping-off when unentitled.
    """
    pack = get_pack(pack_name or get_settings().policy_pack)
    low = query.lower()
    ent = set(entitlements)
    out: list[str] = []

    for rule in pack.get("prohibited", []):
        keywords = (rule.get("signals") or {}).get("keywords") or []
        if any(str(k).lower() in low for k in keywords):
            out.append(str(rule["id"]))

    for c in pack.get("sensitive_classes", []):
        req = c.get("requires_entitlement")
        if c.get("handling") == "block_unless_entitled" and req and str(req) not in ent:
            # only MULTI-WORD keywords on the query side — a bare token like "SAR" or
            # "MNPI" appears in legit compliance Q&A ("when must a SAR be filed?"), so
            # gating on it over-blocks. Disclosure-specific phrases ("deal terms",
            # "suspicious activity report") are the safe query signal; the precise
            # tipping-off-vs-Q&A distinction is the intent-classifier tier (KNOWN_ISSUES).
            keywords = [
                str(k)
                for k in c.get("detect", {}).get("keywords", [])
                if len(str(k).split()) >= 2
            ]
            if any(k.lower() in low for k in keywords):
                out.append(f"unentitled:{c['name']}")
    return out


def screen(text: str, pack_name: str | None = None) -> tuple[str, GuardrailResult]:
    """Guard-first: redact PII (regex + optional Presidio NER), flag injection +
    sensitive classes. Returns clean text."""
    clean, actions = redact_pii(text, pack_name)
    if get_settings().use_presidio_ner:
        clean, ner_actions = redact_ner(clean, pack_name)
        actions.extend(ner_actions)
    for cls in detect_sensitive(text, pack_name):
        actions.append({"class": cls, "action": "flag_sensitive"})
    return clean, GuardrailResult(
        blocked=False, actions=actions, injection_detected=scan_injection(text)
    )
