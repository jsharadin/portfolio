# 🎓 Income Segregation & Mobility Across U.S. Colleges

## Overview

Final project for **ECON 148** at UC Berkeley. This analysis explores the relationship between the **income composition of U.S. colleges** and the **intergenerational economic mobility** they produce, using the **Mobility Report Cards** dataset (Chetty, Friedman, Saez, Turner, Yagan).

The central question: *do colleges that enroll more low-income students actually move them up the income distribution — and how does this vary by tier and institution type?*

## Features

- **Cleaning + EDA** on the Chetty et al. Mobility Report Cards (`mrc_table_2.csv`).
- **Descriptive statistics** on income-segregation across institution tiers (Ivy+, elite, selective, etc.).
- **Mobility-rate visualizations** (access × success rates) by college type.
- **Statistical modeling** of mobility outcomes against student-body composition.

## Tech Stack

- **Python** (3.10+)
- **pandas**, **NumPy**, **SciPy** — data wrangling & stats
- **statsmodels** — regression analysis
- **seaborn**, **matplotlib** — visualization
- **Jupyter Notebook**

## Repository Contents

- `code.ipynb` — full analysis notebook (cleaning → EDA → modeling).
- `presentation.pdf` — final slide deck summarizing findings.

## How to Use

1. **Clone the repo:**
   ```bash
   git clone https://github.com/jsharadin/portfolio.git
   cd "portfolio/research_and_case_studies/income_segregation_&_ mobility_across_colleges"
   ```

2. **Install dependencies:**
   ```bash
   pip install pandas numpy scipy statsmodels seaborn matplotlib jupyter
   ```

3. **Obtain the data.** Download `mrc_table_2.csv` from the [Opportunity Insights Mobility Report Cards page](https://opportunityinsights.org/data/) and place it in this folder.

4. **Run the notebook:**
   ```bash
   jupyter notebook code.ipynb
   ```

## Data Source

- **Chetty, R., Friedman, J. N., Saez, E., Turner, N., & Yagan, D. (2017).** *Mobility Report Cards: The Role of Colleges in Intergenerational Mobility.* NBER Working Paper.
