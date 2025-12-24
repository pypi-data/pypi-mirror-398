"""
Pytest configuration and fixtures for EnhancedPolars test suite.

This module provides shared fixtures for database connections and test data
that are used across multiple test modules.
"""

import os
import sys
from pathlib import Path
from typing import Generator, Dict, Any, Optional
import pytest
import polars as pl

# Add enhancedpolars to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "enhancedpolars"))

# Import sqlutilities for database connections (optional)
try:
    from sqlutilities import DatabaseConnection, SQLDialect
    SQLUTILITIES_AVAILABLE = True
except ImportError:
    SQLUTILITIES_AVAILABLE = False
    DatabaseConnection = None
    SQLDialect = None

# Load environment variables from tst/.env
ENV_FILE = Path(__file__).parent.parent / "tst" / ".env"


def load_env_file(env_path: Path) -> Dict[str, str]:
    """Load environment variables from a file."""
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
                    os.environ[key] = value
    return env_vars


# Load environment on module import
ENV_VARS = load_env_file(ENV_FILE)


# ============================================================================
# Database Configuration
# ============================================================================

@pytest.fixture(scope="session")
def db_config() -> Dict[str, Dict[str, Any]]:
    """Return database configuration for all test databases."""
    if not SQLUTILITIES_AVAILABLE:
        return {}
    return {
        "mysql": {
            "dialect": SQLDialect.MYSQL,
            "host": ENV_VARS.get("MYSQL_HOST", ""),
            "port": int(ENV_VARS.get("MYSQL_HOST_PORT", "0") or "0"),
            "database": ENV_VARS.get("MYSQL_DATABASE", ""),
            "username": ENV_VARS.get("MYSQL_USER", ""),
            "password": ENV_VARS.get("MYSQL_PASSWORD", ""),
        },
        "postgres": {
            "dialect": SQLDialect.POSTGRES,
            "host": ENV_VARS.get("POSTGRES_HOST", ""),
            "port": int(ENV_VARS.get("POSTGRES_HOST_PORT", "0") or "0"),
            "database": ENV_VARS.get("POSTGRES_DB", ""),
            "username": ENV_VARS.get("POSTGRES_USER", ""),
            "password": ENV_VARS.get("POSTGRES_PASSWORD", ""),
        },
        "oracle": {
            "dialect": SQLDialect.ORACLE,
            "host": ENV_VARS.get("ORACLE_HOST", ""),
            "port": int(ENV_VARS.get("ORACLE_HOST_PORT", "0") or "0"),
            "database": ENV_VARS.get("ORACLE_SERVICE_NAME", ""),
            "username": ENV_VARS.get("ORACLE_USER", ""),
            "password": ENV_VARS.get("ORACLE_PASSWORD", ""),
        },
        "sqlserver": {
            "dialect": SQLDialect.SQLSERVER,
            "host": ENV_VARS.get("SQLSERVER_HOST", ""),
            "port": int(ENV_VARS.get("SQLSERVER_HOST_PORT", "0") or "0"),
            "database": ENV_VARS.get("SQLSERVER_DB_NAME", ""),
            "username": ENV_VARS.get("SQLSERVER_USER", ""),
            "password": ENV_VARS.get("SQLSERVER_PASSWORD", ""),
            # Required for self-signed certificates in Docker (ODBC Driver 18)
            "TrustServerCertificate": "yes",
        },
    }


def create_connection(config: Dict[str, Any]) -> Optional["DatabaseConnection"]:
    """Create a database connection from config, return None if connection fails."""
    if not SQLUTILITIES_AVAILABLE:
        return None
    try:
        # Make a copy to avoid modifying the original config
        config = config.copy()

        # Extract known parameters
        dialect = config.pop("dialect")
        host = config.pop("host")
        port = config.pop("port")
        database = config.pop("database")
        username = config.pop("username")
        password = config.pop("password")

        # Pass remaining parameters as kwargs (e.g., TrustServerCertificate)
        conn = DatabaseConnection(
            dialect=dialect,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            **config  # Pass additional params like TrustServerCertificate
        )
        conn.connect()
        return conn
    except Exception as e:
        print(f"Failed to connect to {dialect.name if 'dialect' in dir() else 'unknown'}: {e}")
        return None


# ============================================================================
# Database Connection Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def mysql_connection(db_config) -> Generator[DatabaseConnection, None, None]:
    """Provide a MySQL database connection for testing."""
    conn = create_connection(db_config["mysql"])
    if conn is None:
        pytest.skip("MySQL database not available")
    try:
        yield conn
    finally:
        if conn and conn.is_connected:
            conn.disconnect()


@pytest.fixture(scope="function")
def postgres_connection(db_config) -> Generator[DatabaseConnection, None, None]:
    """Provide a PostgreSQL database connection for testing."""
    conn = create_connection(db_config["postgres"])
    if conn is None:
        pytest.skip("PostgreSQL database not available")
    try:
        yield conn
    finally:
        if conn and conn.is_connected:
            conn.disconnect()


@pytest.fixture(scope="function")
def oracle_connection(db_config) -> Generator[DatabaseConnection, None, None]:
    """Provide an Oracle database connection for testing."""
    conn = create_connection(db_config["oracle"])
    if conn is None:
        pytest.skip("Oracle database not available")
    try:
        yield conn
    finally:
        if conn and conn.is_connected:
            conn.disconnect()


@pytest.fixture(scope="function")
def sqlserver_connection(db_config) -> Generator[DatabaseConnection, None, None]:
    """Provide a SQL Server database connection for testing."""
    conn = create_connection(db_config["sqlserver"])
    if conn is None:
        pytest.skip("SQL Server database not available")
    try:
        yield conn
    finally:
        if conn and conn.is_connected:
            conn.disconnect()


@pytest.fixture(scope="function", params=["mysql", "postgres", "oracle", "sqlserver"])
def any_connection(request, db_config) -> Generator[DatabaseConnection, None, None]:
    """Provide any available database connection for testing (parametrized)."""
    db_name = request.param
    conn = create_connection(db_config[db_name])
    if conn is None:
        pytest.skip(f"{db_name} database not available")
    try:
        yield conn
    finally:
        if conn and conn.is_connected:
            conn.disconnect()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_dataframe() -> pl.DataFrame:
    """Create a sample DataFrame with various data types for testing."""
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "age": [25, 30, 35, 28, 42],
        "salary": [50000.50, 60000.75, 75000.25, 55000.00, 90000.50],
        "is_active": [True, False, True, True, False],
        "hire_date": pl.Series([
            "2020-01-15", "2019-06-20", "2021-03-10", "2020-11-05", "2018-08-22"
        ]).str.to_date("%Y-%m-%d"),
    })


@pytest.fixture
def sample_lazyframe(sample_dataframe) -> pl.LazyFrame:
    """Create a sample LazyFrame for testing lazy operations."""
    return sample_dataframe.lazy()


@pytest.fixture
def large_dataframe() -> pl.DataFrame:
    """Create a larger DataFrame for bulk insert testing."""
    import random
    random.seed(42)

    n_rows = 10000
    return pl.DataFrame({
        "id": list(range(n_rows)),
        "value": [random.random() * 1000 for _ in range(n_rows)],
        "category": [f"cat_{i % 10}" for i in range(n_rows)],
        "description": [f"Description for row {i}" for i in range(n_rows)],
        "is_valid": [i % 2 == 0 for i in range(n_rows)],
    })


@pytest.fixture
def dataframe_with_nulls() -> pl.DataFrame:
    """Create a DataFrame with null values for testing null handling."""
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", None, "Charlie", None, "Eve"],
        "value": [10.5, None, 30.0, 40.5, None],
        "flag": [True, False, None, True, None],
    })


@pytest.fixture
def dataframe_with_special_chars() -> pl.DataFrame:
    """Create a DataFrame with special characters for testing escaping."""
    return pl.DataFrame({
        "id": [1, 2, 3],
        "text": ["Hello 'World'", 'Say "Hi"', "Back\\slash"],
        "unicode": ["Cafe\u0301", "\u4e2d\u6587", "\U0001F600"],  # Accented, Chinese, Emoji
    })


@pytest.fixture
def numeric_precision_dataframe() -> pl.DataFrame:
    """Create a DataFrame with various numeric precisions for testing."""
    return pl.DataFrame({
        "small_int": pl.Series([1, 10, 100], dtype=pl.Int8),
        "medium_int": pl.Series([1000, 10000, 30000], dtype=pl.Int16),
        "large_int": pl.Series([1000000, 2000000000, 9000000000], dtype=pl.Int64),
        "float32": pl.Series([1.5, 2.5, 3.5], dtype=pl.Float32),
        "float64": pl.Series([1.123456789012345, 2.987654321098765, 3.141592653589793], dtype=pl.Float64),
        "decimal_like": [123.45, 678.90, 999.99],
    })


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture
def cleanup_table(request):
    """
    Factory fixture to register tables for cleanup after tests.

    Usage:
        def test_something(cleanup_table, connection):
            table_name = "test_table"
            cleanup_table(connection, table_name)
            # ... test code ...
    """
    tables_to_cleanup = []

    def _register(connection: DatabaseConnection, table_name: str, schema: str = None):
        tables_to_cleanup.append((connection, table_name, schema))
        return table_name

    yield _register

    # Cleanup after test
    for conn, table_name, schema in tables_to_cleanup:
        try:
            if conn and conn.is_connected:
                full_name = f"{schema}.{table_name}" if schema else table_name
                dialect = conn.dialect.resolved_alias

                if dialect == SQLDialect.ORACLE:
                    drop_sql = f'DROP TABLE "{table_name}" PURGE'
                elif dialect == SQLDialect.SQLSERVER:
                    drop_sql = f"DROP TABLE IF EXISTS [{schema or 'dbo'}].[{table_name}]"
                else:
                    drop_sql = f"DROP TABLE IF EXISTS {full_name}"

                try:
                    conn.execute_query(drop_sql)
                except Exception:
                    pass  # Table might not exist
        except Exception as e:
            print(f"Warning: Failed to cleanup table {table_name}: {e}")


# ============================================================================
# Utility Functions
# ============================================================================

def generate_unique_table_name(prefix: str = "test") -> str:
    """Generate a unique table name for testing."""
    import uuid
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}_{short_uuid}"


@pytest.fixture
def unique_table_name():
    """Provide a unique table name generator."""
    return generate_unique_table_name


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "mysql: tests that require MySQL database"
    )
    config.addinivalue_line(
        "markers", "postgres: tests that require PostgreSQL database"
    )
    config.addinivalue_line(
        "markers", "oracle: tests that require Oracle database"
    )
    config.addinivalue_line(
        "markers", "sqlserver: tests that require SQL Server database"
    )
    config.addinivalue_line(
        "markers", "slow: tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests requiring external services"
    )
