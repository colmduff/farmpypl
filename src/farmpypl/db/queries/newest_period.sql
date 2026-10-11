-- db: prices.db
-- Newest observation held for each price series, stalest series first.
--
-- Returns: one row per series_id. The FIRST row is the series furthest behind.
--
-- Advisory only (decision 20): calculations never fetch. This is what tells
-- a person that a refresh_prices() call would be worth making.
SELECT series_id,
       MAX(period_date) AS newest_period_date
FROM prices
GROUP BY series_id
ORDER BY newest_period_date ASC, series_id;
