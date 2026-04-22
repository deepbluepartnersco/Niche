---
description: Generate a two-slide real-estate memo from a Texas property name + address.
argument-hint: <property name>, <full address>  [| <apartments.com url>]
---

You are generating a two-section markdown memo for a Texas property. Follow the steps below in order. Print only the final markdown to the user — no preamble, no trailing commentary.

**Input:** `$ARGUMENTS` — expected format is `<name>, <address>` with an optional `| <apartments.com URL>` to skip the search step. If the user's message doesn't match, parse from the prompt instead.

## Steps

### 1. Parse + resolve metro
- Split the input into `property_name`, `address`, and optional `listing_url`.
- Extract the city from the address (token before `, TX` / `, Texas`).
- Run: `python -c "import sys; sys.path.insert(0,'.'); from src.metro_resolver import resolve_metro; print(resolve_metro('<city>'))"` → expect `DFW` or `Houston`. If it raises, STOP and tell the user the property is outside the supported metros.

### 2. Find the apartments.com listing
- Skip if `listing_url` was provided.
- Use `WebSearch` with query: `"<property_name>" <city> site:apartments.com`
- Pick the first URL matching `apartments.com/<slug>/`. Reject index pages (`/tx/<city>/`), review pages, and blog posts.
- If nothing matches, ask the user for the URL and stop.

### 3. Extract the school list
- `WebFetch` the listing URL with this prompt: "Find the Education / Assigned Schools section. Return JSON: `{assigned_public: [{name, level}], nearby_private: [{name, level}]}`. Level is exactly one of: Elementary, Junior High, High School, K-12. If no private schools are listed, return an empty array."

### 4. Resolve + fetch each school on Niche
For each school, in parallel where possible:
- `WebSearch`: `"<school name>" <city> site:niche.com/k12`
- Pick the first `niche.com/k12/<slug>-tx/` URL (not `/k12/d/...` — that's the district).
- `WebFetch` that URL with: "Return JSON: `{niche_grade, metro_ranking, isd_name}`. `niche_grade` is the overall letter grade (e.g. 'B+', 'A-'). `metro_ranking` is the first ranking in the form `#X of Y Best ... in <METRO>` where METRO matches `<resolved metro>` — return the full string or null. `isd_name` is the school district this school belongs to, or null for private schools."

**Public schools:** if Niche has no page or the fetch fails, keep the school in the list with `niche_grade = null` and `metro_ranking = null`.

**Private schools:** these often have no Niche page at all — especially small religious, Montessori, or preschool programs. Every private school returned by step 3 **must** appear as a row in the final Private Schools table, regardless of whether Niche has a page for it. If `WebSearch` returns zero results, or the top result isn't a `niche.com/k12/<slug>-tx/` URL, or `WebFetch` 404s / returns an error page — skip the fetch for that school, set `niche_grade = null` and `metro_ranking = null`, and move on. **Never drop a private school from the list.**

### 5. Identify + fetch the ISD
- From step 4, take the most-common non-null `isd_name` across public schools. Fallback to the ISD of the first high school, then first elementary.
- Build the ISD URL: `https://www.niche.com/k12/d/<slug>-tx/` where `<slug>` is `isd_name.lower()` with spaces → `-`, dots removed, and trailing `-isd` stripped if Niche's slug form omits it. If the first guess 404s on `WebFetch`, try with `-isd` appended / omitted.
- `WebFetch` with: "Return JSON: `{niche_grade, rankings}`. `niche_grade` is the district's overall letter grade. `rankings` is a list of up to 5 top rankings of the form `#X of Y ... in <METRO>` matching `<resolved metro>`. Prefer rankings that appear in the 'Rankings' section at the top."

### 6. TEA score
- Run: `python -c "import sys; sys.path.insert(0,'.'); from src.tea_lookup import district_score; print(district_score('<isd_name>'))"`.
- If `None` AND you haven't populated TEA data this session: `WebFetch` `https://tea.texas.gov/texas-schools/accountability/academic-accountability/performance-reporting/accountability-rating-system` to find the current district-level scaled score download, then fetch + parse the CSV/Excel into `data/tea_districts.json` as `{"District Name": score_int}`. Re-run the lookup. If still None, leave TEA as `N/A`.

### 7. Fetch the Niche place page
- URL: `https://www.niche.com/places-to-live/<city-slug>-tx/` where `<city-slug>` is the city lowercased, spaces → `-`.
- `WebFetch` with: "Return JSON with keys `overall_grade` (letter grade), `category_grades` (object with keys: Public Schools, Crime & Safety, Housing, Nightlife, Good for Families, Diversity, Jobs, Weather, Cost of Living, Health & Fitness, Outdoor Activities, Commute — values are letter grades), and `rankings` (list of up to 8 top rankings of the form `#X of Y ... in <METRO>` matching `<resolved metro>`)."

### 8. Render
Use `src/markdown_renderer.py` for deterministic output:

```python
python <<'EOF'
import sys; sys.path.insert(0, '.')
from src.models import PropertyReport, PlaceInfo, ISDInfo, School
from src.markdown_renderer import render
# ... construct from step 3–7 data, then print(render(report))
EOF
```

Alternatively, emit the markdown directly following the shape in `README.md`. Either way, the output must match that format exactly.

## Hard rules

- **Do not** invent grades, rankings, or TEA scores. If a field is missing, render `N/A`.
- **Do not** substitute a ranking from a different metro. If the only ranking Niche shows is Texas-wide or national, omit it.
- **Do not** commit cached HTML or fetched pages — don't write to `data/cache/` (the dir is gitignored; using it is optional and session-local).
- **Do not** hit tea.texas.gov unless `district_score` returns None and `data/tea_districts.json` is empty.
- **Private-school row count must equal `nearby_private` count from step 3.** If it doesn't, you dropped one — add it back with N/A values before printing.
- If the address is outside DFW/Houston, refuse cleanly: "This tool supports DFW and Houston metros only."
