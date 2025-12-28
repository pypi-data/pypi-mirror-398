from dataclasses import dataclass


@dataclass
class Schema:
    """Represents a database migration schema."""

    installed_rank: int
    version: str
    description: str
    script: str
    sql: str
