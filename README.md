# Niche

Given a Texas property name + address (DFW or Houston only), produce two markdown "slides" for a real-estate investment memo:

1. **Suburb statistics** — Niche overall grade, 12 category grades, top metro rankings.
2. **Schools** — ISD info (Niche grade + TEA score + rankings) and public/private school tables (Niche grade + metro ranking).

**This repo is designed to be driven by Claude Code.** You don't run a script — you ask Claude to run the `/memo` slash command with a property name and address. Claude does the searching, fetching, and parsing using its own `WebSearch` / `WebFetch` tools, then renders the output via a small Python helper layer.

## Usage (in Claude Code)

```
/memo The Villas at Duncanville, 123 Main St, Duncanville TX 75116
```

Optional: append ` | <apartments.com URL>` to skip the search step:

```
/memo The Villas at Duncanville, 123 Main St, Duncanville TX 75116 | https://www.apartments.com/the-villas-at-duncanville-duncanville-tx/abc123/
```

Or just paste a property name and address into the chat — Claude will recognize the pattern and run the same flow (see `CLAUDE.md` for trigger phrases).

## Setup

```bash
pip install -r requirements.txt
```

That's it. `rapidfuzz` is the only runtime dep. The committed `data/tx_city_metro.json` and `data/tea_districts.json` mean there's no one-time data download step — if `tea_districts.json` is empty on first run, Claude will populate it from tea.texas.gov on demand.

## Why Claude drives (vs. a Python scraper)

The previous plan used `curl_cffi` + Playwright + `ddgs` to scrape Niche / apartments.com / DuckDuckGo. That stack fights Claude Code Web:

- `curl_cffi` needs native libs that don't install cleanly in sandboxed environments.
- Playwright needs full browser binaries — unavailable in web sandboxes.
- DuckDuckGo's HTML scrape is fragile; Claude's `WebSearch` is more reliable.
- Cloudflare on Niche frequently blocks direct requests but serves Claude's fetcher fine.

So the repo now **keeps only the deterministic bits in Python** (data models, fuzzy matching, TEA lookup, markdown rendering) and pushes search/fetch/parse into Claude's tool belt via the `/memo` runbook. You get:

- Zero Cloudflare bypass code to maintain.
- One dependency instead of nine.
- HTML parsing done by an LLM — resilient to markup changes that would break CSS selectors.

Tradeoff: each run hits the live network through Claude (no local cache), and you can't invoke it from cron / CI without Claude Code.

## Output shape

```markdown
## Niche.com — Statistics

**Duncanville (Suburb in DFW)** — Overall Niche Grade: **B**

| Category | Grade | | Category | Grade |
|---|---|---|---|---|
| Public Schools | B− | | Crime & Safety | C |
| Housing | C+ | | Nightlife | B− |
| Good for Families | B | | Diversity | A+ |
| Jobs | B− | | Weather | B+ |
| Cost of Living | B | | Health & Fitness | B− |
| Outdoor Activities | B | | Commute | B− |

**Top Rankings**
- #9 of 125 Most Diverse Suburbs in DFW
- #20 of 287 Most Diverse Places to Live in DFW

---

## Schools

**ISD — Duncanville** · Niche: **B−** · TEA Score: **74**
- #2 of 82 Best School Districts for Athletes in DFW
- #45 of 94 Most Diverse School Districts in DFW

### Public Schools
| Level | School | Niche Grade | Texas Ranking |
|---|---|---|---|
| Elementary | William Lee Hastings Elementary | C− | N/A |
| Junior High | William H Byrd Middle | C+ | N/A |
| High School | Duncanville High School | B− | N/A |

### Private Schools
| Level | School | Niche Grade | Texas Ranking |
|---|---|---|---|
| K-12 | Master's Academy | N/A | N/A |
```

## Project structure

```
.
├── .claude/commands/memo.md    # the runbook Claude follows
├── CLAUDE.md                   # operating manual for Claude
├── README.md                   # this file
├── requirements.txt            # just rapidfuzz
├── data/
│   ├── tea_districts.json      # TEA scaled scores ({} by default)
│   └── tx_city_metro.json      # city → "DFW" | "Houston"
├── src/
│   ├── models.py               # dataclasses
│   ├── markdown_renderer.py    # final render step
│   ├── metro_resolver.py       # city/county → metro
│   ├── name_matcher.py         # fuzzy matching
│   └── tea_lookup.py           # TEA score lookup
└── tests/fixtures/             # saved HTML for offline tests (optional)
```

## Data sources

| Source | Where it shows up | How it's fetched |
|---|---|---|
| apartments.com listing | School list per property | Claude `WebFetch` |
| niche.com place page | Slide 1 (suburb grades + rankings) | Claude `WebFetch` |
| niche.com ISD page | Slide 2 header | Claude `WebFetch` |
| niche.com school page | Slide 2 table rows | Claude `WebFetch` |
| TEA accountability | Slide 2 header (district score) | Claude `WebFetch` on first use, cached to `data/tea_districts.json` |
