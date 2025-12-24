"""
Tests for io.py - PolarsIO extension
"""

import pytest
import polars as pl
import pandas as pd
import numpy as np
import pyarrow as pa
import tempfile
import os
from pathlib import Path
from enhancedpolars.io import PolarsIO


class TestToCsv:
    """Tests for to_csv method."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame."""
        return pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "str_col": ["a", "b", "c"],
        })

    def test_to_csv_basic(self, sample_df):
        """Test basic CSV writing."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_csv(fp)

            # Verify file was created and can be read back
            result = pl.read_csv(fp)
            assert result.shape == sample_df.shape
            assert result.columns == sample_df.columns
        finally:
            os.unlink(fp)

    def test_to_csv_lazyframe(self, sample_df):
        """Test CSV writing from LazyFrame."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df.lazy())
            ext.to_csv(fp)

            result = pl.read_csv(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)


class TestToParquet:
    """Tests for to_parquet method."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame."""
        return pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0],
            "category": ["A", "B", "A"],
        })

    def test_to_parquet_basic(self, sample_df):
        """Test basic Parquet writing."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_parquet(fp)

            result = pl.read_parquet(fp)
            assert result.shape == sample_df.shape
            assert result.columns == sample_df.columns
        finally:
            os.unlink(fp)

    def test_to_parquet_lazyframe(self, sample_df):
        """Test Parquet writing from LazyFrame."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df.lazy())
            ext.to_parquet(fp)

            result = pl.read_parquet(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)


class TestToPartitionedParquet:
    """Tests for to_partitioned_parquet method."""

    @pytest.fixture
    def partitioned_df(self):
        """Create a DataFrame suitable for partitioning."""
        return pl.DataFrame({
            "year": [2020, 2020, 2021, 2021],
            "month": [1, 2, 1, 2],
            "value": [100, 200, 300, 400],
        })

    def test_to_partitioned_parquet_basic(self, partitioned_df):
        """Test basic partitioned Parquet writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = PolarsIO(partitioned_df)
            ext.to_partitioned_parquet(tmpdir, partition_cols=["year"])

            # Verify partitioned structure was created
            assert os.path.exists(os.path.join(tmpdir, "_dataset_metadata.json"))
            # Read back the data
            result = pl.read_parquet(os.path.join(tmpdir, "**/*.parquet"), glob=True)
            assert result.shape[0] == partitioned_df.shape[0]

    def test_to_partitioned_parquet_multiple_cols(self, partitioned_df):
        """Test partitioned Parquet with multiple partition columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = PolarsIO(partitioned_df)
            ext.to_partitioned_parquet(tmpdir, partition_cols=["year", "month"])

            result = pl.read_parquet(os.path.join(tmpdir, "**/*.parquet"), glob=True)
            assert result.shape[0] == partitioned_df.shape[0]

    def test_to_partitioned_parquet_string_col(self, partitioned_df):
        """Test partitioned Parquet with string partition column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = PolarsIO(partitioned_df)
            ext.to_partitioned_parquet(tmpdir, partition_cols="year")  # String instead of list

            result = pl.read_parquet(os.path.join(tmpdir, "**/*.parquet"), glob=True)
            assert result.shape[0] == partitioned_df.shape[0]

    def test_to_partitioned_parquet_empty_cols_raises(self, partitioned_df):
        """Test that empty partition_cols raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = PolarsIO(partitioned_df)
            with pytest.raises(ValueError, match="cannot be empty"):
                ext.to_partitioned_parquet(tmpdir, partition_cols=[])

    def test_to_partitioned_parquet_missing_col_raises(self, partitioned_df):
        """Test that missing partition column raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = PolarsIO(partitioned_df)
            with pytest.raises(ValueError, match="missing from the DataFrame"):
                ext.to_partitioned_parquet(tmpdir, partition_cols=["nonexistent"])


class TestToIpc:
    """Tests for to_ipc method."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame."""
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4.0, 5.0, 6.0],
        })

    def test_to_ipc_basic(self, sample_df):
        """Test basic IPC writing."""
        with tempfile.NamedTemporaryFile(suffix=".arrow", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_ipc(fp)

            result = pl.read_ipc(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)

    def test_to_ipc_stream(self, sample_df):
        """Test IPC stream writing."""
        with tempfile.NamedTemporaryFile(suffix=".arrows", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_ipc(fp, stream=True)

            result = pl.read_ipc_stream(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)

    def test_to_ipc_lazyframe(self, sample_df):
        """Test IPC writing from LazyFrame."""
        with tempfile.NamedTemporaryFile(suffix=".arrow", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df.lazy())
            ext.to_ipc(fp)

            result = pl.read_ipc(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)


class TestToNdjson:
    """Tests for to_ndjson method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "x": [1, 2],
            "y": ["a", "b"],
        })

    def test_to_ndjson_basic(self, sample_df):
        """Test basic NDJSON writing."""
        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_ndjson(fp)

            result = pl.read_ndjson(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)

    def test_to_ndjson_lazyframe(self, sample_df):
        """Test NDJSON writing from LazyFrame."""
        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df.lazy())
            ext.to_ndjson(fp)

            result = pl.read_ndjson(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)


class TestToJson:
    """Tests for to_json method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "x": [1, 2],
            "y": ["a", "b"],
        })

    def test_to_json_basic(self, sample_df):
        """Test basic JSON writing."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_json(fp)

            # Verify file was created
            assert os.path.exists(fp)
            assert os.path.getsize(fp) > 0
        finally:
            os.unlink(fp)


class TestToAvro:
    """Tests for to_avro method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["a", "b", "c"],
        })

    def test_to_avro_basic(self, sample_df):
        """Test basic Avro writing."""
        with tempfile.NamedTemporaryFile(suffix=".avro", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_avro(fp)

            result = pl.read_avro(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)


class TestConversions:
    """Tests for conversion methods."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "str_col": ["a", "b", "c"],
        })

    def test_to_pandas(self, sample_df):
        """Test conversion to pandas DataFrame."""
        ext = PolarsIO(sample_df)
        result = ext.to_pandas()

        assert isinstance(result, pd.DataFrame)
        assert result.shape == sample_df.shape
        assert list(result.columns) == sample_df.columns

    def test_to_pandas_lazyframe(self, sample_df):
        """Test conversion to pandas from LazyFrame."""
        ext = PolarsIO(sample_df.lazy())
        result = ext.to_pandas()

        assert isinstance(result, pd.DataFrame)
        assert result.shape == sample_df.shape

    def test_to_numpy(self, sample_df):
        """Test conversion to numpy array."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        ext = PolarsIO(df)
        result = ext.to_numpy()

        assert isinstance(result, np.ndarray)
        assert result.shape == (3, 2)

    def test_to_numpy_lazyframe(self, sample_df):
        """Test conversion to numpy from LazyFrame."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        ext = PolarsIO(df.lazy())
        result = ext.to_numpy()

        assert isinstance(result, np.ndarray)

    def test_to_arrow(self, sample_df):
        """Test conversion to PyArrow table."""
        ext = PolarsIO(sample_df)
        result = ext.to_arrow()

        assert isinstance(result, pa.Table)
        assert result.num_rows == sample_df.shape[0]
        assert result.num_columns == sample_df.shape[1]

    def test_to_arrow_lazyframe(self, sample_df):
        """Test conversion to PyArrow from LazyFrame."""
        ext = PolarsIO(sample_df.lazy())
        result = ext.to_arrow()

        assert isinstance(result, pa.Table)

    def test_to_list(self, sample_df):
        """Test conversion to list."""
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        ext = PolarsIO(df)
        result = ext.to_list()

        assert isinstance(result, list)
        assert len(result) == 2

    def test_to_dict(self, sample_df):
        """Test conversion to dict."""
        ext = PolarsIO(sample_df)
        result = ext.to_dict()

        assert isinstance(result, dict)
        assert "int_col" in result
        assert "float_col" in result
        assert "str_col" in result

    def test_to_dict_lazyframe(self, sample_df):
        """Test conversion to dict from LazyFrame."""
        ext = PolarsIO(sample_df.lazy())
        result = ext.to_dict()

        assert isinstance(result, dict)


class TestParseDtypeString:
    """Tests for _parse_dtype_string static method."""

    def test_parse_basic_types(self):
        """Test parsing basic dtype strings."""
        assert PolarsIO._parse_dtype_string("Int64") == pl.Int64()
        assert PolarsIO._parse_dtype_string("Int32") == pl.Int32()
        assert PolarsIO._parse_dtype_string("Int16") == pl.Int16()
        assert PolarsIO._parse_dtype_string("Int8") == pl.Int8()
        assert PolarsIO._parse_dtype_string("UInt64") == pl.UInt64()
        assert PolarsIO._parse_dtype_string("UInt32") == pl.UInt32()
        assert PolarsIO._parse_dtype_string("UInt16") == pl.UInt16()
        assert PolarsIO._parse_dtype_string("UInt8") == pl.UInt8()

    def test_parse_float_types(self):
        """Test parsing float dtype strings."""
        assert PolarsIO._parse_dtype_string("Float64") == pl.Float64()
        assert PolarsIO._parse_dtype_string("Float32") == pl.Float32()

    def test_parse_string_types(self):
        """Test parsing string dtype strings."""
        assert PolarsIO._parse_dtype_string("String") == pl.String()
        assert PolarsIO._parse_dtype_string("Utf8") == pl.Utf8()

    def test_parse_other_types(self):
        """Test parsing other dtype strings."""
        assert PolarsIO._parse_dtype_string("Boolean") == pl.Boolean()
        assert PolarsIO._parse_dtype_string("Date") == pl.Date()
        assert PolarsIO._parse_dtype_string("Time") == pl.Time()
        assert PolarsIO._parse_dtype_string("Null") == pl.Null()
        assert PolarsIO._parse_dtype_string("Binary") == pl.Binary()

    def test_parse_datetime(self):
        """Test parsing Datetime dtype strings."""
        result = PolarsIO._parse_dtype_string("Datetime(time_unit='us')")
        assert result == pl.Datetime(time_unit='us')

    def test_parse_datetime_with_timezone(self):
        """Test parsing Datetime with timezone."""
        result = PolarsIO._parse_dtype_string("Datetime(time_unit='us', time_zone='UTC')")
        assert result == pl.Datetime(time_unit='us', time_zone='UTC')

    def test_parse_duration(self):
        """Test parsing Duration dtype strings."""
        result = PolarsIO._parse_dtype_string("Duration(time_unit='ms')")
        assert result == pl.Duration(time_unit='ms')

    def test_parse_unknown_returns_string(self):
        """Test that unknown dtype strings return String type."""
        result = PolarsIO._parse_dtype_string("UnknownType")
        assert result == pl.String()


class TestInheritance:
    """Tests for inheritance from UniversalPolarsDataFrameExtension."""

    def test_inherits_properties(self):
        """Test that PolarsIO inherits base properties."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

        ext = PolarsIO(df)

        assert ext.schema == {"a": pl.Int64, "b": pl.Int64}
        assert ext.length == 3
        assert ext.width == 2
        assert ext.columns == ["a", "b"]
        assert ext.shape == (3, 2)
        assert ext.is_lazy is False

    def test_inherits_lazyframe_properties(self):
        """Test that PolarsIO works with LazyFrame."""
        lf = pl.LazyFrame({
            "a": [1, 2, 3],
        })

        ext = PolarsIO(lf)

        assert ext.is_lazy is True
        assert ext.length == 3


class TestToRecords:
    """Tests for to_records method."""

    def test_to_records(self):
        """Test conversion to series."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

        ext = PolarsIO(df)
        # to_records uses to_series which requires an index parameter
        result = ext.to_records(index=0)

        assert isinstance(result, pl.Series)
        assert result.name == "a"


class TestSignedFiles:
    """Tests for signed file functionality."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0],
        })

    def test_to_csv_signed(self, sample_df):
        """Test signed CSV writing."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_csv(fp, signed=True)

            # Verify the signed file can be verified
            assert PolarsIO.verify_signed_file(fp)
        finally:
            os.unlink(fp)

    def test_to_parquet_signed(self, sample_df):
        """Test signed Parquet writing."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_parquet(fp, signed=True)

            assert PolarsIO.verify_signed_file(fp)
        finally:
            os.unlink(fp)

    def test_to_ipc_signed(self, sample_df):
        """Test signed IPC writing."""
        with tempfile.NamedTemporaryFile(suffix=".arrow", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_ipc(fp, signed=True)

            assert PolarsIO.verify_signed_file(fp)
        finally:
            os.unlink(fp)

    def test_to_parquet_signed_with_partition_raises(self, sample_df):
        """Test that signed=True with partition_cols raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = PolarsIO(sample_df)
            with pytest.raises(ValueError, match="not compatible with partition_cols"):
                ext.to_parquet(tmpdir, signed=True, partition_cols=["id"])


class TestToExcel:
    """Tests for to_excel method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })

    def test_to_excel_basic(self, sample_df):
        """Test basic Excel writing."""
        pytest.importorskip("xlsxwriter", reason="xlsxwriter not installed")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_excel(fp)

            # Verify file was created
            assert os.path.exists(fp)
            assert os.path.getsize(fp) > 0

            # Read back and verify
            result = pl.read_excel(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)

    def test_to_excel_lazyframe(self, sample_df):
        """Test Excel writing from LazyFrame."""
        pytest.importorskip("xlsxwriter", reason="xlsxwriter not installed")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df.lazy())
            ext.to_excel(fp)

            # Verify file was created
            assert os.path.exists(fp)
            result = pl.read_excel(fp)
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)


class TestToDelta:
    """Tests for to_delta method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0],
        })

    def test_to_delta_basic(self, sample_df):
        """Test basic Delta Lake writing."""
        pytest.importorskip("deltalake", reason="deltalake not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            delta_path = os.path.join(tmpdir, "test_delta")
            ext = PolarsIO(sample_df)
            ext.to_delta(delta_path)

            # Verify Delta table was created
            assert os.path.exists(os.path.join(delta_path, "_delta_log"))

            # Read back and verify
            result = pl.read_delta(delta_path)
            assert result.shape == sample_df.shape

    def test_to_delta_lazyframe(self, sample_df):
        """Test Delta Lake writing from LazyFrame."""
        pytest.importorskip("deltalake", reason="deltalake not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            delta_path = os.path.join(tmpdir, "test_delta")
            ext = PolarsIO(sample_df.lazy())
            ext.to_delta(delta_path)

            assert os.path.exists(os.path.join(delta_path, "_delta_log"))


class TestToIceberg:
    """Tests for to_iceberg method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0],
        })

    def test_to_iceberg_requires_catalog(self, sample_df):
        """Test that to_iceberg requires proper catalog setup."""
        pytest.importorskip("pyiceberg", reason="pyiceberg not installed")

        # Iceberg requires a catalog configuration, so this should fail without one
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = PolarsIO(sample_df)
            # Without a proper catalog, this should raise an error
            with pytest.raises(Exception):
                ext.to_iceberg(tmpdir)


class TestToHdf:
    """Tests for to_hdf method."""

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4.0, 5.0, 6.0],
        })

    def test_to_hdf_basic(self, sample_df):
        """Test basic HDF5 writing."""
        pytest.importorskip("tables", reason="pytables not installed")

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_df)
            ext.to_hdf(fp, key="data")

            # Verify file was created
            assert os.path.exists(fp)

            # Read back via pandas
            result = pd.read_hdf(fp, key="data")
            assert result.shape == sample_df.shape
        finally:
            os.unlink(fp)


class TestIOEdgeCases:
    """Edge case tests for IO methods."""

    def test_io_empty_dataframe_csv(self):
        """Test writing empty DataFrame to CSV."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        ext = PolarsIO(df)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fp = f.name

        try:
            ext.to_csv(fp)
            result = pl.read_csv(fp)
            assert len(result) == 0
        finally:
            os.unlink(fp)

    def test_io_empty_dataframe_parquet(self):
        """Test writing empty DataFrame to Parquet."""
        df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64)})
        ext = PolarsIO(df)

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            fp = f.name

        try:
            ext.to_parquet(fp)
            result = pl.read_parquet(fp)
            assert len(result) == 0
        finally:
            os.unlink(fp)

    def test_io_special_characters_csv(self):
        """Test writing DataFrame with special characters to CSV."""
        df = pl.DataFrame({
            "text": ["hello, world", '"quoted"', "line1\nline2"],
        })
        ext = PolarsIO(df)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fp = f.name

        try:
            ext.to_csv(fp)
            result = pl.read_csv(fp)
            assert result["text"].to_list() == df["text"].to_list()
        finally:
            os.unlink(fp)

    def test_io_null_values_parquet(self):
        """Test writing DataFrame with null values to Parquet."""
        df = pl.DataFrame({
            "a": [1, None, 3],
            "b": [None, 2.0, None],
        })
        ext = PolarsIO(df)

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            fp = f.name

        try:
            ext.to_parquet(fp)
            result = pl.read_parquet(fp)
            assert result["a"].null_count() == 1
            assert result["b"].null_count() == 2
        finally:
            os.unlink(fp)

    def test_io_path_object(self):
        """Test writing with Path object instead of string."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        ext = PolarsIO(df)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fp = Path(f.name)

        try:
            ext.to_csv(fp)
            result = pl.read_csv(fp)
            assert result.shape == df.shape
        finally:
            os.unlink(fp)


class TestLazyFrameIOSupport:
    """Tests for LazyFrame support across IO methods."""

    @pytest.fixture
    def sample_lf(self):
        return pl.LazyFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0],
        })

    def test_to_csv_returns_none(self, sample_lf):
        """Test that to_csv returns None (writes to file)."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            fp = f.name

        try:
            ext = PolarsIO(sample_lf)
            result = ext.to_csv(fp)
            assert result is None
        finally:
            os.unlink(fp)

    def test_to_pandas_collects_lazyframe(self, sample_lf):
        """Test that to_pandas properly collects LazyFrame."""
        ext = PolarsIO(sample_lf)
        result = ext.to_pandas()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_to_dict_collects_lazyframe(self, sample_lf):
        """Test that to_dict properly collects LazyFrame."""
        ext = PolarsIO(sample_lf)
        result = ext.to_dict()

        assert isinstance(result, dict)
        assert "id" in result
        assert "value" in result
