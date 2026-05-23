# Jacob Sharadin — Portfolio

Hi! I'm Jacob, a masters student at Universitat Autònoma de Barcelona working at the intersection of **economics, statistics, and machine learning**. This repository collects a curated set of my research and case-study projects — primarily applied econometrics, causal inference, and quantitative finance.

[![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![R](https://img.shields.io/badge/R-4.x-276DC3?logo=r&logoColor=white)](https://www.r-project.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)](https://jupyter.org/)
[![statsmodels](https://img.shields.io/badge/statsmodels-4051B5)](https://www.statsmodels.org/)
[![scikit--learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)

---

## 📂 Projects

### 📈 [Cross-Impact Order Flow Imbalance Analysis](cross_impact_OFI_analysis)
High-frequency trading research computing **multi-level Order Flow Imbalance (OFI)** metrics from limit-order-book data, reducing them via PCA, and analyzing cross-stock price-impact dynamics across ~6.5M rows of message-book data.
**Stack:** Python, pandas, NumPy, scikit-learn (PCA), statsmodels, Databento.

### 🏥 [WHO Health Disparities Analysis](WHO_analysis)
A digital-humanities project examining disparities in healthcare access and quality through socio-economic status, race, and gender — combining WHO Global Health Observatory data with critical theory frameworks (CRT, CDT, feminist theory).
**Stack:** Python, pandas, data visualization, qualitative analysis.

### 🎓 [Income Segregation & Mobility Across U.S. Colleges](income_segregation_%26_%20mobility_across_colleges)
ECON 148 final project analyzing how university enrollment composition relates to intergenerational mobility, using the **Chetty et al. Mobility Report Cards** dataset.
**Stack:** Python, pandas, statsmodels, seaborn, SciPy.

### ⚖️ [Inequality, Crime, & the Legacy of Slavery](inequality_crime_research)
ECON 191 research applying **Instrumental Variables (2SLS / IV-GMM)** to estimate the causal effect of income inequality on county-level crime rates in the U.S., using historical (1860) slave-share data as an instrument.
**Stack:** Python, statsmodels, linearmodels (IV2SLS, IVGMM), bootstrap reweighting.

### 📝 [Easy Grader → Better Evaluation? A Multilevel Look at Teaching Evals](easy_grader_better_eval)
STAT 151 group project using **mixed-effects models with cluster-robust SEs** to assess whether instructor leniency drives student evaluation scores, replicating and extending a prior study.
**Stack:** R, `lme4`, `sandwich`, `clubSandwich`, `lmtest`, `stargazer`.

---

## 🧠 Skills Reflected in This Work

- **Econometrics / Causal Inference:** OLS, 2SLS, IV-GMM, mixed-effects models, cluster-robust inference, bootstrap reweighting.
- **Quantitative Finance:** order-book microstructure, OFI, PCA-based factor reduction, high-frequency data pipelines.
- **Data Engineering:** ingesting `.dbn.zst` market data, cleaning multi-million-row panels, building reproducible notebooks.
- **Languages & Tools:** Python, R, SQL, Jupyter, RMarkdown, Git, LaTeX.

---

## 📫 Contact

- **Email:** jsharadin@berkeley.edu
- **GitHub:** [@jsharadin](https://github.com/jsharadin)

> Each project folder has its own README with a project overview, dependencies, and instructions to reproduce. Click into any project above for details.
