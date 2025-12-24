import json
import os
from typing import Dict

THEORY_DIR = os.path.join(os.path.dirname(__file__))

def list_theories() -> list:
    """Return all available theory JSON filenames."""
    return [
        f.replace(".json", "")
        for f in os.listdir(THEORY_DIR)
        if f.endswith(".json")
    ]


def load_theory(name: str) -> Dict[str, str]:
    """
    Load a theory by name from episteme/theory/<name>.json.
    Returns a dict mapping theorem -> description.
    """
    path = os.path.join(THEORY_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise ValueError(f"Theory '{name}' not found in {THEORY_DIR}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "theorems" not in data:
        raise ValueError(f"Invalid theory file '{name}': missing 'theorems' field")

    return data["theorems"]
