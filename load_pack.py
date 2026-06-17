"""load_pack.py — load a policy pack by deep-merging _base + the vertical overlay
into one dict. Keyless, offline, stdlib + PyYAML. The skeleton's guardrail / eval /
audit modules read fields off the returned dict; nothing else changes when you swap packs.

    pack = load_pack("energy_utilities_us")
    pack["pii_classes"]        # base PII (inherited) — present in every pack
    pack["sensitive_classes"]  # vertical-specific classes (CEII/BCSI, PHI, NPI, ...)
    pack["withhold_escalate"]  # vertical refuse-and-route triggers

For a zero-dependency build, store packs as .json and swap yaml.safe_load for json.loads.
"""

from pathlib import Path
from typing import Any

import yaml

POLICIES_DIR = Path(__file__).parent / "policies"


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge overlay onto base. dicts merge recursively; lists CONCATENATE
    (so base PII + base withhold survive and the vertical adds its own); scalars override."""
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = out[k] + v
        else:
            out[k] = v
    return out


def load_pack(name: str | None, policies_dir: Path = POLICIES_DIR) -> dict[str, Any]:
    base: dict[str, Any] = yaml.safe_load((policies_dir / "_base.yaml").read_text())
    if name in (None, "_base"):
        return base
    overlay = yaml.safe_load((policies_dir / f"{name}.yaml").read_text())
    overlay.pop("extends", None)
    return _deep_merge(base, overlay)


if __name__ == "__main__":
    import sys
    import json

    pack = load_pack(sys.argv[1] if len(sys.argv) > 1 else "energy_utilities_us")
    print(json.dumps(pack, indent=2, default=str))
