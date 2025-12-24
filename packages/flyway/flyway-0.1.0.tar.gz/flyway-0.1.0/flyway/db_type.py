from enum import Enum


class DbType(str, Enum):
    """Supported database types."""

    SQLITE = "sqlite"
    MYSQL = "mysql"
