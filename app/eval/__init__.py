"""app.eval — the control-plane gate + (later) the golden harness.

The gate is the independent control node between the parallel analyst agents and the
ONE synthesizer. Stage-2 support is a cross-family judge (OpenAI judging Claude's claims;
`judge.py`). The synthesizer is reachable only on the gate's pass edge.
"""
