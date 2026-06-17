"""tests/test_audit.py — T9 tamper-evident hash-chained audit (R9)."""

from __future__ import annotations

from pathlib import Path

from app.audit import AuditChain


def _chain() -> AuditChain:
    c = AuditChain()
    c.append(
        "retrieval",
        {"chunks": 3, "top": "reg_bi"},
        "2026-06-17T10:00:00Z",
        ["mnpi_cleared"],
    )
    c.append("gate", {"stage": "rubric", "passed": True}, "2026-06-17T10:00:01Z")
    c.append("decision", {"verdict": "delivered"}, "2026-06-17T10:00:02Z")
    return c


def test_audit_chain_integrity() -> None:
    c = _chain()
    assert len(c.records) == 3
    assert c.records[0].prev_hash == "0" * 64  # genesis
    assert c.records[1].prev_hash == c.records[0].hash  # linked
    assert c.verify() is True


def test_tampering_payload_breaks_chain() -> None:
    c = _chain()
    c.records[1].payload["passed"] = False  # mutate a past record
    assert c.verify() is False


def test_deletion_breaks_chain() -> None:
    c = _chain()
    del c.records[1]  # drop a record (seq/prev_hash no longer line up)
    assert c.verify() is False


def test_persist_and_reload_verifies(tmp_path: Path) -> None:
    c = _chain()
    f = str(tmp_path / "audit_log.jsonl")
    c.to_jsonl(f)
    reloaded = AuditChain.from_jsonl(f)
    assert reloaded.verify() is True
    assert [r.event_type for r in reloaded.records] == ["retrieval", "gate", "decision"]
