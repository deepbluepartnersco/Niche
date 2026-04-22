"""Query TEA accountability data committed at data/tea_districts.json."""
import json
from functools import cache
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz, process

_DATA_PATH = Path(__file__).parent.parent / "data" / "tea_districts.json"


@cache
def _districts() -> dict[str, int]:
    if not _DATA_PATH.exists():
        return {}
    return json.loads(_DATA_PATH.read_text())


def district_score(isd_name: str) -> Optional[int]:
    """Fuzzy-match ISD name → TEA accountability score (0-100).

    Returns None if no match clears the confidence threshold, or if the
    data file is empty/missing (Claude populates it on demand — see CLAUDE.md).
    """
    districts = _districts()
    if not districts:
        return None
    match = process.extractOne(
        isd_name,
        districts.keys(),
        scorer=fuzz.token_set_ratio,
        score_cutoff=85,
    )
    if not match:
        return None
    return districts[match[0]]
