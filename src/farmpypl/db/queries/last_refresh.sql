-- db: prices.db
-- The most recent refresh attempt, successful or not.
--
-- Returns: zero rows if no refresh has been written to this file, otherwise
--          one row (attempted_at, ok, n_rows, message).
--
-- Every call to refresh_prices() logs one row per source, including failures,
-- so this is how a caller sees when prices were last fetched and whether the
-- fetch worked.
SELECT attempted_at, ok, n_rows, message
FROM refresh_log
ORDER BY attempted_at DESC
LIMIT 1;
