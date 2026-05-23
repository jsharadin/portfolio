-- ============================================================
-- queries.sql
-- A guided tour of SQL against the FRED macro database.
-- Queries progress from simple selects to window functions
-- and multi-series joins.
-- ============================================================


-- ------------------------------------------------------------
-- 1. Basic inspection
-- ------------------------------------------------------------

-- 1a. Catalog of available series
SELECT series_id, name, frequency, units
FROM series
ORDER BY frequency, series_id;

-- 1b. Row counts per series
SELECT s.series_id, s.name, COUNT(o.value) AS n_obs,
       MIN(o.obs_date) AS first_obs,
       MAX(o.obs_date) AS last_obs
FROM series s
LEFT JOIN observations o USING (series_id)
GROUP BY s.series_id, s.name
ORDER BY s.series_id;


-- ------------------------------------------------------------
-- 2. Filtering and aggregation
-- ------------------------------------------------------------

-- 2a. Average unemployment rate by decade
SELECT (CAST(strftime('%Y', obs_date) AS INTEGER) / 10) * 10 AS decade,
       ROUND(AVG(value), 2) AS avg_unrate,
       ROUND(MIN(value), 2) AS min_unrate,
       ROUND(MAX(value), 2) AS max_unrate
FROM observations
WHERE series_id = 'UNRATE'
GROUP BY decade
ORDER BY decade;

-- 2b. Months where unemployment exceeded 8%
SELECT obs_date, value AS unrate
FROM observations
WHERE series_id = 'UNRATE'
  AND value >= 8.0
ORDER BY obs_date;


-- ------------------------------------------------------------
-- 3. Window functions — year-over-year change
-- ------------------------------------------------------------

-- 3a. CPI year-over-year inflation
SELECT obs_date,
       value AS cpi,
       LAG(value, 12) OVER (ORDER BY obs_date) AS cpi_12mo_ago,
       ROUND(
         100.0 * (value / LAG(value, 12) OVER (ORDER BY obs_date) - 1),
         2
       ) AS yoy_inflation_pct
FROM observations
WHERE series_id = 'CPIAUCSL'
ORDER BY obs_date DESC
LIMIT 24;

-- 3b. 12-month rolling average unemployment
SELECT obs_date,
       value AS unrate,
       ROUND(
         AVG(value) OVER (ORDER BY obs_date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW),
         2
       ) AS unrate_12mo_avg
FROM observations
WHERE series_id = 'UNRATE'
ORDER BY obs_date DESC
LIMIT 24;


-- ------------------------------------------------------------
-- 4. Joining series — monthly panel
-- ------------------------------------------------------------

-- 4a. Side-by-side: unemployment, Fed funds, inflation (last 5 years)
WITH cpi_yoy AS (
    SELECT obs_date,
           100.0 * (value / LAG(value, 12) OVER (ORDER BY obs_date) - 1) AS inflation
    FROM observations
    WHERE series_id = 'CPIAUCSL'
)
SELECT u.obs_date,
       ROUND(u.value, 2)              AS unemployment,
       ROUND(f.value, 2)              AS fed_funds,
       ROUND(c.inflation, 2)          AS inflation_yoy
FROM      observations u
LEFT JOIN observations f ON f.series_id = 'FEDFUNDS' AND f.obs_date = u.obs_date
LEFT JOIN cpi_yoy      c ON c.obs_date  = u.obs_date
WHERE u.series_id = 'UNRATE'
  AND u.obs_date >= DATE('now', '-5 years')
ORDER BY u.obs_date;


-- ------------------------------------------------------------
-- 5. Recession-era flags (NBER-style heuristic)
-- ------------------------------------------------------------

-- 5a. Months where the unemployment rate rose by at least 0.5 pp
--     compared to its 12-month minimum (Sahm-rule style flag)
WITH unrate AS (
    SELECT obs_date, value,
           MIN(value) OVER (ORDER BY obs_date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS min_12mo
    FROM observations
    WHERE series_id = 'UNRATE'
)
SELECT obs_date,
       ROUND(value, 2)              AS unrate,
       ROUND(min_12mo, 2)           AS min_12mo,
       ROUND(value - min_12mo, 2)   AS rise_from_min
FROM unrate
WHERE value - min_12mo >= 0.5
ORDER BY obs_date;


-- ------------------------------------------------------------
-- 6. Yield curve — 10y vs Fed Funds (monthly snapshot)
-- ------------------------------------------------------------

-- 6a. Monthly average 10y yield minus monthly Fed Funds rate
WITH dgs10_monthly AS (
    SELECT DATE(strftime('%Y-%m-01', obs_date)) AS month,
           AVG(value) AS dgs10
    FROM observations
    WHERE series_id = 'DGS10'
    GROUP BY DATE(strftime('%Y-%m-01', obs_date))
)
SELECT d.month,
       ROUND(d.dgs10, 2)           AS dgs10,
       ROUND(f.value, 2)           AS fed_funds,
       ROUND(d.dgs10 - f.value, 2) AS term_spread
FROM dgs10_monthly d
JOIN observations f
  ON f.series_id = 'FEDFUNDS' AND f.obs_date = d.month
ORDER BY d.month DESC
LIMIT 36;
