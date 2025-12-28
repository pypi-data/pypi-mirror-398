# Flyway-Python

![License](https://img.shields.io/badge/license-Apache2.0-green)
![Language](https://img.shields.io/badge/Language-Python-blue.svg)
[![version](https://img.shields.io/github/v/tag/hezhangjian/flyway-python?label=release&color=blue)](https://github.com/hezhangjian/flyway-python/releases)

## 📋 Requirements

- Python 3.11+

## 🚀 Install

```
pip install flyway
```

## NOTICE

If you are using MySQL and need to execute multiple SQL statements, make sure to add `client_flag=CLIENT.MULTI_STATEMENTS` in pymysql param. This is required to allow the execution of multiple SQL statements in a single query.

## 📖 Usage

### Basic Example

```python
import sqlite3
from flyway import Migrator, MigratorConfig, DbType

# Create database connection
conn = sqlite3.connect("example.db")

# Configure migrator
config = MigratorConfig(
    db_type=DbType.SQLITE,
    user="admin"
)

# Create migrator instance
migrator = Migrator(conn, config)

# Run migrations from db/migration folder
migrator.migrate()
```

### MySQL Example

```python
import pymysql
from pymysql.constants import CLIENT
from flyway import Migrator, MigratorConfig, DbType

# Create MySQL connection
# Note: Add client_flag=CLIENT.MULTI_STATEMENTS if your migration files contain multiple SQL statements
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="password",
    database="mydb",
    client_flag=CLIENT.MULTI_STATEMENTS
)

# Configure migrator
config = MigratorConfig(
    db_type=DbType.MYSQL,
    user="root"
)

# Create migrator instance
migrator = Migrator(conn, config)

# Run migrations from custom path
migrator.migrate_from_path("/path/to/migrations")
```

### Migration File Naming

Migration files should follow the naming convention:
```
V<version>__<description>.sql
```

Examples:
- `V1_0__Create_users_table.sql`
- `V1_1__Add_email_column.sql`
- `V2_0__Create_posts_table.sql`

The version format uses underscores (e.g., `1_0` for version `1.0`).

### Migration Directory Structure

By default, migrations are loaded from `db/migration/` directory:

```
project/
├── db/
│   └── migration/
│       ├── V1_0__Create_users_table.sql
│       ├── V1_1__Add_email_column.sql
│       └── V2_0__Create_posts_table.sql
└── main.py
```

You can also specify a custom path using `migrate_from_path()` method.
