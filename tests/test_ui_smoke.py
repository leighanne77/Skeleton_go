"""tests/test_ui_smoke.py — T1 acceptance: the UI launches and both never-blurred
states render, the Operator view renders, and the MNPI entitlement flip works.

Uses Streamlit's AppTest to execute ui/app.py headlessly against the stub backend
(no browser). Replaced/extended when the real graph lands at T3+.
"""
from __future__ import annotations

from streamlit.testing.v1 import AppTest

APP = "ui/streamlit_app.py"


def test_app_boots_clean() -> None:
    at = AppTest.from_file(APP).run()
    assert not at.exception
    assert any("gated before it reaches you" in m.value for m in at.markdown)


def test_delivered_state_renders() -> None:
    at = AppTest.from_file(APP).run()
    at.button[0].click().run()  # default preset = MRB 10-K briefing
    assert not at.exception
    assert any("DELIVERED" in s.value for s in at.success)
    assert len(at.metric) == 1  # the delayed quote block


def test_routed_state_renders() -> None:
    at = AppTest.from_file(APP).run()
    at.text_input[0].set_value("give me the live execution price right now to place a trade").run()
    at.button[0].click().run()
    assert not at.exception
    assert any("ROUTED" in w.value for w in at.warning)
    assert not at.success  # never a delivered answer alongside a routed verdict


def test_operator_view_renders() -> None:
    at = AppTest.from_file(APP).run()
    at.button[0].click().run()
    at.radio[0].set_value("Operator").run()
    assert not at.exception
    assert len(at.code) >= 2  # entitlement decision + audit chain blocks


def test_mnpi_entitlement_flip() -> None:
    at = AppTest.from_file(APP).run()
    # unentitled → routed
    at.text_input[0].set_value("What are the Project Atlas deal terms?").run()
    at.button[0].click().run()
    assert any("ROUTED" in w.value for w in at.warning)
    # entitled → delivered (same query)
    at.multiselect[0].set_value(["mnpi_cleared"]).run()
    at.button[0].click().run()
    assert not at.exception
    assert any("DELIVERED" in s.value for s in at.success)
