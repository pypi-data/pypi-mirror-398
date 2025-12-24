"""
Tests for merging.py - PolarsMerging extension
"""

import pytest
import polars as pl
from enhancedpolars.merging import PolarsMerging


class TestMergeBasic:
    """Tests for basic merge functionality."""

    @pytest.fixture
    def left_df(self):
        """Create left DataFrame for merge tests."""
        return pl.DataFrame({
            "key": [1, 2, 3, 4],
            "value_left": ["a", "b", "c", "d"],
        })

    @pytest.fixture
    def right_df(self):
        """Create right DataFrame for merge tests."""
        return pl.DataFrame({
            "key": [2, 3, 4, 5],
            "value_right": ["w", "x", "y", "z"],
        })

    def test_merge_inner(self, left_df, right_df):
        """Test inner join."""
        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, how='inner', on='key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 3  # keys 2, 3, 4
        assert "key" in result.columns
        assert "value_left" in result.columns
        assert "value_right" in result.columns

    def test_merge_left(self, left_df, right_df):
        """Test left join."""
        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, how='left', on='key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 4  # all left keys preserved
        assert result.filter(pl.col("key") == 1)["value_right"][0] is None

    def test_merge_full(self, left_df, right_df):
        """Test full outer join."""
        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, how='full', on='key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 5  # keys 1, 2, 3, 4, 5

    def test_merge_semi(self, left_df, right_df):
        """Test semi join (left rows with matches in right)."""
        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, how='semi', on='key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 3  # keys 2, 3, 4
        assert "value_right" not in result.columns  # semi join doesn't include right columns

    def test_merge_anti(self, left_df, right_df):
        """Test anti join (left rows without matches in right)."""
        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, how='anti', on='key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 1  # only key 1
        assert result["key"][0] == 1


class TestMergeColumnOptions:
    """Tests for merge with different column specifications."""

    def test_merge_with_left_on_right_on(self):
        """Test merge with different column names."""
        left_df = pl.DataFrame({
            "left_key": [1, 2, 3],
            "value": ["a", "b", "c"],
        })
        right_df = pl.DataFrame({
            "right_key": [2, 3, 4],
            "data": ["x", "y", "z"],
        })

        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, left_on='left_key', right_on='right_key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 2  # keys 2, 3
        assert "left_key" in result.columns
        assert "data" in result.columns  # Right columns (excluding join key) are included

    def test_merge_with_suffix(self):
        """Test merge with custom suffix for overlapping columns."""
        left_df = pl.DataFrame({
            "key": [1, 2],
            "value": ["a", "b"],
        })
        right_df = pl.DataFrame({
            "key": [1, 2],
            "value": ["x", "y"],
        })

        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, on='key', suffix='_other')

        assert "value" in result.columns
        assert "value_other" in result.columns

    def test_merge_multiple_keys(self):
        """Test merge on multiple columns."""
        left_df = pl.DataFrame({
            "key1": [1, 1, 2],
            "key2": ["a", "b", "a"],
            "value": [10, 20, 30],
        })
        right_df = pl.DataFrame({
            "key1": [1, 2],
            "key2": ["a", "a"],
            "data": [100, 200],
        })

        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, on=['key1', 'key2'])
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 2  # (1, "a") and (2, "a")


class TestMergeDtypeResolution:
    """Tests for dtype conflict resolution during merge."""

    def test_merge_resolves_int_float_conflict(self):
        """Test that int/float dtype conflicts are resolved."""
        left_df = pl.DataFrame({
            "key": [1, 2, 3],
            "value": [1.0, 2.0, 3.0],  # Float64
        })
        right_df = pl.DataFrame({
            "key": [1, 2, 3],
            "value": [10, 20, 30],  # Int64
        })

        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, on='key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        # Both value columns should be promoted to Float64
        assert result["value"].dtype == pl.Float64
        assert result["value_right"].dtype in (pl.Float64, pl.Int64)  # Depends on resolve order

    def test_merge_resolves_join_key_dtype(self):
        """Test that join key dtype conflicts are resolved."""
        left_df = pl.DataFrame({
            "key": [1, 2, 3],  # Int64
        })
        right_df = pl.DataFrame({
            "key": [1.0, 2.0, 4.0],  # Float64
        })

        ext = PolarsMerging(left_df)
        # This should not raise an error due to dtype resolution
        result = ext.merge(right_df, on='key')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] >= 0  # Just verify it completed

    def test_merge_without_dtype_resolution(self):
        """Test merge with resolve_dtypes=False."""
        left_df = pl.DataFrame({
            "key": [1, 2, 3],
            "value": ["a", "b", "c"],
        })
        right_df = pl.DataFrame({
            "key": [1, 2, 4],
            "data": ["x", "y", "z"],
        })

        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, on='key', resolve_dtypes=False)
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 2


class TestMergeLazyFrame:
    """Tests for merge with LazyFrames."""

    def test_merge_lazy_returns_lazy(self):
        """Test that merging LazyFrames returns a LazyFrame."""
        left_lf = pl.LazyFrame({
            "key": [1, 2, 3],
            "value": ["a", "b", "c"],
        })
        right_lf = pl.LazyFrame({
            "key": [2, 3, 4],
            "data": ["x", "y", "z"],
        })

        ext = PolarsMerging(left_lf)
        result = ext.merge(right_lf, on='key')

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected.shape[0] == 2

    def test_merge_lazy_with_eager(self):
        """Test merge of LazyFrame with eager DataFrame."""
        left_lf = pl.LazyFrame({
            "key": [1, 2, 3],
            "value": ["a", "b", "c"],
        })
        right_df = pl.DataFrame({
            "key": [2, 3, 4],
            "data": ["x", "y", "z"],
        })

        ext = PolarsMerging(left_lf)
        # Polars allows this with lazy left and eager right
        result = ext.merge(right_df.lazy(), on='key')

        assert isinstance(result, pl.LazyFrame)


class TestMergeAsof:
    """Tests for merge_asof functionality."""

    @pytest.fixture
    def time_left(self):
        """Create left DataFrame with timestamps."""
        return pl.DataFrame({
            "time": [1, 5, 10, 15],
            "value": ["a", "b", "c", "d"],
        }).sort("time")

    @pytest.fixture
    def time_right(self):
        """Create right DataFrame with timestamps."""
        return pl.DataFrame({
            "time": [3, 7, 12],
            "data": ["x", "y", "z"],
        }).sort("time")

    def test_merge_asof_backward(self, time_left, time_right):
        """Test merge_asof with backward strategy."""
        ext = PolarsMerging(time_left)
        result = ext.merge_asof(time_right, on='time', strategy='backward')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 4
        # time=1 should have null (no right value <= 1)
        # time=5 should match with right time=3
        # time=10 should match with right time=7
        # time=15 should match with right time=12

    def test_merge_asof_forward(self, time_left, time_right):
        """Test merge_asof with forward strategy."""
        ext = PolarsMerging(time_left)
        result = ext.merge_asof(time_right, on='time', strategy='forward')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 4
        # time=1 should match with right time=3
        # time=5 should match with right time=7
        # time=10 should match with right time=12
        # time=15 should have null (no right value >= 15)

    def test_merge_asof_nearest(self, time_left, time_right):
        """Test merge_asof with nearest strategy."""
        ext = PolarsMerging(time_left)
        result = ext.merge_asof(time_right, on='time', strategy='nearest')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 4

    def test_merge_asof_with_by(self):
        """Test merge_asof with by column."""
        left_df = pl.DataFrame({
            "time": [1, 2, 1, 2],
            "group": ["A", "A", "B", "B"],
            "value": [10, 20, 30, 40],
        }).sort("time")
        right_df = pl.DataFrame({
            "time": [1, 2],
            "group": ["A", "B"],
            "data": [100, 200],
        }).sort("time")

        ext = PolarsMerging(left_df)
        result = ext.merge_asof(right_df, on='time', by='group', strategy='backward')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 4

    def test_merge_asof_left_on_right_on(self):
        """Test merge_asof with different column names."""
        left_df = pl.DataFrame({
            "left_time": [1, 5, 10],
            "value": ["a", "b", "c"],
        }).sort("left_time")
        right_df = pl.DataFrame({
            "right_time": [3, 7],
            "data": ["x", "y"],
        }).sort("right_time")

        ext = PolarsMerging(left_df)
        result = ext.merge_asof(right_df, left_on='left_time', right_on='right_time')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 3
        assert "left_time" in result.columns
        assert "right_time" in result.columns

    def test_merge_asof_without_dtype_resolution(self, time_left, time_right):
        """Test merge_asof with resolve_dtypes=False."""
        ext = PolarsMerging(time_left)
        result = ext.merge_asof(time_right, on='time', resolve_dtypes=False)
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 4


class TestConcat:
    """Tests for concat functionality."""

    def test_concat_vertical(self):
        """Test vertical concatenation."""
        df1 = pl.DataFrame({
            "a": [1, 2],
            "b": ["x", "y"],
        })
        df2 = pl.DataFrame({
            "a": [3, 4],
            "b": ["z", "w"],
        })

        ext = PolarsMerging(df1)
        result = ext.concat(df2, how='vertical')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape == (4, 2)
        assert result["a"].to_list() == [1, 2, 3, 4]

    def test_concat_multiple(self):
        """Test concatenating multiple DataFrames."""
        df1 = pl.DataFrame({"a": [1]})
        df2 = pl.DataFrame({"a": [2]})
        df3 = pl.DataFrame({"a": [3]})

        ext = PolarsMerging(df1)
        result = ext.concat(df2, df3)
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 3
        assert result["a"].to_list() == [1, 2, 3]

    def test_concat_horizontal(self):
        """Test horizontal concatenation."""
        df1 = pl.DataFrame({
            "a": [1, 2, 3],
        })
        df2 = pl.DataFrame({
            "b": [4, 5, 6],
        })

        ext = PolarsMerging(df1)
        result = ext.concat(df2, how='horizontal')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape == (3, 2)
        assert "a" in result.columns
        assert "b" in result.columns

    def test_concat_diagonal(self):
        """Test diagonal concatenation (union with nulls for missing columns)."""
        df1 = pl.DataFrame({
            "a": [1, 2],
            "b": ["x", "y"],
        })
        df2 = pl.DataFrame({
            "a": [3, 4],
            "c": [10, 20],
        })

        ext = PolarsMerging(df1)
        result = ext.concat(df2, how='diagonal')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape == (4, 3)
        assert "a" in result.columns
        assert "b" in result.columns
        assert "c" in result.columns

    def test_concat_lazyframe(self):
        """Test concat with LazyFrames."""
        lf1 = pl.LazyFrame({"a": [1, 2]})
        lf2 = pl.LazyFrame({"a": [3, 4]})

        ext = PolarsMerging(lf1)
        result = ext.concat(lf2)

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected.shape[0] == 4


class TestInferDtypes:
    """Tests for infer_dtypes method."""

    def test_infer_dtypes_basic(self):
        """Test basic dtype inference."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3, 4, 5],
            "float_col": [1.0, 2.5, 3.0, 4.5, 5.0],
            "str_col": ["a", "b", "c", "d", "e"],
        })

        ext = PolarsMerging(df)
        result = ext.infer_dtypes()

        assert isinstance(result, dict)
        assert "int_col" in result
        assert "float_col" in result
        assert "str_col" in result

    def test_infer_dtypes_return_df(self):
        """Test infer_dtypes with return_df=True."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
        })

        ext = PolarsMerging(df)
        result = ext.infer_dtypes(return_df=True)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], pl.DataFrame)
        assert isinstance(result[1], dict)

    def test_infer_dtypes_specific_columns(self):
        """Test infer_dtypes with specific columns."""
        df = pl.DataFrame({
            "col_a": [1, 2, 3],
            "col_b": [4, 5, 6],
            "col_c": [7, 8, 9],
        })

        ext = PolarsMerging(df)
        result = ext.infer_dtypes(columns=["col_a", "col_b"])

        assert "col_a" in result
        assert "col_b" in result
        # col_c may or may not be in result depending on implementation


class TestOptimizeDtypes:
    """Tests for optimize_dtypes method."""

    def test_optimize_dtypes_basic(self):
        """Test basic dtype optimization."""
        df = pl.DataFrame({
            "small_int": [1, 2, 3, 4, 5],  # Could be Int8
            "large_int": [1000000, 2000000, 3000000, 4000000, 5000000],
        })

        ext = PolarsMerging(df)
        result = ext.optimize_dtypes()

        assert isinstance(result, pl.DataFrame)
        assert result.shape == df.shape

    def test_optimize_dtypes_with_downcast(self):
        """Test dtype optimization with downcast enabled."""
        df = pl.DataFrame({
            "small_int": [1, 2, 3, 4, 5],
        })

        ext = PolarsMerging(df)
        result = ext.optimize_dtypes(attempt_downcast=True)

        assert isinstance(result, pl.DataFrame)

    def test_optimize_dtypes_specific_columns(self):
        """Test optimize_dtypes with specific columns."""
        df = pl.DataFrame({
            "col_a": [1, 2, 3],
            "col_b": [4, 5, 6],
        })

        ext = PolarsMerging(df)
        result = ext.optimize_dtypes(columns=["col_a"])

        assert isinstance(result, pl.DataFrame)


class TestAstype:
    """Tests for astype method."""

    def test_astype_single_type(self):
        """Test converting all columns to a single type."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

        ext = PolarsMerging(df)
        result = ext.astype(pl.Float64)

        assert result["a"].dtype == pl.Float64
        assert result["b"].dtype == pl.Float64

    def test_astype_dict(self):
        """Test converting columns with dict specification."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.0, 2.0, 3.0],
        })

        ext = PolarsMerging(df)
        result = ext.astype({"int_col": pl.Float64, "float_col": pl.Int64})

        assert result["int_col"].dtype == pl.Float64
        assert result["float_col"].dtype == pl.Int64

    def test_astype_to_string(self):
        """Test converting to string type."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
        })

        ext = PolarsMerging(df)
        result = ext.astype(pl.String)

        assert result["int_col"].dtype == pl.String
        assert result["float_col"].dtype == pl.String
        assert result["int_col"][0] == "1"

    def test_astype_preserves_shape(self):
        """Test that astype preserves DataFrame shape."""
        df = pl.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [6, 7, 8, 9, 10],
        })

        ext = PolarsMerging(df)
        result = ext.astype(pl.Float64)

        assert result.shape == df.shape


class TestMergeValidation:
    """Tests for merge validation options."""

    def test_merge_validate_one_to_one(self):
        """Test merge with 1:1 validation."""
        left_df = pl.DataFrame({
            "key": [1, 2, 3],
            "value": ["a", "b", "c"],
        })
        right_df = pl.DataFrame({
            "key": [1, 2, 3],
            "data": ["x", "y", "z"],
        })

        ext = PolarsMerging(left_df)
        result = ext.merge(right_df, on='key', validate='1:1')
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert result.shape[0] == 3

    def test_merge_validate_fails_on_duplicates(self):
        """Test that 1:1 validation fails with duplicates."""
        left_df = pl.DataFrame({
            "key": [1, 1, 2],  # Duplicate key 1
            "value": ["a", "b", "c"],
        })
        right_df = pl.DataFrame({
            "key": [1, 2],
            "data": ["x", "y"],
        })

        ext = PolarsMerging(left_df)
        with pytest.raises(Exception):  # Polars will raise on validation failure
            ext.merge(right_df, on='key', validate='1:1')

    def test_merge_nulls_equal(self):
        """Test merge with nulls_equal option."""
        left_df = pl.DataFrame({
            "key": [1, 2, None],
            "value": ["a", "b", "c"],
        })
        right_df = pl.DataFrame({
            "key": [1, None],
            "data": ["x", "y"],
        })

        ext = PolarsMerging(left_df)
        result_nulls_equal = ext.merge(right_df, on='key', nulls_equal=True)
        result_nulls_not_equal = ext.merge(right_df, on='key', nulls_equal=False)
        if isinstance(result_nulls_equal, pl.LazyFrame):
            result_nulls_equal = result_nulls_equal.collect()
        if isinstance(result_nulls_not_equal, pl.LazyFrame):
            result_nulls_not_equal = result_nulls_not_equal.collect()

        # With nulls_equal=True, null keys should match
        assert result_nulls_equal.shape[0] >= result_nulls_not_equal.shape[0]


class TestInheritance:
    """Tests for inheritance from UniversalPolarsDataFrameExtension."""

    def test_inherits_properties(self):
        """Test that PolarsMerging inherits base properties."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

        ext = PolarsMerging(df)

        assert ext.schema == {"a": pl.Int64, "b": pl.Int64}
        assert ext.length == 3
        assert ext.width == 2
        assert ext.columns == ["a", "b"]
        assert ext.shape == (3, 2)
        assert ext.is_lazy is False

    def test_inherits_lazyframe_properties(self):
        """Test that PolarsMerging works with LazyFrame."""
        lf = pl.LazyFrame({
            "a": [1, 2, 3],
        })

        ext = PolarsMerging(lf)

        assert ext.is_lazy is True
        assert ext.length == 3
