"""Render a PropertyReport → two-section markdown matching the slide layout."""
from .models import PropertyReport, School

CATEGORY_ORDER = [
    ("Public Schools", "Crime & Safety"),
    ("Housing", "Nightlife"),
    ("Good for Families", "Diversity"),
    ("Jobs", "Weather"),
    ("Cost of Living", "Health & Fitness"),
    ("Outdoor Activities", "Commute"),
]

METRO_LABEL = {
    "DFW": "Dallas-Fort Worth Area",
    "Houston": "Houston Area",
}


def render(report: PropertyReport) -> str:
    return "\n\n---\n\n".join([_render_slide1(report), _render_slide2(report)])


def _render_slide1(report: PropertyReport) -> str:
    p = report.place
    lines = [
        "## Niche.com — Statistics",
        "",
        f"**{p.name} (Suburb in {p.metro})** — Overall Niche Grade: **{p.overall_grade or 'N/A'}**",
        "",
        "| Category | Grade | | Category | Grade |",
        "|---|---|---|---|---|",
    ]
    for left, right in CATEGORY_ORDER:
        l_grade = p.category_grades.get(left, "N/A")
        r_grade = p.category_grades.get(right, "N/A")
        lines.append(f"| {left} | {l_grade} | | {right} | {r_grade} |")
    lines += ["", f"**All Rankings in the {METRO_LABEL[p.metro]}**"]
    lines += [f"- {r}" for r in p.rankings] if p.rankings else ["- _(none)_"]
    return "\n".join(lines)


def _render_slide2(report: PropertyReport) -> str:
    isd = report.isd
    tea = isd.tea_score if isd.tea_score is not None else "N/A"
    lines = [
        "## Schools",
        "",
        f"**ISD — {isd.name}** · Niche: **{isd.niche_grade or 'N/A'}** · TEA Score: **{tea}**",
    ]
    lines += [f"- {r}" for r in isd.rankings] if isd.rankings else ["- _(none)_"]
    lines += ["", "### Public Schools", _school_table(report.public_schools)]
    lines += ["", "### Private Schools", _school_table(report.private_schools)]
    return "\n".join(lines)


def _school_table(schools: list[School]) -> str:
    if not schools:
        return "_(none found)_"
    rows = ["| Level | School | Niche Grade | Texas Ranking |", "|---|---|---|---|"]
    for s in schools:
        rows.append(
            f"| {s.level} | {s.name} | {s.niche_grade or 'N/A'} | {s.metro_ranking or 'N/A'} |"
        )
    return "\n".join(rows)
