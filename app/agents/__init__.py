"""app.agents — the SWAPPABLE worker layer (retriever, specialists, synthesizer).

Workers are tools/specialists behind thin interfaces; the control-plane gate
(app/eval/gate.py) is NOT here — it is the independent node the synthesizer is
reachable through only on the pass edge.
"""
