"""run.py — entrypoint. Launches the Streamlit UI (T1).

At T3+ this also builds the governed graph the UI calls; for now it just launches
the UI against the stub backend. Keyless, offline.

    python run.py            # → streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    app = ROOT / "ui" / "streamlit_app.py"
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)])


if __name__ == "__main__":
    raise SystemExit(main())
