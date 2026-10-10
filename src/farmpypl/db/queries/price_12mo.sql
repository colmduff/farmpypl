-- db: cso.db
-- Mean of one price series over the 12 months up to its latest observation.
--
-- Params:  :item   e.g. 'Dairy nuts and cubes (16-18% protein)'
-- Returns: one row. If the item has no data, n_obs is 0 and the rest NULL,
--          so check n_obs before trusting mean_value.
--
-- Works for any frequency because the window is a date range, not a row count:
-- monthly CSO prices give 12 rows, weekly Oil Bulletin diesel about 52, and
-- half-yearly Eurostat electricity 2. (cso_milk_price_12mo.sql takes the last 12
-- rows, which is right only for monthly series.)
WITH series AS (
    SELECT value, period, period_date
    FROM prices
    WHERE item = :item AND value IS NOT NULL
),
window AS (
    SELECT * FROM series
    WHERE period_date > (SELECT date(MAX(period_date), '-12 months') FROM series)
)
SELECT AVG(value)       AS mean_value,
       COUNT(*)         AS n_obs,
       (SELECT period FROM window ORDER BY period_date ASC  LIMIT 1) AS first_period,
       (SELECT period FROM window ORDER BY period_date DESC LIMIT 1) AS last_period,
       MAX(period_date) AS last_period_date
FROM window;
