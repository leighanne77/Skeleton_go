"""app/guardrails.py — guard-first input/output screening (rubric item 6).

Pack-driven, deterministic, keyless:
  • PII (pack `pii_classes`, regex) → redact/mask per `handling`. NER-only classes
    (street_address / person_name) are an optional Presidio upgrade, off by default.
  • Injection screen — instruction-injection markers in retrieved/untrusted content are
    flagged and never followed (retrieved content is data, never commands).
  • Sensitive-class keyword screen (pack `sensitive_classes`) — a secondary signal; the
    PRIMARY entitlement gate is manifest tags at retrieval time (see retriever.py).

Guard-first: PII is stripped before any text reaches the user; injection is flagged
before any retrieved instruction could be acted on.
"""

from __future__ import annotations

import re

from app.config import get_settings
from app.models import GuardrailResult
from app.policy import get_pack

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


def detect_sensitive(text: str, pack_name: str | None = None) -> list[str]:
    pack = get_pack(pack_name or get_settings().policy_pack)
    low = text.lower()
    hits: list[str] = []
    for c in pack.get("sensitive_classes", []):
        keywords = c.get("detect", {}).get("keywords", [])
        if any(str(k).lower() in low for k in keywords):
            hits.append(str(c["name"]))
    return hits


def screen(text: str, pack_name: str | None = None) -> tuple[str, GuardrailResult]:
    """Guard-first: redact PII, flag injection + sensitive classes. Returns clean text."""
    clean, actions = redact_pii(text, pack_name)
    for cls in detect_sensitive(text, pack_name):
        actions.append({"class": cls, "action": "flag_sensitive"})
    return clean, GuardrailResult(
        blocked=False, actions=actions, injection_detected=scan_injection(text)
    )
