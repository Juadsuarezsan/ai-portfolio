import json
from pathlib import Path

from eval.schemas import GoldCase

GOLD_DIR = Path(__file__).parent / "gold"


def load_gold_cases() -> list[GoldCase]:
    """Load every case_*.json file from backend/eval/gold/."""
    if not GOLD_DIR.exists():
        return []
    cases: list[GoldCase] = []
    for path in sorted(GOLD_DIR.glob("case_*.json")):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        cases.append(GoldCase(**data))
    return cases
