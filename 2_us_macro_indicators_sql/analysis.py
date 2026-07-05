"""
analysis.py
US Macroeconomic Indicators — load FRED CSVs into SQLite, run a set of
SQL analyses, and produce summary charts.

Run from the project root:

    python analysis.py

Outputs:
    macro.db                              SQLite database with two tables
    outputs/unemployment_history.png      Plot
    outputs/inflation_vs_fedfunds.png     Plot
    outputs/term_spread.png               Plot
"""

from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "outputs"
DB_PATH = ROOT / "macro.db"

SERIES_FILES = {
    "UNRATE":   "UNRATE.csv",
    "CPIAUCSL": "CPIAUCSL.csv",
    "FEDFUNDS": "FEDFUNDS.csv",
    "GDP":      "GDP.csv",
    "DGS10":    "DGS10.csv",
    "INDPRO":   "INDPRO.csv",
    "PAYEMS":   "PAYEMS.csv",
    "M2SL":     "M2SL.csv",
}


def build_database() -> sqlite3.Connection:
    """Create the schema and load every CSV into the observations table."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript((SQL_DIR / "schema.sql").read_text())

    frames = []
    for series_id, fname in SERIES_FILES.items():
        df = pd.read_csv(DATA_DIR / fname)
        df.columns = ["obs_date", "value"]
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df.insert(0, "series_id", series_id)
        frames.append(df)

    all_obs = pd.concat(frames, ignore_index=True)
    all_obs.to_sql("observations", conn, if_exists="append", index=False)
    conn.commit()
    return conn


def print_summary(conn: sqlite3.Connection) -> None:
    """Quick sanity check — counts and date ranges per series."""
    summary = pd.read_sql(
        """
        SELECT s.series_id, s.name, s.frequency,
               COUNT(o.value) AS n_obs,
               MIN(o.obs_date) AS first_obs,
               MAX(o.obs_date) AS last_obs
        FROM series s
        LEFT JOIN observations o USING (series_id)
        GROUP BY s.series_id, s.name, s.frequency
        ORDER BY s.series_id
        """,
        conn,
    )
    print("\n=== Loaded series ===")
    print(summary.to_string(index=False))


def unemployment_by_decade(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql(
        """
        SELECT (CAST(strftime('%Y', obs_date) AS INTEGER) / 10) * 10 AS decade,
               ROUND(AVG(value), 2) AS avg_unrate,
               ROUND(MIN(value), 2) AS min_unrate,
               ROUND(MAX(value), 2) AS max_unrate
        FROM observations
        WHERE series_id = 'UNRATE'
        GROUP BY decade
        ORDER BY decade
        """,
        conn,
    )


def inflation_panel(conn: sqlite3.Connection) -> pd.DataFrame:
    """Monthly panel of YoY inflation alongside the Fed Funds rate."""
    return pd.read_sql(
        """
        WITH cpi_yoy AS (
            SELECT obs_date,
                   100.0 * (value / LAG(value, 12) OVER (ORDER BY obs_date) - 1)
                       AS inflation
            FROM observations
            WHERE series_id = 'CPIAUCSL'
        )
        SELECT c.obs_date,
               c.inflation,
               f.value AS fed_funds
        FROM cpi_yoy c
        JOIN observations f
          ON f.series_id = 'FEDFUNDS' AND f.obs_date = c.obs_date
        WHERE c.inflation IS NOT NULL
        ORDER BY c.obs_date
        """,
        conn,
        parse_dates=["obs_date"],
    )


def term_spread(conn: sqlite3.Connection) -> pd.DataFrame:
    """Monthly 10-year Treasury yield minus Fed Funds rate."""
    return pd.read_sql(
        """
        WITH dgs10_monthly AS (
            SELECT DATE(strftime('%Y-%m-01', obs_date)) AS month,
                   AVG(value) AS dgs10
            FROM observations
            WHERE series_id = 'DGS10'
            GROUP BY DATE(strftime('%Y-%m-01', obs_date))
        )
        SELECT d.month AS obs_date,
               d.dgs10,
               f.value AS fed_funds,
               d.dgs10 - f.value AS spread
        FROM dgs10_monthly d
        JOIN observations f
          ON f.series_id = 'FEDFUNDS' AND f.obs_date = d.month
        ORDER BY d.month
        """,
        conn,
        parse_dates=["obs_date"],
    )


def make_plots(conn: sqlite3.Connection) -> None:
    OUT_DIR.mkdir(exist_ok=True)

    # Unemployment history
    unrate = pd.read_sql(
        "SELECT obs_date, value FROM observations WHERE series_id='UNRATE' ORDER BY obs_date",
        conn,
        parse_dates=["obs_date"],
    )
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(unrate["obs_date"], unrate["value"], linewidth=1)
    ax.set_title("US Unemployment Rate, 1948 – Present")
    ax.set_ylabel("Percent")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "unemployment_history.png", dpi=120)
    plt.close(fig)

    # Inflation vs Fed Funds
    panel = inflation_panel(conn)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(panel["obs_date"], panel["inflation"], label="CPI YoY (%)", linewidth=1)
    ax.plot(panel["obs_date"], panel["fed_funds"], label="Fed Funds (%)", linewidth=1)
    ax.set_title("Inflation vs. the Federal Funds Rate")
    ax.set_ylabel("Percent")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "inflation_vs_fedfunds.png", dpi=120)
    plt.close(fig)

    # Term spread
    spread = term_spread(conn)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(spread["obs_date"], spread["spread"], linewidth=1)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Term Spread: 10-Year Treasury minus Fed Funds")
    ax.set_ylabel("Percentage points")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "term_spread.png", dpi=120)
    plt.close(fig)


def main() -> None:
    conn = build_database()
    print_summary(conn)

    print("\n=== Average unemployment by decade ===")
    print(unemployment_by_decade(conn).to_string(index=False))

    print("\n=== Inflation panel (last 12 rows) ===")
    print(inflation_panel(conn).tail(12).to_string(index=False))

    print("\n=== Term spread (last 12 rows) ===")
    print(term_spread(conn).tail(12).to_string(index=False))

    make_plots(conn)
    conn.close()
    print(f"\nWrote database to {DB_PATH.name} and plots to {OUT_DIR.name}/")


if __name__ == "__main__":
    main()
