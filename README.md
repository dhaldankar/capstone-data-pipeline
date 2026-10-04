# Mamaearth Returns & Growth Intelligence Pipeline

Capstone submission for *Data Analytics with AI & Gen AI* (E&ICT Academy, IIT Roorkee).

**Live report:** https://dhaldankar.github.io/capstone-data-pipeline/

This project answers one business question — *where are returns really coming from, and what is the true revenue picture once the data is cleaned?* — across three connected layers:

1. **SQL** builds a relational store from the raw CSVs and runs nine business reports.
2. **Python / pandas** independently cleans the same CSVs, reconciles the revenue, tests the hypotheses, and writes verified findings plus two charts.
3. **GenAI** turns those findings into a Situation–Complication–Resolution business narrative via any OpenAI-compatible provider (OpenAI, DeepSeek, …), with an offline fallback that needs no API key.

Reported revenue is **discounted order value**, not profit or revenue after refunds. The three CSVs in `data/` are the unchanged source files.

## The live report

Every push to `main` runs `.github/workflows/pages.yml`, which builds the static report offline and deploys it to GitHub Pages. The page is the fastest way to see the results: the revenue reconciliation, return-rate breakdown, outlier-corrected trend, both charts, the business narrative, and the SQL report outputs.

To enable it on a fresh clone: push to `main`, then set **Settings → Pages → Build and deployment → Source: GitHub Actions**. The workflow needs no API key.

## Run it locally

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run capstone run-all --offline --reset-db
```

That one command seeds the database, runs the analysis and charts, generates the offline narrative, and renders the site to `pages/index.html` (open it in a browser — no server needed). Use `--online` instead of `--offline` to call the configured LLM provider.

To run each layer on its own:

```bash
uv run capstone db reset --yes   # run schema.sql then seed_data.sql in SQLite
uv run capstone reports          # run the nine SQL reports (Part 1)
uv run capstone analyze          # clean, reconcile, analyse; write narrator/findings.json (Part 2)
uv run capstone charts           # write both PNGs to visualizations/ (Part 2)
uv run capstone narrate          # offline narrative; add --online to call the LLM provider (Part 3)
uv run capstone render           # build the static site in pages/
```

The required standalone scripts also run directly and read the CSVs without the database:

```bash
uv run python analysis/clean_and_eda.py
uv run python analysis/visualize.py
uv run python narrator/generate_narrative.py --offline
```

## What each part delivers

### Part 1 — SQL relational layer & reporting (`sql/`)

- `schema.sql` — `customers`, `products`, `orders` with correct types, `NOT NULL`, `DEFAULT`, primary keys and foreign keys. `discount_pct` and `rating` stay nullable.
- `seed_data.sql` — re-runnable insert script generated from the unchanged CSVs (45 / 16 / 180 rows). Blank discount and rating cells load as `NULL`.
- `reports.sql` — the nine reports (a–i) on the raw data, each with its exact SQLite output recorded as a comment above the query. Discounts are divided by `100.0` to avoid integer division.

### Part 2 — Python wrangling & EDA (`analysis/`)

`clean_and_eda.py` reads the raw CSVs and owns all cleaning, reconciliation, statistics and the findings export:

- standardises `payment_method` casing (7 raw values → 3),
- drops the 5 duplicate orders on the natural key,
- fills missing discount with 0 and missing rating with the median,
- merges the tables and reconciles the total against Part 1,
- flags quantity outliers with the IQR rule (flagged, not dropped),
- tests the COD return hypothesis, segments return rate by payment × city tier, builds the correlation matrix, and computes the outlier-corrected monthly trend.

`visualize.py` owns the two charts: the return-rate bar chart and the outlier-corrected monthly revenue line chart, saved to `visualizations/`.

**Key results:** raw order value ₹99,860.20 (180 orders) reconciles to ₹97,358.30 (175 unique orders); the ₹2,501.90 difference is fully explained by the five duplicates. COD returns at 44.4% (vs UPI 18.9%, Card 14.7%), peaking at 54.5% for COD in Tier-2 cities. All measured correlations are negligible. January's apparent lead is driven by two bulk orders; March is the true peak at ₹20,318.90 once they are excluded for the trend.

### Part 3 — GenAI insight narrator (`narrator/`)

`generate_narrative.py` builds its prompt from `findings.json` (never hardcoded) and:

- calls any OpenAI-compatible provider with a Situation–Complication–Resolution system instruction, `temperature=0`, `max_tokens=2048`, and a 30 s timeout, wrapped in try/except that returns a dict,
- requests JSON-mode structured output and validates the response against a Pydantic `ScrNarrative` schema before rendering,
- falls back to a template-based narrative that runs with no API key or network,
- runs a numeric-accuracy check confirming five key figures appear in the narrative.

`findings.json` is written by code (Part 2), and its shape is validated with Pydantic. `sample_output.txt` holds the narrative; configure a provider (below) and run without `--offline` to overwrite it with a validated live response.

#### Provider configuration

The narrator uses the OpenAI-compatible Chat Completions API, so any provider that speaks that format works by pointing `LLM_BASE_URL` at its endpoint. Configuration is centralized in `common/config.py`, which loads a `.env` file from the project root on import. Copy `.env.example` to `.env` and fill in:

| Variable | Purpose | Default |
| --- | --- | --- |
| `LLM_PROVIDER` | Label for attribution/logging only | `openai` |
| `LLM_API_KEY` | API key for the provider; blank → offline fallback | *(unset)* |
| `LLM_BASE_URL` | OpenAI-compatible endpoint; blank → OpenAI default | *(unset)* |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |

OpenAI example:

```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

DeepSeek example (OpenAI-compatible):

```bash
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

Values already set in the shell/CI environment take precedence over `.env`. When `LLM_API_KEY` is unset, or the call fails or returns inaccurate numbers, the pipeline uses the verified offline narrative.

## Layout

```
.
├── sql/           schema.sql · seed_data.sql · reports.sql
├── data/          customers.csv · products.csv · orders.csv   (unchanged source)
├── analysis/      clean_and_eda.py · visualize.py
├── visualizations/  return_rate_by_payment.png · monthly_revenue_trend.png
├── narrator/      findings.json · generate_narrative.py · sample_output.txt
├── reporting/     render.py · templates · static        (builds pages/)
├── common/        config · database · schemas            (coordination only)
└── cli.py         command runner
```

`cli.py`, `common/` and `reporting/` only coordinate execution, connections, validation and presentation — no layer reports a number it did not compute or receive from the layer before it.
