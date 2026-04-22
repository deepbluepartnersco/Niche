"""Map a Texas city or county to its metro ('DFW' or 'Houston')."""
import json
import re
from pathlib import Path

from .models import Metro

DFW_COUNTIES = {
    "Collin", "Dallas", "Denton", "Ellis", "Hood", "Hunt", "Johnson",
    "Kaufman", "Parker", "Rockwall", "Somervell", "Tarrant", "Wise",
}

HOUSTON_COUNTIES = {
    "Austin", "Brazoria", "Chambers", "Fort Bend", "Galveston", "Harris",
    "Liberty", "Montgomery", "Waller",
}

_CITY_TABLE_PATH = Path(__file__).parent.parent / "data" / "tx_city_metro.json"


def resolve_metro(county_or_city: str) -> Metro:
    """Map a Texas county or city name → 'DFW' or 'Houston'.

    If the input contains "county" / "co." it's looked up as a county;
    otherwise as a city. The two paths don't cross-fall-back, because
    several city names collide with county names (e.g. Austin).
    """
    looks_like_county = bool(
        re.search(r"\bcount(?:y|ies)\b|\bco\.?\b", county_or_city, flags=re.I)
    )
    normalized = re.sub(
        r",?\s*(county|co\.?)\s*,?\s*(tx)?\.?$",
        "",
        county_or_city,
        flags=re.I,
    ).strip().title()

    if looks_like_county:
        if normalized in DFW_COUNTIES:
            return "DFW"
        if normalized in HOUSTON_COUNTIES:
            return "Houston"
    else:
        if _CITY_TABLE_PATH.exists():
            cities: dict[str, str] = json.loads(_CITY_TABLE_PATH.read_text())
            if normalized in cities:
                return cities[normalized]  # type: ignore[return-value]
    raise ValueError(f"'{county_or_city}' is not in DFW or Houston metro")
