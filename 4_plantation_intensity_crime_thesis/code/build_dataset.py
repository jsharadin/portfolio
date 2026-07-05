"""
Build county-level dataset linking 1860 census (slavery, agriculture)
to modern UCR county crime data (1990, 2000, 2010, 2016).

Sources (all local, in ../research/data):
 - NHGIS 1860 county file (1860_ag_census.dta): population by status
   (white / free colored / slave), cash value of farms, improved acres,
   farms by acreage class, slaveholdings by size.
 - ICPSR UCR county "Crimes Reported" files: 9785 (1990, Part 4),
   3451 (2000, Part 4), 33523 (2010, Part 4), 37059 (2016, Part 4).
 - Kaggle UCR-derived county file for the county-name -> FIPS crosswalk.

Output: ../output/analysis_panel.csv (county x year) and
        ../output/analysis_2010.csv (cross-section)
"""
import re
import numpy as np
import pandas as pd

DATA = "/Users/jakesharadin/Library/CloudStorage/OneDrive-Personal/Desktop/berkeley/2024_3_fall/econ_191/research/data"
OUT = "/Users/jakesharadin/Library/CloudStorage/OneDrive-Personal/Desktop/berkeley/2024_3_fall/econ_191/new_paper/output"

SLAVE_STATES = {
    "Alabama": "AL", "Arkansas": "AR", "Delaware": "DE", "Florida": "FL",
    "Georgia": "GA", "Kentucky": "KY", "Louisiana": "LA", "Maryland": "MD",
    "Mississippi": "MS", "Missouri": "MO", "North Carolina": "NC",
    "South Carolina": "SC", "Tennessee": "TN", "Texas": "TX", "Virginia": "VA",
}

# ---------------------------------------------------------------- 1860 census
ag = pd.read_stata(f"{DATA}/gini_(inequality)/1860/1860_ag_census.dta")
ag = ag[ag["state"].isin(SLAVE_STATES)].copy()

c1860 = pd.DataFrame({
    "state_1860": ag["state"],
    "county_name_1860": ag["areaname"].str.strip(),
    "totpop_1860": ag["ag3001"],
    "white_1860": ag["ah3001"],
    "free_col_1860": ag["ah3002"],
    "slave_1860": ag["ah3003"],
    "foreign_1860": ag["ah6002"],
    "farm_value_1860": ag["ag5001"],
    "impr_acres_1860": ag["ag4001"],
    "unimpr_acres_1860": ag["ag4002"],
})

# farms by acreage class (counts), NHGIS ag8001-ag8007
size_bins = ["ag8001", "ag8002", "ag8003", "ag8004", "ag8005", "ag8006", "ag8007"]
# class midpoints; open top class set to 1.5x its lower bound
midpts = np.array([6.0, 14.5, 34.5, 74.5, 299.5, 749.5, 1500.0])

def grouped_gini(counts, m=midpts):
    """Between-group Gini from grouped data (farms by acreage class).
    Lower bound of the true farm-size Gini (within-class dispersion ignored)."""
    n = np.asarray(counts, dtype=float)
    if n.sum() < 10:        # require at least 10 farms
        return np.nan
    p = n / n.sum()
    mu = (p * m).sum()
    if mu <= 0:
        return np.nan
    g = 0.0
    for i in range(len(m)):
        for j in range(len(m)):
            g += p[i] * p[j] * abs(m[i] - m[j])
    return g / (2 * mu)

c1860["n_farms_1860"] = ag[size_bins].sum(axis=1)
c1860["land_gini_1860"] = ag[size_bins].apply(lambda r: grouped_gini(r.values), axis=1)

# slaveholdings by size, ag9001-ag9021 (1,2,...,9 slaves; 10-14;15-19;20-29;
# 30-39;40-49;50-69;70-99;100-199;200-299;300-499;500-999;1000+)
sh_cols = [f"ag9{str(i).zfill(3)}" for i in range(1, 22)]
sh_mid = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 17, 24.5, 34.5, 44.5,
                   59.5, 84.5, 149.5, 249.5, 399.5, 749.5, 1500])
c1860["n_slaveholders_1860"] = ag[sh_cols].sum(axis=1)

c1860["slave_share_1860"] = c1860["slave_1860"] / c1860["totpop_1860"]
c1860["foreign_share_1860"] = c1860["foreign_1860"] / c1860["totpop_1860"]
c1860["log_pop_1860"] = np.log(c1860["totpop_1860"])
c1860["farm_value_pc_1860"] = c1860["farm_value_1860"] / c1860["totpop_1860"]
c1860["log_farm_value_pc_1860"] = np.log(c1860["farm_value_pc_1860"].replace(0, np.nan))
tot_acres = c1860["impr_acres_1860"] + c1860["unimpr_acres_1860"]
c1860["impr_share_1860"] = c1860["impr_acres_1860"] / tot_acres.replace(0, np.nan)
# average slaveholding size among holders (intensity of plantation economy)
c1860["slaves_per_holder_1860"] = (
    c1860["slave_1860"] / c1860["n_slaveholders_1860"].replace(0, np.nan))

c1860 = c1860[(c1860["totpop_1860"] > 0)].copy()
print(f"1860 slave-state counties: {len(c1860)}")
print(f"  with valid land gini: {c1860['land_gini_1860'].notna().sum()}")

# ------------------------------------------------------- name -> FIPS crosswalk
xw = pd.read_csv(f"{DATA}/crime/crime_data_w_population_and_crime_rate.csv",
                 usecols=["county_name", "FIPS_ST", "FIPS_CTY"])
xw[["cname", "stabb"]] = xw["county_name"].str.rsplit(", ", n=1, expand=True)

def norm(s):
    s = s.lower().strip()
    s = re.sub(r"\b(county|parish)\b", "", s)
    s = s.replace("saint ", "st ").replace("st. ", "st ").replace("ste. ", "ste ")
    s = re.sub(r"[.'\-]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

xw["key"] = xw["cname"].map(norm)
xw = xw.drop_duplicates(["stabb", "key"])

c1860["key"] = c1860["county_name_1860"].map(norm)
c1860["stabb"] = c1860["state_1860"].map(SLAVE_STATES)

# direct match within same modern state
m1 = c1860.merge(xw[["stabb", "key", "FIPS_ST", "FIPS_CTY"]],
                 on=["stabb", "key"], how="left")
# 1860 Virginia counties that are in modern West Virginia
va_unmatched = m1["FIPS_ST"].isna() & (m1["stabb"] == "VA")
wv = xw[xw["stabb"] == "WV"][["key", "FIPS_ST", "FIPS_CTY"]]
fix = (m1.loc[va_unmatched, ["key"]]
         .merge(wv, on="key", how="left"))
m1.loc[va_unmatched, ["FIPS_ST", "FIPS_CTY"]] = fix[["FIPS_ST", "FIPS_CTY"]].values

matched = m1["FIPS_ST"].notna()
print(f"crosswalk: matched {matched.sum()} of {len(m1)} "
      f"({matched.mean():.1%}); unmatched VA (now-WV renames etc.): "
      f"{((~matched) & (m1['stabb']=='VA')).sum()}")
cw = m1[matched].copy()
cw["fips"] = cw["FIPS_ST"].astype(int) * 1000 + cw["FIPS_CTY"].astype(int)
# a few 1860 counties can map to the same modern fips (renames); keep first
cw = cw.drop_duplicates("fips")

# ------------------------------------------------------------- crime files
def load_crime_year(year):
    if year == 1990:
        df = pd.read_stata(f"{DATA}/crime/1990/ICPSR_1990/DS0004/09785-0004-Data.dta",
                           convert_categoricals=False)
        df = df.rename(columns={
            "V5": "FIPS_ST", "V6": "FIPS_CTY", "V7": "cpop", "V8": "covpop",
            "V11": "murder", "V12": "rape", "V13": "robbery", "V14": "agasslt",
            "V15": "burglary", "V16": "larceny", "V17": "mvtheft"})
        df["covind"] = np.where(df["cpop"] > 0, 100 * df["covpop"] / df["cpop"], 0)
    else:
        paths = {2000: "2000/ICPSR_2000/DS0004/03451-0004-Data.dta",
                 2010: "2010/ICPSR_2010/DS0004/33523-0004-Data.dta",
                 2016: "2016/ICPSR_2016/DS0004/37059-0004-Data.dta"}
        df = pd.read_stata(f"{DATA}/crime/{paths[year]}", convert_categoricals=False)
        df = df.rename(columns={
            "CPOPCRIM": "covpop", "CPOPARST": "cpop", "COVIND": "covind",
            "MURDER": "murder", "RAPE": "rape", "ROBBERY": "robbery",
            "AGASSLT": "agasslt", "BURGLRY": "burglary", "LARCENY": "larceny",
            "MVTHEFT": "mvtheft"})
    df["fips"] = df["FIPS_ST"].astype(int) * 1000 + df["FIPS_CTY"].astype(int)
    df["violent"] = df[["murder", "rape", "robbery", "agasslt"]].sum(axis=1)
    df["property"] = df[["burglary", "larceny", "mvtheft"]].sum(axis=1)
    df = df[df["covpop"] > 0].copy()
    for v in ["violent", "property", "murder"]:
        df[f"{v}_rate"] = 1e5 * df[v] / df["covpop"]
    df["year"] = year
    return df[["fips", "year", "covpop", "cpop", "covind",
               "murder", "violent", "property",
               "murder_rate", "violent_rate", "property_rate"]]

crime = pd.concat([load_crime_year(y) for y in [1990, 2000, 2010, 2016]])
print("crime county-years:", len(crime))

# --------------------------------------------------------------- merge & save
keep = ["fips", "stabb", "state_1860", "county_name_1860", "totpop_1860",
        "slave_1860", "slave_share_1860", "foreign_share_1860", "log_pop_1860",
        "log_farm_value_pc_1860", "impr_share_1860", "land_gini_1860",
        "n_farms_1860", "n_slaveholders_1860", "slaves_per_holder_1860",
        "farm_value_1860"]
panel = cw[keep].merge(crime, on="fips", how="inner")
panel["log_violent_rate"] = np.log(panel["violent_rate"].replace(0, np.nan))
panel["log_property_rate"] = np.log(panel["property_rate"].replace(0, np.nan))
panel["asinh_violent_rate"] = np.arcsinh(panel["violent_rate"])
panel["log_covpop"] = np.log(panel["covpop"])

panel.to_csv(f"{OUT}/analysis_panel.csv", index=False)
x10 = panel[panel["year"] == 2010].copy()
x10.to_csv(f"{OUT}/analysis_2010.csv", index=False)

print(f"\npanel: {len(panel)} county-years, {panel['fips'].nunique()} counties")
print(f"2010 cross-section: {len(x10)} counties, "
      f"{x10['stabb'].nunique()} states")
print("\nslave share 1860 in 2010 sample:")
print(x10["slave_share_1860"].describe().round(3).to_string())
print("\nviolent==0 share 2010: ", (x10['violent_rate']==0).mean().round(3),
      "| murder==0 share 2010:", (x10['murder']==0).mean().round(3))
