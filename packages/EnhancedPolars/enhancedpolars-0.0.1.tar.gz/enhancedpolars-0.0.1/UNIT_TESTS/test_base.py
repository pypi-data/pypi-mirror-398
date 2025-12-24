"""
Tests for base.py - UniversalPolarsDataFrameExtension
"""

import pytest
import polars as pl
import math
from enhancedpolars.base import UniversalPolarsDataFrameExtension


class TestUniversalPolarsDataFrameExtension:
    """Tests for UniversalPolarsDataFrameExtension base class."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pl.DataFrame({
            "int_col": [1, 2, 3, 4, 5],
            "float_col": [1.0, 2.5, float('nan'), 4.0, None],
            "str_col": ["a", "b", None, "d", "e"],
            "bool_col": [True, False, True, None, False],
        })

    @pytest.fixture
    def sample_lf(self, sample_df):
        """Create a sample LazyFrame for testing."""
        return sample_df.lazy()


class TestProperties:
    """Tests for extension properties."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4.0, 5.0, 6.0],
            "c": ["x", "y", "z"],
        })

    def test_schema_dataframe(self, sample_df):
        """Test schema property with DataFrame."""
        ext = UniversalPolarsDataFrameExtension(sample_df)
        schema = ext.schema
        assert "a" in schema
        assert "b" in schema
        assert "c" in schema
        assert schema["a"] == pl.Int64
        assert schema["b"] == pl.Float64
        assert schema["c"] == pl.String

    def test_schema_lazyframe(self, sample_df):
        """Test schema property with LazyFrame."""
        ext = UniversalPolarsDataFrameExtension(sample_df.lazy())
        schema = ext.schema
        assert "a" in schema
        assert schema["a"] == pl.Int64

    def test_length_dataframe(self, sample_df):
        """Test length property with DataFrame."""
        ext = UniversalPolarsDataFrameExtension(sample_df)
        assert ext.length == 3

    def test_length_lazyframe(self, sample_df):
        """Test length property with LazyFrame."""
        ext = UniversalPolarsDataFrameExtension(sample_df.lazy())
        assert ext.length == 3

    def test_height_dataframe(self, sample_df):
        """Test height property (alias for length)."""
        ext = UniversalPolarsDataFrameExtension(sample_df)
        assert ext.height == 3
        assert ext.height == ext.length

    def test_width_dataframe(self, sample_df):
        """Test width property."""
        ext = UniversalPolarsDataFrameExtension(sample_df)
        assert ext.width == 3

    def test_columns_dataframe(self, sample_df):
        """Test columns property."""
        ext = UniversalPolarsDataFrameExtension(sample_df)
        assert ext.columns == ["a", "b", "c"]

    def test_shape_dataframe(self, sample_df):
        """Test shape property."""
        ext = UniversalPolarsDataFrameExtension(sample_df)
        assert ext.shape == (3, 3)

    def test_is_lazy_dataframe(self, sample_df):
        """Test is_lazy property with DataFrame."""
        ext = UniversalPolarsDataFrameExtension(sample_df)
        assert ext.is_lazy is False

    def test_is_lazy_lazyframe(self, sample_df):
        """Test is_lazy property with LazyFrame."""
        ext = UniversalPolarsDataFrameExtension(sample_df.lazy())
        assert ext.is_lazy is True

    def test_empty_dataframe(self):
        """Test properties with empty DataFrame."""
        df = pl.DataFrame({"a": [], "b": []}).cast({"a": pl.Int64, "b": pl.Float64})
        ext = UniversalPolarsDataFrameExtension(df)
        assert ext.length == 0
        assert ext.width == 2
        assert ext.shape == (0, 2)
        assert ext.columns == ["a", "b"]


class TestIsnull:
    """Tests for isnull/isna methods."""

    def test_isnull_with_nulls(self):
        """Test isnull detects null values."""
        df = pl.DataFrame({
            "a": [1, None, 3],
            "b": ["x", None, "z"],
        })
        ext = UniversalPolarsDataFrameExtension(df)
        result = ext.isnull()

        assert result["a"].to_list() == [False, True, False]
        assert result["b"].to_list() == [False, True, False]

    def test_isnull_with_nan(self):
        """Test isnull detects NaN in float columns."""
        df = pl.DataFrame({
            "float_col": [1.0, float('nan'), 3.0, None],
        })
        ext = UniversalPolarsDataFrameExtension(df)
        result = ext.isnull()

        # Both NaN and null should be detected, but 3.0 is valid
        assert result["float_col"].to_list() == [False, True, False, True]

    def test_isnull_no_missing(self):
        """Test isnull with no missing values."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })
        ext = UniversalPolarsDataFrameExtension(df)
        result = ext.isnull()

        assert all(not v for v in result["a"].to_list())
        assert all(not v for v in result["b"].to_list())

    def test_isna_alias(self):
        """Test isna is alias for isnull."""
        df = pl.DataFrame({"a": [1, None, 3]})
        ext = UniversalPolarsDataFrameExtension(df)

        isnull_result = ext.isnull()
        isna_result = ext.isna()

        assert isnull_result["a"].to_list() == isna_result["a"].to_list()

    def test_isnull_lazyframe(self):
        """Test isnull with LazyFrame."""
        lf = pl.LazyFrame({"a": [1, None, 3]})
        ext = UniversalPolarsDataFrameExtension(lf)
        result = ext.isnull()

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected["a"].to_list() == [False, True, False]


class TestNotnull:
    """Tests for notnull/notna methods."""

    def test_notnull_with_nulls(self):
        """Test notnull detects non-null values."""
        df = pl.DataFrame({
            "a": [1, None, 3],
            "b": ["x", None, "z"],
        })
        ext = UniversalPolarsDataFrameExtension(df)
        result = ext.notnull()

        assert result["a"].to_list() == [True, False, True]
        assert result["b"].to_list() == [True, False, True]

    def test_notnull_with_nan(self):
        """Test notnull handles NaN in float columns."""
        df = pl.DataFrame({
            "float_col": [1.0, float('nan'), 3.0, None],
        })
        ext = UniversalPolarsDataFrameExtension(df)
        result = ext.notnull()

        # Both NaN and null should be False
        assert result["float_col"].to_list() == [True, False, True, False]

    def test_notna_alias(self):
        """Test notna is alias for notnull."""
        df = pl.DataFrame({"a": [1, None, 3]})
        ext = UniversalPolarsDataFrameExtension(df)

        notnull_result = ext.notnull()
        notna_result = ext.notna()

        assert notnull_result["a"].to_list() == notna_result["a"].to_list()

    def test_notnull_lazyframe(self):
        """Test notnull with LazyFrame."""
        lf = pl.LazyFrame({"a": [1, None, 3]})
        ext = UniversalPolarsDataFrameExtension(lf)
        result = ext.notnull()

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected["a"].to_list() == [True, False, True]


class TestSetColumns:
    """Tests for set_columns method."""

    def test_set_columns_basic(self):
        """Test basic column renaming."""
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        ext = UniversalPolarsDataFrameExtension(df)

        result = ext.set_columns(["x", "y"])

        assert result.columns == ["x", "y"]
        assert result["x"].to_list() == [1, 2]
        assert result["y"].to_list() == [3, 4]

    def test_set_columns_lazyframe(self):
        """Test column renaming with LazyFrame."""
        lf = pl.LazyFrame({"a": [1, 2], "b": [3, 4]})
        ext = UniversalPolarsDataFrameExtension(lf)

        result = ext.set_columns(["x", "y"])

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected.columns == ["x", "y"]

    def test_set_columns_tuple_input(self):
        """Test set_columns accepts tuple."""
        df = pl.DataFrame({"a": [1], "b": [2]})
        ext = UniversalPolarsDataFrameExtension(df)

        result = ext.set_columns(("x", "y"))
        assert result.columns == ["x", "y"]

    def test_set_columns_wrong_length(self):
        """Test set_columns raises error for wrong number of columns."""
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
        ext = UniversalPolarsDataFrameExtension(df)

        with pytest.raises(ValueError, match="Number of new column names"):
            ext.set_columns(["x", "y"])

    def test_set_columns_not_list(self):
        """Test set_columns raises error for non-list input."""
        df = pl.DataFrame({"a": [1], "b": [2]})
        ext = UniversalPolarsDataFrameExtension(df)

        with pytest.raises(TypeError, match="must be a list or tuple"):
            ext.set_columns("xy")

    def test_set_columns_non_string_names(self):
        """Test set_columns raises error for non-string column names."""
        df = pl.DataFrame({"a": [1], "b": [2]})
        ext = UniversalPolarsDataFrameExtension(df)

        with pytest.raises(TypeError, match="must be a string"):
            ext.set_columns(["x", 123])

    def test_set_columns_preserves_original(self):
        """Test that set_columns doesn't modify original DataFrame."""
        df = pl.DataFrame({"a": [1], "b": [2]})
        ext = UniversalPolarsDataFrameExtension(df)

        ext.set_columns(["x", "y"])

        # Original should be unchanged
        assert df.columns == ["a", "b"]


class TestCaching:
    """Tests for property caching behavior."""

    def test_schema_cached(self):
        """Test that schema is cached after first access."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameExtension(df)

        assert ext._schema is None
        _ = ext.schema
        assert ext._schema is not None

    def test_length_cached(self):
        """Test that length is cached after first access."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameExtension(df)

        assert ext._length is None
        _ = ext.length
        assert ext._length == 3

    def test_columns_cached(self):
        """Test that columns is cached after first access."""
        df = pl.DataFrame({"a": [1], "b": [2]})
        ext = UniversalPolarsDataFrameExtension(df)

        assert ext._columns is None
        _ = ext.columns
        assert ext._columns == ["a", "b"]
