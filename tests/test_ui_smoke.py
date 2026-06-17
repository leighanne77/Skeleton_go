"""tests/test_ui_smoke.py — UI acceptance: welcome gate, the two surfaces, the gate
states, and the entitlement flip all render.

Munich-Re-styled build: the app opens on a welcome screen (dismissed by "Enter the
Stock Briefing"); verdict banners are branded HTML (st.markdown); the advisor and
"Show my work" surfaces are switched by session-state via the gear / back buttons;
the entitlement toggle lives on the operator surface.

Uses Streamlit's AppTest (no browser) against the stub backend. Replaced/extended
when the real graph lands at T3+.
"""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

APP = "ui/streamlit_app.py"


def _md(at: AppTest) -> str:
    # exclude the injected <style> block — its class names (.nw-quote, .nw-delivered)
    # would otherwise pollute text matches against the rendered surface.
    return " || ".join(m.value for m in at.markdown if "<style>" not in m.value)


def _enter(at: AppTest) -> AppTest:
    """Dismiss the welcome screen → land on the advisor surface."""
    at.button(key="enter").click().run()
    return at


def test_welcome_screen_then_enter() -> None:
    at = AppTest.from_file(APP).run()
    assert not at.exception
    assert "Defensible for compliance" in _md(at)  # welcome copy is up
    _enter(at)
    assert not at.exception
    assert at.button(key="run_advisor")  # landed on the advisor surface


def test_delivered_state_renders() -> None:
    at = _enter(AppTest.from_file(APP).run())
    at.button(key="run_advisor").click().run()  # default quick task = MRB 10-K briefing
    assert not at.exception
    md = _md(at)
    assert "DELIVERED" in md
    assert "nw-quote" in md  # the delayed quote card rendered
    assert "ROUTED" not in md


def test_routed_state_renders() -> None:
    at = _enter(AppTest.from_file(APP).run())
    at.text_input(key="q").set_value(
        "give me the live execution price right now to place a trade"
    ).run()
    at.button(key="run_advisor").click().run()
    assert not at.exception
    md = _md(at)
    assert "ROUTED" in md
    assert "DELIVERED" not in md
    assert "nw-quote" not in md  # no quote card on a routed verdict


def test_gear_opens_show_my_work() -> None:
    at = _enter(AppTest.from_file(APP).run())
    at.button(key="run_advisor").click().run()
    at.button(key="to_operator").click().run()  # the gear
    assert not at.exception
    assert any("Show my work" in m.value for m in at.markdown)
    assert len(at.code) >= 2  # entitlement decision + audit chain blocks


def test_entitlement_flip_on_operator() -> None:
    at = _enter(AppTest.from_file(APP).run())
    # unentitled MNPI ask → routed
    at.text_input(key="q").set_value("What are the Project Atlas deal terms?").run()
    at.button(key="run_advisor").click().run()
    assert "ROUTED" in _md(at)
    # open Show my work, grant the clearance, re-run the same query → delivers
    at.button(key="to_operator").click().run()
    at.multiselect(key="op_entitlements").set_value(["mnpi_cleared"]).run()
    at.button(key="rerun_op").click().run()
    assert not at.exception
    assert any(
        "delivered" in m.value for m in at.markdown
    )  # operator verdict line flips
