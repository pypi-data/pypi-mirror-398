import sqlite3
import tempfile
from pathlib import Path

import pytest

from flyway.db_type import DbType
from flyway.migrator import MigratorConfig, Migrator
from flyway.schema import Schema


@pytest.fixture(scope="function")
def sqlite_connection():
    """Create a SQLite database connection using temporary file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture(scope="function")
def sqlite_memory_connection():
    """Create an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def migrator(sqlite_connection):
    """Create a Migrator instance for testing."""
    config = MigratorConfig(
        db_type=DbType.SQLITE,
        user="test_user",
    )
    return Migrator(sqlite_connection, config)


def test_sqlite_migrate_by_schemas(sqlite_memory_connection):
    """Test migrating SQLite database using provided schemas."""
    # Create migrator with in-memory database
    migrator = Migrator(
        sqlite_memory_connection,
        MigratorConfig(
            db_type=DbType.SQLITE,
            user="sqlite",
        ),
    )

    # Define schemas matching the Go test
    schemas = [
        Schema(
            installed_rank=0,
            version="1",
            description="Create users table",
            script="V1__Create_users.sql",
            sql="CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);",
        ),
        Schema(
            installed_rank=1,
            version="2",
            description="Add email column",
            script="V2__Add_email.sql",
            sql="ALTER TABLE users ADD COLUMN email TEXT;",
        ),
    ]

    # Run migrations
    migrator.migrate_by_schemas(schemas)

    # Verify migrations were recorded
    cursor = sqlite_memory_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM flyway_schema_history")
    migration_count = cursor.fetchone()[0]
    cursor.close()

    assert migration_count == 2, "Migrations should be applied"
