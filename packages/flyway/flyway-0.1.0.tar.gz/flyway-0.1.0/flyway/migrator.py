"""Migrator class for database migrations."""
import os
import re
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from flyway.schema import Schema
from flyway.database import Database, SQLiteDatabase, MySQLDatabase
from flyway.db_type import DbType


@dataclass
class MigratorConfig:
    """Configuration for the migrator."""

    db_type: DbType
    user: str


class Migrator:
    """Database migrator for managing schema versions."""

    def __init__(self, connection: Any, config: MigratorConfig):
        """Initialize the migrator.

        Args:
            connection: Database connection object
            config: Migrator configuration
        """
        self.conn = connection
        self.config = config
        if config.db_type == DbType.SQLITE:
            self.adapter: Database = SQLiteDatabase(connection)
        elif config.db_type == DbType.MYSQL:
            self.adapter: Database = MySQLDatabase(connection)
        else:
            raise ValueError(f"Unsupported database type: {config.db_type}")
        self.adapter.create_schema_history_table()

    def create_database(db_type: DbType, connection: Any) -> Database:
        """Create a database adapter based on database type."""
        if db_type == DbType.SQLITE:
            return SQLiteDatabase(connection)
        elif db_type == DbType.MYSQL:
            return MySQLDatabase(connection)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def migrate(self) -> None:
        """Migrate applies the schema in db/migration folder."""
        cwd_dir = os.getcwd()
        sql_dir = os.path.join(cwd_dir, "db/migration")
        self.migrate_from_path(sql_dir)

    def migrate_from_path(self, path: str) -> None:
        """Migrate from a specific path.

        Args:
            path: Path to migration files
        """
        schemas = self._load_schemas_from_path(path)
        self.migrate_by_schemas(schemas)

    def migrate_by_schemas(self, schemas: list[Schema]) -> None:
        """Migrate using provided schemas.

        Args:
            schemas: List of schema objects to migrate
        """
        if not schemas:
            return

        # Acquire lock for migration
        try:
            self.adapter.acquire_lock()

            # Apply migrations
            for idx, schema in enumerate(schemas, start=1):
                # Check if version is already migrated
                if self.adapter.is_version_migrated(schema.version):
                    continue

                try:
                    start_time = time.time()

                    # Execute migration SQL
                    self.adapter.execute_sql(schema.sql)

                    # Calculate execution time
                    execution_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds

                    # Calculate checksum using CRC32-IEEE
                    checksum = zlib.crc32(schema.sql.encode('utf-8'))
                    # Convert to signed int32 to match Go's int32 type
                    if checksum > 0x7FFFFFFF:
                        checksum = checksum - 0x100000000

                    # Record migration in history
                    self.adapter.record_migration(
                        installed_rank=idx,
                        version=schema.version,
                        description=schema.description,
                        script=schema.script,
                        checksum=checksum,
                        user=self.config.user,
                        execution_time=execution_time,
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to apply migration V{schema.version}__{schema.description}: {str(e)}"
                    ) from e
        finally:
            # Always release lock
            self.adapter.release_lock()

    def _load_schemas_from_path(self, path: str) -> list[Schema]:
        """Load schemas from migration files in the given path.

        Args:
            path: Path to migration files

        Returns:
            List of Schema objects

        Raises:
            ValueError: If migration files are not properly formatted
        """
        migration_dir = Path(path)
        if not migration_dir.exists():
            return []

        schemas = []
        pattern = re.compile(r"^V(\d+_\d+)__([a-zA-Z0-9_]+)\.sql$")

        installed_rank = 1
        # Sort by filename to ensure consistent order
        for file_path in sorted(migration_dir.glob("V*.sql")):
            match = pattern.match(file_path.name)
            if not match:
                raise ValueError(
                    f"Invalid migration file name: {file_path.name}. "
                    "Expected format: V<version>__<description>.sql"
                )

            version = match.group(1).replace("_", ".")
            description = match.group(2)

            with open(file_path, "r", encoding="utf-8") as f:
                sql = f.read()

            schemas.append(
                Schema(
                    installed_rank=installed_rank,
                    version=version,
                    description=description,
                    script=file_path.name,
                    sql=sql,
                )
            )

            installed_rank += 1

        return schemas
