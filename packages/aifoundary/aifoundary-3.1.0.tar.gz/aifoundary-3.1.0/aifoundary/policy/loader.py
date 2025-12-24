import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_policy(path: str) -> dict:
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"Policy file not found: {p}")

    if p.suffix in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("pyyaml is required for YAML policies")
        return yaml.safe_load(p.read_text())

    if p.suffix == ".json":
        return json.loads(p.read_text())

    raise ValueError("Policy must be YAML or JSON")
