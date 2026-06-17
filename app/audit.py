"""app/audit.py — append-only, hash-chained audit log (the third moat pillar).

Every governed run writes a tamper-evident chain of `AuditRecord`s. Each record's
hash covers the previous hash + the record's canonical content, so any mutation or
deletion of a past record breaks the chain (`verify` returns False). Append-only by
construction — there is no update/delete. Persists to JSONL; reload + verify proves
integrity off disk.

Timestamps are passed IN by the caller (not read from a wall-clock here) so the chain
is reproducible in tests and the demo.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.models import AuditRecord

GENESIS = "0" * 64


def _digest(prev_hash: str, rec: dict[str, object]) -> str:
    canon = json.dumps(rec, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256((prev_hash + canon).encode("utf-8")).hexdigest()


def _content(
    seq: int,
    timestamp: str,
    event_type: str,
    payload: dict[str, object],
    scope: list[str],
) -> dict[str, object]:
    return {
        "seq": seq,
        "timestamp": timestamp,
        "event_type": event_type,
        "payload": payload,
        "entitlement_scope": scope,
    }


class AuditChain:
    """In-memory append-only hash chain. Persist with `to_jsonl` / reload with `from_jsonl`."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def append(
        self,
        event_type: str,
        payload: dict[str, object],
        timestamp: str,
        entitlement_scope: list[str] | None = None,
    ) -> AuditRecord:
        seq = len(self.records)
        prev = self.records[-1].hash if self.records else GENESIS
        scope = entitlement_scope or []
        h = _digest(prev, _content(seq, timestamp, event_type, payload, scope))
        rec = AuditRecord(
            seq=seq,
            timestamp=timestamp,
            event_type=event_type,
            payload=payload,
            entitlement_scope=scope,
            prev_hash=prev,
            hash=h,
        )
        self.records.append(rec)
        return rec

    def verify(self) -> bool:
        """True iff every link and digest is intact (no mutation/deletion/reorder)."""
        prev = GENESIS
        for i, r in enumerate(self.records):
            if r.seq != i or r.prev_hash != prev:
                return False
            expected = _digest(
                prev,
                _content(
                    r.seq, r.timestamp, r.event_type, r.payload, r.entitlement_scope
                ),
            )
            if r.hash != expected:
                return False
            prev = r.hash
        return True

    def to_jsonl(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(r.model_dump_json() for r in self.records) + "\n")

    @classmethod
    def from_jsonl(cls, path: str) -> AuditChain:
        chain = cls()
        for line in Path(path).read_text().splitlines():
            if line.strip():
                chain.records.append(AuditRecord.model_validate_json(line))
        return chain
