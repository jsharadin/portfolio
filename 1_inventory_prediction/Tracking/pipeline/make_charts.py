"""Render README chart images from the data/ folder -> charts/*.png"""

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)

BROWN, TAN, CREAM = "#5B3A29", "#B08968", "#FFF6E9"
plt.rcParams.update({"font.family": "sans-serif", "axes.edgecolor": "#C9B79C",
                     "axes.labelcolor": BROWN, "text.color": BROWN,
                     "xtick.color": BROWN, "ytick.color": BROWN, "figure.dpi": 150})

weekly = pd.read_csv(DATA / "weekly_demand.csv", parse_dates=["week_start"], index_col=0)
fc = pd.read_csv(DATA / "forecast.csv")
fc = fc[fc.week_start != "SUMMARY"].copy()
fc["week_start"] = pd.to_datetime(fc["week_start"])
sales = pd.read_csv(DATA / "sales_history.csv", parse_dates=["week_start"])

# 1. weekly sales + forecast
total = weekly.sum(axis=1)
fc_total = fc.groupby("week_start")["forecast_bottles"].sum()
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.plot(total.index, total.values, color=BROWN, lw=1.8, label="Actual (simulated history)")
ax.plot([total.index[-1], *fc_total.index], [total.iloc[-1], *fc_total.values],
        color=TAN, lw=2, ls="--", label="8-week forecast")
ax.fill_between(total.index, total.values, color=BROWN, alpha=0.08)
ax.set_title("Chilk Weekly Bottles Sold — History & Forecast", fontsize=12, fontweight="bold")
ax.set_ylabel("Bottles / week"); ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "weekly_sales_forecast.png", facecolor="white"); plt.close(fig)

# 2. revenue by channel
ch = sales.groupby("channel")["revenue"].sum().sort_values()
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.barh(ch.index, ch.values, color=BROWN)
ax.set_title("Revenue by Channel (72 weeks)", fontsize=12, fontweight="bold")
ax.set_xlabel("Revenue ($)"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "revenue_by_channel.png", facecolor="white"); plt.close(fig)

# 3. flavor mix
fl = sales.groupby("flavor")["sold"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.bar(fl.index, fl.values, color=[BROWN, TAN] * 4)
ax.set_title("Bottles Sold by Flavor", fontsize=12, fontweight="bold")
ax.set_ylabel("Bottles"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "flavor_mix.png", facecolor="white"); plt.close(fig)

print("charts written to", OUT)
