"""
Tests for groupby.py - PolarsUniversalGroupBy extension
"""

import pytest
import polars as pl
from datetime import datetime, timedelta
from enhancedpolars.groupby import PolarsUniversalGroupBy, UniversalPolarsDataFrameGroupByExtension


class TestAggBasic:
    """Tests for basic aggregation functionality."""

    @pytest.fixture
    def grouped_df(self):
        """Create a DataFrame for groupby tests."""
        return pl.DataFrame({
            "group": ["A", "A", "B", "B", "B"],
            "value": [1, 2, 3, 4, 5],
            "other": [10.0, 20.0, 30.0, 40.0, 50.0],
        })

    def test_agg_polars_style(self, grouped_df):
        """Test aggregation with Polars-style expressions."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.agg(pl.col("value").sum().alias("value_sum"))

        assert result.shape[0] == 2
        assert "value_sum" in result.columns
        # Group A: 1+2=3, Group B: 3+4+5=12
        result_sorted = result.sort("group")
        assert result_sorted.filter(pl.col("group") == "A")["value_sum"][0] == 3
        assert result_sorted.filter(pl.col("group") == "B")["value_sum"][0] == 12

    def test_agg_pandas_style_single(self, grouped_df):
        """Test aggregation with pandas-style dict (single agg per column)."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.agg({"value": "sum", "other": "mean"})

        assert result.shape[0] == 2
        assert "value" in result.columns
        assert "other" in result.columns

    def test_agg_pandas_style_multiple(self, grouped_df):
        """Test aggregation with pandas-style dict (multiple aggs per column)."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.agg({"value": ["sum", "mean", "max"]})

        assert result.shape[0] == 2
        assert "value_sum" in result.columns
        assert "value_mean" in result.columns
        assert "value_max" in result.columns

    def test_agg_named_kwargs(self, grouped_df):
        """Test aggregation with named keyword arguments."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.agg(total_value=pl.col("value").sum())

        assert "total_value" in result.columns

    def test_agg_nunique_alias(self, grouped_df):
        """Test that 'nunique' is aliased to 'n_unique'."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.agg({"value": "nunique"})

        assert result.shape[0] == 2

    def test_agg_invalid_function_raises(self, grouped_df):
        """Test that invalid aggregation function raises ValueError."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        with pytest.raises(ValueError, match="not supported"):
            gb.agg({"value": "invalid_func"})


class TestApply:
    """Tests for apply method."""

    @pytest.fixture
    def grouped_df(self):
        return pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1, 2, 3, 4],
        })

    def test_apply_basic(self, grouped_df):
        """Test basic apply functionality."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])

        def double_values(df):
            return df.with_columns(pl.col("value") * 2)

        result = gb.apply(double_values)

        assert result.shape[0] == 4
        # All values should be doubled
        assert result["value"].sum() == (1+2+3+4) * 2

    def test_apply_returns_subset(self, grouped_df):
        """Test apply that returns a subset of rows."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])

        def take_first(df):
            return df.head(1)

        result = gb.apply(take_first)

        assert result.shape[0] == 2  # One row per group


class TestFillMethods:
    """Tests for ffill, bfill, and fillna methods."""

    @pytest.fixture
    def df_with_nulls(self):
        return pl.DataFrame({
            "group": ["A", "A", "A", "B", "B", "B"],
            "value": [1, None, 3, None, 5, None],
            "idx": [1, 2, 3, 1, 2, 3],
        })

    def test_ffill_basic(self, df_with_nulls):
        """Test forward fill with groups."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        result = gb.ffill(columns=["value"])

        result_sorted = result.sort(["group", "idx"])
        # Group A: [1, 1, 3], Group B: [None, 5, 5]
        group_a = result_sorted.filter(pl.col("group") == "A")
        assert group_a["value"].to_list() == [1, 1, 3]

    def test_bfill_basic(self, df_with_nulls):
        """Test backward fill with groups."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        result = gb.bfill(columns=["value"])

        result_sorted = result.sort(["group", "idx"])
        # Group A: [1, 3, 3], Group B: [5, 5, None]
        group_a = result_sorted.filter(pl.col("group") == "A")
        assert group_a["value"].to_list() == [1, 3, 3]

    def test_ffill_all_columns(self, df_with_nulls):
        """Test forward fill on all columns (excluding group cols)."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        result = gb.ffill()

        assert result.shape == df_with_nulls.shape

    def test_fillna_with_value(self, df_with_nulls):
        """Test fillna with a literal value."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        result = gb.fillna(value=0, columns=["value"])

        assert result["value"].null_count() == 0
        assert 0 in result["value"].to_list()

    def test_fillna_with_strategy_mean(self, df_with_nulls):
        """Test fillna with mean strategy."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        result = gb.fillna(strategy="mean", columns=["value"])

        # Should fill nulls with group mean
        assert result["value"].null_count() == 0

    def test_fillna_with_strategy_zero(self, df_with_nulls):
        """Test fillna with zero strategy."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        result = gb.fillna(strategy="zero", columns=["value"])

        assert result["value"].null_count() == 0
        assert 0 in result["value"].to_list()

    def test_fillna_with_strategy_one(self, df_with_nulls):
        """Test fillna with one strategy."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        result = gb.fillna(strategy="one", columns=["value"])

        assert result["value"].null_count() == 0
        assert 1 in result["value"].to_list()

    def test_fillna_requires_value_or_strategy(self, df_with_nulls):
        """Test that fillna raises if neither value nor strategy provided."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        with pytest.raises(ValueError, match="Either 'value' or 'strategy'"):
            gb.fillna(columns=["value"])

    def test_fillna_invalid_strategy_raises(self, df_with_nulls):
        """Test that invalid strategy raises ValueError."""
        gb = PolarsUniversalGroupBy(df_with_nulls, ["group"])
        with pytest.raises(ValueError, match="Unknown strategy"):
            gb.fillna(strategy="invalid", columns=["value"])


class TestEwm:
    """Tests for exponential weighted moving calculations."""

    @pytest.fixture
    def time_series_df(self):
        return pl.DataFrame({
            "group": ["A", "A", "A", "B", "B", "B"],
            "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        })

    def test_ewm_basic_mean(self, time_series_df):
        """Test EWM mean calculation."""
        gb = PolarsUniversalGroupBy(time_series_df, ["group"])
        result = gb.ewm("value", alpha=0.5, smooth="mean")

        assert "smooth" in result.columns
        assert result.shape[0] == 6

    def test_ewm_with_span(self, time_series_df):
        """Test EWM with span parameter."""
        gb = PolarsUniversalGroupBy(time_series_df, ["group"])
        result = gb.ewm("value", span=3, smooth="mean")

        assert "smooth" in result.columns

    def test_ewm_with_com(self, time_series_df):
        """Test EWM with center of mass parameter."""
        gb = PolarsUniversalGroupBy(time_series_df, ["group"])
        result = gb.ewm("value", com=2, smooth="mean")

        assert "smooth" in result.columns

    def test_ewm_multiple_aggs(self, time_series_df):
        """Test EWM with multiple aggregation types."""
        gb = PolarsUniversalGroupBy(time_series_df, ["group"])
        result = gb.ewm("value", alpha=0.5, avg="mean", volatility="std")

        assert "avg" in result.columns
        assert "volatility" in result.columns

    def test_ewm_default_alpha(self, time_series_df):
        """Test EWM with default alpha value."""
        gb = PolarsUniversalGroupBy(time_series_df, ["group"])
        result = gb.ewm("value", smooth="mean")  # No smoothing param provided

        assert "smooth" in result.columns

    def test_ewm_multiple_smoothing_params_raises(self, time_series_df):
        """Test that multiple smoothing parameters raise ValueError."""
        gb = PolarsUniversalGroupBy(time_series_df, ["group"])
        with pytest.raises(ValueError, match="Only one of"):
            gb.ewm("value", alpha=0.5, span=3, smooth="mean")

    def test_ewm_invalid_agg_raises(self, time_series_df):
        """Test that invalid aggregation raises ValueError."""
        gb = PolarsUniversalGroupBy(time_series_df, ["group"])
        with pytest.raises(ValueError, match="Unsupported EWM aggregation"):
            gb.ewm("value", alpha=0.5, invalid="invalid_agg")


class TestResample:
    """Tests for resample (group_by_dynamic wrapper)."""

    @pytest.fixture
    def time_df(self):
        """Create a time series DataFrame."""
        return pl.DataFrame({
            "group": ["A", "A", "A", "B", "B", "B"],
            "time": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 1, 0),
            ],
            "value": [1, 2, 3, 4, 5, 6],
        }).sort("time")

    def test_resample_basic(self, time_df):
        """Test basic resample functionality."""
        gb = PolarsUniversalGroupBy(time_df, ["group"])
        result = gb.resample("time", every="1h", value_sum=pl.col("value").sum())

        assert "value_sum" in result.columns

    def test_resample_with_offset(self, time_df):
        """Test resample with offset."""
        gb = PolarsUniversalGroupBy(time_df, ["group"])
        result = gb.resample("time", every="1h", offset="30m", value_sum=pl.col("value").sum())

        assert "value_sum" in result.columns


class TestUpsample:
    """Tests for upsample method."""

    @pytest.fixture
    def sparse_time_df(self):
        """Create a sparse time series DataFrame."""
        return pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "time": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 1, 0),
            ],
            "value": [1, 2, 3, 4],
        })

    def test_upsample_basic(self, sparse_time_df):
        """Test basic upsample functionality."""
        gb = PolarsUniversalGroupBy(sparse_time_df, ["group"])
        result = gb.upsample("time", every="30m")

        # Should have more rows after upsampling
        assert result.shape[0] >= sparse_time_df.shape[0]


class TestDelegation:
    """Tests for delegation to native Polars GroupBy methods."""

    @pytest.fixture
    def grouped_df(self):
        return pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1, 2, 3, 4],
        })

    def test_native_max(self, grouped_df):
        """Test delegation to native max() method."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.max()

        assert result.shape[0] == 2
        result_sorted = result.sort("group")
        assert result_sorted["value"].to_list() == [2, 4]

    def test_native_min(self, grouped_df):
        """Test delegation to native min() method."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.min()

        assert result.shape[0] == 2
        result_sorted = result.sort("group")
        assert result_sorted["value"].to_list() == [1, 3]

    def test_native_mean(self, grouped_df):
        """Test delegation to native mean() method."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.mean()

        assert result.shape[0] == 2
        result_sorted = result.sort("group")
        assert result_sorted["value"].to_list() == [1.5, 3.5]

    def test_native_sum(self, grouped_df):
        """Test delegation to native sum() method."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.sum()

        assert result.shape[0] == 2
        result_sorted = result.sort("group")
        assert result_sorted["value"].to_list() == [3, 7]

    def test_native_count(self, grouped_df):
        """Test delegation to native count() method."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        result = gb.len()

        assert result.shape[0] == 2
        assert result["len"].to_list() == [2, 2]

    def test_invalid_method_raises(self, grouped_df):
        """Test that invalid method raises AttributeError."""
        gb = PolarsUniversalGroupBy(grouped_df, ["group"])
        with pytest.raises(AttributeError):
            gb.nonexistent_method()


class TestUniversalPolarsDataFrameGroupByExtension:
    """Tests for UniversalPolarsDataFrameGroupByExtension class."""

    def test_call_creates_groupby(self):
        """Test that __call__ creates a PolarsUniversalGroupBy object."""
        df = pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1, 2, 3, 4],
        })

        ext = UniversalPolarsDataFrameGroupByExtension(df)
        gb = ext("group")

        assert isinstance(gb, PolarsUniversalGroupBy)

    def test_call_multiple_groups(self):
        """Test __call__ with multiple group columns."""
        df = pl.DataFrame({
            "group1": ["A", "A", "B", "B"],
            "group2": ["X", "Y", "X", "Y"],
            "value": [1, 2, 3, 4],
        })

        ext = UniversalPolarsDataFrameGroupByExtension(df)
        gb = ext("group1", "group2")

        assert isinstance(gb, PolarsUniversalGroupBy)
        result = gb.sum()
        assert result.shape[0] == 4  # All combinations


class TestLazyFrame:
    """Tests for GroupBy with LazyFrames."""

    def test_groupby_lazy(self):
        """Test groupby with LazyFrame."""
        lf = pl.LazyFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1, 2, 3, 4],
        })

        gb = PolarsUniversalGroupBy(lf, ["group"])
        result = gb.sum()

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected.shape[0] == 2

    def test_agg_lazy(self):
        """Test agg with LazyFrame."""
        lf = pl.LazyFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1, 2, 3, 4],
        })

        gb = PolarsUniversalGroupBy(lf, ["group"])
        result = gb.agg({"value": "sum"})

        assert isinstance(result, pl.LazyFrame)


class TestInterpolate:
    """Tests for interpolate method with groups."""

    @pytest.fixture
    def df_with_gaps(self):
        return pl.DataFrame({
            "group": ["A", "A", "A", "B", "B", "B"],
            "idx": [1, 2, 3, 1, 2, 3],
            "value": [1.0, None, 3.0, 4.0, None, 6.0],
        })

    def test_interpolate_basic(self, df_with_gaps):
        """Test basic interpolation with groups."""
        gb = PolarsUniversalGroupBy(df_with_gaps, ["group"])
        result = gb.interpolate(columns=["value"], by="idx")

        # Nulls should be filled by interpolation
        assert result["value"].null_count() == 0

    def test_interpolate_all_columns(self, df_with_gaps):
        """Test interpolation on all applicable columns."""
        gb = PolarsUniversalGroupBy(df_with_gaps, ["group"])
        result = gb.interpolate(by="idx")

        assert result.shape == df_with_gaps.shape


class TestInheritance:
    """Tests for inheritance from UniversalPolarsDataFrameExtension."""

    def test_inherits_properties(self):
        """Test that PolarsUniversalGroupBy inherits base properties."""
        df = pl.DataFrame({
            "group": ["A", "A", "B"],
            "value": [1, 2, 3],
        })

        gb = PolarsUniversalGroupBy(df, ["group"])

        assert gb.schema == {"group": pl.String, "value": pl.Int64}
        assert gb.length == 3
        assert gb.width == 2
        assert gb.columns == ["group", "value"]
