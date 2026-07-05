"""
Demand forecast for the Chilk inventory planner.

Reads data/sales_history.csv, aggregates weekly demand per flavor, and
produces an 8-week forward forecast per flavor using Holt's linear
exponential smoothing (level + damped trend), plus a safety-stock
recommendation:

    safety_stock = z * sigma_demand * sqrt(lead_time_weeks)

with z = 1.65 (~95% service level) and a 3-week ingredient lead time
(all key Chilk ingredients had a 21-day lead time per the original tracker).

Usage:  python forecast_demand.py
Output: ../data/forecast.csv  (per flavor: 8 weekly forecasts + safety stock)
        ../data/weekly_demand.csv (historical weekly totals per flavor)
"""

from pathlib import Path
import numpy as np
import pandas as pd

HORIZON = 8          # weeks ahead
ALPHA, BETA = 0.35, 0.15   # smoothing params (level, trend)
PHI = 0.9            # trend damping
Z = 1.65             # ~95% service level
LEAD_TIME_WEEKS = 3


def holt_damped(y, alpha=ALPHA, beta=BETA, phi=PHI, horizon=HORIZON):
    level, trend = y[0], y[1] - y[0] if len(y) > 1 else 0.0
    for t in range(1, len(y)):
        prev_level = level
        level = alpha * y[t] + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - prev_level) + (1 - beta) * phi * trend
    return [max(0.0, level + sum(phi ** i for i in range(1, h + 1)) * trend)
            for h in range(1, horizon + 1)]


def main():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    sales = pd.read_csv(data_dir / "sales_history.csv", parse_dates=["week_start"])

    weekly = (sales.groupby(["week_start", "flavor"])["sold"].sum()
              .unstack(fill_value=0).sort_index())
    weekly.to_csv(data_dir / "weekly_demand.csv")

    last_week = weekly.index.max()
    future_weeks = pd.date_range(last_week + pd.Timedelta(weeks=1), periods=HORIZON, freq="W-MON")

    rows = []
    for flavor in weekly.columns:
        y = weekly[flavor].values.astype(float)
        y_active = y[np.argmax(y > 0):]          # trim pre-launch zeros
        fc = holt_damped(y_active)
        sigma = y_active[-12:].std(ddof=1) if len(y_active) >= 4 else y_active.std()
        ss = Z * sigma * np.sqrt(LEAD_TIME_WEEKS)
        for wk, f in zip(future_weeks, fc):
            rows.append({"week_start": wk.date(), "flavor": flavor,
                         "forecast_bottles": round(f, 1)})
        rows_ss = {"flavor": flavor,
                   "avg_last_4wk": round(y_active[-4:].mean(), 1),
                   "forecast_next_4wk": round(sum(fc[:4]), 1),
                   "safety_stock": int(np.ceil(ss))}
        rows.append({"week_start": "SUMMARY", **rows_ss})

    out = pd.DataFrame(rows)
    out.to_csv(data_dir / "forecast.csv", index=False)
    print(out[out.week_start == "SUMMARY"][["flavor", "avg_last_4wk", "forecast_next_4wk", "safety_stock"]])

    # ---- backtest: train on all but last 8 weeks, predict the held-out 8 ----
    bt = []
    for flavor in weekly.columns:
        y = weekly[flavor].values.astype(float)
        y_active = y[np.argmax(y > 0):]
        if len(y_active) < 16:
            continue
        train, test = y_active[:-HORIZON], y_active[-HORIZON:]
        pred = holt_damped(train)
        bt.append({"flavor": flavor,
                   "actual_8wk": int(test.sum()),
                   "predicted_8wk": round(sum(pred), 1)})
    pd.DataFrame(bt).to_csv(data_dir / "backtest.csv", index=False)
    print("\nbacktest written:", bt)


if __name__ == "__main__":
    main()
