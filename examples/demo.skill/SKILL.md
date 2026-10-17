# Database migration

How to run zero-downtime schema migrations safely.

## Safe migrations

Run `scripts/migrate.py` to apply the migration. It creates an index using
`sql/create_index.sql` before rewriting the table.

If the transaction fails, execute the rollback procedure in `scripts/rollback.py`.

## Rollback

Call `rollback_migration` to revert a failed migration. See `create_index` for the
index that must be dropped first.

<!-- purposefully references a missing target to trigger E001 in the demo -->
See `scripts/does_not_exist.py` for the legacy path.
