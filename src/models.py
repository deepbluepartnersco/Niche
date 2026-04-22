from dataclasses import dataclass, field
from typing import Literal, Optional

Metro = Literal["DFW", "Houston"]
SchoolLevel = Literal["Elementary", "Junior High", "High School", "K-12"]
SchoolType = Literal["Public", "Private"]


@dataclass
class School:
    name: str
    level: SchoolLevel
    type: SchoolType
    niche_url: Optional[str] = None
    niche_grade: Optional[str] = None
    metro_ranking: Optional[str] = None


@dataclass
class ISDInfo:
    name: str
    niche_grade: Optional[str] = None
    tea_score: Optional[int] = None
    rankings: list[str] = field(default_factory=list)


@dataclass
class PlaceInfo:
    name: str
    metro: Metro
    overall_grade: Optional[str] = None
    category_grades: dict[str, str] = field(default_factory=dict)
    rankings: list[str] = field(default_factory=list)


@dataclass
class PropertyReport:
    property_name: str
    address: str
    place: PlaceInfo
    isd: ISDInfo
    public_schools: list[School]
    private_schools: list[School]
