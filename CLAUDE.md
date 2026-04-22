# CLAUDE.md

Operating manual for this repo when running in Claude Code (web or CLI).

## What this repo does

Takes a Texas property name + address (DFW or Houston only) and produces a two-section markdown memo: suburb stats from Niche.com and school info from Niche + TEA. **You — Claude — are the orchestrator.** There is no Python CLI. Scraping is done via your `WebSearch` and `WebFetch` tools; Python is only for deterministic logic (metro resolution, fuzzy name matching, rendering).

## Entry point

When the user gives you a property name + address, run the `/memo` slash command: see `.claude/commands/memo.md` for the full runbook. That file is the single source of truth for the pipeline.

Trigger phrases: "memo for ...", "generate a report on ...", "run this property: ...", or a bare `<name>, <address>` pair in the user's message.

## Layout

```
.
├── .claude/commands/memo.md    # the runbook you follow
├── CLAUDE.md                   # this file
├── README.md                   # user-facing docs
├── requirements.txt            # just rapidfuzz
├── data/
│   ├── tea_districts.json      # committed snapshot ({} until populated)
│   └── tx_city_metro.json      # committed city → metro table
├── src/
│   ├── models.py               # dataclasses (PropertyReport, PlaceInfo, ISDInfo, School)
│   ├── markdown_renderer.py    # render(PropertyReport) -> str
│   ├── metro_resolver.py       # resolve_metro(city_or_county) -> "DFW" | "Houston"
│   ├── name_matcher.py         # fuzz.token_set_ratio wrapper
│   └── tea_lookup.py           # district_score(isd_name) -> int | None
└── tests/fixtures/             # (empty; add saved HTML here if useful)
```

## Conventions

- Python 3.10+. Dataclasses over Pydantic/TypedDict — keep the model layer zero-dep.
- Fuzzy matching uses `rapidfuzz.fuzz.token_set_ratio` everywhere (cutoff 80–85).
- Metros are the literal strings `"DFW"` and `"Houston"`. Don't add others.
- `SchoolLevel` literal values: `"Elementary"`, `"Junior High"`, `"High School"`, `"K-12"` (ASCII hyphen — the README's "K–12" en-dash is display-only).
- Output format is defined by `markdown_renderer.render()`. Don't drift from it.

## What NOT to do

- **Don't restore the scraper stack.** No `curl_cffi`, no `playwright`, no `ddgs`, no `typer`, no `usaddress`. If you feel the urge to add one, read the README's "Why Claude drives" section first.
- **Don't invent data.** Missing grade → `N/A`. Missing ranking → omit the bullet. Missing TEA score → `N/A`. Never fabricate a number because the layout expects one.
- **Don't use a ranking from the wrong metro.** Only DFW-in-DFW and Houston-in-Houston. Drop Texas-wide or national rankings.
- **Don't commit** `data/cache/` contents or populated `.env` files. `data/tea_districts.json` and `data/tx_city_metro.json` ARE committed — that's intentional.
- **Don't widen scope** to San Antonio, Austin, etc. unless the user explicitly asks. The ranking extraction is metro-specific.
- **Don't add a CLI.** No `scripts/run.py`. The user invokes `/memo`; that is the interface.

## Running Python helpers

Always from repo root:
```bash
python -c "import sys; sys.path.insert(0, '.'); from src.metro_resolver import resolve_metro; print(resolve_metro('Plano'))"
```
The `sys.path` hack exists because `src/` is not an installed package. Don't add `pyproject.toml` unless the user asks.

## Failure handling

- Address outside DFW/Houston → refuse: "This tool supports DFW and Houston metros only."
- apartments.com listing not found → ask the user for the URL.
- Niche school page not found → keep the school in the output with `N/A` grade + ranking.
- ISD page 404 → try the slug with/without trailing `-isd`. If still 404, use `ISDInfo(name=<best guess>, niche_grade=None, rankings=[])`.
- TEA data file empty → optionally fetch from `tea.texas.gov` (runbook step 6). If that fails, TEA score = `N/A`.
