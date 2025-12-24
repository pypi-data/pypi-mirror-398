"""
Tests for indexing.py - Pandas-style indexing for Polars DataFrames
"""

import pytest
import polars as pl
import numpy as np
from enhancedpolars.indexing import (
    UniversalPolarsDataFrameIndexingExtension,
    LocAccessor,
    ILocAccessor,
    AtAccessor,
    IatAccessor,
    IterRowsAccessor,
    cast_value_to_column_type,
)


class TestCastValueToColumnType:
    """Tests for cast_value_to_column_type helper function."""

    def test_cast_int_to_int64(self):
        """Test casting int to Int64."""
        result = cast_value_to_column_type(5, pl.Int64)
        assert result == 5

    def test_cast_float_to_float64(self):
        """Test casting float to Float64."""
        result = cast_value_to_column_type(3.14, pl.Float64)
        assert result == 3.14

    def test_cast_none_value(self):
        """Test None values pass through."""
        result = cast_value_to_column_type(None, pl.Int64)
        assert result is None

    def test_cast_nan_to_none(self):
        """Test NaN is converted to None."""
        result = cast_value_to_column_type(float('nan'), pl.Float64)
        assert result is None


class TestUniversalPolarsDataFrameIndexingExtension:
    """Tests for the main indexing extension class."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [10.0, 20.0, 30.0, 40.0, 50.0],
            "c": ["x", "y", "z", "w", "v"],
        })

    @pytest.fixture
    def ext(self, sample_df):
        return UniversalPolarsDataFrameIndexingExtension(sample_df)


class TestBooleanIndexing:
    """Tests for __getitem__ boolean indexing."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [10.0, 20.0, 30.0, 40.0, 50.0],
        })

    def test_boolean_series_indexing(self, sample_df):
        """Test boolean indexing with Polars Series."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        mask = pl.Series([True, False, True, False, True])
        result = ext[mask]
        assert len(result) == 3
        assert result["a"].to_list() == [1, 3, 5]

    def test_boolean_list_indexing(self, sample_df):
        """Test boolean indexing with Python list."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        mask = [True, False, True, False, True]
        result = ext[mask]
        assert len(result) == 3

    def test_boolean_numpy_indexing(self, sample_df):
        """Test boolean indexing with numpy array."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        mask = np.array([True, False, True, False, True])
        result = ext[mask]
        assert len(result) == 3

    def test_invalid_indexing_raises(self, sample_df):
        """Test invalid indexing raises TypeError."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        with pytest.raises(TypeError):
            ext["invalid"]


class TestIndexProperty:
    """Tests for index property."""

    def test_index_returns_series(self):
        """Test index property returns a Series."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        index = ext.index
        assert isinstance(index, pl.Series)
        assert index.to_list() == [0, 1, 2]

    def test_index_empty_dataframe(self):
        """Test index on empty DataFrame."""
        df = pl.DataFrame({"a": []}).cast({"a": pl.Int64})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        index = ext.index
        assert len(index) == 0


class TestXsMethod:
    """Tests for xs (cross-section) method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6],
            "C": [7, 8, 9],
        })

    def test_xs_row_by_index(self, sample_df):
        """Test xs to get row by integer index."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.xs(1, axis=0)
        assert len(result) == 1
        assert result["A"][0] == 2

    def test_xs_row_negative_index(self, sample_df):
        """Test xs with negative row index."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.xs(-1, axis=0)
        assert result["A"][0] == 3

    def test_xs_column_by_name(self, sample_df):
        """Test xs to get column by name."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.xs("B", axis=1)
        assert result["B"].to_list() == [4, 5, 6]

    def test_xs_multiple_columns(self, sample_df):
        """Test xs with multiple column names."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.xs(["A", "C"], axis=1)
        assert result.columns == ["A", "C"]

    def test_xs_row_out_of_bounds(self, sample_df):
        """Test xs raises IndexError for out of bounds row."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        with pytest.raises(IndexError):
            ext.xs(10, axis=0)

    def test_xs_column_not_found(self, sample_df):
        """Test xs raises KeyError for missing column."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        with pytest.raises(KeyError):
            ext.xs("Z", axis=1)

    def test_xs_level_not_implemented(self, sample_df):
        """Test xs raises NotImplementedError for level parameter."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        with pytest.raises(NotImplementedError):
            ext.xs(0, level=0)


class TestWhereMethod:
    """Tests for where method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6],
        })

    def test_where_with_expression(self, sample_df):
        """Test where with Polars expression."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.where(pl.col("A") > 1, 0)
        # Where condition is False (A <= 1), replace with 0
        assert result["A"].to_list() == [0, 2, 3]

    def test_where_with_series(self, sample_df):
        """Test where with boolean Series."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        mask = pl.Series([True, False, True])
        result = ext.where(mask, -1)
        assert result["A"].to_list() == [1, -1, 3]

    def test_where_with_list(self, sample_df):
        """Test where with boolean list."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.where([True, False, True], 0)
        assert result["A"].to_list() == [1, 0, 3]

    def test_where_other_none(self, sample_df):
        """Test where with other=None uses null."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.where(pl.col("A") > 1, None)
        assert result["A"][0] is None


class TestAnyAllMethods:
    """Tests for any and all methods."""

    def test_any_axis_none_true(self):
        """Test any with axis=None returns True when any value is True."""
        df = pl.DataFrame({"a": [False, True, False], "b": [False, False, False]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        assert ext.any(axis=None) is True

    def test_any_axis_none_false(self):
        """Test any with axis=None returns False when all values are False."""
        df = pl.DataFrame({"a": [False, False, False], "b": [False, False, False]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        assert ext.any(axis=None) is False

    def test_any_axis_0(self):
        """Test any along axis=0 (columns)."""
        df = pl.DataFrame({"a": [True, False, False], "b": [False, False, False]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.any(axis=0)
        assert result["a"][0] is True
        assert result["b"][0] is False

    def test_any_axis_1(self):
        """Test any along axis=1 (rows)."""
        df = pl.DataFrame({"a": [True, False, False], "b": [False, True, False]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.any(axis=1)
        assert result["any"].to_list() == [True, True, False]

    def test_all_axis_none_true(self):
        """Test all with axis=None returns True when all values are True."""
        df = pl.DataFrame({"a": [True, True, True], "b": [True, True, True]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        assert ext.all(axis=None) is True

    def test_all_axis_none_false(self):
        """Test all with axis=None returns False when any value is False."""
        df = pl.DataFrame({"a": [True, True, True], "b": [True, False, True]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        assert ext.all(axis=None) is False

    def test_all_axis_0(self):
        """Test all along axis=0 (columns)."""
        df = pl.DataFrame({"a": [True, True, True], "b": [True, False, True]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.all(axis=0)
        assert result["a"][0] is True
        assert result["b"][0] is False

    def test_all_axis_1(self):
        """Test all along axis=1 (rows)."""
        df = pl.DataFrame({"a": [True, True, False], "b": [True, False, False]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.all(axis=1)
        assert result["all"].to_list() == [True, False, False]


class TestResetIndex:
    """Tests for reset_index method."""

    def test_reset_index_add_column(self):
        """Test reset_index adds index column."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.reset_index()
        assert "index" in result.columns
        assert result["index"].to_list() == [0, 1, 2]

    def test_reset_index_custom_name(self):
        """Test reset_index with custom column name."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.reset_index(name="row_id")
        assert "row_id" in result.columns
        assert result["row_id"].to_list() == [0, 1, 2]

    def test_reset_index_drop(self):
        """Test reset_index with drop=True returns original."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.reset_index(drop=True)
        assert result.columns == ["a"]


class TestDropna:
    """Tests for dropna method."""

    def test_dropna_any(self):
        """Test dropna with how='any'."""
        df = pl.DataFrame({
            "a": [1, None, 3],
            "b": [4, 5, None],
        })
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.dropna(how='any')
        assert len(result) == 1
        assert result["a"][0] == 1

    def test_dropna_all(self):
        """Test dropna with how='all'."""
        df = pl.DataFrame({
            "a": [1, None, None],
            "b": [4, None, None],
        })
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.dropna(how='all')
        # Rows 1 and 2 have all null values, so they are dropped
        # Only row 0 (a=1, b=4) remains
        assert len(result) == 1

    def test_dropna_subset(self):
        """Test dropna with subset of columns."""
        df = pl.DataFrame({
            "a": [1, None, 3],
            "b": [4, 5, None],
        })
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.dropna(subset=['a'])
        assert len(result) == 2

    def test_dropna_with_nan(self):
        """Test dropna handles NaN in float columns."""
        df = pl.DataFrame({
            "a": [1.0, float('nan'), 3.0],
        })
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.dropna()
        assert len(result) == 2


class TestSplit:
    """Tests for split method."""

    def test_split_two_parts(self):
        """Test split into 2 parts."""
        df = pl.DataFrame({"a": list(range(10))})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        parts = ext.split(n_parts=2, shuffle=False)
        assert len(parts) == 2
        assert len(parts[0]) + len(parts[1]) == 10

    def test_split_with_frac(self):
        """Test split with custom fractions."""
        df = pl.DataFrame({"a": list(range(100))})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        parts = ext.split(n_parts=3, frac=[0.6, 0.2, 0.2], shuffle=False)
        assert len(parts) == 3
        assert len(parts[0]) == 60

    def test_split_reproducible(self):
        """Test split with random_state is reproducible."""
        df = pl.DataFrame({"a": list(range(20))})
        ext1 = UniversalPolarsDataFrameIndexingExtension(df)
        ext2 = UniversalPolarsDataFrameIndexingExtension(df)
        parts1 = ext1.split(n_parts=2, random_state=42)
        parts2 = ext2.split(n_parts=2, random_state=42)
        assert parts1[0]["a"].to_list() == parts2[0]["a"].to_list()

    def test_split_invalid_n_parts(self):
        """Test split raises for n_parts < 2."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(ValueError):
            ext.split(n_parts=1)

    def test_split_frac_sum_not_one(self):
        """Test split raises when frac doesn't sum to 1."""
        df = pl.DataFrame({"a": list(range(10))})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(ValueError):
            ext.split(n_parts=2, frac=[0.5, 0.3])


class TestSample:
    """Tests for sample method."""

    def test_sample_n(self):
        """Test sample with n parameter."""
        df = pl.DataFrame({"a": list(range(100))})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sample(n=10)
        assert len(result) == 10

    def test_sample_frac(self):
        """Test sample with frac parameter."""
        df = pl.DataFrame({"a": list(range(100))})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sample(frac=0.1)
        assert len(result) == 10

    def test_sample_reproducible(self):
        """Test sample with random_state is reproducible."""
        df = pl.DataFrame({"a": list(range(100))})
        ext1 = UniversalPolarsDataFrameIndexingExtension(df)
        ext2 = UniversalPolarsDataFrameIndexingExtension(df)
        r1 = ext1.sample(n=10, random_state=42)
        r2 = ext2.sample(n=10, random_state=42)
        assert r1["a"].to_list() == r2["a"].to_list()

    def test_sample_both_n_and_frac_raises(self):
        """Test sample raises when both n and frac provided."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(ValueError):
            ext.sample(n=2, frac=0.5)

    def test_sample_neither_n_nor_frac_raises(self):
        """Test sample raises when neither n nor frac provided."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(ValueError):
            ext.sample()


class TestSortValues:
    """Tests for sort_values method."""

    def test_sort_values_single_column(self):
        """Test sort by single column."""
        df = pl.DataFrame({"a": [3, 1, 2]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sort_values("a")
        assert result["a"].to_list() == [1, 2, 3]

    def test_sort_values_descending(self):
        """Test sort descending."""
        df = pl.DataFrame({"a": [1, 3, 2]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sort_values("a", ascending=False)
        assert result["a"].to_list() == [3, 2, 1]

    def test_sort_values_multiple_columns(self):
        """Test sort by multiple columns."""
        df = pl.DataFrame({"a": [1, 1, 2], "b": [3, 1, 2]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sort_values(["a", "b"])
        assert result["b"].to_list() == [1, 3, 2]

    def test_sort_values_missing_column(self):
        """Test sort raises for missing column."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(KeyError):
            ext.sort_values("z")


class TestIterrows:
    """Tests for iterrows method."""

    def test_iterrows_basic(self):
        """Test iterrows returns index and row dict."""
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        rows = list(ext.iterrows())
        assert len(rows) == 2
        assert rows[0] == (0, {"a": 1, "b": 3})
        assert rows[1] == (1, {"a": 2, "b": 4})

    def test_iterrows_empty(self):
        """Test iterrows on empty DataFrame."""
        df = pl.DataFrame({"a": []}).cast({"a": pl.Int64})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        rows = list(ext.iterrows())
        assert len(rows) == 0


class TestLocAccessor:
    """Tests for LocAccessor."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [10, 20, 30, 40, 50],
            "c": ["x", "y", "z", "w", "v"],
        })

    def test_loc_single_row(self, sample_df):
        """Test loc with single row index."""
        loc = LocAccessor(sample_df)
        result = loc[0]
        assert len(result) == 1

    def test_loc_row_slice(self, sample_df):
        """Test loc with row slice."""
        loc = LocAccessor(sample_df)
        result = loc[1:3]
        assert len(result) == 2

    def test_loc_row_and_column(self, sample_df):
        """Test loc with row and column."""
        loc = LocAccessor(sample_df)
        result = loc[0, "a"]
        assert result == 1

    def test_loc_row_and_columns_list(self, sample_df):
        """Test loc with row and list of columns."""
        loc = LocAccessor(sample_df)
        result = loc[0, ["a", "b"]]
        assert result.columns == ["a", "b"]

    def test_loc_boolean_mask(self, sample_df):
        """Test loc with boolean mask."""
        loc = LocAccessor(sample_df)
        mask = [True, False, True, False, True]
        result = loc[mask]
        assert len(result) == 3

    def test_loc_set_raises_not_implemented(self, sample_df):
        """Test loc setter raises NotImplementedError."""
        loc = LocAccessor(sample_df)
        with pytest.raises(NotImplementedError):
            loc[0, "a"] = 100


class TestILocAccessor:
    """Tests for ILocAccessor."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [10, 20, 30, 40, 50],
        })

    def test_iloc_single_row(self, sample_df):
        """Test iloc with single row position."""
        iloc = ILocAccessor(sample_df)
        result = iloc[0]
        assert len(result) == 1

    def test_iloc_negative_index(self, sample_df):
        """Test iloc with negative index."""
        iloc = ILocAccessor(sample_df)
        result = iloc[-1]
        assert result["a"][0] == 5

    def test_iloc_row_and_column(self, sample_df):
        """Test iloc with row and column positions."""
        iloc = ILocAccessor(sample_df)
        result = iloc[0, 0]
        assert result == 1

    def test_iloc_row_slice(self, sample_df):
        """Test iloc with row slice."""
        iloc = ILocAccessor(sample_df)
        result = iloc[1:3]
        assert len(result) == 2

    def test_iloc_column_slice(self, sample_df):
        """Test iloc with column slice."""
        iloc = ILocAccessor(sample_df)
        result = iloc[:, 0:1]
        assert result.columns == ["a"]


class TestAtAccessor:
    """Tests for AtAccessor."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

    def test_at_get_value(self, sample_df):
        """Test at to get single value."""
        at = AtAccessor(sample_df)
        assert at[0, "a"] == 1
        assert at[1, "b"] == 5

    def test_at_negative_index(self, sample_df):
        """Test at with negative row index."""
        at = AtAccessor(sample_df)
        assert at[-1, "a"] == 3

    def test_at_invalid_args(self, sample_df):
        """Test at raises for invalid arguments."""
        at = AtAccessor(sample_df)
        with pytest.raises(ValueError):
            at[0]  # Missing column


class TestIatAccessor:
    """Tests for IatAccessor."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

    def test_iat_get_value(self, sample_df):
        """Test iat to get single value by position."""
        iat = IatAccessor(sample_df)
        assert iat[0, 0] == 1
        assert iat[1, 1] == 5

    def test_iat_negative_index(self, sample_df):
        """Test iat with negative indices."""
        iat = IatAccessor(sample_df)
        assert iat[-1, -1] == 6

    def test_iat_invalid_args(self, sample_df):
        """Test iat raises for invalid arguments."""
        iat = IatAccessor(sample_df)
        with pytest.raises(ValueError):
            iat[0]  # Missing column position


class TestIterRowsAccessor:
    """Tests for IterRowsAccessor."""

    def test_iterrows_accessor(self):
        """Test IterRowsAccessor iteration."""
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        accessor = IterRowsAccessor(df)
        rows = list(accessor)
        assert rows[0] == (0, {"a": 1, "b": 3})
        assert rows[1] == (1, {"a": 2, "b": 4})

    def test_iterrows_accessor_lazyframe(self):
        """Test IterRowsAccessor with LazyFrame."""
        lf = pl.LazyFrame({"a": [1, 2], "b": [3, 4]})
        accessor = IterRowsAccessor(lf)
        rows = list(accessor)
        assert len(rows) == 2


class TestSetMethods:
    """Tests for set_loc, set_iloc, set_at, set_iat methods."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

    def test_set_loc(self, sample_df):
        """Test set_loc method."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.set_loc(0, "a", 100)
        assert result["a"][0] == 100

    def test_set_iloc(self, sample_df):
        """Test set_iloc method."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.set_iloc(0, 0, 100)
        assert result["a"][0] == 100

    def test_set_at(self, sample_df):
        """Test set_at method."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.set_at(0, "a", 100)
        assert result["a"][0] == 100

    def test_set_iat(self, sample_df):
        """Test set_iat method."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_df)
        result = ext.set_iat(0, 0, 100)
        assert result["a"][0] == 100


class TestSampleAdvanced:
    """Advanced tests for sample method including stratified and weighted sampling."""

    @pytest.fixture
    def grouped_df(self):
        """Create DataFrame with group column for stratified sampling."""
        return pl.DataFrame({
            "group": ["A"] * 30 + ["B"] * 30 + ["C"] * 40,
            "value": list(range(100)),
        })

    def test_sample_stratified(self, grouped_df):
        """Test stratified sampling maintains group proportions."""
        ext = UniversalPolarsDataFrameIndexingExtension(grouped_df)
        result = ext.sample(n=20, stratify="group", random_state=42)

        # Check total count
        assert len(result) == 20

        # Check groups are represented
        groups = result["group"].unique().to_list()
        assert "A" in groups
        assert "B" in groups
        assert "C" in groups

    def test_sample_stratified_frac(self, grouped_df):
        """Test stratified sampling with frac parameter."""
        ext = UniversalPolarsDataFrameIndexingExtension(grouped_df)
        result = ext.sample(frac=0.5, stratify="group", random_state=42)

        # Should sample 50% = 50 rows
        assert len(result) == 50

    def test_sample_stratify_column_not_found(self, grouped_df):
        """Test stratified sampling raises for non-existent column."""
        ext = UniversalPolarsDataFrameIndexingExtension(grouped_df)
        with pytest.raises(ValueError, match="not found"):
            ext.sample(n=10, stratify="nonexistent")

    def test_sample_with_replace(self):
        """Test sampling with replacement."""
        df = pl.DataFrame({"a": list(range(5))})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        # With replace, we can sample more than the original size
        result = ext.sample(n=10, replace=True, random_state=42)
        assert len(result) == 10

    def test_sample_frac_out_of_range(self):
        """Test sample raises for frac out of range."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(ValueError, match="must be between"):
            ext.sample(frac=1.5)

    def test_sample_n_exceeds_without_replace(self):
        """Test sample raises when n exceeds rows without replacement."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(ValueError, match="Cannot sample"):
            ext.sample(n=10, replace=False)

    def test_sample_empty_dataframe(self):
        """Test sample on empty DataFrame."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sample(n=0)
        assert len(result) == 0

    def test_sample_with_shuffle(self):
        """Test sample with shuffle parameter."""
        df = pl.DataFrame({"a": list(range(100))})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sample(n=50, shuffle=True, random_state=42)
        assert len(result) == 50


class TestLazyFrameSupport:
    """Tests for LazyFrame support across indexing methods."""

    @pytest.fixture
    def sample_lf(self):
        return pl.LazyFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [10, 20, 30, 40, 50],
            "group": ["A", "A", "B", "B", "A"],
        })

    def test_sample_lazyframe(self, sample_lf):
        """Test sample with LazyFrame returns LazyFrame."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_lf)
        result = ext.sample(n=3, random_state=42)
        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert len(collected) == 3

    def test_sample_lazyframe_stratified(self, sample_lf):
        """Test stratified sample with LazyFrame."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_lf)
        result = ext.sample(n=4, stratify="group", random_state=42)
        assert isinstance(result, pl.LazyFrame)

    def test_split_lazyframe(self, sample_lf):
        """Test split with LazyFrame returns LazyFrames."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_lf)
        parts = ext.split(n_parts=2, random_state=42)
        assert all(isinstance(p, pl.LazyFrame) for p in parts)

    def test_dropna_lazyframe(self, sample_lf):
        """Test dropna with LazyFrame."""
        lf = pl.LazyFrame({"a": [1, None, 3], "b": [4, 5, None]})
        ext = UniversalPolarsDataFrameIndexingExtension(lf)
        result = ext.dropna()
        assert isinstance(result, pl.LazyFrame)
        assert len(result.collect()) == 1

    def test_sort_values_lazyframe(self, sample_lf):
        """Test sort_values with LazyFrame."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_lf)
        result = ext.sort_values("a", ascending=False)
        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected["a"].to_list() == [5, 4, 3, 2, 1]

    def test_reset_index_lazyframe(self, sample_lf):
        """Test reset_index with LazyFrame."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_lf)
        result = ext.reset_index()
        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert "index" in collected.columns

    def test_where_lazyframe(self, sample_lf):
        """Test where with LazyFrame."""
        ext = UniversalPolarsDataFrameIndexingExtension(sample_lf)
        result = ext.where(pl.col("a") > 2, 0)
        assert isinstance(result, pl.LazyFrame)


class TestLocEdgeCases:
    """Edge case tests for LocAccessor."""

    def test_loc_empty_dataframe(self):
        """Test loc on empty DataFrame."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        loc = LocAccessor(df)
        result = loc[:]
        assert len(result) == 0

    def test_loc_column_slice_with_row_slice(self):
        """Test loc with both row and column slices."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        loc = LocAccessor(df)
        result = loc[0:2, "a":"b"]
        assert len(result) == 2
        assert result.columns == ["a", "b"]

    def test_loc_column_not_found_raises(self):
        """Test loc raises ColumnNotFoundError for non-existent column."""
        import polars.exceptions as pl_exc
        df = pl.DataFrame({"a": [1, 2, 3]})
        loc = LocAccessor(df)
        with pytest.raises(pl_exc.ColumnNotFoundError):
            loc[0, "nonexistent"]


class TestILocEdgeCases:
    """Edge case tests for ILocAccessor."""

    def test_iloc_empty_dataframe(self):
        """Test iloc on empty DataFrame."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        iloc = ILocAccessor(df)
        result = iloc[:]
        assert len(result) == 0

    def test_iloc_list_of_indices(self):
        """Test iloc with list of row indices."""
        df = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
        iloc = ILocAccessor(df)
        result = iloc[[0, 2, 4]]
        assert len(result) == 3
        assert result["a"].to_list() == [1, 3, 5]

    def test_iloc_negative_column_index(self):
        """Test iloc with negative column index."""
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
        iloc = ILocAccessor(df)
        result = iloc[0, -1]
        assert result == 3

    def test_iloc_column_list(self):
        """Test iloc with list of column positions."""
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
        iloc = ILocAccessor(df)
        result = iloc[0, [0, 2]]
        assert result.columns == ["a", "c"]


class TestAccessorNullHandling:
    """Tests for accessor handling of null values."""

    def test_at_returns_none_for_null(self):
        """Test at returns None for null value."""
        df = pl.DataFrame({"a": [1, None, 3]})
        at = AtAccessor(df)
        assert at[1, "a"] is None

    def test_iat_returns_none_for_null(self):
        """Test iat returns None for null value."""
        df = pl.DataFrame({"a": [1, None, 3]})
        iat = IatAccessor(df)
        assert iat[1, 0] is None

    def test_loc_row_with_nulls(self):
        """Test loc gets row containing nulls."""
        df = pl.DataFrame({"a": [1, None, 3], "b": [None, 2, 3]})
        loc = LocAccessor(df)
        result = loc[1]
        assert result["a"][0] is None
        assert result["b"][0] == 2


class TestXsEdgeCases:
    """Edge case tests for xs method."""

    def test_xs_invalid_axis(self):
        """Test xs raises for invalid axis."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(ValueError, match="axis must be"):
            ext.xs(0, axis=2)

    def test_xs_invalid_row_key_type(self):
        """Test xs raises for non-integer row key."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(TypeError, match="Row key must be integer"):
            ext.xs("0", axis=0)

    def test_xs_invalid_column_key_type(self):
        """Test xs raises for invalid column key type."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        with pytest.raises(TypeError, match="Column key must be string"):
            ext.xs(0, axis=1)


class TestWhereEdgeCases:
    """Edge case tests for where method."""

    def test_where_scalar_replacement(self):
        """Test where with scalar replacement value."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.where(pl.col("a") > 1, 0)
        assert result["a"].to_list() == [0, 2, 3]

    def test_where_none_replacement(self):
        """Test where with None as replacement."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.where(pl.col("a") > 1, None)
        assert result["a"][0] is None


class TestSplitEdgeCases:
    """Edge case tests for split method."""

    def test_split_empty_dataframe(self):
        """Test split on empty DataFrame."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        parts = ext.split(n_parts=2)
        assert len(parts) == 2
        assert all(len(p) == 0 for p in parts)

    def test_split_small_dataframe(self):
        """Test split when DataFrame has fewer rows than parts."""
        df = pl.DataFrame({"a": [1, 2]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        parts = ext.split(n_parts=5)
        # Some parts will be empty
        total_rows = sum(len(p) for p in parts)
        assert total_rows == 2


class TestDropnaEdgeCases:
    """Edge case tests for dropna method."""

    def test_dropna_empty_dataframe(self):
        """Test dropna on empty DataFrame."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.dropna()
        assert len(result) == 0

    def test_dropna_no_nulls(self):
        """Test dropna when there are no nulls."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.dropna()
        assert len(result) == 3


class TestSortValuesEdgeCases:
    """Edge case tests for sort_values method."""

    def test_sort_values_with_nulls(self):
        """Test sort values handles nulls."""
        df = pl.DataFrame({"a": [3, None, 1, None, 2]})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sort_values("a")
        # Just verify it doesn't crash and is sorted
        non_null_values = [v for v in result["a"].to_list() if v is not None]
        assert non_null_values == sorted(non_null_values)

    def test_sort_values_empty_dataframe(self):
        """Test sort values on empty DataFrame."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        ext = UniversalPolarsDataFrameIndexingExtension(df)
        result = ext.sort_values("a")
        assert len(result) == 0
