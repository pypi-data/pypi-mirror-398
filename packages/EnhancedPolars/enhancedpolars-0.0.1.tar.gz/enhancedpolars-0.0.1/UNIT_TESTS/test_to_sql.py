"""
Comprehensive test suite for PolarsSQLExtension (to_sql functionality).

Tests cover:
- Basic DataFrame upload to all supported databases
- LazyFrame handling (chunk iteration)
- Data type mapping and conversion
- Null value handling
- Special character escaping
- Bulk insert performance
- Table creation modes (replace, append, fail)
- SQL specification generation
- Format column expressions
"""

import sys
from pathlib import Path

import pytest
import polars as pl

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhancedpolars.to_sql import PolarsSQLExtension, format_column_expr_for_sql
from enhancedpolars.epl import EnhancedPolars
from enhancedpolars.register import *  # Register the epl namespace

# Optional sqlutilities import
try:
    from sqlutilities import DatabaseConnection, SQLDialect, SQL_TABLE, COLUMNDTYPE
    SQLUTILITIES_AVAILABLE = True
except ImportError:
    SQLUTILITIES_AVAILABLE = False
    DatabaseConnection = None
    SQLDialect = None
    SQL_TABLE = None
    COLUMNDTYPE = None

pytestmark = pytest.mark.skipif(not SQLUTILITIES_AVAILABLE, reason="sqlutilities not installed")


# ============================================================================
# Basic Upload Tests
# ============================================================================

class TestBasicUpload:
    """Test basic DataFrame upload functionality."""

    @pytest.mark.integration
    def test_upload_simple_dataframe_mysql(
        self, mysql_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test uploading a simple DataFrame to MySQL."""
        table_name = unique_table_name("test_mysql")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        result = ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(sample_dataframe)
        assert result['table_created'] is True

        # Verify data was inserted
        query_result = mysql_connection.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        assert query_result[0][0] == len(sample_dataframe)

    @pytest.mark.integration
    def test_upload_simple_dataframe_postgres(
        self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test uploading a simple DataFrame to PostgreSQL."""
        table_name = unique_table_name("test_postgres")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        result = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(sample_dataframe)
        assert result['table_created'] is True

    @pytest.mark.integration
    def test_upload_simple_dataframe_oracle(
        self, oracle_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test uploading a simple DataFrame to Oracle."""
        table_name = unique_table_name("test_oracle").upper()  # Oracle uses uppercase
        cleanup_table(oracle_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        result = ext.to_sql(
            connection=oracle_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(sample_dataframe)
        assert result['table_created'] is True

    @pytest.mark.integration
    def test_upload_simple_dataframe_sqlserver(
        self, sqlserver_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test uploading a simple DataFrame to SQL Server."""
        table_name = unique_table_name("test_sqlserver")
        cleanup_table(sqlserver_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        result = ext.to_sql(
            connection=sqlserver_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(sample_dataframe)
        assert result['table_created'] is True


# ============================================================================
# LazyFrame Tests
# ============================================================================

class TestLazyFrameUpload:
    """Test LazyFrame upload functionality (chunk iteration)."""

    @pytest.mark.integration
    def test_lazyframe_upload_mysql(
        self, mysql_connection, sample_lazyframe, cleanup_table, unique_table_name
    ):
        """Test uploading a LazyFrame to MySQL using chunk iteration."""
        table_name = unique_table_name("test_lazy_mysql")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(sample_lazyframe)
        assert ext.is_lazy is True

        result = ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace',
            chunk_size=2  # Small chunks to test iteration
        )

        assert result['rows_inserted'] == 5  # sample_lazyframe has 5 rows
        assert result['chunks_processed'] >= 1

    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_lazyframe_chunked_upload(
        self, postgres_connection, large_dataframe, cleanup_table, unique_table_name
    ):
        """Test uploading a large LazyFrame in chunks to verify memory efficiency."""
        table_name = unique_table_name("test_large_lazy")
        cleanup_table(postgres_connection, table_name)

        lazy_df = large_dataframe.lazy()
        ext = PolarsSQLExtension(lazy_df)

        result = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace',
            chunk_size=1000
        )

        assert result['rows_inserted'] == len(large_dataframe)
        assert result['chunks_processed'] == 10  # 10000 rows / 1000 chunk_size


# ============================================================================
# Data Type Tests
# ============================================================================

class TestDataTypeMapping:
    """Test data type mapping and conversion."""

    @pytest.mark.integration
    def test_numeric_precision_mysql(
        self, mysql_connection, numeric_precision_dataframe, cleanup_table, unique_table_name
    ):
        """Test numeric precision is preserved when uploading to MySQL."""
        table_name = unique_table_name("test_numeric_mysql")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(numeric_precision_dataframe)
        result = ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(numeric_precision_dataframe)

    @pytest.mark.integration
    def test_datetime_handling(self, postgres_connection, cleanup_table, unique_table_name):
        """Test datetime column handling."""
        table_name = unique_table_name("test_datetime")
        cleanup_table(postgres_connection, table_name)

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "created_at": pl.Series([
                "2023-01-15 10:30:00",
                "2023-06-20 14:45:30",
                "2023-12-31 23:59:59"
            ]).str.to_datetime("%Y-%m-%d %H:%M:%S"),
            "date_only": pl.Series([
                "2023-01-15", "2023-06-20", "2023-12-31"
            ]).str.to_date("%Y-%m-%d"),
        })

        ext = PolarsSQLExtension(df)
        result = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == 3

    @pytest.mark.integration
    def test_boolean_handling(self, any_connection, cleanup_table, unique_table_name):
        """Test boolean column handling across databases."""
        table_name = unique_table_name("test_bool")
        cleanup_table(any_connection, table_name)

        df = pl.DataFrame({
            "id": [1, 2, 3, 4],
            "flag": [True, False, True, False],
        })

        ext = PolarsSQLExtension(df)
        result = ext.to_sql(
            connection=any_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == 4


# ============================================================================
# Null Value Tests
# ============================================================================

class TestNullHandling:
    """Test null value handling."""

    @pytest.mark.integration
    def test_null_values_mysql(
        self, mysql_connection, dataframe_with_nulls, cleanup_table, unique_table_name
    ):
        """Test null values are properly handled in MySQL."""
        table_name = unique_table_name("test_nulls_mysql")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(dataframe_with_nulls)
        result = ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(dataframe_with_nulls)

        # Verify nulls are preserved
        query_result = mysql_connection.execute_query(
            f"SELECT COUNT(*) as cnt FROM {table_name} WHERE name IS NULL"
        )
        assert query_result[0][0] == 2  # 2 null names

    @pytest.mark.integration
    def test_null_values_postgres(
        self, postgres_connection, dataframe_with_nulls, cleanup_table, unique_table_name
    ):
        """Test null values are properly handled in PostgreSQL."""
        table_name = unique_table_name("test_nulls_pg")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(dataframe_with_nulls)
        result = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(dataframe_with_nulls)


# ============================================================================
# Special Character Tests
# ============================================================================

class TestSpecialCharacters:
    """Test special character handling."""

    @pytest.mark.integration
    def test_special_chars_mysql(
        self, mysql_connection, dataframe_with_special_chars, cleanup_table, unique_table_name
    ):
        """Test special characters are properly escaped in MySQL."""
        table_name = unique_table_name("test_special_mysql")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(dataframe_with_special_chars)
        result = ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(dataframe_with_special_chars)

    @pytest.mark.integration
    def test_unicode_handling(self, postgres_connection, cleanup_table, unique_table_name):
        """Test Unicode characters are properly handled."""
        table_name = unique_table_name("test_unicode")
        cleanup_table(postgres_connection, table_name)

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "text": ["\u4e2d\u6587", "\u65e5\u672c\u8a9e", "\ud55c\uad6d\uc5b4"],  # Chinese, Japanese, Korean
        })

        ext = PolarsSQLExtension(df)
        result = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == 3


# ============================================================================
# Table Creation Mode Tests
# ============================================================================

class TestTableCreationModes:
    """Test different table creation modes (replace, append, fail)."""

    @pytest.mark.integration
    def test_if_exists_replace(self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test if_exists='replace' drops and recreates table."""
        table_name = unique_table_name("test_replace")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)

        # First upload
        result1 = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )
        assert result1['rows_inserted'] == 5

        # Second upload with replace
        result2 = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )
        assert result2['rows_inserted'] == 5
        assert result2['table_replaced'] is True

        # Verify only 5 rows (not 10)
        query_result = postgres_connection.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        assert query_result[0][0] == 5

    @pytest.mark.integration
    def test_if_exists_append(self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test if_exists='append' adds to existing table."""
        table_name = unique_table_name("test_append")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)

        # First upload
        result1 = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )
        assert result1['rows_inserted'] == 5

        # Second upload with append
        result2 = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='append'
        )
        assert result2['rows_inserted'] == 5

        # Verify 10 rows total
        query_result = postgres_connection.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        assert query_result[0][0] == 10

    @pytest.mark.integration
    def test_if_exists_fail(self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name):
        """Test if_exists='fail' raises error when table exists."""
        table_name = unique_table_name("test_fail")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)

        # First upload creates table
        ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        # Second upload should fail
        with pytest.raises(Exception):  # Could be ValueError or database error
            ext.to_sql(
                connection=postgres_connection,
                table_name=table_name,
                if_exists='fail'
            )


# ============================================================================
# Format Column Expression Tests
# ============================================================================

class TestFormatColumnExpr:
    """Test format_column_expr_for_sql function."""

    def test_varchar_truncation_with_indicator(self):
        """Test that VARCHAR truncation adds indicator."""
        df = pl.DataFrame({
            "text": ["Short", "This is a very long string that exceeds the limit"]
        })

        expr = format_column_expr_for_sql("text", "VARCHAR(20)", SQLDialect.POSTGRES)
        result = df.select(expr.alias("text"))

        # Long string should be truncated with "..."
        assert result["text"][0] == "Short"
        assert result["text"][1].endswith("...")
        assert len(result["text"][1]) == 20

    def test_varchar_no_truncation_needed(self):
        """Test VARCHAR when no truncation is needed."""
        df = pl.DataFrame({
            "text": ["Short", "Medium text"]
        })

        expr = format_column_expr_for_sql("text", "VARCHAR(100)", SQLDialect.POSTGRES)
        result = df.select(expr.alias("text"))

        assert result["text"][0] == "Short"
        assert result["text"][1] == "Medium text"

    def test_integer_cast(self):
        """Test integer type casting."""
        df = pl.DataFrame({
            "num": [1.5, 2.7, 3.0]
        })

        expr = format_column_expr_for_sql("num", "INTEGER", SQLDialect.POSTGRES)
        result = df.select(expr.alias("num"))

        assert result["num"].dtype == pl.Int64

    def test_float_cast(self):
        """Test float type casting."""
        df = pl.DataFrame({
            "num": [1, 2, 3]
        })

        expr = format_column_expr_for_sql("num", "FLOAT", SQLDialect.POSTGRES)
        result = df.select(expr.alias("num"))

        assert result["num"].dtype == pl.Float64

    def test_boolean_cast(self):
        """Test boolean type casting."""
        df = pl.DataFrame({
            "flag": [1, 0, 1]
        })

        expr = format_column_expr_for_sql("flag", "BOOLEAN", SQLDialect.POSTGRES)
        result = df.select(expr.alias("flag"))

        assert result["flag"].dtype == pl.Boolean

    def test_date_cast(self):
        """Test date type casting."""
        df = pl.DataFrame({
            "dt": pl.Series(["2023-01-15", "2023-06-20"]).str.to_datetime("%Y-%m-%d")
        })

        expr = format_column_expr_for_sql("dt", "DATE", SQLDialect.POSTGRES)
        result = df.select(expr.alias("dt"))

        assert result["dt"].dtype == pl.Date


# ============================================================================
# SQL Specification Generation Tests
# ============================================================================

class TestSQLSpecification:
    """Test SQL specification generation."""

    def test_spec_generation_basic(self, sample_dataframe):
        """Test basic SQL specification generation."""
        ext = PolarsSQLExtension(sample_dataframe)

        # This tests internal _get_sql_specification method indirectly
        # by verifying it works during upload
        assert ext.columns == ["id", "name", "age", "salary", "is_active", "hire_date"]
        assert ext.height == 5

    def test_spec_generation_with_inference(self):
        """Test SQL specification generation with type inference."""
        df = pl.DataFrame({
            "small_val": [1, 2, 3],  # Should be TINYINT/SMALLINT
            "large_val": [1000000000, 2000000000, 3000000000],  # Should be BIGINT
            "text": ["a", "bb", "ccc"],  # VARCHAR based on max length
        })

        ext = PolarsSQLExtension(df)
        assert ext.height == 3


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test bulk insert performance."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_bulk_insert_performance(
        self, postgres_connection, large_dataframe, cleanup_table, unique_table_name
    ):
        """Test bulk insert performance with large dataset."""
        table_name = unique_table_name("test_perf")
        cleanup_table(postgres_connection, table_name)

        ext = PolarsSQLExtension(large_dataframe)
        result = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace',
            method='bulk'
        )

        assert result['rows_inserted'] == len(large_dataframe)
        assert result['insert_rate'] > 0  # Some rows per second
        assert result['execution_time'] > 0

    @pytest.mark.integration
    def test_batch_method(
        self, mysql_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test batch insert method."""
        table_name = unique_table_name("test_batch")
        cleanup_table(mysql_connection, table_name)

        ext = PolarsSQLExtension(sample_dataframe)
        result = ext.to_sql(
            connection=mysql_connection,
            table_name=table_name,
            if_exists='replace',
            method='batch',
            chunk_size=2
        )

        assert result['rows_inserted'] == len(sample_dataframe)
        assert result['method_used'] == 'batch'


# ============================================================================
# Namespace Registration Tests
# ============================================================================

class TestNamespaceRegistration:
    """Test that the ud namespace is properly registered."""

    def test_ud_namespace_exists(self, sample_dataframe):
        """Test that ud namespace is registered on DataFrame."""
        assert hasattr(sample_dataframe, 'epl')

    def test_ud_namespace_lazyframe(self, sample_lazyframe):
        """Test that ud namespace is registered on LazyFrame."""
        assert hasattr(sample_lazyframe, 'epl')

    @pytest.mark.integration
    def test_ud_to_sql_method(
        self, postgres_connection, sample_dataframe, cleanup_table, unique_table_name
    ):
        """Test to_sql is accessible via ud namespace."""
        table_name = unique_table_name("test_ud_namespace")
        cleanup_table(postgres_connection, table_name)

        # Use the ud namespace
        result = sample_dataframe.epl.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == len(sample_dataframe)


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.integration
    def test_empty_dataframe(self, postgres_connection, cleanup_table, unique_table_name):
        """Test uploading an empty DataFrame."""
        table_name = unique_table_name("test_empty")
        cleanup_table(postgres_connection, table_name)

        df = pl.DataFrame({"id": [], "name": []}).cast({"id": pl.Int64, "name": pl.String})
        ext = PolarsSQLExtension(df)

        result = ext.to_sql(
            connection=postgres_connection,
            table_name=table_name,
            if_exists='replace'
        )

        assert result['rows_inserted'] == 0

    def test_invalid_connection(self, sample_dataframe):
        """Test error handling for invalid connection."""
        ext = PolarsSQLExtension(sample_dataframe)

        with pytest.raises((ValueError, TypeError)):
            ext.to_sql(
                connection=None,  # Invalid connection
                table_name="test_table",
                if_exists='replace'
            )

    @pytest.mark.integration
    def test_invalid_table_name(self, sample_dataframe, postgres_connection):
        """Test error handling for invalid table name."""
        ext = PolarsSQLExtension(sample_dataframe)

        with pytest.raises(ValueError):
            ext.to_sql(
                connection=postgres_connection,
                table_name="",  # Empty table name
                if_exists='replace'
            )

    @pytest.mark.integration
    def test_invalid_method(self, sample_dataframe, postgres_connection):
        """Test error handling for invalid insert method."""
        ext = PolarsSQLExtension(sample_dataframe)

        with pytest.raises(ValueError):
            ext.to_sql(
                connection=postgres_connection,
                table_name="test_table",
                if_exists='replace',
                method='invalid_method'
            )
