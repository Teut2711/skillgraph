import sqlite3

from .rollback import rollback_migration


def migrate(db_path: str) -> None:
    """Apply the pending schema migration."""
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS migrations (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()


def create_index(db_path: str) -> None:
    """Create the helper index used during migration."""
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_migrations ON migrations(id)")
    conn.commit()
    conn.close()
