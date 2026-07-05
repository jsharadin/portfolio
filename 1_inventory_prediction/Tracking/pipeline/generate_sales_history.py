"""
Generate a SIMULATED weekly sales history for the Chilk portfolio project.

Chilk's real recorded sales history was short and sparse (the company sold
mainly at LA farmers markets for a few months in early 2022). To make the
forecasting side of this project demonstrable, this script simulates 72 weeks
of plausible weekly sales (Jan 2021 - May 2022) calibrated to the real
business:

- Channels are the real Chilk channels (farmers markets, Duffl delivery,
  campus partners, caravan, LokelsOnly, Uber Eats).
- Flavors are the real product line (Strawberry, Chocolate, Cinnamon, Banana,
  Thai Tea, Taro, Coffee).
- Volumes are anchored to real observations, e.g. ~26-41 bottles/week sold at
  LA farmers markets in Feb 2022, growing over time.
- Seasonality follows the academic calendar (customers were college students):
  dips in winter break and summer, peaks in spring quarter.
- Retail price: $4.99/bottle (from the real Unit Economics workbook).

ALL OUTPUT IS CLEARLY SIMULATED and reproducible (fixed random seed).

Usage:  python generate_sales_history.py
Output: ../data/sales_history.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
PRICE = 4.99
START = "2021-01-04"  # first Monday of 2021
WEEKS = 72

# channel -> (base weekly volume at maturity, week business went live in channel)
CHANNELS = {
    "LA Farmers Markets": (38, 0),
    "SB Farmers Markets": (16, 20),
    "Berkeley Farmers Market": (12, 36),
    "UCLA Duffl": (22, 10),
    "UCSB Duffl": (9, 30),
    "Campus Partners": (14, 6),
    "LA Caravan": (10, 44),
    "LokelsOnly": (4, 0),
    "Uber Eats": (6, 26),
}

# flavor -> long-run share of demand (sums to 1.0)
FLAVORS = {
    "Strawberry": 0.24,
    "Chocolate": 0.22,
    "Cinnamon": 0.17,
    "Banana": 0.13,
    "Thai Tea": 0.14,
    "Taro": 0.06,
    "Coffee": 0.04,
}

# flavor launch week (Taro/Coffee were late additions to the menu)
FLAVOR_LAUNCH = {"Taro": 40, "Coffee": 52}


def academic_seasonality(week_dates):
    """Multiplier from the academic calendar: low in breaks, high in spring."""
    m = np.ones(len(week_dates))
    for i, d in enumerate(week_dates):
        if d.month in (12, 1) and (d.month == 12 and d.day > 10 or d.month == 1 and d.day < 10):
            m[i] = 0.35  # winter break
        elif d.month in (7, 8):
            m[i] = 0.55  # summer
        elif d.month in (4, 5):
            m[i] = 1.25  # spring quarter peak
        elif d.month == 9 and d.day < 20:
            m[i] = 0.75  # move-in
    return m


def main():
    rng = np.random.default_rng(SEED)
    dates = pd.date_range(START, periods=WEEKS, freq="W-MON")
    season = academic_seasonality(dates)
    # overall ramp: startup growth saturating over ~60 weeks
    ramp = 1 / (1 + np.exp(-(np.arange(WEEKS) - 28) / 12))

    rows = []
    for ch, (base, live_week) in CHANNELS.items():
        for w, date in enumerate(dates):
            if w < live_week:
                continue
            ch_ramp = min(1.0, (w - live_week + 1) / 8)  # channel spin-up
            lam = base * ramp[w] * ch_ramp * season[w]
            total = rng.poisson(max(lam, 0.05))
            if total == 0:
                continue
            # split bottles across flavors available that week
            avail = {f: s for f, s in FLAVORS.items() if w >= FLAVOR_LAUNCH.get(f, 0)}
            p = np.array(list(avail.values()))
            split = rng.multinomial(total, p / p.sum())
            for flavor, sold in zip(avail, split):
                if sold == 0:
                    continue
                forecasted = max(0, int(round(sold * rng.normal(1.15, 0.25))))
                delivered = max(sold, forecasted)
                rows.append({
                    "week_start": date.date(),
                    "channel": ch,
                    "flavor": flavor,
                    "forecasted": forecasted,
                    "delivered": delivered,
                    "sold": int(sold),
                    "unsold": delivered - int(sold),
                    "revenue": round(sold * PRICE, 2),
                })

    df = pd.DataFrame(rows).sort_values(["week_start", "channel", "flavor"])
    out = Path(__file__).resolve().parent.parent / "data" / "sales_history.csv"
    df.to_csv(out, index=False)
    print(f"wrote {len(df)} rows -> {out}")
    print(df.groupby(df.week_start.map(lambda d: d.year))[["sold", "revenue"]].sum())


if __name__ == "__main__":
    main()
