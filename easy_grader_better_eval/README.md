# 📝 Easy Grader → Better Evaluation?

## Overview

Group project replicating and extending prior research on whether **instructor leniency** drives **student evaluation of teaching (SET) scores**. We use **mixed-effects models** with **cluster-robust standard errors** to disentangle instructor effects from course-level confounders.

The full paper is in `final_paper.pdf`.

## Features

- **Replication** of a prior published model on the same evaluation dataset.
- **Mixed-effects modeling** (`lme4`) to handle the nested structure of evaluations within courses and instructors.
- **Cluster-robust inference** via `sandwich` and `clubSandwich` to correct for within-cluster correlation.
- **Feature selection**, assumption checks, and correlation diagnostics.
- **Publication-quality regression tables** via `stargazer`.

## Tech Stack

- **R** (4.x)
- **lme4** — mixed-effects models
- **sandwich**, **lmtest**, **clubSandwich** — robust / cluster-robust SE
- **dplyr** — data wrangling
- **ggplot2**, **corrplot** — visualization
- **stargazer** — regression tables

## Project Workflow

1. Form hypothesis
2. Exploratory data analysis
3. Data cleaning
4. Feature selection
5. Assumptions and limitations
6. Conclusion

## Contents

- `code.Rmd` — full RMarkdown source (cleaning → EDA → modeling → diagnostics).
- `final_paper.pdf` — final write-up.

## How to Use

1. **Clone the repo:**
   ```bash
   git clone https://github.com/jsharadin/portfolio.git
   cd portfolio/easy_grader_better_eval
   ```

2. **Install R dependencies:**
   ```r
   install.packages(c("lme4", "sandwich", "lmtest", "dplyr", "ggplot2",
                      "clubSandwich", "stargazer", "corrplot"))
   ```

3. **Update the data path.** `code.Rmd` references a local `replication.csv`. Change the path near the top of the file to point to your copy.

4. **Knit the RMarkdown** in RStudio (or `rmarkdown::render("code.Rmd")`) to reproduce the analysis.
