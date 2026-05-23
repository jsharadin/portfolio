# ⚖️ Inequality, Crime, & the Legacy of Slavery

## Overview

Independent research project (UC Berkeley) estimating the **causal effect of historical land inequality on modern county-level crime rates** in the United States. Because inequality is endogenous to crime, we use **Instrumental Variables (2SLS and IV-GMM)** with the **1860 county-level slave share** as a historical instrument for present-day inequality — building on the literature that traces persistent economic disparities to the legacy of slavery.

The full write-up is in `inequality_crime_slavery_paper.pdf`.

## Features

- **2SLS** and **IV-GMM** estimation of the inequality → crime relationship.
- **OLS benchmarks** with successive control sets (0, 1, 2, 3 layers of demographic/economic controls) for transparency.
- **Historical instrument**: 1860 slave-share data merged with modern county-level economic and crime panels.
- **Bootstrap reweighting** (population-weighted) to assess robustness across alternative weighting schemes.
- **Multicollinearity diagnostics** (VIF) and feature standardization.

## Tech Stack

- **Python** (tested on 3.9)
- **pandas**, **NumPy**, **pickle** — data wrangling
- **statsmodels** — OLS, diagnostics
- **linearmodels** — `IV2SLS`, `IVGMM`
- **scikit-learn** — StandardScaler, KMeans
- **seaborn**, **matplotlib** — visualization

## Repository Structure

```
inequality_crime_research/
├── inequality_crime_slavery_paper.pdf   # Final paper
└── notebooks/
    ├── preprocessing.ipynb        # Build the merged county-year panel
    ├── eda.ipynb                  # Exploratory analysis
    ├── ols_reg.ipynb              # OLS benchmarks
    ├── iv_reg.ipynb               # First-stage + 2SLS
    ├── iv_reg_evolve.ipynb        # IV with evolving specifications
    ├── iv-gmm_regressions.ipynb   # IV-GMM with multiple instruments
    └── reweight_bootstrap.ipynb   # Bootstrap reweighting robustness
```

## How to Use

1. **Clone the repo:**
   ```bash
   git clone https://github.com/jsharadin/portfolio.git
   cd portfolio/inequality_crime_research
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Obtain the data.** The raw `.dta` files and intermediate `.pkl` panels are not included due to size and licensing. The paper documents the source datasets (Census, FBI UCR, 1860 historical census).

4. **Run the notebooks** in the order listed above.

## Key Result

Read `inequality_crime_slavery_paper.pdf` for the full discussion, identifying assumptions, and limitations.
