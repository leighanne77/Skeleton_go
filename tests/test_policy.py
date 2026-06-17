"""tests/test_policy.py — T2: the policy loader merges _base + the vertical (R6, R10)."""

from __future__ import annotations

from app.policy import get_pack


def test_policy_pack_load() -> None:
    pack = get_pack("financial_services_us")

    # base PII inherited
    pii = {c["name"] for c in pack["pii_classes"]}
    assert {"ssn", "email", "phone_us"} <= pii

    # vertical sensitive_classes present
    sensitive = {c["name"] for c in pack["sensitive_classes"]}
    assert {"mnpi", "sar_data", "npi"} <= sensitive

    # prohibited concatenated: a base universal + a vertical rule both present
    prohibited = {r["id"] for r in pack["prohibited"]}
    assert "no_uncited_claim" in prohibited  # from _base
    assert "no_personalized_advice" in prohibited  # from the vertical
    assert "no_realtime_quote" in prohibited  # the briefing's signature guardrail

    # golden_negatives concatenated: the 6 universal + the vertical signatures
    cases = {g["case_type"] for g in pack["golden_negatives"]}
    assert {
        "rejects_unsupported_span",
        "rejects_empty_retrieval",
        "rejects_prompt_injection",
    } <= cases  # base universal
    assert {"rejects_mnpi_disclosure", "rejects_realtime_quote"} <= cases  # vertical

    # vertical thresholds override base (base entailment 0.7 → vertical 0.72)
    assert pack["thresholds"]["entailment"] == 0.72


def test_default_pack_is_financial_services() -> None:
    pack = get_pack()  # uses configured policy_pack
    assert pack["pack_id"] == "financial_services_us"
