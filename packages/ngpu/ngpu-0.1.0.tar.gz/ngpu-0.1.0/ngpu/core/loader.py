import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filename}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)