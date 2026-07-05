# US Macroeconomic Indicators — SQL + Python

A small portfolio project that pulls eight macroeconomic time series from
[FRED](https://fred.stlouisfed.org/), loads them into a relational database,
and uses SQL (joins, aggregations, window functions) plus Python (pandas,
matplotlib) to produce a short set of analyses and charts.

The project is intentionally simple: the goal is to demonstrate a clean
SQL + Python workflow, not to model anything ambitious.

## Data

Eight series, downloaded from FRED as CSVs and committed to `data/`:

| Series ID | Description                          | Frequency |
|-----------|--------------------------------------|-----------|
| UNRATE    | Civilian unemployment rate           | Monthly   |
| CPIAUCSL  | Consumer Price Index (All Urban)     | Monthly   |
| FEDFUNDS  | Effective Federal Funds rate         | Monthly   |
| GDP       | Gross Domestic Product               | Quarterly |
| DGS10     | 10-Year Treasury yield               | Daily     |
| INDPRO    | Industrial Production index          | Monthly   |
| PAYEMS    | Total nonfarm payroll employment     | Monthly   |
| M2SL      | M2 money stock                       | Monthly   |

## Project layout

```
sql_practice/
├── data/                 raw CSVs from FRED
├── sql/
│   ├── schema.sql        table definitions + series metadata
│   └── queries.sql       guided tour of queries (basic → window functions)
├── outputs/              charts produced by analysis.py
├── analysis.py           end-to-end pipeline
├── macro.db              SQLite database (generated)
└── README.md
```

## Schema

Two tables. `series` holds metadata; `observations` is a long-format table
keyed by `(series_id, obs_date)`. Mixing frequencies in one table keeps the
joins simple — daily series can be averaged to a monthly grain at query time.

```sql
CREATE TABLE series (
    series_id  TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    frequency  TEXT NOT NULL,
    units      TEXT NOT NULL,
    source     TEXT NOT NULL DEFAULT 'FRED'
);

CREATE TABLE observations (
    series_id  TEXT NOT NULL,
    obs_date   DATE NOT NULL,
    value      REAL,
    PRIMARY KEY (series_id, obs_date),
    FOREIGN KEY (series_id) REFERENCES series(series_id)
);
```

## Running it

```bash
pip install pandas matplotlib
python analysis.py
```

That builds `macro.db`, prints a few summaries to the console, and writes
three plots to `outputs/`.

## What the SQL covers

`sql/queries.sql` is organized by difficulty:

1. **Inspection** — catalog, row counts, date ranges.
2. **Filtering + aggregation** — average unemployment by decade, high-unemployment months.
3. **Window functions** — CPI year-over-year inflation with `LAG(value, 12)`;
   12-month rolling averages.
4. **Multi-series joins** — monthly panel of unemployment, Fed Funds, and inflation.
5. **Sahm-style recession flag** — months where unemployment rose ≥ 0.5pp above its 12-month minimum.
6. **Term spread** — daily 10-year yield aggregated to monthly, joined to Fed Funds.

## Outputs

`analysis.py` produces three charts in `outputs/`:

- `unemployment_history.png` — UNRATE since 1948.
- `inflation_vs_fedfunds.png` — CPI YoY vs. the effective Fed Funds rate.
- `term_spread.png` — 10-year Treasury yield minus the Fed Funds rate
  (negative readings have historically preceded recessions).

## Running against SQL Server instead of SQLite

The project defaults to SQLite for portability. To run the same workflow
against SQL Server in Docker:

```bash
docker start sqlserver   # container with port 1433 exposed
```

Then in `analysis.py`, swap the SQLite connection for SQLAlchemy:

```python
from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://sa:Docker152!@localhost,1433/master"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)
```

A couple of SQLite-specific functions in `sql/queries.sql` need T-SQL
equivalents — `strftime('%Y', obs_date)` becomes `YEAR(obs_date)`, and
`DATE('now', '-5 years')` becomes `DATEADD(year, -5, GETDATE())`.

## Data source

All series come from the Federal Reserve Bank of St. Louis (FRED).
Download URL pattern:
`https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>`
