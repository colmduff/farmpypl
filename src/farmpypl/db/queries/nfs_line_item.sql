-- db: nfs.db
-- One NFS figure, read by its label, for one farm system and year.
--
-- Params:  :category   NFS system name, e.g. 'Dairying' (constants.NFS_SYSTEM)
--          :year       e.g. 2025
--          :section    e.g. 'DIRECT COSTS (€)'
--          :line_item  e.g. 'Purchased Concentrates'
-- Returns: one row, or none if the label is wrong.
--
-- breakdown = 'system' matters: only tables 8A-8E break down by system. The
-- regional tables (14A-14E) are all farms, not dairy.
SELECT value
FROM observations
WHERE breakdown = 'system'
  AND category = :category
  AND year = :year
  AND section = :section
  AND line_item = :line_item
  AND is_metadata = 0;
