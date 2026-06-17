"""tests/test_memory.py — T8 deliberate memory policy (R5/R8). Cross-session OFF."""

from __future__ import annotations

import pytest

from app import memory


def test_memory_policy_session_and_working_on() -> None:
    # YAML parses on/off as booleans → session/working are truthy, cross_session falsy
    p = memory.policy("financial_services_us")
    assert memory._on(p.get("session"))
    assert memory._on(p.get("working"))


def test_cross_session_off_by_design() -> None:
    assert memory.cross_session_enabled("financial_services_us") is False
    # both worked verticals must keep cross-session off
    assert memory.cross_session_enabled("energy_utilities_us") is False


def test_persist_cross_session_refuses() -> None:
    with pytest.raises(RuntimeError, match="cross-session"):
        memory.persist_cross_session("user:dana", {"last_ticker": "MSFT"})
