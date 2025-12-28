import pytest
from testcontainers.mysql import MySqlContainer

from flyway.db_type import DbType
from flyway.migrator import MigratorConfig, Migrator
from flyway.schema import Schema


@pytest.fixture(scope="function")
def mysql_connection():
    """Create a MySQL database connection using testcontainers."""
    with MySqlContainer("mysql:8.0") as mysql_container:
        # Import mysql connector - using mysql-connector-python
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=mysql_container.get_container_host_ip(),
                port=mysql_container.get_exposed_port(3306),
                user=mysql_container.username,
                password=mysql_container.password,
                database=mysql_container.dbname,
                allow_local_infile=True,
            )
            yield conn
            conn.close()
        except ImportError:
            # Fallback to pymysql if mysql-connector-python is not available
            import pymysql
            conn = pymysql.connect(
                host=mysql_container.get_container_host_ip(),
                port=mysql_container.get_exposed_port(3306),
                user=mysql_container.username,
                password=mysql_container.password,
                database=mysql_container.dbname,
            )
            yield conn
            conn.close()


@pytest.fixture(scope="function")
def migrator(mysql_connection):
    """Create a Migrator instance for testing."""
    config = MigratorConfig(
        db_type=DbType.MYSQL,
        user="test_user",
    )
    return Migrator(mysql_connection, config)


def test_mysql_migrate_by_schemas(mysql_connection):
    """Test migrating MySQL database using provided schemas."""
    # Create migrator with MySQL database
    migrator = Migrator(
        mysql_connection,
        MigratorConfig(
            db_type=DbType.MYSQL,
            user="mysql_user",
        ),
    )

    # Define schemas matching the SQLite test but with MySQL syntax
    schemas = [
        Schema(
            installed_rank=0,
            version="1",
            description="Create_users_table",
            script="V1__Create_users_table.sql",
            sql="CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255));",
        ),
        Schema(
            installed_rank=1,
            version="2",
            description="Add_email_column",
            script="V2__Add_email_column.sql",
            sql="ALTER TABLE users ADD COLUMN email VARCHAR(255);",
        ),
    ]

    # Run migrations
    migrator.migrate_by_schemas(schemas)

    # Verify migrations were recorded
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM flyway_schema_history")
    migration_count = cursor.fetchone()[0]
    cursor.close()

    assert migration_count == 2, "Migrations should be applied"

    # Verify that the users table was created with email column
    cursor = mysql_connection.cursor()
    cursor.execute("DESCRIBE users")
    columns = cursor.fetchall()
    cursor.close()

    column_names = [col[0] for col in columns]
    assert "id" in column_names, "users table should have id column"
    assert "name" in column_names, "users table should have name column"
    assert "email" in column_names, "users table should have email column"
