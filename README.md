# Mamaearth Returns and Growth Intelligence Pipeline

This project answers where returns concentrate and how five duplicate orders and two unusually large orders affect the revenue story. SQLite reports use the **raw** CSVs. Pandas independently reads the same CSVs, removes duplicate orders, flags outliers and writes verified findings. Gemini or an offline template converts those findings into a business narrative. Jinja renders a static report for GitHub Pages. The reported revenue is discounted order value, not profit or revenue after refunds.

The three source CSVs in `data/` are unchanged from the assignment. Python 3.11+ and [uv](https://docs.astral.sh/uv/) are required.

## Install and run

```bash
uv sync --locked
uv run capstone db reset --yes
uv run capstone reports
uv run capstone analyze
uv run capstone charts
uv run capstone narrate
uv run capstone render
```

The `db reset` command runs `sql/schema.sql` then `sql/seed_data.sql` in SQLite. `reports` executes `sql/reports.sql`, whose comments record each query's actual SQLite output. Its loyalty-tier `ALTER TABLE` is repeatable through the command runner. To execute manually in the SQLite CLI against a fresh database: `.read sql/schema.sql`, `.read sql/seed_data.sql`, `.read sql/reports.sql` in that order. The SQL layer has 45 customers, 16 products and 180 orders; 15 blank ratings and blank discounts are loaded as NULL.

The required standalone scripts work too: `uv run python analysis/clean_and_eda.py` then `uv run python analysis/visualize.py`. They read the CSVs directly and can run before SQL. Analysis generates `narrator/findings.json`; charts generate both PNGs under `visualizations/`. `uv run python narrator/generate_narrative.py --offline` runs without a key or network. Set `GEMINI_API_KEY` in the environment and run `uv run python narrator/generate_narrative.py` to try Gemini. A successful and numerically validated Gemini response overwrites `narrator/sample_output.txt`; review and commit that actual sample before submission. The included sample is explicitly identified as an offline baseline until a live response is generated.

For the complete build: `uv run capstone run-all --offline --reset-db` (or `--online` to attempt Gemini). `--reset-db` replaces the local database; without it, `run-all` expects a seeded database. `db clear` preserves tables, while `db drop` removes the SQLite file. Both require `--yes`. The static site is written to `dist/index.html` and `dist/assets/`; open the HTML file in a browser. No web server is needed.

## Reconciliation and results

Raw order value is INR 99,860.20 across 180 orders. Removing five repeat submissions worth INR 2,501.90 yields INR 97,358.30 across 175 unique orders. COD returns are 44.4%, compared with UPI 18.9% and Card 14.7%. COD in Tier-2 cities reaches 54.5%. All six measured correlations are negligible. January looks highest with the two flagged bulk orders; excluding them only for the trend makes March the highest at INR 20,318.90. The main cleaned revenue total retains both bulk orders.

`analysis/clean_and_eda.py` owns all cleaning, reconciliation, statistical analysis, checks and findings export. `analysis/visualize.py` owns both charts. `narrator/generate_narrative.py` owns the Gemini and offline narratives and five numeric checks. `pipelines/run.py`, `common/` and `reporting/` only coordinate execution, connections, validated structures and presentation. Native Python annotations express types; Pydantic checks the shape of findings.

## GitHub Pages

Push this repository to GitHub with `main` as the source branch, then enable **Settings → Pages → Build and deployment → GitHub Actions**. The workflow builds the static report offline and deploys `dist/` on each push to `main`, or when run manually. The repository link is the capstone submission; the Pages URL is a supplementary view. The workflow does not need a Gemini key and cannot substitute for the requested saved live Gemini sample.
