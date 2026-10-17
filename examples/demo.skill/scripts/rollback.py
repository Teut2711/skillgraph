def rollback_migration(db_path: str) -> None:
    """Revert a failed migration by restoring the previous table."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS migrations_new")
    conn.commit()
    conn.close()
