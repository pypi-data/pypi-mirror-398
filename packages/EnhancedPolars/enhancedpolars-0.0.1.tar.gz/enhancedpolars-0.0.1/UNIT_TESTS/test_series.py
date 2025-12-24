"""
Comprehensive test suite for Series extensions (series.py).

Tests cover:
- Null/NaN detection methods
- SQL dtype generation
- SQL formatting
- Precision/scale calculation
"""

import sys
from pathlib import Path
import math

import pytest
import polars as pl
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import to register the namespace
from enhancedpolars.ml_pipeline import SeriesMLUtils

# Optional sqlutilities import
try:
    from sqlutilities import SQLDialect
    SQLUTILITIES_AVAILABLE = True
except ImportError:
    SQLUTILITIES_AVAILABLE = False
    SQLDialect = None


# ============================================================================
# Null/NaN Detection Tests
# ============================================================================

class TestNullNanDetection:
    """Test null and NaN detection methods."""

    def test_isnull_with_nulls(self):
        """Test isnull with null values."""
        s = pl.Series("test", [1, None, 3, None, 5])

        result = s.epl.isnull()

        assert result.to_list() == [False, True, False, True, False]

    def test_isnull_with_nan(self):
        """Test isnull with NaN values in float series."""
        s = pl.Series("test", [1.0, float('nan'), 3.0, float('nan'), 5.0])

        result = s.epl.isnull()

        assert result[0] is False
        assert result[1] is True  # NaN
        assert result[2] is False
        assert result[3] is True  # NaN
        assert result[4] is False

    def test_isnull_mixed(self):
        """Test isnull with both null and NaN."""
        s = pl.Series("test", [1.0, None, float('nan'), 4.0])

        result = s.epl.isnull()

        assert result[0] is False
        assert result[1] is True  # Null
        assert result[2] is True  # NaN
        assert result[3] is False

    def test_isnull_no_missing(self):
        """Test isnull with no missing values."""
        s = pl.Series("test", [1, 2, 3, 4, 5])

        result = s.epl.isnull()

        assert all(v is False for v in result.to_list())

    def test_notnull(self):
        """Test notnull method."""
        s = pl.Series("test", [1, None, 3, None, 5])

        result = s.epl.notnull()

        assert result.to_list() == [True, False, True, False, True]

    def test_notnull_float_with_nan(self):
        """Test notnull with NaN in float."""
        s = pl.Series("test", [1.0, float('nan'), 3.0])

        result = s.epl.notnull()

        assert result[0] is True
        assert result[1] is False  # NaN should be False
        assert result[2] is True


# ============================================================================
# Null/NaN Expression Tests
# ============================================================================

class TestNullNanExpressions:
    """Test expression generation for null/NaN detection."""

    def test_isnull_expr_int(self):
        """Test isnull_expr for integer series."""
        s = pl.Series("test", [1, None, 3])

        expr = s.epl.isnull_expr()

        # Apply expression in DataFrame context
        df = pl.DataFrame({"test": s})
        result = df.select(expr.alias("is_null_nan"))["is_null_nan"]

        assert result.to_list() == [False, True, False]

    def test_isnull_expr_float(self):
        """Test isnull_expr for float series."""
        s = pl.Series("test", [1.0, float('nan'), 3.0])

        expr = s.epl.isnull_expr()

        df = pl.DataFrame({"test": s})
        result = df.select(expr.alias("is_null_nan"))["is_null_nan"]

        assert result[0] is False
        assert result[1] is True  # NaN
        assert result[2] is False

    def test_notnull_expr(self):
        """Test notnull_expr."""
        s = pl.Series("test", [1, None, 3])

        expr = s.epl.notnull_expr()

        df = pl.DataFrame({"test": s})
        result = df.select(expr.alias("is_valid"))["is_valid"]

        assert result.to_list() == [True, False, True]


# ============================================================================
# SQL Formatting Tests
# ============================================================================

@pytest.mark.skipif(not SQLUTILITIES_AVAILABLE, reason="sqlutilities not installed")
class TestFormatForSql:
    """Test format_for_sql method."""

    def test_format_varchar_truncation(self):
        """Test VARCHAR formatting with truncation."""
        s = pl.Series("test", ["short", "this is a very long string that needs truncation"])

        result = s.epl.format_for_sql("VARCHAR(20)", SQLDialect.POSTGRES)

        assert result[0] == "short"
        assert len(result[1]) == 20
        assert result[1].endswith("...")

    def test_format_varchar_no_truncation(self):
        """Test VARCHAR formatting without truncation."""
        s = pl.Series("test", ["short", "medium"])

        result = s.epl.format_for_sql("VARCHAR(100)", SQLDialect.POSTGRES)

        assert result[0] == "short"
        assert result[1] == "medium"

    def test_format_integer(self):
        """Test INTEGER formatting."""
        s = pl.Series("test", [1.5, 2.7, 3.0])

        result = s.epl.format_for_sql("INTEGER", SQLDialect.POSTGRES)

        assert result.dtype == pl.Int64

    def test_format_float(self):
        """Test FLOAT formatting."""
        s = pl.Series("test", [1, 2, 3])

        result = s.epl.format_for_sql("FLOAT", SQLDialect.POSTGRES)

        assert result.dtype == pl.Float64

    def test_format_boolean(self):
        """Test BOOLEAN formatting."""
        s = pl.Series("test", [1, 0, 1])

        result = s.epl.format_for_sql("BOOLEAN", SQLDialect.POSTGRES)

        assert result.dtype == pl.Boolean

    def test_format_date(self):
        """Test DATE formatting."""
        s = pl.Series("test", ["2023-01-15", "2023-06-20"]).str.to_datetime("%Y-%m-%d")

        result = s.epl.format_for_sql("DATE", SQLDialect.POSTGRES)

        assert result.dtype == pl.Date


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases for series extensions."""

    def test_empty_series_null_detection(self):
        """Test null detection on empty series."""
        s = pl.Series("test", [], dtype=pl.Int64)

        result = s.epl.isnull()

        assert len(result) == 0

    def test_all_null_series(self):
        """Test series with all nulls."""
        s = pl.Series("test", [None, None, None])

        result = s.epl.isnull()

        assert all(v is True for v in result.to_list())

    def test_all_nan_series(self):
        """Test series with all NaN."""
        s = pl.Series("test", [float('nan'), float('nan'), float('nan')])

        result = s.epl.isnull()

        assert all(v is True for v in result.to_list())

    @pytest.mark.skipif(not SQLUTILITIES_AVAILABLE, reason="sqlutilities not installed")
    def test_unnamed_series_format(self):
        """Test formatting unnamed series."""
        s = pl.Series([1, 2, 3])  # No name

        result = s.epl.format_for_sql("INTEGER", SQLDialect.POSTGRES)

        assert len(result) == 3

    @pytest.mark.skipif(not SQLUTILITIES_AVAILABLE, reason="sqlutilities not installed")
    def test_special_characters_in_strings(self):
        """Test SQL formatting with special characters."""
        s = pl.Series("test", ["Hello 'World'", 'Say "Hi"', "Back\\slash"])

        # Should not raise an error
        result = s.epl.format_for_sql("VARCHAR(100)", SQLDialect.POSTGRES)

        assert len(result) == 3
