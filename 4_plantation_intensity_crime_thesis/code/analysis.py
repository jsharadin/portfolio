"""
Analysis: The legacy of slavery and contemporary violent crime.
Produces all tables (.tex fragments) and figures for the paper,
plus key_numbers.json used while writing.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/Users/jakesharadin/Library/CloudStorage/OneDrive-Personal/Desktop/berkeley/2024_3_fall/econ_191/new_paper/output"
rng = np.random.default_rng(42)

panel = pd.read_csv(f"{OUT}/analysis_panel.csv")
x10 = pd.read_csv(f"{OUT}/analysis_2010.csv")

CONTROLS = ["log_pop_1860", "log_farm_value_pc_1860", "foreign_share_1860",
            "impr_share_1860"]
key = {}

def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""

def fmt(b, se, p):
    return f"{b:.3f}{stars(p)}", f"({se:.3f})"

# ============================================================ Table 1: summary
def w(v, d=3):
    return f"{v:,.{d}f}"

sumvars = [
    ("slave_share_1860", "Slave share of population, 1860"),
    ("land_gini_1860", "Land Gini (farm acreage), 1860"),
    ("totpop_1860", "County population, 1860"),
    ("farm_value_1860", "Cash value of farms (\\$), 1860"),
    ("violent_rate", "Violent crime rate per 100k, 2010"),
    ("murder_rate", "Murder rate per 100k, 2010"),
    ("property_rate", "Property crime rate per 100k, 2010"),
]
rows = []
for v, lab in sumvars:
    s = x10[v].dropna()
    d = 0 if s.mean() > 100 else 3
    rows.append(f"{lab} & {w(s.mean(),d)} & {w(s.std(),d)} & {w(s.min(),d)} & "
                f"{w(s.median(),d)} & {w(s.max(),d)} & {len(s):,} \\\\")
with open(f"{OUT}/tables/t1_summary.tex", "w") as f:
    f.write("\n".join(rows))

# ===================================================== OLS cross-section 2010
def run_ols(df, yvar, specs, cluster="stabb"):
    res = []
    for rhs in specs:
        d = df.dropna(subset=[yvar, "slave_share_1860"] +
                      [c for c in CONTROLS if c in rhs]).copy()
        m = smf.ols(f"{yvar} ~ {rhs}", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": d[cluster]})
        res.append((m, len(d)))
    return res

S = "slave_share_1860"
FE = "C(stabb)"
CTL = " + ".join(CONTROLS)
specs = [S, f"{S} + {FE}", f"{S} + {CTL} + {FE}"]

ols_v = run_ols(x10, "log_violent_rate", specs)
ols_p = run_ols(x10, "log_property_rate", specs)

# ----- wild cluster bootstrap (Rademacher, null imposed) for main OLS spec
def wild_cluster_p(df, yvar, rhs_full, B=999):
    d = df.dropna(subset=[yvar, S] + CONTROLS).copy().reset_index(drop=True)
    y = d[yvar].values
    Xf = pd.get_dummies(d[["slave_share_1860"] + CONTROLS + ["stabb"]],
                        columns=["stabb"], drop_first=True).astype(float)
    Xf = sm.add_constant(Xf)
    Xr = Xf.drop(columns=["slave_share_1860"])
    mr = sm.OLS(y, Xr).fit()
    u_r, yhat_r = mr.resid, mr.fittedvalues
    mfull = sm.OLS(y, Xf).fit(cov_type="cluster", cov_kwds={"groups": d["stabb"]})
    t_obs = mfull.tvalues["slave_share_1860"]
    states = d["stabb"].unique()
    count = 0
    for b in range(B):
        wmap = dict(zip(states, rng.choice([-1.0, 1.0], size=len(states))))
        ystar = yhat_r + u_r * d["stabb"].map(wmap).values
        mb = sm.OLS(ystar, Xf).fit(cov_type="cluster",
                                   cov_kwds={"groups": d["stabb"]})
        if abs(mb.tvalues["slave_share_1860"]) >= abs(t_obs):
            count += 1
    return (count + 1) / (B + 1), t_obs

wb_p, t_obs = wild_cluster_p(x10, "log_violent_rate", specs[2])
key["wild_bootstrap_p"] = wb_p
key["t_obs_main"] = t_obs

# ============================================ PPML murder counts, 2010
def run_ppml(df, specs):
    out = []
    for rhs in specs:
        need = [c for c in CONTROLS if c in rhs]
        d = df.dropna(subset=["murder", "covpop", S] + need).copy()
        m = smf.glm(f"murder ~ {rhs}", data=d, family=sm.families.Poisson(),
                    offset=np.log(d["covpop"])).fit(
            cov_type="cluster", cov_kwds={"groups": d["stabb"]})
        out.append((m, len(d)))
    return out

ppml_m = run_ppml(x10, specs)

# ----------------- write Table 2 (OLS violent + property) and Table 3 (PPML)
def table_panel(results, label):
    lines = [f"\\multicolumn{{4}}{{l}}{{\\textbf{{{label}}}}} \\\\"]
    coefs, ses, ns = [], [], []
    for m, n in results:
        b, se, p = m.params[S], m.bse[S], m.pvalues[S]
        c, s_ = fmt(b, se, p)
        coefs.append(c); ses.append(s_); ns.append(f"{n:,}")
    lines.append("Slave share, 1860 & " + " & ".join(coefs) + " \\\\")
    lines.append(" & " + " & ".join(ses) + " \\\\")
    return lines, ns

l1, n1 = table_panel(ols_v, "Panel A. Dependent variable: log violent crime rate, 2010")
l2, n2 = table_panel(ols_p, "Panel B. Dependent variable: log property crime rate, 2010")
t2 = l1 + ["\\addlinespace"] + l2 + [
    "\\midrule",
    "State fixed effects & & Y & Y \\\\",
    "1860 county controls & & & Y \\\\",
    f"Observations (Panel A) & {n1[0]} & {n1[1]} & {n1[2]} \\\\",
    f"Observations (Panel B) & {n2[0]} & {n2[1]} & {n2[2]} \\\\",
]
with open(f"{OUT}/tables/t2_ols.tex", "w") as f:
    f.write("\n".join(t2))

l3, n3 = table_panel(ppml_m, "Dependent variable: murder count, 2010 (exposure: covered population)")
t3 = l3 + [
    "\\midrule",
    "State fixed effects & & Y & Y \\\\",
    "1860 county controls & & & Y \\\\",
    f"Observations & {n3[0]} & {n3[1]} & {n3[2]} \\\\",
]
with open(f"{OUT}/tables/t3_ppml.tex", "w") as f:
    f.write("\n".join(t3))

key["ols_v_main"] = {"b": ols_v[2][0].params[S], "se": ols_v[2][0].bse[S],
                     "p": ols_v[2][0].pvalues[S], "n": ols_v[2][1]}
key["ols_v_biv"] = {"b": ols_v[0][0].params[S], "se": ols_v[0][0].bse[S]}
key["ols_p_main"] = {"b": ols_p[2][0].params[S], "se": ols_p[2][0].bse[S],
                     "p": ols_p[2][0].pvalues[S]}
key["ppml_main"] = {"b": ppml_m[2][0].params[S], "se": ppml_m[2][0].bse[S],
                    "p": ppml_m[2][0].pvalues[S]}
sd = x10[S].std()
key["sd_slave_share"] = sd
key["effect_1sd_violent_pct"] = 100 * (np.exp(ols_v[2][0].params[S] * sd) - 1)
key["effect_1sd_murder_pct"] = 100 * (np.exp(ppml_m[2][0].params[S] * sd) - 1)

# ===================================================== Panel: pooled + by year
res_by_year = {}
for yr in [1990, 2000, 2010, 2016]:
    d = panel[panel["year"] == yr]
    m = run_ols(d, "log_violent_rate", [specs[2]])[0][0]
    res_by_year[yr] = (m.params[S], m.bse[S], m.pvalues[S])

d = panel.dropna(subset=["log_violent_rate", S] + CONTROLS).copy()
m_pool = smf.ols(f"log_violent_rate ~ {S} + {CTL} + {FE} + C(year)",
                 data=d).fit(cov_type="cluster", cov_kwds={"groups": d["fips"]})
key["panel_pooled"] = {"b": m_pool.params[S], "se": m_pool.bse[S],
                       "p": m_pool.pvalues[S], "n": len(d),
                       "counties": d["fips"].nunique()}

rows = []
for yr, (b, se, p) in res_by_year.items():
    c, s_ = fmt(b, se, p)
    rows.append(f"{yr} & {c} & {s_} & "
                f"{len(panel[panel['year']==yr].dropna(subset=['log_violent_rate', S]+CONTROLS)):,} \\\\")
cpool, spool = fmt(m_pool.params[S], m_pool.bse[S], m_pool.pvalues[S])
rows.append("\\midrule")
rows.append(f"Pooled (year FE, county-clustered) & {cpool} & {spool} & {len(d):,} \\\\")
with open(f"{OUT}/tables/t4_panel.tex", "w") as f:
    f.write("\n".join(rows))

# ================================================ Mechanism: land inequality
d = x10.dropna(subset=["land_gini_1860", S] + CONTROLS).copy()
m_gini = smf.ols(f"land_gini_1860 ~ {S} + {CTL} + {FE}", data=d).fit(
    cov_type="cluster", cov_kwds={"groups": d["stabb"]})
m_sph = smf.ols(f"slaves_per_holder_1860 ~ {S} + {CTL} + {FE}",
                data=d.dropna(subset=["slaves_per_holder_1860"])).fit(
    cov_type="cluster",
    cov_kwds={"groups": d.dropna(subset=["slaves_per_holder_1860"])["stabb"]})
# horse race
d2 = x10.dropna(subset=["log_violent_rate", "land_gini_1860", S] + CONTROLS).copy()
m_hr0 = smf.ols(f"log_violent_rate ~ land_gini_1860 + {CTL} + {FE}", data=d2).fit(
    cov_type="cluster", cov_kwds={"groups": d2["stabb"]})
m_hr = smf.ols(f"log_violent_rate ~ {S} + land_gini_1860 + {CTL} + {FE}",
               data=d2).fit(cov_type="cluster", cov_kwds={"groups": d2["stabb"]})

def cell(m, v):
    if v not in m.params: return "", ""
    return fmt(m.params[v], m.bse[v], m.pvalues[v])

rows = []
mods = [m_gini, m_sph, m_hr0, m_hr]
for vname, vlab in [(S, "Slave share, 1860"),
                    ("land_gini_1860", "Land Gini, 1860")]:
    cs, ss = [], []
    for m in mods:
        c, s_ = cell(m, vname)
        cs.append(c); ss.append(s_)
    rows.append(f"{vlab} & " + " & ".join(cs) + " \\\\")
    rows.append(" & " + " & ".join(ss) + " \\\\")
rows.append("\\midrule")
rows.append("State FE \\& 1860 controls & Y & Y & Y & Y \\\\")
ns = [int(m.nobs) for m in mods]
rows.append("Observations & " + " & ".join(f"{n:,}" for n in ns) + " \\\\")
with open(f"{OUT}/tables/t5_mechanism.tex", "w") as f:
    f.write("\n".join(rows))
key["gini_on_slave"] = {"b": m_gini.params[S], "se": m_gini.bse[S],
                        "p": m_gini.pvalues[S]}
key["hr_slave"] = {"b": m_hr.params[S], "se": m_hr.bse[S]}
key["hr_gini"] = {"b": m_hr.params["land_gini_1860"],
                  "se": m_hr.bse["land_gini_1860"],
                  "p": m_hr.pvalues["land_gini_1860"]}
key["hr_gini_alone"] = {"b": m_hr0.params["land_gini_1860"],
                        "se": m_hr0.bse["land_gini_1860"],
                        "p": m_hr0.pvalues["land_gini_1860"]}

# ============================================================== Robustness
rob = []
def add_rob(label, m, n):
    c, s_ = fmt(m.params[S], m.bse[S], m.pvalues[S])
    rob.append(f"{label} & {c} & {s_} & {n:,} \\\\")

# baseline repeated for reference
add_rob("Baseline (col. 3, Table 2)", ols_v[2][0], ols_v[2][1])
# coverage >= 75
d = x10[x10["covind"] >= 75]
m = run_ols(d, "log_violent_rate", [specs[2]])[0]
add_rob("UCR coverage index $\\geq$ 75", m[0], m[1])
# population weighted
d = x10.dropna(subset=["log_violent_rate", S] + CONTROLS).copy()
mw = smf.wls(f"log_violent_rate ~ {S} + {CTL} + {FE}", data=d,
             weights=d["covpop"]).fit(cov_type="cluster",
                                      cov_kwds={"groups": d["stabb"]})
add_rob("Weighted by covered population", mw, len(d))
# asinh
m = run_ols(x10, "asinh_violent_rate", [specs[2]])[0]
add_rob("asinh(violent crime rate)", m[0], m[1])
# drop Virginia (boundary/independent-city issues)
d = x10[x10["stabb"] != "VA"]
m = run_ols(d, "log_violent_rate", [specs[2]])[0]
add_rob("Excluding Virginia", m[0], m[1])
# winsorize outcome at 1/99
d = x10.copy()
lo, hi = d["violent_rate"].quantile([0.01, 0.99])
d["log_violent_rate"] = np.log(d["violent_rate"].clip(lo, hi))
m = run_ols(d, "log_violent_rate", [specs[2]])[0]
add_rob("Violent rate winsorized at 1/99 pct.", m[0], m[1])
with open(f"{OUT}/tables/t6_robust.tex", "w") as f:
    f.write("\n".join(rob))

# leave-one-state-out range
loso = []
for st in x10["stabb"].unique():
    m = run_ols(x10[x10["stabb"] != st], "log_violent_rate", [specs[2]])[0][0]
    loso.append(m.params[S])
key["loso_min"], key["loso_max"] = float(np.min(loso)), float(np.max(loso))

# ============================================================== Figures
plt.rcParams.update({"figure.dpi": 200, "font.size": 11})

# F1: within-state binscatter
d = x10.dropna(subset=["log_violent_rate", S] + CONTROLS).copy()
def residualize(df, var, rhs):
    return smf.ols(f"{var} ~ {rhs}", data=df).fit().resid
ry = residualize(d, "log_violent_rate", f"{CTL} + {FE}") + d["log_violent_rate"].mean()
rx = residualize(d, S, f"{CTL} + {FE}") + d[S].mean()
q = pd.qcut(rx, 20, duplicates="drop")
bs = pd.DataFrame({"x": rx.groupby(q, observed=True).mean(),
                   "y": ry.groupby(q, observed=True).mean()})
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(rx, ry, s=6, alpha=0.18, color="#7aa6a6")
ax.scatter(bs["x"], bs["y"], s=46, color="#1f5f5f", zorder=3, label="Vigintile means")
b0 = np.polyfit(rx, ry, 1)
xs = np.linspace(rx.min(), rx.max(), 50)
ax.plot(xs, np.polyval(b0, xs), color="#1f5f5f", lw=1.6)
ax.set_xlabel("Slave share of county population, 1860\n(residualized on state FE and 1860 controls)")
ax.set_ylabel("Log violent crime rate, 2010 (residualized)")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(f"{OUT}/figures/f1_binscatter.png", bbox_inches="tight")
plt.close(fig)

# F2: coefficient by census year
fig, ax = plt.subplots(figsize=(7, 4.5))
yrs = list(res_by_year.keys())
bs_ = [res_by_year[y][0] for y in yrs]
ci = [1.96 * res_by_year[y][1] for y in yrs]
ax.errorbar(yrs, bs_, yerr=ci, fmt="o", capsize=4, color="#1f5f5f")
ax.axhline(0, color="gray", lw=0.8, ls="--")
ax.set_xticks(yrs)
ax.set_xlabel("UCR year")
ax.set_ylabel("Coefficient on slave share, 1860\n(log violent crime rate, 95% CI)")
fig.tight_layout()
fig.savefig(f"{OUT}/figures/f2_byyear.png", bbox_inches="tight")
plt.close(fig)

# F3: slave share vs land gini (mechanism)
d3 = x10.dropna(subset=["land_gini_1860", S]).copy()
q = pd.qcut(d3[S], 20, duplicates="drop")
g = d3.groupby(q, observed=True).agg(x=(S, "mean"), y=("land_gini_1860", "mean"))
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.scatter(d3[S], d3["land_gini_1860"], s=6, alpha=0.18, color="#a68b7a")
ax.scatter(g["x"], g["y"], s=46, color="#6e4423", zorder=3, label="Vigintile means")
ax.set_xlabel("Slave share of county population, 1860")
ax.set_ylabel("Land Gini (farm acreage, grouped), 1860")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(f"{OUT}/figures/f3_gini.png", bbox_inches="tight")
plt.close(fig)

# F4: distribution of slave share
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(x10[S], bins=40, color="#4d8a8a", edgecolor="white")
ax.set_xlabel("Slave share of county population, 1860")
ax.set_ylabel("Number of counties")
fig.tight_layout()
fig.savefig(f"{OUT}/figures/f4_hist.png", bbox_inches="tight")
plt.close(fig)

with open(f"{OUT}/key_numbers.json", "w") as f:
    json.dump({k: (v if not isinstance(v, dict) else
                   {kk: float(vv) for kk, vv in v.items()})
               for k, v in key.items()}, f, indent=1, default=float)
print(json.dumps(key, indent=1, default=str))
