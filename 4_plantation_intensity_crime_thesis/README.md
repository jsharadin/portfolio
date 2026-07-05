# Plantation Intensity and Violent Crime in U.S. Counties, 1990-2016

Redesigned version of the ECON 191 thesis (reduced-form persistence design,
replacing the slavery-as-IV-for-inequality design).

- `paper.pdf` / `paper.tex` — the paper (19 pp.)
- `code/build_dataset.py` — links NHGIS 1860 county census to ICPSR UCR
  county offenses-known files (1990/2000/2010/2016); 1,071 counties.
  Fixes the county-code merge bug in the original thesis (ICPSR county
  codes repeat across states).
- `code/analysis.py` — all tables/figures: OLS w/ state FE + state-clustered
  SEs + wild cluster bootstrap; PPML for murder counts; 4-wave panel;
  farm-size-Gini mechanism test; robustness.
- `output/` — analysis datasets (CSV), table fragments, figures, key numbers.

Reproduce: `python3 code/build_dataset.py && python3 code/analysis.py && ./compile.sh`

## Extension (cotton IV, spatial SEs, Gouda positioning)

- `code/extension_iv_spatial.py` — merges ABS (2016) replication data
  (cotton suitability, FAO-GAEZ) and Census gazetteer centroids; runs
  2SLS (manual just-identified, state-clustered), Anderson-Rubin CI,
  and Conley spatial-HAC SEs (Bartlett, 100/200/500 km).
- `output/external/` — archived copies of the two downloaded inputs
  (abs_county.dta is a CSV despite the extension; Gaz file is latin-1).
- Paper Section 8 "Probing identification": IV (Table 7), Conley SEs,
  and the comparison with Gouda & Rigterink (2025, Social Science Quarterly).
- Treatment validation: NHGIS-built slave share correlates 0.998 with
  ABS pslave1860.
