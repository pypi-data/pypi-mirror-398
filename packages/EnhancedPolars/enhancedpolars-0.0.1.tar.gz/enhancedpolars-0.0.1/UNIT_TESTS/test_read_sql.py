"""
Comprehensive test suite for SQL read functionality.

Tests cover:
- Reading data from all supported databases
- Query execution and result conversion to Polars
- Large result set handling
- Data type preservation from database to Polars
- Null value handling
- Round-trip testing (write then read)
"""

import sys
from pathlib import Path

import pytest
import polars as pl

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhancedpolars.to_sql import PolarsSQLExtension
from enhancedpolars.epl import EnhancedPolars
from enhancedpolars.register import *  # Register the epl namespace

# Optional sqlutilities import
try:
    from sqlutilities import DatabaseConnection, SQLDialect
    SQLUTILITIES_AVAILABLE = True
except ImportError:
    SQLUTILITIES_AVAILABLE = False
    DatabaseConnection = None
    SQLDialect = None

pytestmark = pytest.mark.skipif(not SQLUTILITIES_AVAILABLE, reason="sqlutilities not installed")


# ============================================================================
# Basic Read Tests
# ============================================================================

class TestBasicRead:
    """Test basic SQL read functionality."""

    @pytest.mark.integration
    def test_read_query_mysql(self, mysql_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test reading data from MySQL using execute_query."""
        table_name = unique_table_name("test_read_mysql")
        cleanup_table(mysql_connection, table_name)

        # First upload some data
        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read it back
        result = mysql_connection.execute_query(f"SELECT * FROM {table_name}")

        assert len(result) == len(sample_dataframe)
        # Result can be tuples or dicts depending on driver
        assert len(result[0]) >= 2  # At least id and name columns

    @pytest.mark.integration
    def test_read_query_postgres(self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test reading data from PostgreSQL using execute_query."""
        table_name = unique_table_name("test_read_pg")
        cleanup_table(postgres_connection, table_name)

        # Upload data
        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read it back
        result = postgres_connection.execute_query(f"SELECT * FROM {table_name}")

        assert len(result) == len(sample_dataframe)

    @pytest.mark.integration
    def test_read_query_oracle(self, oracle_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test reading data from Oracle using execute_query."""
        table_name = unique_table_name("test_read_ora").upper()
        cleanup_table(oracle_connection, table_name)

        # Upload data
        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=oracle_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read it back
        result = oracle_connection.execute_query(f'SELECT * FROM "{table_name}"')

        assert len(result) == len(sample_dataframe)

    @pytest.mark.integration
    def test_read_query_sqlserver(self, sqlserver_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test reading data from SQL Server using execute_query."""
        table_name = unique_table_name("test_read_ss")
        cleanup_table(sqlserver_connection, table_name)

        # Upload data
        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=sqlserver_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read it back
        result = sqlserver_connection.execute_query(f"SELECT * FROM {table_name}")

        assert len(result) == len(sample_dataframe)


# ============================================================================
# Query Result to Polars Conversion
# ============================================================================

class TestResultConversion:
    """Test converting query results to Polars DataFrames."""

    @pytest.mark.integration
    def test_result_to_polars_dataframe(self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test converting query result to Polars DataFrame."""
        table_name = unique_table_name("test_convert")
        cleanup_table(postgres_connection, table_name)

        # Upload data
        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read and convert - results are tuples, need schema
        result = postgres_connection.execute_query(f"SELECT * FROM {table_name}")

        # Convert tuples to Polars DataFrame with schema
        df = pl.DataFrame(result, schema=sample_dataframe.columns, orient="row")

        assert isinstance(df, pl.DataFrame)
        assert len(df) == len(sample_dataframe)
        assert set(df.columns) == set(sample_dataframe.columns)

    @pytest.mark.integration
    def test_filtered_query_result(self, mysql_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test filtered query result conversion."""
        table_name = unique_table_name("test_filter")
        cleanup_table(mysql_connection, table_name)

        # Upload data
        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read filtered - results are tuples, need schema
        result = mysql_connection.execute_query(
            f"SELECT * FROM {table_name} WHERE age > 30"
        )

        df = pl.DataFrame(result, schema=sample_dataframe.columns, orient="row")

        # Should have fewer rows
        assert len(df) < len(sample_dataframe)
        assert all(df["age"] > 30)


# ============================================================================
# Round-Trip Tests
# ============================================================================

class TestRoundTrip:
    """Test write-then-read round trips."""

    @pytest.mark.integration
    def test_roundtrip_integers(self, postgres_connection, cleanup_table, unique_table_name):
        """Test round-trip for integer columns."""
        table_name = unique_table_name("test_rt_int")
        cleanup_table(postgres_connection, table_name)

        original = pl.DataFrame({
            "small": pl.Series([1, 10, 100], dtype=pl.Int16),
            "medium": pl.Series([1000, 10000, 100000], dtype=pl.Int32),
            "large": pl.Series([1000000000, 2000000000, 3000000000], dtype=pl.Int64),
        })

        # Write
        ext = PolarsSQLExtension(original)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read back - results are tuples, need schema
        result = postgres_connection.execute_query(f"SELECT * FROM {table_name}")
        df = pl.DataFrame(result, schema=original.columns, orient="row")

        # Verify values
        assert df["small"].to_list() == [1, 10, 100]
        assert df["medium"].to_list() == [1000, 10000, 100000]
        assert df["large"].to_list() == [1000000000, 2000000000, 3000000000]

    @pytest.mark.integration
    def test_roundtrip_floats(self, mysql_connection, cleanup_table, unique_table_name):
        """Test round-trip for float columns."""
        table_name = unique_table_name("test_rt_float")
        cleanup_table(mysql_connection, table_name)

        original = pl.DataFrame({
            "float_col": [1.5, 2.75, 3.125],
            "double_col": [1.123456789, 2.987654321, 3.141592653],
        })

        # Write
        ext = PolarsSQLExtension(original)
        ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read back - results are tuples, need schema
        result = mysql_connection.execute_query(f"SELECT * FROM {table_name}")
        df = pl.DataFrame(result, schema=original.columns, orient="row")

        # Verify values (with float tolerance)
        assert abs(df["float_col"][0] - 1.5) < 0.001
        assert abs(df["double_col"][0] - 1.123456789) < 0.0001

    @pytest.mark.integration
    def test_roundtrip_strings(self, postgres_connection, cleanup_table, unique_table_name):
        """Test round-trip for string columns."""
        table_name = unique_table_name("test_rt_str")
        cleanup_table(postgres_connection, table_name)

        original = pl.DataFrame({
            "short_text": ["a", "bb", "ccc"],
            "long_text": ["Hello, World!", "This is a longer string", "Testing 123"],
        })

        # Write
        ext = PolarsSQLExtension(original)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read back - results are tuples, need schema
        result = postgres_connection.execute_query(f"SELECT * FROM {table_name}")
        df = pl.DataFrame(result, schema=original.columns, orient="row")

        # Verify values
        assert df["short_text"].to_list() == ["a", "bb", "ccc"]
        assert df["long_text"].to_list() == ["Hello, World!", "This is a longer string", "Testing 123"]

    @pytest.mark.integration
    def test_roundtrip_nulls(self, sqlserver_connection, cleanup_table, unique_table_name):
        """Test round-trip for null values."""
        table_name = unique_table_name("test_rt_null")
        cleanup_table(sqlserver_connection, table_name)

        original = pl.DataFrame({
            "nullable_int": [1, None, 3],
            "nullable_str": ["a", None, "c"],
        })

        # Write
        ext = PolarsSQLExtension(original)
        ext.to_sql(
            connection=sqlserver_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read back - convert to tuples to handle pyodbc.Row objects
        result = sqlserver_connection.execute_query(f"SELECT * FROM {table_name}")
        rows_as_tuples = [tuple(row) for row in result]
        df = pl.DataFrame(rows_as_tuples, schema=original.columns, orient="row")

        # Verify nulls are preserved
        assert df["nullable_int"][1] is None
        assert df["nullable_str"][1] is None

    @pytest.mark.integration
    def test_roundtrip_booleans(self, any_connection, cleanup_table, unique_table_name):
        """Test round-trip for boolean columns across databases."""
        table_name = unique_table_name("test_rt_bool")
        cleanup_table(any_connection, table_name)

        original = pl.DataFrame({
            "flags": [True, False, True, False],
        })

        # Write
        ext = PolarsSQLExtension(original)
        ext.to_sql(
            connection=any_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read back - results are tuples, need schema
        # Convert to tuples to handle pyodbc.Row objects (SQL Server)
        result = any_connection.execute_query(f"SELECT * FROM {table_name}")
        rows_as_tuples = [tuple(row) for row in result]
        df = pl.DataFrame(rows_as_tuples, schema=original.columns, orient="row")

        # Verify values (some DBs return int, convert)
        bool_vals = [bool(v) for v in df["flags"].to_list()]
        assert bool_vals == [True, False, True, False]


# ============================================================================
# Large Result Set Tests
# ============================================================================

class TestLargeResultSets:
    """Test handling of large result sets."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_read_large_result(self, postgres_connection, large_dataframe, cleanup_table, unique_table_name):
        """Test reading a large result set."""
        table_name = unique_table_name("test_large_read")
        cleanup_table(postgres_connection, table_name)

        # Upload large data
        ext = PolarsSQLExtension(large_dataframe)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read all back - results are tuples, need schema
        result = postgres_connection.execute_query(f"SELECT * FROM {table_name}")
        df = pl.DataFrame(result, schema=large_dataframe.columns, orient="row")

        assert len(df) == len(large_dataframe)

    @pytest.mark.integration
    def test_read_with_limit(self, mysql_connection, large_dataframe, cleanup_table, unique_table_name):
        """Test reading with LIMIT clause."""
        table_name = unique_table_name("test_limit")
        cleanup_table(mysql_connection, table_name)

        # Upload data
        ext = PolarsSQLExtension(large_dataframe)
        ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Read with limit - results are tuples, need schema
        result = mysql_connection.execute_query(
            f"SELECT * FROM {table_name} LIMIT 100"
        )
        df = pl.DataFrame(result, schema=large_dataframe.columns, orient="row")

        assert len(df) == 100


# ============================================================================
# Aggregation Query Tests
# ============================================================================

class TestAggregationQueries:
    """Test aggregation queries."""

    @pytest.mark.integration
    def test_count_query(self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test COUNT aggregation query."""
        table_name = unique_table_name("test_count")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        result = postgres_connection.execute_query(
            f"SELECT COUNT(*) as cnt FROM {table_name}"
        )

        # Result is tuple, use positional access
        assert result[0][0] == len(sample_dataframe)

    @pytest.mark.integration
    def test_sum_avg_query(self, mysql_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test SUM and AVG aggregation queries."""
        table_name = unique_table_name("test_agg")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        result = mysql_connection.execute_query(
            f"SELECT SUM(age) as total_age, AVG(salary) as avg_salary FROM {table_name}"
        )

        expected_sum = sample_dataframe["age"].sum()
        expected_avg = sample_dataframe["salary"].mean()

        # Result is tuple: (total_age, avg_salary)
        assert result[0][0] == expected_sum
        assert abs(result[0][1] - expected_avg) < 0.01

    @pytest.mark.integration
    def test_group_by_query(self, postgres_connection, cleanup_table, unique_table_name):
        """Test GROUP BY query."""
        table_name = unique_table_name("test_groupby")
        cleanup_table(postgres_connection, table_name)

        df = pl.DataFrame({
            "category": ["A", "A", "B", "B", "C"],
            "value": [10, 20, 30, 40, 50],
        })

        ext = PolarsSQLExtension(df)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        result = postgres_connection.execute_query(
            f"SELECT category, SUM(value) as total FROM {table_name} GROUP BY category ORDER BY category"
        )

        # Results are tuples, provide schema for aggregation query
        result_df = pl.DataFrame(result, schema=["category", "total"], orient="row")

        assert len(result_df) == 3
        assert result_df.filter(pl.col("category") == "A")["total"][0] == 30
        assert result_df.filter(pl.col("category") == "B")["total"][0] == 70
        assert result_df.filter(pl.col("category") == "C")["total"][0] == 50


# ============================================================================
# Join Query Tests
# ============================================================================

class TestJoinQueries:
    """Test JOIN queries across tables."""

    @pytest.mark.integration
    def test_inner_join(self, postgres_connection, cleanup_table, unique_table_name):
        """Test INNER JOIN query."""
        users_table = unique_table_name("users")
        orders_table = unique_table_name("orders")
        cleanup_table(postgres_connection, users_table)
        cleanup_table(postgres_connection, orders_table)

        users = pl.DataFrame({
            "user_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        orders = pl.DataFrame({
            "order_id": [101, 102, 103, 104],
            "user_id": [1, 1, 2, 3],
            "amount": [100.0, 200.0, 150.0, 300.0],
        })

        # Upload both tables
        PolarsSQLExtension(users).to_sql(
            connection=postgres_connection,
            table_name=users_table,
            if_exists='replace'
        )
        PolarsSQLExtension(orders).to_sql(
            connection=postgres_connection,
            table_name=orders_table,
            if_exists='replace'
        )

        # Join query
        result = postgres_connection.execute_query(f"""
            SELECT u.name, SUM(o.amount) as total_spent
            FROM {users_table} u
            INNER JOIN {orders_table} o ON u.user_id = o.user_id
            GROUP BY u.name
            ORDER BY total_spent DESC
        """)

        # Results are tuples, provide schema for join query
        result_df = pl.DataFrame(result, schema=["name", "total_spent"], orient="row")

        assert len(result_df) == 3
        # Alice has most orders (100 + 200 = 300), Charlie has 300 too
        assert result_df["name"][0] in ["Alice", "Charlie"]


# ============================================================================
# Connection State Tests
# ============================================================================

class TestConnectionState:
    """Test connection state handling during reads."""

    @pytest.mark.integration
    def test_multiple_queries_same_connection(
        self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test executing multiple queries on the same connection."""
        table_name = unique_table_name("test_multi")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Execute multiple queries
        for i in range(5):
            result = postgres_connection.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
            # Result is tuple, use positional access
            assert result[0][0] == len(sample_dataframe)

    @pytest.mark.integration
    def test_query_after_write(
        self, mysql_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test query execution immediately after write."""
        table_name = unique_table_name("test_after_write")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)

        # Write
        ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Immediate read - results are tuples, need schema
        result = mysql_connection.execute_query(f"SELECT * FROM {table_name} ORDER BY id")
        df = pl.DataFrame(result, schema=sample_dataframe.columns, orient="row")

        assert len(df) == len(sample_dataframe)
        assert df["id"][0] == sample_dataframe["id"][0]
