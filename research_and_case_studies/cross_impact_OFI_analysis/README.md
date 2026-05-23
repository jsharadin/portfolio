# 📈 Cross-Impact Order Flow Imbalance (OFI) Analysis

## Overview

This project investigates **Order Flow Imbalance (OFI)** as a microstructure signal for short-horizon price moves in high-frequency equity markets. Working from raw limit-order-book message data (Databento `.dbn.zst` format), the pipeline computes **multi-level OFI metrics**, reduces them with **PCA**, and analyzes both contemporaneous and **cross-stock** price-impact relationships across ~6.5M rows of market data.

The project was completed as a feature-analysis work trial.

## Features

- **End-to-end HFT pipeline** — raw message-book ingest → cleaning → multi-level OFI computation → analysis.
- **Multi-level OFI** — separately captures imbalances at each of the top *N* book levels rather than collapsing to a single signal.
- **PCA dimensionality reduction** — extracts the dominant common factor across book levels.
- **Cross-impact analysis** — regresses a stock's returns on its own and *other* stocks' OFI to study spillover effects.
- **Reproducible notebooks** organized by stage (data load → preprocessing → computation/analysis).

## Tech Stack

- **Python** (3.10+)
- **pandas**, **NumPy** — data wrangling
- **Databento** + **zstandard** — market-data ingest (`.dbn.zst`)
- **scikit-learn** — PCA, StandardScaler
- **statsmodels** — regression / inference
- **matplotlib**, **seaborn** — visualization

## Repository Structure

```
cross_impact_OFI_analysis/
├── data/
│   └── data_load.ipynb         # Ingest .dbn.zst → merged DataFrame → df.pkl
├── notebooks/
│   ├── preprocessing.ipynb     # Clean + feature engineer
│   └── ofi_computation_and_analysis.ipynb   # OFI, PCA, regressions
├── scripts/
│   └── batch_job.py            # Batch-mode equivalent of the notebooks
├── results/                    # Generated plots & summaries
└── requirements.txt
```

## How to Use

1. **Clone the repo:**
   ```bash
   git clone https://github.com/jsharadin/portfolio.git
   cd portfolio/research_and_case_studies/cross_impact_OFI_analysis
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Obtain the data.** The raw `.dbn.zst` files are not included due to GitHub's file-size limits. Pull them from [Databento](https://databento.com/) (or any equivalent source) and place them in the `data/` folder.

4. **Run the pipeline in order:**
   - `data/data_load.ipynb` → produces `df.pkl`
   - `notebooks/preprocessing.ipynb`
   - `notebooks/ofi_computation_and_analysis.ipynb`

5. **View results** in the `results/` folder.

## Future Work

- Extend cross-impact analysis to a larger universe of tickers.
- Compare PCA-OFI with alternative book-pressure features (queue imbalance, microprice).
- Backtest a simple market-making / liquidity-taking signal driven by the OFI factor.
