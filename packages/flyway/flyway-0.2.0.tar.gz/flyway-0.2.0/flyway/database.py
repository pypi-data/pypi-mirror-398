from abc import ABC, abstractmethod
from textwrap import dedent
from typing import Any


class Database(ABC):
    """Abstract base class for database adapters."""

    @abstractmethod
    def create_schema_history_table(self) -> None:
        """Create the schema history table if it doesn't exist."""
        pass

    @abstractmethod
    def record_migration(
            self,
            installed_rank: int,
            version: str,
            description: str,
            script: str,
            checksum: int,
            user: str,
            execution_time: int,
    ) -> None:
        """Record a migration in the schema history table.

        Args:
            installed_rank: Rank of the installed migration
            version: Version string of the migration
            description: Description of the migration
            script: Script filename
            checksum: Checksum of the script
            user: User who installed the migration
            execution_time: Execution time in milliseconds
        """
        pass

    @abstractmethod
    def is_version_migrated(self, version: str) -> bool:
        """Check if a version has been migrated.

        Args:
            version: Version string to check

        Returns:
            True if version has been migrated, False otherwise.
        """
        pass

    @abstractmethod
    def acquire_lock(self) -> None:
        """Acquire a lock for migration operations.

        Raises:
            RuntimeError: If lock cannot be acquired.
        """
        pass

    @abstractmethod
    def release_lock(self) -> None:
        """Release the migration lock.

        Raises:
            RuntimeError: If lock cannot be released.
        """
        pass

    @abstractmethod
    def execute_sql(self, sql: str) -> None:
        """Execute SQL statement(s)."""
        pass


class MySQLDatabase(Database):
    """MySQL database adapter."""

    def __init__(self, connection: Any):
        """Initialize MySQL adapter."""
        self.conn = connection
        self._lock_acquired = False

    def create_schema_history_table(self) -> None:
        """Create the schema history table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            dedent("""
                CREATE TABLE IF NOT EXISTS flyway_schema_history
                (
                    installed_rank INT NOT NULL,
                    version VARCHAR(50) COLLATE utf8mb4_bin DEFAULT NULL,
                    description VARCHAR(200) COLLATE utf8mb4_bin NOT NULL,
                    type VARCHAR(20) COLLATE utf8mb4_bin NOT NULL,
                    script VARCHAR(1000) COLLATE utf8mb4_bin NOT NULL,
                    checksum INT DEFAULT NULL,
                    installed_by VARCHAR(100) COLLATE utf8mb4_bin NOT NULL,
                    installed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    execution_time INT NOT NULL,
                    success TINYINT(1) NOT NULL,
                    PRIMARY KEY (installed_rank),
                    KEY flyway_schema_history_s_idx (success)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
            """).strip()
        )
        cursor.close()
        self.conn.commit()

    def record_migration(
            self,
            installed_rank: int,
            version: str,
            description: str,
            script: str,
            checksum: int,
            user: str,
            execution_time: int,
    ) -> None:
        """Record a migration in the schema history table."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO flyway_schema_history
            (installed_rank, version, description, type, script, checksum, installed_by, execution_time, success)
            VALUES (%s, %s, %s, 'SQL', %s, %s, %s, %s, %s)
            """,
            (installed_rank, version, description, script, checksum, user, execution_time, True),
        )
        cursor.close()
        self.conn.commit()

    def is_version_migrated(self, version: str) -> bool:
        """Check if a version has been migrated."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM flyway_schema_history WHERE version = %s AND success = TRUE",
            (version,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    def acquire_lock(self) -> None:
        """Acquire a lock for migration operations."""
        if self._lock_acquired:
            return
        # MySQL uses GET_LOCK() for application-level locking
        cursor = self.conn.cursor()
        cursor.execute("SELECT GET_LOCK('flyway_lock', 10)")
        result = cursor.fetchone()
        cursor.close()
        if result and result[0] == 1:
            self._lock_acquired = True
        else:
            raise RuntimeError("Failed to acquire migration lock")

    def release_lock(self) -> None:
        """Release the migration lock."""
        if not self._lock_acquired:
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT RELEASE_LOCK('flyway_lock')")
        cursor.fetchone()
        cursor.close()
        self._lock_acquired = False

    def execute_sql(self, sql: str) -> None:
        """Execute SQL statement(s).

        Executes the entire SQL string directly, similar to executing a SQL file.
        Requires multiStatements=true in MySQL connection string for multiple statements.
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        cursor.close()
        self.conn.commit()


class SQLiteDatabase(Database):
    """SQLite database adapter."""

    def __init__(self, connection: Any):
        """Initialize SQLite adapter."""
        self.conn = connection

    def create_schema_history_table(self) -> None:
        """Create the schema history table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            dedent("""
                CREATE TABLE IF NOT EXISTS flyway_schema_history
                (
                    installed_rank INTEGER NOT NULL,
                    version TEXT DEFAULT NULL,
                    description TEXT NOT NULL,
                    type TEXT NOT NULL,
                    script TEXT NOT NULL,
                    checksum INTEGER DEFAULT NULL,
                    installed_by TEXT NOT NULL,
                    installed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    execution_time INTEGER NOT NULL,
                    success INTEGER NOT NULL,
                    PRIMARY KEY (installed_rank),
                    CHECK (success IN (0, 1))
                );
            """).strip()
        )
        cursor.close()
        self.conn.commit()

    def record_migration(
            self,
            installed_rank: int,
            version: str,
            description: str,
            script: str,
            checksum: int,
            user: str,
            execution_time: int,
    ) -> None:
        """Record a migration in the schema history table."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO flyway_schema_history
            (installed_rank, version, description, type, script, checksum, installed_by, execution_time, success)
            VALUES (?, ?, ?, 'SQL', ?, ?, ?, ?, ?)
            """,
            (installed_rank, version, description, script, checksum, user, execution_time, 1),
        )
        cursor.close()
        self.conn.commit()

    def is_version_migrated(self, version: str) -> bool:
        """Check if a version has been migrated."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM flyway_schema_history WHERE version = ? AND success = 1",
            (version,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    def acquire_lock(self) -> None:
        pass

    def release_lock(self) -> None:
        pass

    def execute_sql(self, sql: str) -> None:
        """Execute SQL statement(s)."""
        cursor = self.conn.cursor()
        # SQLite's executescript() can handle multiple statements automatically
        cursor.executescript(sql)
        cursor.close()
        self.conn.commit()
