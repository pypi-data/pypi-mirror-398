from enum import StrEnum


class DbType(StrEnum):
    """Supported database types."""

    SQLITE = "sqlite"
    MYSQL = "mysql"
