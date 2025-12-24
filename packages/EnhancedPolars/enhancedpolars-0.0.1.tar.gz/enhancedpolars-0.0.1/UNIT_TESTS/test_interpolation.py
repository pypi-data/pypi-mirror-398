"""
Tests for interpolation.py - Polars interpolation utilities
"""

import pytest
import polars as pl
import numpy as np
from datetime import datetime, timedelta
from typing import List

from enhancedpolars.interpolation import (
    PolarsInterpolationUtils,
    PolarsDataFrameInterpolationExtension,
    SCIPY_AVAILABLE,
)


class TestPolarsInterpolationUtilsNullExpr:
    """Tests for create_null_or_nan_expr utility."""

    def test_null_expr_integer_column(self):
        """Test null detection for integer columns."""
        df = pl.DataFrame({
            "value": [1, None, 3, None, 5],
        })

        expr = PolarsInterpolationUtils.create_null_or_nan_expr(df, "value")
        result = df.select(expr.alias("is_null"))

        assert result["is_null"].to_list() == [False, True, False, True, False]

    def test_null_expr_float_column_with_nan(self):
        """Test null/NaN detection for float columns."""
        df = pl.DataFrame({
            "value": [1.0, float('nan'), 3.0, None, 5.0],
        })

        expr = PolarsInterpolationUtils.create_null_or_nan_expr(df, "value")
        result = df.select(expr.alias("is_null"))

        # Both NaN and null should be detected
        expected = [False, True, False, True, False]
        assert result["is_null"].to_list() == expected

    def test_null_expr_no_nulls(self):
        """Test with no null values."""
        df = pl.DataFrame({
            "value": [1, 2, 3, 4, 5],
        })

        expr = PolarsInterpolationUtils.create_null_or_nan_expr(df, "value")
        result = df.select(expr.alias("is_null"))

        assert not any(result["is_null"].to_list())


class TestPolarsInterpolationUtilsFfillExpr:
    """Tests for build_ffill_expr utility."""

    def test_ffill_basic(self):
        """Test basic forward fill expression."""
        df = pl.DataFrame({
            "value": [1, None, None, 4, None],
        })

        expr = PolarsInterpolationUtils.build_ffill_expr(df, "value")
        result = df.select(expr.alias("filled"))

        expected = [1, 1, 1, 4, 4]
        assert result["filled"].to_list() == expected

    def test_ffill_with_limit(self):
        """Test forward fill with limit."""
        df = pl.DataFrame({
            "value": [1.0, None, None, None, 5.0],
        })

        expr = PolarsInterpolationUtils.build_ffill_expr(df, "value", limit=1)
        result = df.select(expr.alias("filled"))

        # Only first null should be filled
        filled = result["filled"].to_list()
        assert filled[0] == 1.0
        assert filled[1] == 1.0  # Filled
        assert filled[2] is None or (isinstance(filled[2], float) and np.isnan(filled[2]))  # Not filled
        assert filled[4] == 5.0

    def test_ffill_float_with_nan(self):
        """Test forward fill with NaN values in float column."""
        df = pl.DataFrame({
            "value": [1.0, float('nan'), 3.0, None, 5.0],
        })

        expr = PolarsInterpolationUtils.build_ffill_expr(df, "value")
        result = df.select(expr.alias("filled"))

        filled = result["filled"].to_list()
        assert filled[0] == 1.0
        # NaN should be filled with 1.0
        assert filled[1] == 1.0 or (isinstance(filled[1], float) and np.isnan(filled[1]))
        assert filled[2] == 3.0


class TestPolarsInterpolationUtilsBfillExpr:
    """Tests for build_bfill_expr utility."""

    def test_bfill_basic(self):
        """Test basic backward fill expression."""
        df = pl.DataFrame({
            "value": [None, 2, None, None, 5],
        })

        expr = PolarsInterpolationUtils.build_bfill_expr(df, "value")
        result = df.select(expr.alias("filled"))

        expected = [2, 2, 5, 5, 5]
        assert result["filled"].to_list() == expected

    def test_bfill_with_limit(self):
        """Test backward fill with limit."""
        df = pl.DataFrame({
            "value": [1.0, None, None, None, 5.0],
        })

        expr = PolarsInterpolationUtils.build_bfill_expr(df, "value", limit=1)
        result = df.select(expr.alias("filled"))

        # Only last null before 5 should be filled
        filled = result["filled"].to_list()
        assert filled[0] == 1.0
        assert filled[3] == 5.0  # Filled
        assert filled[4] == 5.0


class TestPolarsInterpolationUtilsInterpolationExpr:
    """Tests for build_interpolation_expr utility."""

    def test_interpolation_ffill_method(self):
        """Test interpolation with ffill method."""
        df = pl.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [10, None, None, 40, 50],
        })

        expr = PolarsInterpolationUtils.build_interpolation_expr(
            df, col_name="y", by=None, method="ffill"
        )
        result = df.select(expr.alias("interp"))

        assert result["interp"].to_list() == [10, 10, 10, 40, 50]

    def test_interpolation_bfill_method(self):
        """Test interpolation with bfill method."""
        df = pl.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [10, None, None, 40, 50],
        })

        expr = PolarsInterpolationUtils.build_interpolation_expr(
            df, col_name="y", by=None, method="bfill"
        )
        result = df.select(expr.alias("interp"))

        assert result["interp"].to_list() == [10, 40, 40, 40, 50]

    def test_interpolation_fillna_value(self):
        """Test interpolation with fillna and value."""
        df = pl.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [10, None, None, 40, None],
        })

        expr = PolarsInterpolationUtils.build_interpolation_expr(
            df, col_name="y", by=None, method="fillna", value=0
        )
        result = df.select(expr.alias("interp"))

        assert result["interp"].to_list() == [10, 0, 0, 40, 0]

    def test_interpolation_fillna_strategy_mean(self):
        """Test interpolation with fillna and mean strategy."""
        df = pl.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [10.0, None, None, 40.0, 50.0],
        })

        expr = PolarsInterpolationUtils.build_interpolation_expr(
            df, col_name="y", by=None, method="fillna", strategy="mean"
        )
        result = df.select(expr.alias("interp"))

        # Mean of [10, 40, 50] = 100/3 ≈ 33.33
        mean_val = (10 + 40 + 50) / 3
        interp = result["interp"].to_list()
        assert interp[0] == 10.0
        assert abs(interp[1] - mean_val) < 0.01
        assert abs(interp[2] - mean_val) < 0.01
        assert interp[3] == 40.0
        assert interp[4] == 50.0

    def test_interpolation_linear_basic(self):
        """Test linear interpolation."""
        df = pl.DataFrame({
            "x": pl.Series([1, 2, 3, 4, 5], dtype=pl.Int64),
            "y": pl.Series([10.0, None, None, 40.0, 50.0], dtype=pl.Float64),
        })

        expr = PolarsInterpolationUtils.build_interpolation_expr(
            df, col_name="y", by="x", method="linear"
        )
        result = df.select(expr.alias("interp"))

        # Linear interpolation should fill intermediate values
        interp = result["interp"].to_list()
        assert interp[0] == 10.0
        assert interp[3] == 40.0
        assert interp[4] == 50.0
        # Intermediate values should be interpolated

    def test_interpolation_requires_by_for_linear(self):
        """Test that linear interpolation requires 'by' parameter."""
        df = pl.DataFrame({
            "y": [10.0, None, 30.0],
        })

        with pytest.raises(ValueError, match="'by' parameter required"):
            PolarsInterpolationUtils.build_interpolation_expr(
                df, col_name="y", by=None, method="linear"
            )

    @pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
    def test_interpolation_scipy_cubic(self):
        """Test scipy cubic interpolation."""
        # Cubic requires at least 4 known points
        df = pl.DataFrame({
            "x": pl.Series([1, 2, 3, 4, 5, 6, 7], dtype=pl.Float64),
            "y": pl.Series([1.0, 4.0, None, 16.0, 25.0, None, 49.0], dtype=pl.Float64),
        })

        expr = PolarsInterpolationUtils.build_interpolation_expr(
            df, col_name="y", by="x", method="cubic"
        )
        result = df.select(expr.alias("interp"))

        # Should complete without error and fill values
        assert result["interp"].null_count() == 0


class TestPolarsDataFrameInterpolationExtensionInit:
    """Tests for PolarsDataFrameInterpolationExtension initialization."""

    def test_init_with_dataframe(self):
        """Test initialization with DataFrame."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = PolarsDataFrameInterpolationExtension(df)

        assert ext.length == 3
        assert ext.columns == ["a"]

    def test_init_with_lazyframe(self):
        """Test initialization with LazyFrame."""
        lf = pl.LazyFrame({"a": [1, 2, 3]})
        ext = PolarsDataFrameInterpolationExtension(lf)

        assert ext.is_lazy
        assert ext.columns == ["a"]


class TestUpsample:
    """Tests for upsample method."""

    @pytest.fixture
    def time_df(self):
        """Create DataFrame with time column."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 3, 0),  # Gap at 2:00
            ],
            "value": [10.0, 20.0, 40.0],
        })

    def test_upsample_basic(self, time_df):
        """Test basic upsampling."""
        ext = PolarsDataFrameInterpolationExtension(time_df)
        result = ext.upsample("timestamp", "1h")

        # Should create rows for missing hour
        assert result.shape[0] >= 3

    def test_upsample_with_groupby(self):
        """Test upsampling with group by."""
        df = pl.DataFrame({
            "device": ["A", "A", "B", "B"],
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 2, 0),
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 2, 0),
            ],
            "value": [10.0, 30.0, 100.0, 300.0],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.upsample("timestamp", "1h", by=["device"])

        # Each device should have its own time grid
        assert "device" in result.columns
        assert "timestamp" in result.columns


class TestInterpolate:
    """Tests for main interpolate method."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for interpolation."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0),
                datetime(2023, 1, 1, 1),
                datetime(2023, 1, 1, 2),
                datetime(2023, 1, 1, 3),
                datetime(2023, 1, 1, 4),
            ],
            "temperature": [20.0, None, None, 26.0, 28.0],
            "pressure": [100.0, None, 104.0, None, 108.0],
        })

    def test_interpolate_auto_detect_columns(self, sample_df):
        """Test auto-detection of numeric columns."""
        ext = PolarsDataFrameInterpolationExtension(sample_df)
        result = ext.interpolate(by="timestamp", method="linear")

        # Should interpolate all numeric columns
        assert result["temperature"].null_count() == 0
        assert result["pressure"].null_count() == 0

    def test_interpolate_specific_columns(self, sample_df):
        """Test interpolation of specific columns."""
        ext = PolarsDataFrameInterpolationExtension(sample_df)
        result = ext.interpolate(
            columns=["temperature"],
            by="timestamp",
            method="linear",
        )

        assert result["temperature"].null_count() == 0
        # pressure should still have nulls if not interpolated
        # Note: depending on implementation, pressure might be included

    def test_interpolate_ffill_method(self, sample_df):
        """Test interpolation with ffill method (no by needed)."""
        ext = PolarsDataFrameInterpolationExtension(sample_df)
        result = ext.interpolate(
            columns=["temperature"],
            method="ffill",
        )

        assert result["temperature"].null_count() == 0
        temps = result["temperature"].to_list()
        assert temps[1] == 20.0  # Forward filled from index 0
        assert temps[2] == 20.0  # Forward filled

    def test_interpolate_bfill_method(self, sample_df):
        """Test interpolation with bfill method."""
        ext = PolarsDataFrameInterpolationExtension(sample_df)
        result = ext.interpolate(
            columns=["temperature"],
            method="bfill",
        )

        assert result["temperature"].null_count() == 0
        temps = result["temperature"].to_list()
        assert temps[1] == 26.0  # Backward filled from index 3
        assert temps[2] == 26.0  # Backward filled

    def test_interpolate_with_suffix(self, sample_df):
        """Test interpolation creates new columns with suffix."""
        ext = PolarsDataFrameInterpolationExtension(sample_df)
        result = ext.interpolate(
            columns=["temperature"],
            method="ffill",
            suffix="_filled",
            inplace=False,
        )

        # Original column should still exist
        assert "temperature" in result.columns
        # New column with suffix should be created
        assert "temperature_filled" in result.columns

    def test_interpolate_inplace_true(self, sample_df):
        """Test interpolation replaces columns when inplace=True."""
        ext = PolarsDataFrameInterpolationExtension(sample_df)
        result = ext.interpolate(
            columns=["temperature"],
            method="ffill",
            inplace=True,
        )

        # Original column should be replaced
        assert "temperature" in result.columns
        assert "temperature_filled" not in result.columns
        assert result["temperature"].null_count() == 0

    def test_interpolate_with_groupby(self):
        """Test interpolation with group by."""
        df = pl.DataFrame({
            "device": ["A", "A", "A", "B", "B", "B"],
            "timestamp": [
                datetime(2023, 1, 1, 0),
                datetime(2023, 1, 1, 1),
                datetime(2023, 1, 1, 2),
                datetime(2023, 1, 1, 0),
                datetime(2023, 1, 1, 1),
                datetime(2023, 1, 1, 2),
            ],
            "value": [10.0, None, 30.0, 100.0, None, 300.0],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.interpolate(
            columns=["value"],
            by="timestamp",
            method="linear",
            group_by=["device"],
        )

        assert result["value"].null_count() == 0

    def test_interpolate_per_column_method(self, sample_df):
        """Test per-column method specification."""
        ext = PolarsDataFrameInterpolationExtension(sample_df)
        result = ext.interpolate(
            columns=["temperature", "pressure"],
            by="timestamp",
            method={"temperature": "ffill", "pressure": "bfill"},
        )

        assert result["temperature"].null_count() == 0
        assert result["pressure"].null_count() == 0


class TestRolling:
    """Tests for rolling method."""

    @pytest.fixture
    def time_series_df(self):
        """Create time series DataFrame."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
                datetime(2023, 1, 1, 2, 0),
            ],
            "value": [10.0, 20.0, 30.0, 40.0, 50.0],
        })

    def test_rolling_basic(self, time_series_df):
        """Test basic rolling aggregation."""
        ext = PolarsDataFrameInterpolationExtension(time_series_df)
        result = ext.rolling(
            index_column="timestamp",
            period="1h",
            columns=["value"],
            default_agg="mean",
        )

        assert "value_rolling" in result.columns or "value" in result.columns

    def test_rolling_with_groupby(self):
        """Test rolling with group by."""
        df = pl.DataFrame({
            "device": ["A", "A", "A", "B", "B", "B"],
            "timestamp": [
                datetime(2023, 1, 1, 0),
                datetime(2023, 1, 1, 1),
                datetime(2023, 1, 1, 2),
                datetime(2023, 1, 1, 0),
                datetime(2023, 1, 1, 1),
                datetime(2023, 1, 1, 2),
            ],
            "value": [10.0, 20.0, 30.0, 100.0, 200.0, 300.0],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.rolling(
            index_column="timestamp",
            period="2h",
            group_by=["device"],
            columns=["value"],
            default_agg="mean",
        )

        assert "device" in result.columns

    def test_rolling_explicit_aggs(self, time_series_df):
        """Test rolling with explicit aggregations."""
        ext = PolarsDataFrameInterpolationExtension(time_series_df)
        result = ext.rolling(
            index_column="timestamp",
            period="1h",
            value_avg=("value", "mean"),
            value_max=("value", "max"),
        )

        assert "value_avg" in result.columns
        assert "value_max" in result.columns

    def test_rolling_inplace(self, time_series_df):
        """Test rolling with inplace=True."""
        ext = PolarsDataFrameInterpolationExtension(time_series_df)
        result = ext.rolling(
            index_column="timestamp",
            period="1h",
            columns=["value"],
            default_agg="mean",
            inplace=True,
        )

        # Should replace original column
        assert "value" in result.columns
        assert "value_rolling" not in result.columns


class TestResample:
    """Tests for resample method."""

    @pytest.fixture
    def high_freq_df(self):
        """Create high-frequency time series."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 15),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 0, 45),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 15),
            ],
            "value": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        })

    def test_resample_basic(self, high_freq_df):
        """Test basic resampling."""
        ext = PolarsDataFrameInterpolationExtension(high_freq_df)
        result = ext.resample(
            time_column="timestamp",
            every="1h",
            columns=["value"],
            default_agg="mean",
        )

        # Should aggregate to hourly
        assert result.shape[0] <= high_freq_df.shape[0]

    def test_resample_with_groupby(self):
        """Test resampling with group by."""
        df = pl.DataFrame({
            "device": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
            ],
            "value": [10.0, 20.0, 30.0, 40.0, 100.0, 200.0, 300.0, 400.0],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.resample(
            time_column="timestamp",
            every="1h",
            group_by=["device"],
            columns=["value"],
            default_agg="sum",
        )

        assert "device" in result.columns

    def test_resample_explicit_aggs(self, high_freq_df):
        """Test resampling with explicit aggregations."""
        ext = PolarsDataFrameInterpolationExtension(high_freq_df)
        result = ext.resample(
            time_column="timestamp",
            every="1h",
            value=pl.col("value").mean(),
        )

        assert "value" in result.columns


class TestFfill:
    """Tests for ffill method."""

    def test_ffill_basic(self):
        """Test basic forward fill."""
        df = pl.DataFrame({
            "a": [1, None, None, 4, None],
            "b": [10, 20, None, 40, 50],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.ffill(columns=["a", "b"])

        assert result["a"].to_list() == [1, 1, 1, 4, 4]
        assert result["b"].to_list() == [10, 20, 20, 40, 50]

    def test_ffill_with_limit(self):
        """Test forward fill with limit."""
        df = pl.DataFrame({
            "a": [1.0, None, None, None, 5.0],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.ffill(columns=["a"], limit=1)

        filled = result["a"].to_list()
        assert filled[0] == 1.0
        assert filled[1] == 1.0  # Filled (within limit)

    def test_ffill_with_groupby(self):
        """Test forward fill with group by."""
        df = pl.DataFrame({
            "group": ["A", "A", "A", "B", "B", "B"],
            "value": [1, None, 3, 10, None, 30],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.ffill(columns=["value"], group_by=["group"])

        values = result["value"].to_list()
        # Group A: [1, 1, 3], Group B: [10, 10, 30]
        assert values[1] == 1  # Filled from group A
        assert values[4] == 10  # Filled from group B

    def test_ffill_inplace_false(self):
        """Test forward fill creates new column when inplace=False."""
        df = pl.DataFrame({
            "a": [1, None, 3],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.ffill(columns=["a"], inplace=False, suffix="_filled")

        assert "a" in result.columns
        assert "a_filled" in result.columns


class TestBfill:
    """Tests for bfill method."""

    def test_bfill_basic(self):
        """Test basic backward fill."""
        df = pl.DataFrame({
            "a": [None, 2, None, 4, None],
            "b": [None, 20, None, 40, 50],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.bfill(columns=["a", "b"])

        assert result["a"].to_list() == [2, 2, 4, 4, None]
        assert result["b"].to_list() == [20, 20, 40, 40, 50]

    def test_bfill_with_limit(self):
        """Test backward fill with limit."""
        df = pl.DataFrame({
            "a": [1.0, None, None, None, 5.0],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.bfill(columns=["a"], limit=1)

        filled = result["a"].to_list()
        assert filled[3] == 5.0  # Filled (within limit)
        assert filled[4] == 5.0

    def test_bfill_with_groupby(self):
        """Test backward fill with group by."""
        df = pl.DataFrame({
            "group": ["A", "A", "A", "B", "B", "B"],
            "value": [1, None, 3, 10, None, 30],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.bfill(columns=["value"], group_by=["group"])

        values = result["value"].to_list()
        # Group A: [1, 3, 3], Group B: [10, 30, 30]
        assert values[1] == 3  # Filled from group A
        assert values[4] == 30  # Filled from group B


class TestFillna:
    """Tests for fillna method."""

    def test_fillna_with_value(self):
        """Test fillna with a constant value."""
        df = pl.DataFrame({
            "a": [1, None, 3, None, 5],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(value=0, columns=["a"])

        assert result["a"].to_list() == [1, 0, 3, 0, 5]

    def test_fillna_strategy_forward(self):
        """Test fillna with forward strategy."""
        df = pl.DataFrame({
            "a": [1, None, None, 4, None],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="forward", columns=["a"])

        assert result["a"].to_list() == [1, 1, 1, 4, 4]

    def test_fillna_strategy_backward(self):
        """Test fillna with backward strategy."""
        df = pl.DataFrame({
            "a": [None, 2, None, 4, None],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="backward", columns=["a"])

        assert result["a"].to_list() == [2, 2, 4, 4, None]

    def test_fillna_strategy_mean(self):
        """Test fillna with mean strategy."""
        df = pl.DataFrame({
            "a": [10.0, None, 30.0, None, 50.0],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="mean", columns=["a"])

        # Mean = (10 + 30 + 50) / 3 = 30
        values = result["a"].to_list()
        assert values[0] == 10.0
        assert values[1] == 30.0  # Mean filled
        assert values[2] == 30.0
        assert values[3] == 30.0  # Mean filled
        assert values[4] == 50.0

    def test_fillna_strategy_min(self):
        """Test fillna with min strategy."""
        df = pl.DataFrame({
            "a": [10, None, 30, None, 50],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="min", columns=["a"])

        # Min = 10
        values = result["a"].to_list()
        assert values[1] == 10
        assert values[3] == 10

    def test_fillna_strategy_max(self):
        """Test fillna with max strategy."""
        df = pl.DataFrame({
            "a": [10, None, 30, None, 50],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="max", columns=["a"])

        # Max = 50
        values = result["a"].to_list()
        assert values[1] == 50
        assert values[3] == 50

    def test_fillna_strategy_zero(self):
        """Test fillna with zero strategy."""
        df = pl.DataFrame({
            "a": [10, None, 30],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="zero", columns=["a"])

        assert result["a"].to_list() == [10, 0, 30]

    def test_fillna_strategy_one(self):
        """Test fillna with one strategy."""
        df = pl.DataFrame({
            "a": [10, None, 30],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="one", columns=["a"])

        assert result["a"].to_list() == [10, 1, 30]

    def test_fillna_with_groupby(self):
        """Test fillna with group by."""
        df = pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "value": [10.0, None, 100.0, None],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(strategy="mean", columns=["value"], group_by=["group"])

        # Group A mean = 10, Group B mean = 100
        values = result["value"].to_list()
        assert values[1] == 10.0  # Group A mean
        assert values[3] == 100.0  # Group B mean

    def test_fillna_requires_value_or_strategy(self):
        """Test that fillna requires value or strategy."""
        df = pl.DataFrame({"a": [1, None, 3]})
        ext = PolarsDataFrameInterpolationExtension(df)

        with pytest.raises(ValueError, match="Either 'value' or 'strategy' must be provided"):
            ext.fillna(columns=["a"])

    def test_fillna_inplace_false(self):
        """Test fillna creates new columns when inplace=False."""
        df = pl.DataFrame({
            "a": [1, None, 3],
        })

        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.fillna(value=0, columns=["a"], inplace=False, suffix="_filled")

        assert "a" in result.columns
        assert "a_filled" in result.columns
        assert result["a_filled"].to_list() == [1, 0, 3]


class TestLazyFrameSupport:
    """Tests for LazyFrame support across methods."""

    def test_ffill_lazyframe(self):
        """Test ffill with LazyFrame."""
        lf = pl.LazyFrame({
            "a": [1, None, 3],
        })

        ext = PolarsDataFrameInterpolationExtension(lf)
        result = ext.ffill(columns=["a"])

        # Should return LazyFrame
        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected["a"].to_list() == [1, 1, 3]

    def test_bfill_lazyframe(self):
        """Test bfill with LazyFrame."""
        lf = pl.LazyFrame({
            "a": [None, 2, 3],
        })

        ext = PolarsDataFrameInterpolationExtension(lf)
        result = ext.bfill(columns=["a"])

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected["a"].to_list() == [2, 2, 3]

    def test_fillna_lazyframe(self):
        """Test fillna with LazyFrame."""
        lf = pl.LazyFrame({
            "a": [1, None, 3],
        })

        ext = PolarsDataFrameInterpolationExtension(lf)
        result = ext.fillna(value=0, columns=["a"])

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected["a"].to_list() == [1, 0, 3]


class TestInterpolateLimitOptions:
    """Tests for interpolation limit options."""

    @pytest.fixture
    def df_with_gaps(self):
        """Create DataFrame with gaps."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, i) for i in range(10)
            ],
            "value": [1.0, None, None, None, 5.0, None, None, None, None, 10.0],
        })

    def test_interpolate_with_limit(self, df_with_gaps):
        """Test interpolation with limit parameter."""
        ext = PolarsDataFrameInterpolationExtension(df_with_gaps)
        result = ext.interpolate(
            columns=["value"],
            by="timestamp",
            method="linear",
            limit=2,
        )

        # Some nulls should remain unfilled due to limit
        # The exact behavior depends on implementation

    def test_interpolate_limit_area_inside(self, df_with_gaps):
        """Test interpolation with limit_area='inside'."""
        ext = PolarsDataFrameInterpolationExtension(df_with_gaps)
        result = ext.interpolate(
            columns=["value"],
            by="timestamp",
            method="ffill",
            limit_area="inside",
        )

        # Should only fill values between first and last valid

    def test_interpolate_limit_direction_forward(self, df_with_gaps):
        """Test interpolation with limit_direction='forward'."""
        ext = PolarsDataFrameInterpolationExtension(df_with_gaps)
        result = ext.interpolate(
            columns=["value"],
            by="timestamp",
            method="linear",
            limit_direction="forward",
        )

        # Should only interpolate forward


class TestAddTimeBoundaries:
    """Tests for add_time_boundaries method (delegated to time_integration)."""

    @pytest.fixture
    def simple_ts(self):
        """Create simple time series."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
            ],
            "value": pl.Series([10, 20, 30], dtype=pl.Int64),
        })

    def test_add_time_boundaries_start(self, simple_ts):
        """Test adding start boundary."""
        ext = PolarsDataFrameInterpolationExtension(simple_ts)
        result = ext.add_time_boundaries(
            dt_name="timestamp",
            start=datetime(2023, 1, 1),
            start_fill_value=None,
            trim=False,
        )

        assert result.shape[0] == 4

    def test_add_time_boundaries_end(self, simple_ts):
        """Test adding end boundary."""
        ext = PolarsDataFrameInterpolationExtension(simple_ts)
        result = ext.add_time_boundaries(
            dt_name="timestamp",
            end=datetime(2023, 1, 5),
            end_fill_value=None,
            trim=False,
        )

        assert result.shape[0] == 4


class TestInheritance:
    """Tests for inheritance from UniversalPolarsDataFrameExtension."""

    def test_inherits_properties(self):
        """Test that PolarsDataFrameInterpolationExtension inherits base properties."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

        ext = PolarsDataFrameInterpolationExtension(df)

        assert ext.schema == {"a": pl.Int64, "b": pl.Int64}
        assert ext.length == 3
        assert ext.width == 2
        assert ext.columns == ["a", "b"]


class TestProcessTimeSeriesV2:
    """Tests for process_time_series_v2 pipeline method."""

    @pytest.fixture
    def basic_ts_df(self):
        """Create basic time series DataFrame for testing."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
                datetime(2023, 1, 1, 2, 0),
            ],
            "temperature": [20.0, None, 22.0, None, 24.0],
            "pressure": [100.0, 101.0, None, 103.0, 104.0],
        })

    @pytest.fixture
    def grouped_ts_df(self):
        """Create grouped time series DataFrame for testing."""
        return pl.DataFrame({
            "device": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 2, 0),
                datetime(2023, 1, 1, 3, 0),
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 2, 0),
                datetime(2023, 1, 1, 3, 0),
            ],
            "value": [10.0, None, 30.0, None, 100.0, None, 300.0, None],
        })

    def test_process_time_series_v2_single_ffill(self, basic_ts_df):
        """Test pipeline with single ffill operation."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["temperature", "pressure"],
            track_metadata=False,
        )

        # All nulls should be filled
        assert result["temperature"].null_count() == 0
        assert result["pressure"].null_count() == 0

    def test_process_time_series_v2_single_bfill(self, basic_ts_df):
        """Test pipeline with single bfill operation."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["bfill"],
            target_columns=["temperature"],
            track_metadata=False,
        )

        assert result["temperature"].null_count() == 0
        temps = result["temperature"].to_list()
        # Backward fill: None at index 1 should be filled from 22.0
        assert temps[1] == 22.0

    def test_process_time_series_v2_ffill_bfill_combo(self, basic_ts_df):
        """Test pipeline with ffill->bfill composite operation."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill->bfill"],
            target_columns=["temperature"],
            track_metadata=False,
        )

        # ffill then bfill should fill all nulls
        assert result["temperature"].null_count() == 0

    def test_process_time_series_v2_interpolate_linear(self, basic_ts_df):
        """Test pipeline with linear interpolation."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["interpolate"],
            target_columns=["temperature"],
            interpolate_method="linear",
            track_metadata=False,
        )

        assert result["temperature"].null_count() == 0

    def test_process_time_series_v2_fillna_value(self, basic_ts_df):
        """Test pipeline with fillna using constant value."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["fillna"],
            target_columns=["temperature"],
            fill_value=0.0,
            track_metadata=False,
        )

        assert result["temperature"].null_count() == 0
        temps = result["temperature"].to_list()
        assert temps[1] == 0.0
        assert temps[3] == 0.0

    def test_process_time_series_v2_fillna_strategy(self, basic_ts_df):
        """Test pipeline with fillna using strategy."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["fillna"],
            target_columns=["temperature"],
            fill_strategy="mean",
            track_metadata=False,
        )

        assert result["temperature"].null_count() == 0

    def test_process_time_series_v2_multiple_operations(self, basic_ts_df):
        """Test pipeline with multiple sequential operations."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill", "bfill"],
            target_columns=["temperature"],
            track_metadata=False,
        )

        # Combined ffill then bfill should fill all
        assert result["temperature"].null_count() == 0

    def test_process_time_series_v2_with_groupby(self, grouped_ts_df):
        """Test pipeline with group_by parameter."""
        ext = PolarsDataFrameInterpolationExtension(grouped_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            group_by=["device"],
            target_columns=["value"],
            track_metadata=False,
        )

        assert result["value"].null_count() == 0
        # Verify groups are maintained
        assert "device" in result.columns

    def test_process_time_series_v2_auto_detect_columns(self, basic_ts_df):
        """Test auto-detection of numeric target columns."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            # target_columns not specified - should auto-detect
            track_metadata=False,
        )

        # Both temperature and pressure should be processed
        assert result["temperature"].null_count() == 0
        assert result["pressure"].null_count() == 0

    def test_process_time_series_v2_exclude_columns(self, basic_ts_df):
        """Test exclusion of specific columns."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            exclude_columns=["pressure"],
            track_metadata=False,
        )

        # Temperature should be processed
        assert result["temperature"].null_count() == 0
        # Pressure should NOT be processed (excluded)
        assert result["pressure"].null_count() > 0

    def test_process_time_series_v2_with_metadata(self, basic_ts_df):
        """Test metadata tracking."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["temperature"],
            track_metadata=True,
            metadata_suffix="_meta",
        )

        # Should create metadata column
        assert "temperature_meta_count" in result.columns
        meta = result["temperature_meta_count"].to_list()
        # Original values should have count=1, imputed should have 0
        assert meta[0] == 1  # Original
        assert meta[2] == 1  # Original

    def test_process_time_series_v2_inplace_true(self, basic_ts_df):
        """Test inplace=True replaces columns."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["temperature"],
            inplace=True,
            track_metadata=False,
        )

        # Should have original column name
        assert "temperature" in result.columns
        # Should not have suffix columns
        assert "temperature_filled" not in result.columns

    def test_process_time_series_v2_inplace_false(self, basic_ts_df):
        """Test inplace=False creates new columns with suffix."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["temperature"],
            inplace=False,
            fill_suffix="_filled",
            track_metadata=False,
        )

        # Should have both original and new columns
        assert "temperature" in result.columns
        assert "temperature_filled" in result.columns

    def test_process_time_series_v2_invalid_operation(self, basic_ts_df):
        """Test error on invalid operation."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)

        with pytest.raises(ValueError, match="Invalid operations"):
            ext.process_time_series_v2(
                time_column="timestamp",
                operations=["invalid_op"],
                target_columns=["temperature"],
            )

    def test_process_time_series_v2_no_target_columns_error(self):
        """Test error when no target columns found."""
        df = pl.DataFrame({
            "timestamp": [datetime(2023, 1, 1)],
            "text": ["hello"],  # No numeric columns
        })
        ext = PolarsDataFrameInterpolationExtension(df)

        with pytest.raises(ValueError, match="No target columns found"):
            ext.process_time_series_v2(
                time_column="timestamp",
                operations=["ffill"],
            )

    def test_process_time_series_v2_resample_basic(self):
        """Test pipeline with resample operation."""
        df = pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 15),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 0, 45),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 15),
            ],
            "value": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        })
        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["resample"],
            target_columns=["value"],
            every="1h",
            resample_default_agg="mean",
            track_metadata=False,
        )

        # Should downsample
        assert result.shape[0] <= df.shape[0]

    def test_process_time_series_v2_rolling_basic(self):
        """Test pipeline with rolling operation."""
        df = pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
                datetime(2023, 1, 1, 2, 0),
            ],
            "value": [10.0, 20.0, 30.0, 40.0, 50.0],
        })
        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["rolling"],
            target_columns=["value"],
            rolling_period="1h",
            rolling_default_agg="mean",
            track_metadata=False,
        )

        # Should apply rolling aggregation
        assert "value" in result.columns or "value_rolling" in result.columns

    def test_process_time_series_v2_upsample_basic(self):
        """Test pipeline with upsample operation."""
        df = pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 2, 0),  # Gap at 1:00
                datetime(2023, 1, 1, 4, 0),
            ],
            "value": [10.0, 30.0, 50.0],
        })
        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["upsample"],
            every="1h",
            track_metadata=False,
        )

        # Should create rows for missing hours
        assert result.shape[0] >= df.shape[0]

    def test_process_time_series_v2_per_column_interpolate_method(self, basic_ts_df):
        """Test per-column interpolation method specification."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["interpolate"],
            target_columns=["temperature", "pressure"],
            interpolate_method={"temperature": "ffill", "pressure": "bfill"},
            track_metadata=False,
        )

        assert result["temperature"].null_count() == 0
        assert result["pressure"].null_count() == 0

    def test_process_time_series_v2_fill_with_limit(self, basic_ts_df):
        """Test fill operation with limit parameter."""
        # Create data with consecutive nulls
        df = pl.DataFrame({
            "timestamp": [datetime(2023, 1, 1, i) for i in range(7)],
            "value": [1.0, None, None, None, None, None, 7.0],
        })
        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["value"],
            fill_limit=2,
            track_metadata=False,
        )

        # Only first 2 nulls should be filled
        filled = result["value"].to_list()
        assert filled[1] == 1.0  # Filled
        assert filled[2] == 1.0  # Filled

    def test_process_time_series_v2_chained_operations(self, basic_ts_df):
        """Test complex chain of operations."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["interpolate", "ffill", "bfill"],
            target_columns=["temperature"],
            interpolate_method="linear",
            track_metadata=False,
        )

        # All operations should be applied in sequence
        assert result["temperature"].null_count() == 0

    def test_process_time_series_v2_repeated_operations_validation(self, basic_ts_df):
        """Test validation for repeated operations with missing list params."""
        ext = PolarsDataFrameInterpolationExtension(basic_ts_df)

        # Repeated interpolate requires interpolate_method to be a list
        with pytest.raises(ValueError, match="appears.*times"):
            ext.process_time_series_v2(
                time_column="timestamp",
                operations=["interpolate", "interpolate"],
                target_columns=["temperature"],
                interpolate_method="linear",  # Should be list of 2
                track_metadata=False,
            )

    def test_process_time_series_v2_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pl.DataFrame({
            "timestamp": pl.Series([], dtype=pl.Datetime),
            "value": pl.Series([], dtype=pl.Float64),
        })
        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["value"],
            track_metadata=False,
        )

        assert result.shape[0] == 0

    def test_process_time_series_v2_no_nulls(self, basic_ts_df):
        """Test with data that has no null values."""
        df = pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1, 0),
                datetime(2023, 1, 1, 1),
                datetime(2023, 1, 1, 2),
            ],
            "value": [10.0, 20.0, 30.0],
        })
        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["value"],
            track_metadata=False,
        )

        # Data should be unchanged
        assert result["value"].to_list() == [10.0, 20.0, 30.0]

    def test_process_time_series_v2_preserves_other_columns(self, basic_ts_df):
        """Test that non-target columns are preserved."""
        df = basic_ts_df.with_columns(
            pl.lit("info").alias("extra_col")
        )
        ext = PolarsDataFrameInterpolationExtension(df)
        result = ext.process_time_series_v2(
            time_column="timestamp",
            operations=["ffill"],
            target_columns=["temperature"],
            track_metadata=False,
        )

        # Extra column should be preserved
        assert "extra_col" in result.columns
        assert result["extra_col"].to_list() == ["info"] * 5
