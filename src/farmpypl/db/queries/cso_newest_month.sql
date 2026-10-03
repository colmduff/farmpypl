-- db: cso.db
-- Newest month held for each CSO series, stalest series first.
--
-- Returns: one row per series_id. The FIRST row is the one that decides
--          whether a refresh is due, because it is the furthest behind.
--
-- newest_month_end is the last day of that month ('2026-07-01' -> '2026-07-31').
-- Age is measured from month END: July's figures cannot exist before 31 July,
-- so counting from the 1st would make every month look a month staler.
SELECT series_id,
       MAX(period_date)                                  AS newest_period_date,
       date(MAX(period_date), '+1 month', '-1 day')      AS newest_month_end
FROM prices
GROUP BY series_id
ORDER BY newest_period_date ASC, series_id;
