-- db: cso.db
-- Rolling 12-month mean of one monthly price series.
--
-- Params:  :item   e.g. 'Milk (per litre), actual fat and protein'
-- Returns: one row. If the item has no data, n_months is 0 and the rest NULL,
--          so check n_months before trusting mean_value.
--
-- Orders by period_date ('2026-07-01'), never by period ('2026 July'): as text,
-- '2026 May' sorts after '2026 July', which silently picks the wrong window.
-- Values are EUR per unit, unformatted (queries/milk_price_annual.sql is the
-- human-readable version of the same calculation).
WITH last12 AS (
    SELECT value, period, period_date
    FROM prices
    WHERE item = :item AND value IS NOT NULL
    ORDER BY period_date DESC
    LIMIT 12
)
SELECT AVG(value)       AS mean_value,
       MIN(value)       AS min_value,
       MAX(value)       AS max_value,
       COUNT(*)         AS n_months,
       (SELECT period FROM last12 ORDER BY period_date ASC  LIMIT 1) AS first_period,
       (SELECT period FROM last12 ORDER BY period_date DESC LIMIT 1) AS last_period,
       MAX(period_date) AS last_period_date
FROM last12;
