-- db: cso.db
-- The most recent refresh attempt, successful or not.
--
-- Returns: zero rows if a refresh has never been attempted against this file
--          (true of the bundled snapshot); otherwise one row.
--
-- Why this exists: CSO publishes some weeks after month end. Between the
-- 6-week threshold and publication, every run would otherwise call the API and
-- find nothing new. Rule: refresh only if the newest month ended more than
-- 42 days ago AND the last attempt was more than 24 hours ago.
SELECT attempted_at, ok, n_rows, message
FROM refresh_log
ORDER BY attempted_at DESC
LIMIT 1;
