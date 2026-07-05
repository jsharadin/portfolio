"""
Extension: (1) cotton-suitability IV for 1860 slave share,
(2) Conley spatial standard errors for the main OLS estimate,
(3) cross-validation of the treatment against ABS (2016) replication data.

External inputs (downloaded):
 - /tmp/abs_county.dta : Acharya-Blackwell-Sen (2016) county replication data
   (CSV despite extension): cottonsuit, rugged, rail1860, water1860, lat/lon.
 - /tmp/Gaz_counties_national.txt : Census 2010 gazetteer (county centroids).
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels.iv import IV2SLS

OUT = "/Users/jakesharadin/Library/CloudStorage/OneDrive-Personal/Desktop/berkeley/2024_3_fall/econ_191/new_paper/output"

x10 = pd.read_csv(f"{OUT}/analysis_2010.csv")
CONTROLS = ["log_pop_1860", "log_farm_value_pc_1860", "foreign_share_1860",
            "impr_share_1860"]
S = "slave_share_1860"
key = {}

# ---------------------------------------------------------------- merge ABS
abs_df = pd.read_csv("/tmp/abs_county.dta")
abs_df = abs_df.rename(columns={"state.abb": "state_abb"})
abs_keep = abs_df[["fips", "cottonsuit", "rugged", "rail1860", "water1860",
                   "latitude", "longitude", "pslave1860"]].copy()
x = x10.merge(abs_keep, on="fips", how="left")

# centroid fallback from the Census gazetteer
gaz = pd.read_csv("/tmp/Gaz_counties_national.txt", sep="\t", encoding="latin-1")
gaz.columns = [c.strip() for c in gaz.columns]
gaz["fips"] = gaz["GEOID"].astype(int)
x = x.merge(gaz[["fips", "INTPTLAT", "INTPTLONG"]], on="fips", how="left")
x["lat"] = x["latitude"].fillna(x["INTPTLAT"])
x["lon"] = x["longitude"].fillna(x["INTPTLONG"])

# cross-validation of treatment construction
cv = x.dropna(subset=[S, "pslave1860"])
key["corr_with_abs_pslave"] = float(np.corrcoef(cv[S], cv["pslave1860"])[0, 1])
key["n_with_cottonsuit"] = int(x["cottonsuit"].notna().sum())

# ------------------------------------------------- Conley spatial SEs (OLS)
def conley_se(df, yvar, rhs_vars, cutoffs_km=(100, 200, 500)):
    d = df.dropna(subset=[yvar] + rhs_vars + ["lat", "lon"]).copy()
    X = pd.get_dummies(d[rhs_vars + ["stabb"]], columns=["stabb"],
                       drop_first=True).astype(float)
    X = sm.add_constant(X)
    y = d[yvar].values
    res = sm.OLS(y, X).fit()
    e = res.resid.values if hasattr(res.resid, "values") else res.resid
    Xm = X.values
    k = Xm.shape[1]
    XX_inv = np.linalg.inv(Xm.T @ Xm)
    # haversine distance matrix (km)
    lat = np.radians(d["lat"].values); lon = np.radians(d["lon"].values)
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlon / 2) ** 2
    dist = 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    out = {}
    Xe = Xm * e[:, None]
    for ck in cutoffs_km:
        w = np.clip(1 - dist / ck, 0, None)        # Bartlett kernel
        S_mat = Xe.T @ (w @ Xe)
        V = XX_inv @ S_mat @ XX_inv
        j = list(X.columns).index(S)
        out[ck] = float(np.sqrt(max(V[j, j], 0)))
    return float(res.params.iloc[list(X.columns).index(S)] if hasattr(res.params, 'iloc') else res.params[j]), out, len(d)

b_main, conley, n_conley = conley_se(x, "log_violent_rate", [S] + CONTROLS)
key["conley"] = {"b": b_main, "n": n_conley,
                 **{f"se_{c}km": v for c, v in conley.items()}}

# ------------------------------------------------------------ IV: 2SLS
def run_iv(df, yvar, extra_exog=None):
    extra = extra_exog or []
    need = [yvar, S, "cottonsuit"] + CONTROLS + extra
    d = df.dropna(subset=need).copy()
    exog = pd.get_dummies(d[CONTROLS + extra + ["stabb"]], columns=["stabb"],
                          drop_first=True).astype(float)
    exog = sm.add_constant(exog)
    m = IV2SLS(d[yvar], exog, d[[S]], d[["cottonsuit"]]).fit(
        cov_type="clustered", clusters=d["stabb"])
    fs = m.first_stage.diagnostics
    # first stage coefficient (manual, same spec)
    mf = sm.OLS(d[S], pd.concat([exog, d[["cottonsuit"]]], axis=1)).fit(
        cov_type="cluster", cov_kwds={"groups": d["stabb"]})
    return m, mf, float(fs.loc[S, "f.stat"]), len(d)

iv_v, fs_v, F_v, n_v = run_iv(x, "log_violent_rate")
iv_p, fs_p, F_p, n_p = run_iv(x, "log_property_rate")
# with geography controls (ruggedness, rail, water access 1860)
GEO = ["rugged", "rail1860", "water1860"]
iv_vg, fs_vg, F_vg, n_vg = run_iv(x, "log_violent_rate", GEO)

# reduced form
def reduced_form(df, yvar, extra=None):
    extra = extra or []
    need = [yvar, "cottonsuit"] + CONTROLS + extra
    d = df.dropna(subset=need).copy()
    m = smf.ols(f"{yvar} ~ cottonsuit + " + " + ".join(CONTROLS + extra) +
                " + C(stabb)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["stabb"]})
    return m, len(d)
rf_v, n_rf = reduced_form(x, "log_violent_rate")

def stars(p): return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""
def fmt(b, se, p): return f"{b:.3f}{stars(p)}", f"({se:.3f})"

rows = []
# Panel A: first stage
c1, s1 = fmt(fs_v.params["cottonsuit"], fs_v.bse["cottonsuit"], fs_v.pvalues["cottonsuit"])
c2, s2 = fmt(fs_vg.params["cottonsuit"], fs_vg.bse["cottonsuit"], fs_vg.pvalues["cottonsuit"])
rows += [r"\multicolumn{4}{l}{\textbf{Panel A. First stage. Dep.\ var.: slave share, 1860}} \\",
         f"Cotton suitability & {c1} & {c2} & \\\\",
         f" & {s1} & {s2} & \\\\",
         f"First-stage $F$ & {F_v:.1f} & {F_vg:.1f} & \\\\",
         r"\addlinespace"]
# Panel B: 2SLS + reduced form
c1, s1 = fmt(iv_v.params[S], iv_v.std_errors[S], iv_v.pvalues[S])
c2, s2 = fmt(iv_vg.params[S], iv_vg.std_errors[S], iv_vg.pvalues[S])
c3, s3 = fmt(rf_v.params["cottonsuit"], rf_v.bse["cottonsuit"], rf_v.pvalues["cottonsuit"])
rows += [r"\multicolumn{4}{l}{\textbf{Panel B. Dep.\ var.: log violent crime rate, 2010}} \\",
         f"Slave share, 1860 (2SLS) & {c1} & {c2} & \\\\",
         f" & {s1} & {s2} & \\\\",
         f"Cotton suitability (reduced form) & & & {c3} \\\\",
         f" & & & {s3} \\\\",
         r"\addlinespace"]
# Panel C: property placebo-ish
c1, s1 = fmt(iv_p.params[S], iv_p.std_errors[S], iv_p.pvalues[S])
rows += [r"\multicolumn{4}{l}{\textbf{Panel C. Dep.\ var.: log property crime rate, 2010 (2SLS)}} \\",
         f"Slave share, 1860 & {c1} & & \\\\",
         f" & {s1} & & \\\\"]
rows += [r"\midrule",
         "State FE \\& 1860 controls & Y & Y & Y \\\\",
         "Geography controls & & Y & \\\\",
         f"Observations & {n_v:,} & {n_vg:,} & {n_rf:,} \\\\"]
with open(f"{OUT}/tables/t7_iv.tex", "w") as f:
    f.write("\n".join(rows))

key["iv_violent"] = {"b": float(iv_v.params[S]), "se": float(iv_v.std_errors[S]),
                     "p": float(iv_v.pvalues[S]), "F": F_v, "n": n_v}
key["iv_violent_geo"] = {"b": float(iv_vg.params[S]), "se": float(iv_vg.std_errors[S]),
                         "p": float(iv_vg.pvalues[S]), "F": F_vg}
key["iv_property"] = {"b": float(iv_p.params[S]), "se": float(iv_p.std_errors[S]),
                      "p": float(iv_p.pvalues[S])}
key["fs_coef"] = {"b": float(fs_v.params["cottonsuit"]), "se": float(fs_v.bse["cottonsuit"])}
key["rf_violent"] = {"b": float(rf_v.params["cottonsuit"]), "se": float(rf_v.bse["cottonsuit"]),
                     "p": float(rf_v.pvalues["cottonsuit"])}

with open(f"{OUT}/key_numbers_ext.json", "w") as f:
    json.dump(key, f, indent=1, default=float)
print(json.dumps(key, indent=1, default=float))

# persist merged file for reproducibility
x.to_csv(f"{OUT}/analysis_2010_ext.csv", index=False)
