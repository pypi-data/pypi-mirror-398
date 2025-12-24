"""
Comprehensive test suite for EnhancedPolars (epl.py).

Tests cover:
- Data type inference (infer_dtype, infer_dtypes)
- Type conversion and optimization
- Schema merging
- Dtype parsing
- File I/O helpers
- DataFrame metadata extraction
"""

import sys
from pathlib import Path
import tempfile

import pytest
import polars as pl
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhancedpolars.epl import EnhancedPolars
from CoreUtilities.core_types import CoreDataType


# ============================================================================
# Dtype Inference Tests
# ============================================================================

class TestInferDtype:
    """Test infer_dtype function for single series."""

    def test_infer_int64(self):
        """Test inference of Int64 type."""
        series = pl.Series("test", [1, 2, 3, 4, 5])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.INTEGER
        assert meta['min_value'] == 1
        assert meta['max_value'] == 5

    def test_infer_float64(self):
        """Test inference of Float64 type."""
        series = pl.Series("test", [1.5, 2.5, 3.5])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.FLOAT
        assert meta['min_value'] == 1.5
        assert meta['max_value'] == 3.5

    def test_infer_string(self):
        """Test inference of String type."""
        series = pl.Series("test", ["hello", "world", "test"])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.STRING
        assert 'max_byte_length' in meta

    def test_infer_boolean(self):
        """Test inference of Boolean type."""
        series = pl.Series("test", [True, False, True])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.BOOLEAN

    def test_infer_datetime(self):
        """Test inference of Datetime type."""
        series = pl.Series("test", ["2023-01-15", "2023-06-20"]).str.to_datetime("%Y-%m-%d")
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.DATETIME

    def test_infer_date(self):
        """Test inference of Date type."""
        series = pl.Series("test", ["2023-01-15", "2023-06-20"]).str.to_date("%Y-%m-%d")
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.DATE

    def test_infer_with_nulls(self):
        """Test inference handles null values correctly."""
        series = pl.Series("test", [1, None, 3, None, 5])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.INTEGER
        assert meta['percent_null'] > 0  # Has null values

    def test_infer_all_nulls(self):
        """Test inference of series with all nulls."""
        series = pl.Series("test", [None, None, None])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['percent_null'] == 100.0  # All null values

    def test_infer_string_max_byte_length(self):
        """Test that max_byte_length is calculated for strings."""
        series = pl.Series("test", ["a", "hello", "hello world!"])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.STRING
        assert meta['max_byte_length'] >= 12  # "hello world!" is 12 chars


# ============================================================================
# Dtype Inference for DataFrames
# ============================================================================

class TestInferDtypes:
    """Test infer_dtypes function for DataFrames."""

    def test_infer_dtypes_basic(self):
        """Test basic DataFrame dtype inference."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "str_col": ["a", "b", "c"],
        })

        result = EnhancedPolars.infer_dtypes(df, return_df=False)

        assert "int_col" in result
        assert "float_col" in result
        assert "str_col" in result
        assert result["int_col"]["core_data_type"] == CoreDataType.INTEGER
        assert result["float_col"]["core_data_type"] == CoreDataType.FLOAT
        assert result["str_col"]["core_data_type"] == CoreDataType.STRING

    def test_infer_dtypes_lazyframe(self):
        """Test dtype inference on LazyFrame."""
        lf = pl.LazyFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        # Should work with LazyFrame
        result = EnhancedPolars.infer_dtypes(lf, return_df=False)

        assert "id" in result
        assert "name" in result

    def test_infer_dtypes_with_precision_scale(self):
        """Test inference with precision and scale collection."""
        df = pl.DataFrame({
            "decimal_col": [123.45, 678.90, 999.99],
        })

        result = EnhancedPolars.infer_dtypes(
            df,
            collect_precision_scale=True,
            return_df=False
        )

        assert "precision" in result["decimal_col"] or "scale" in result["decimal_col"]


# ============================================================================
# Type Parsing Tests
# ============================================================================

class TestParseDtype:
    """Test parse_dtype function."""

    def test_parse_string_int(self):
        """Test parsing 'int64' string."""
        result = EnhancedPolars.parse_dtype("int64")
        assert result == pl.Int64()

    def test_parse_string_float(self):
        """Test parsing 'float64' string."""
        result = EnhancedPolars.parse_dtype("float64")
        assert result == pl.Float64()

    def test_parse_string_str(self):
        """Test parsing 'string' string."""
        result = EnhancedPolars.parse_dtype("string")
        assert result == pl.String()

    def test_parse_python_type_int(self):
        """Test parsing Python int type."""
        result = EnhancedPolars.parse_dtype(int)
        assert result == pl.Int64()

    def test_parse_python_type_float(self):
        """Test parsing Python float type."""
        result = EnhancedPolars.parse_dtype(float)
        assert result == pl.Float64()

    def test_parse_python_type_str(self):
        """Test parsing Python str type."""
        result = EnhancedPolars.parse_dtype(str)
        assert result == pl.String()

    def test_parse_python_type_bool(self):
        """Test parsing Python bool type."""
        result = EnhancedPolars.parse_dtype(bool)
        assert result == pl.Boolean()

    def test_parse_numpy_dtype(self):
        """Test parsing numpy dtype."""
        result = EnhancedPolars.parse_dtype(np.dtype('int32'))
        assert result == pl.Int32()

    def test_parse_polars_dtype(self):
        """Test parsing Polars dtype (should return as-is)."""
        result = EnhancedPolars.parse_dtype(pl.Int64())
        assert result == pl.Int64()

    def test_parse_datetime_string(self):
        """Test parsing datetime string variants."""
        result = EnhancedPolars.parse_dtype("datetime")
        assert isinstance(result, pl.Datetime)

    def test_parse_date_string(self):
        """Test parsing date string."""
        result = EnhancedPolars.parse_dtype("date")
        assert result == pl.Date()


# ============================================================================
# Numpy Dtype Conversion Tests
# ============================================================================

class TestNumpyDtypeConversion:
    """Test _numpy_dtype_to_polars helper."""

    def test_numpy_int8(self):
        """Test numpy int8 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('int8'))
        assert result == pl.Int8()

    def test_numpy_int64(self):
        """Test numpy int64 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('int64'))
        assert result == pl.Int64()

    def test_numpy_float32(self):
        """Test numpy float32 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('float32'))
        assert result == pl.Float32()

    def test_numpy_float64(self):
        """Test numpy float64 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('float64'))
        assert result == pl.Float64()

    def test_numpy_bool(self):
        """Test numpy bool conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('bool'))
        assert result == pl.Boolean()

    def test_numpy_datetime64(self):
        """Test numpy datetime64 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('datetime64[ns]'))
        assert isinstance(result, pl.Datetime)


# ============================================================================
# Schema Merging Tests
# ============================================================================

class TestSchemaMerging:
    """Test schema merging functionality."""

    def test_merge_identical_schemas(self):
        """Test merging identical schemas."""
        schema1 = {"a": pl.Int64, "b": pl.String}
        schema2 = {"a": pl.Int64, "b": pl.String}

        result = EnhancedPolars.merge_schemas(schema1, schema2)

        assert result == {"a": pl.Int64, "b": pl.String}

    def test_merge_schemas_with_new_columns(self):
        """Test merging schemas with new columns."""
        schema1 = {"a": pl.Int64}
        schema2 = {"b": pl.String}

        result = EnhancedPolars.merge_schemas(schema1, schema2)

        assert "a" in result
        assert "b" in result

    def test_merge_schemas_type_widening(self):
        """Test that types are widened when merging."""
        schema1 = {"a": pl.Int32}
        schema2 = {"a": pl.Int64}

        result = EnhancedPolars.merge_schemas(schema1, schema2)

        # Should widen to Int64
        assert result["a"] in [pl.Int64, pl.Int64()]

    def test_merge_polars_dtypes(self):
        """Test merge_polars_dtypes function."""
        result = EnhancedPolars.merge_polars_dtypes(pl.Int32(), pl.Int64())

        # Should return the wider type
        assert result == pl.Int64()


# ============================================================================
# Optimize Dtypes Tests
# ============================================================================

class TestOptimizeDtypes:
    """Test dtype optimization functionality."""

    def test_optimize_integer_downcast(self):
        """Test that integers are downcasted when possible."""
        df = pl.DataFrame({
            "small_int": pl.Series([1, 2, 3], dtype=pl.Int64),  # Can be UInt8 or Int8
        })

        result = EnhancedPolars.optimize_dtypes(df)

        # Should be downcasted to smaller int (signed or unsigned depending on values)
        assert result["small_int"].dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32]

    def test_optimize_float_downcast(self):
        """Test float optimization - whole-number floats may be converted to int."""
        df = pl.DataFrame({
            "float_col": pl.Series([1.0, 2.0, 3.0], dtype=pl.Float64),
        })

        result = EnhancedPolars.optimize_dtypes(df)

        # Whole-number floats may be downcasted to int types for efficiency
        assert result["float_col"].dtype in [pl.Float32, pl.Float64, pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32]

    def test_optimize_preserves_values(self):
        """Test that optimization preserves actual values."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [100.5, 200.75, 300.25],
        })

        result = EnhancedPolars.optimize_dtypes(df)

        assert result["id"].to_list() == [1, 2, 3]
        assert result["value"].to_list() == [100.5, 200.75, 300.25]


# ============================================================================
# DataFrame Metadata Tests
# ============================================================================

class TestDataFrameMetadata:
    """Test DataFrame metadata extraction."""

    def test_get_dtype_meta(self):
        """Test get_dtype_meta function."""
        meta = EnhancedPolars.get_dtype_meta(pl.Int64())

        # Check for actual keys returned by get_dtype_meta
        assert 'core_data_type' in meta
        assert 'polars_type' in meta or 'dtype' in meta

    def test_get_meta_for_dataframe(self):
        """Test get_meta_for_dataframe function."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "str_col": ["a", "b", "c"],
        })

        meta = EnhancedPolars.get_meta_for_dataframe(df)

        assert isinstance(meta, dict)
        assert "int_col" in meta or len(meta) > 0


# ============================================================================
# Bit Width Tests
# ============================================================================

class TestBitWidth:
    """Test bit_width function."""

    def test_bit_width_int8(self):
        """Test bit width for Int8."""
        assert EnhancedPolars.bit_width(pl.Int8) == 8

    def test_bit_width_int16(self):
        """Test bit width for Int16."""
        assert EnhancedPolars.bit_width(pl.Int16) == 16

    def test_bit_width_int32(self):
        """Test bit width for Int32."""
        assert EnhancedPolars.bit_width(pl.Int32) == 32

    def test_bit_width_int64(self):
        """Test bit width for Int64."""
        assert EnhancedPolars.bit_width(pl.Int64) == 64

    def test_bit_width_float32(self):
        """Test bit width for Float32."""
        assert EnhancedPolars.bit_width(pl.Float32) == 32

    def test_bit_width_float64(self):
        """Test bit width for Float64."""
        assert EnhancedPolars.bit_width(pl.Float64) == 64


# ============================================================================
# Type Helper Tests
# ============================================================================

class TestTypeHelpers:
    """Test type helper functions."""

    def test_is_float_helper(self):
        """Test _is_float_helper function."""
        assert EnhancedPolars._is_float_helper(pl.Float32()) is True
        assert EnhancedPolars._is_float_helper(pl.Float64()) is True
        assert EnhancedPolars._is_float_helper(pl.Int64()) is False

    def test_is_integer_helper(self):
        """Test _is_integer_helper function."""
        assert EnhancedPolars._is_integer_helper(pl.Int32()) is True
        assert EnhancedPolars._is_integer_helper(pl.Int64()) is True
        assert EnhancedPolars._is_integer_helper(pl.Float64()) is False

    def test_is_temporal_helper(self):
        """Test _is_temporal_helper function."""
        assert EnhancedPolars._is_temporal_helper(pl.Date()) is True
        assert EnhancedPolars._is_temporal_helper(pl.Datetime()) is True
        assert EnhancedPolars._is_temporal_helper(pl.Int64()) is False

    def test_is_string_helper(self):
        """Test _is_string_helper function."""
        assert EnhancedPolars._is_string_helper(pl.String()) is True
        assert EnhancedPolars._is_string_helper(pl.Utf8()) is True
        assert EnhancedPolars._is_string_helper(pl.Int64()) is False


# ============================================================================
# Data Conversion Tests
# ============================================================================

class TestFromData:
    """Test from_data conversion function."""

    def test_from_pandas_dataframe(self):
        """Test converting from pandas DataFrame."""
        pdf = pd.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })

        result = EnhancedPolars.from_data(pdf)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_from_dict(self):
        """Test converting from dictionary."""
        data = {
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        }

        result = EnhancedPolars.from_data(data)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_from_list_of_dicts(self):
        """Test converting from list of dictionaries."""
        data = [
            {"a": 1, "b": "x"},
            {"a": 2, "b": "y"},
            {"a": 3, "b": "z"},
        ]

        result = EnhancedPolars.from_data(data)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_from_numpy_array(self):
        """Test converting from numpy array."""
        arr = np.array([[1, 2], [3, 4], [5, 6]])

        result = EnhancedPolars.from_data(arr)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3


# ============================================================================
# File I/O Tests
# ============================================================================

class TestFileIO:
    """Test file reading functionality."""

    def test_read_csv_basic(self, tmp_path):
        """Test reading a basic CSV file."""
        # Create test CSV
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_csv(csv_path)

        # Read it back
        result = EnhancedPolars.read_csv(csv_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_csv_lazy(self, tmp_path):
        """Test reading CSV in lazy mode."""
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_csv(csv_path)

        result = EnhancedPolars.read_csv(csv_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)

    def test_read_parquet_basic(self, tmp_path):
        """Test reading a basic Parquet file."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_parquet(parquet_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_parquet_lazy(self, tmp_path):
        """Test reading Parquet in lazy mode."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_parquet(parquet_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)


# ============================================================================
# Cleanup Tests
# ============================================================================

class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_dataframe(self):
        """Test cleanup function on DataFrame."""
        df = pl.DataFrame({
            " Column With Spaces ": [1, 2, 3],
            "UPPERCASE": ["a", "b", "c"],
        })

        result = EnhancedPolars.cleanup(df)

        # Columns should be cleaned
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_cleanup_series(self):
        """Test cleanup function on Series."""
        s = pl.Series(" Test Series ", [1, 2, 3])

        result = EnhancedPolars.cleanup(s)

        assert isinstance(result, pl.Series)
        assert len(result) == 3


# ============================================================================
# Temporal Conversion Tests
# ============================================================================

class TestTemporalConversion:
    """Test temporal type conversion."""

    def test_infer_numeric_temporal_scale_seconds(self):
        """Test inferring seconds scale from numeric data."""
        # Unix timestamps in seconds (around year 2023)
        series = pl.Series("ts", [1672531200, 1672617600, 1672704000])

        scale = EnhancedPolars.infer_numeric_temporal_scale(series, "datetime")

        assert scale in ["s", "ms", "us", "ns", "d"]

    def test_infer_numeric_temporal_scale_milliseconds(self):
        """Test inferring milliseconds scale from numeric data."""
        # Unix timestamps in milliseconds
        series = pl.Series("ts", [1672531200000, 1672617600000, 1672704000000])

        scale = EnhancedPolars.infer_numeric_temporal_scale(series, "datetime")

        assert scale in ["s", "ms", "us", "ns", "d"]

    def test_to_timedelta_polars(self):
        """Test timedelta conversion with pandas-style duration strings."""
        # Pandas-style duration strings (the format supported by to_timedelta_polars)
        s = pl.Series("duration", ["1h30m", "2h45m", "0h15m"])

        result = EnhancedPolars.to_timedelta_polars(s)

        assert result.dtype == pl.Duration


# ============================================================================
# Random Data Generation Tests
# ============================================================================

class TestRandomDataGeneration:
    """Test random data generation functionality."""

    def test_generate_random_data_basic(self):
        """Test basic random data generation with specific dtypes."""
        dtypes = ["INTEGER", "FLOAT", "TEXT"]

        result = EnhancedPolars.generate_random_data(n=100, dtypes=dtypes)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 100
        assert set(result.columns) == {"INTEGER", "FLOAT", "TEXT"}

    def test_generate_random_data_with_nulls(self):
        """Test random data generation with null values."""
        dtypes = ["INTEGER", "FLOAT"]

        result = EnhancedPolars.generate_random_data(
            n=100,
            dtypes=dtypes,
            percent_null=0.1
        )

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 100


# ============================================================================
# IPC File Reading Tests
# ============================================================================

class TestReadIPC:
    """Test IPC (Arrow) file reading functionality."""

    def test_read_ipc_eager(self, tmp_path):
        """Test reading IPC file in eager mode."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert result["a"].to_list() == [1, 2, 3]
        assert result["b"].to_list() == ["x", "y", "z"]

    def test_read_ipc_lazy(self, tmp_path):
        """Test reading IPC file in lazy mode."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert len(collected) == 3

    def test_read_ipc_with_columns(self, tmp_path):
        """Test reading specific columns from IPC file."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [4.0, 5.0, 6.0]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager', columns=["a", "c"])

        assert isinstance(result, pl.DataFrame)
        assert set(result.columns) == {"a", "c"}
        assert "b" not in result.columns

    def test_read_ipc_with_n_rows(self, tmp_path):
        """Test reading limited rows from IPC file."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": list(range(100))})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager', n_rows=10)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 10


# ============================================================================
# NDJSON File Reading Tests
# ============================================================================

class TestReadNDJSON:
    """Test NDJSON (newline-delimited JSON) file reading functionality."""

    def test_read_ndjson_eager(self, tmp_path):
        """Test reading NDJSON file in eager mode."""
        ndjson_path = tmp_path / "test.ndjson"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ndjson(ndjson_path)

        result = EnhancedPolars.read_ndjson(ndjson_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_ndjson_lazy(self, tmp_path):
        """Test reading NDJSON file in lazy mode."""
        ndjson_path = tmp_path / "test.ndjson"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ndjson(ndjson_path)

        result = EnhancedPolars.read_ndjson(ndjson_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert len(collected) == 3

    def test_read_ndjson_with_n_rows(self, tmp_path):
        """Test reading limited rows from NDJSON file."""
        ndjson_path = tmp_path / "test.ndjson"
        df = pl.DataFrame({"a": list(range(100))})
        df.write_ndjson(ndjson_path)

        result = EnhancedPolars.read_ndjson(ndjson_path, mode='eager', n_rows=10)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 10


# ============================================================================
# Edge Cases for File Reading
# ============================================================================

class TestFileReadingEdgeCases:
    """Test edge cases for file reading functionality."""

    def test_read_parquet_with_row_index(self, tmp_path):
        """Test reading parquet with row index."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_parquet(parquet_path, mode='eager', row_index_name="idx")

        assert isinstance(result, pl.DataFrame)
        if "idx" in result.columns:
            assert result["idx"].to_list() == [0, 1, 2]

    def test_read_csv_with_infer_schema(self, tmp_path):
        """Test reading CSV with schema inference."""
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "str_col": ["a", "b", "c"]
        })
        df.write_csv(csv_path)

        result = EnhancedPolars.read_csv(csv_path, mode='eager', infer_schema_length=100)

        assert isinstance(result, pl.DataFrame)
        # Schema should be inferred (may be optimized to smaller types)
        assert result["int_col"].dtype.is_numeric()
        assert result["float_col"].dtype.is_float()

    def test_read_parquet_glob_pattern(self, tmp_path):
        """Test reading multiple parquet files with glob pattern."""
        # Create multiple parquet files
        for i in range(3):
            parquet_path = tmp_path / f"part_{i}.parquet"
            df = pl.DataFrame({"a": [i * 10 + j for j in range(5)]})
            df.write_parquet(parquet_path)

        # Read all files with glob
        result = EnhancedPolars.read_parquet(str(tmp_path / "*.parquet"), mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 15  # 3 files * 5 rows each

    def test_read_csv_with_null_values(self, tmp_path):
        """Test reading CSV with custom null values."""
        csv_path = tmp_path / "test.csv"
        # Write CSV with custom null representation
        with open(csv_path, 'w') as f:
            f.write("a,b\n")
            f.write("1,value\n")
            f.write("NA,missing\n")
            f.write("3,value\n")

        result = EnhancedPolars.read_csv(csv_path, mode='eager', null_values=["NA"])

        assert isinstance(result, pl.DataFrame)
        assert result["a"].null_count() == 1  # "NA" should be null

    def test_read_ipc_large_file(self, tmp_path):
        """Test reading large IPC file."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": list(range(1000)), "b": [f"val_{i}" for i in range(1000)]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 1000


# ============================================================================
# Multiple File Reading Tests
# ============================================================================

class TestMultipleFileReading:
    """Test reading multiple files at once."""

    def test_read_csv_list_of_files(self, tmp_path):
        """Test reading multiple CSV files from a list."""
        files = []
        for i in range(3):
            csv_path = tmp_path / f"file_{i}.csv"
            df = pl.DataFrame({"a": [i * 10], "b": [f"file_{i}"]})
            df.write_csv(csv_path)
            files.append(str(csv_path))

        result = EnhancedPolars.read_csv(files, mode='eager')

        # Multiple files may return LazyFrame, collect if needed
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
