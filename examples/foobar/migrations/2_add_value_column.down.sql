BEGIN TRANSACTION;
PRAGMA user_version = 1;
ALTER TABLE Data DROP COLUMN value;
COMMIT;
