-- ============================================================
-- schema.sql
-- US Macroeconomic Indicators (FRED)
--
-- Each FRED series lives in its own normalized table so that
-- mixed frequencies (monthly, quarterly, daily) stay clean.
-- A `series` lookup table holds metadata and labels.
-- ============================================================

DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS series;

CREATE TABLE series (
    series_id   TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    frequency   TEXT NOT NULL,    -- 'D', 'M', 'Q'
    units       TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'FRED'
);

CREATE TABLE observations (
    series_id   TEXT NOT NULL,
    obs_date    DATE NOT NULL,
    value       REAL,
    PRIMARY KEY (series_id, obs_date),
    FOREIGN KEY (series_id) REFERENCES series(series_id)
);

CREATE INDEX idx_obs_date ON observations(obs_date);
CREATE INDEX idx_obs_series ON observations(series_id);

-- Series metadata
INSERT INTO series (series_id, name, frequency, units) VALUES
    ('UNRATE',   'Civilian Unemployment Rate',     'M', 'Percent'),
    ('CPIAUCSL', 'CPI for All Urban Consumers',    'M', 'Index 1982-84=100'),
    ('FEDFUNDS', 'Effective Federal Funds Rate',   'M', 'Percent'),
    ('GDP',      'Gross Domestic Product',         'Q', 'Billions of $'),
    ('DGS10',    '10-Year Treasury Yield',         'D', 'Percent'),
    ('INDPRO',   'Industrial Production Index',    'M', 'Index 2017=100'),
    ('PAYEMS',   'Total Nonfarm Payroll Employment','M', 'Thousands of Persons'),
    ('M2SL',     'M2 Money Stock',                 'M', 'Billions of $');
