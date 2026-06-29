"""app.agents — the SWAPPABLE worker layer (retriever, parallel analyst agents, synthesizer).

The analyst agents (`analysts.py`, cross-family clients in `llm.py`) run concurrently
upstream of the gate and only PROPOSE cited findings; the synthesizer (`synthesizer.py`)
DISPOSES — it writes the answer in ONE place, reachable only on the gate's pass edge. The
control-plane gate (app/eval/gate.py) is NOT here — it is the independent node between
the agents and the synthesizer.
"""
