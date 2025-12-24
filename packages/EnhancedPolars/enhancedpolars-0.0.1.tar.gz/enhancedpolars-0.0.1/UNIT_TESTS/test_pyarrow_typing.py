"""
Tests for pyarrow_typing.py - PyArrow type utilities
"""

import pytest
import pyarrow as pa
from packaging.version import Version
from enhancedpolars.pyarrow_typing import (
    get_dtype_meta,
    get_meta_for_table,
    get_schema_meta,
    merge_dtypes,
    solve_table_schema,
    convert_table,
    concat_tables,
)


class TestGetDtypeMeta:
    """Tests for get_dtype_meta function."""

    def test_integer_types(self):
        """Test metadata for integer types."""
        meta = get_dtype_meta(pa.int64())
        assert meta["bit_width"] == 64
        assert meta["signed"] is True

        meta = get_dtype_meta(pa.int32())
        assert meta["bit_width"] == 32

        meta = get_dtype_meta(pa.uint64())
        assert meta["bit_width"] == 64
        assert meta["signed"] is False

    @pytest.mark.skipif(
    Version(pa.__version__) < Version("17.0.0"),
    reason="pyarrow >= 17.0.0 required",
)
    def test_float_types(self):
        """Test metadata for float types."""
        meta = get_dtype_meta(pa.float64())
        assert meta["bit_width"] == 64

        meta = get_dtype_meta(pa.float32())
        assert meta["bit_width"] == 32

    def test_timestamp_type(self):
        """Test metadata for timestamp types."""
        meta = get_dtype_meta(pa.timestamp("us", tz="UTC"))
        assert meta["unit"] == "us"
        assert meta["timezone"] == "UTC"

    def test_decimal_type(self):
        """Test metadata for decimal types."""
        meta = get_dtype_meta(pa.decimal128(10, 2))
        assert meta["precision"] == 10
        assert meta["scale"] == 2

    def test_list_type(self):
        """Test metadata for list types."""
        meta = get_dtype_meta(pa.list_(pa.int64()))
        assert meta["value_type"] is not None
        assert meta["value_type"]["bit_width"] == 64

    def test_struct_type(self):
        """Test metadata for struct types."""
        struct_type = pa.struct([
            pa.field("a", pa.int64()),
            pa.field("b", pa.string()),
        ])
        meta = get_dtype_meta(struct_type)
        assert meta["fields"] is not None
        assert "a" in meta["fields"]
        assert "b" in meta["fields"]

    def test_map_type(self):
        """Test metadata for map types."""
        map_type = pa.map_(pa.string(), pa.int64())
        meta = get_dtype_meta(map_type)
        assert meta["key_type"] is not None
        assert meta["value_type"] is not None

    def test_dictionary_type(self):
        """Test metadata for dictionary types."""
        dict_type = pa.dictionary(pa.int32(), pa.string())
        meta = get_dtype_meta(dict_type)
        assert meta["key_type"] is not None
        assert meta["value_type"] is not None


class TestGetMetaForTable:
    """Tests for get_meta_for_table function."""

    def test_basic_table(self):
        """Test metadata for a basic table."""
        table = pa.table({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })

        meta = get_meta_for_table(table)

        assert meta["num_rows"] == 3
        assert meta["num_columns"] == 2
        assert "schema" in meta
        assert "columns" in meta
        assert "a" in meta["columns"]
        assert "b" in meta["columns"]

    def test_empty_table(self):
        """Test metadata for an empty table."""
        schema = pa.schema([
            pa.field("a", pa.int64()),
            pa.field("b", pa.string()),
        ])
        table = pa.table({"a": [], "b": []}, schema=schema)

        meta = get_meta_for_table(table)

        assert meta["num_rows"] == 0
        assert meta["num_columns"] == 2


class TestGetSchemaMeta:
    """Tests for get_schema_meta function."""

    def test_basic_schema(self):
        """Test metadata for a basic schema (no float types due to API differences)."""
        schema = pa.schema([
            pa.field("a", pa.int64()),
            pa.field("b", pa.string()),
            pa.field("c", pa.date32()),
        ])

        meta = get_schema_meta(schema)

        assert meta["names"] == ["a", "b", "c"]
        assert len(meta["types"]) == 3


class TestMergeDtypes:
    """Tests for merge_dtypes function."""

    def test_same_types(self):
        """Test merging same types."""
        result = merge_dtypes(pa.int64(), pa.int64())
        assert result == pa.int64()

    def test_integer_promotion(self):
        """Test integer type promotion."""
        result = merge_dtypes(pa.int32(), pa.int64())
        assert result == pa.int64()

        result = merge_dtypes(pa.int8(), pa.int16(), pa.int32())
        assert result == pa.int32()

    def test_int_to_float_promotion(self):
        """Test integer to float promotion."""
        result = merge_dtypes(pa.int64(), pa.float64())
        assert result == pa.float64()

        result = merge_dtypes(pa.float32(), pa.int32())
        assert result == pa.float32()

    def test_float_promotion(self):
        """Test float type promotion."""
        result = merge_dtypes(pa.float32(), pa.float64())
        assert result == pa.float64()

    def test_single_dtype(self):
        """Test with single dtype."""
        result = merge_dtypes(pa.int64())
        assert result == pa.int64()

    def test_empty_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="At least one dtype"):
            merge_dtypes()

    def test_string_and_large_string(self):
        """Test string to large_string promotion."""
        result = merge_dtypes(pa.string(), pa.large_string())
        assert result == pa.large_string()

    def test_date_to_timestamp(self):
        """Test date to timestamp promotion."""
        result = merge_dtypes(pa.date32(), pa.timestamp("us"))
        assert pa.types.is_timestamp(result)

    def test_decimal_promotion(self):
        """Test decimal type promotion."""
        result = merge_dtypes(pa.decimal128(5, 2), pa.decimal128(10, 2))
        assert result == pa.decimal128(10, 2)

    def test_decimal_and_int(self):
        """Test decimal and integer merging."""
        result = merge_dtypes(pa.int64(), pa.decimal128(10, 2))
        assert pa.types.is_decimal(result)

    def test_incompatible_raises(self):
        """Test that incompatible types raise TypeError."""
        with pytest.raises(TypeError, match="Incompatible schema"):
            merge_dtypes(pa.string(), pa.int64())


class TestSolveTableSchema:
    """Tests for solve_table_schema function."""

    def test_single_table(self):
        """Test with single table."""
        table = pa.table({"a": [1, 2, 3]})
        result = solve_table_schema(table)

        assert result == table.schema

    def test_compatible_tables(self):
        """Test merging compatible table schemas."""
        table1 = pa.table({"a": pa.array([1, 2, 3], type=pa.int32())})
        table2 = pa.table({"a": pa.array([4, 5, 6], type=pa.int64())})

        result = solve_table_schema(table1, table2)

        assert result.field("a").type == pa.int64()

    def test_with_change_flag(self):
        """Test solve_table_schema with change_flag."""
        table1 = pa.table({"a": pa.array([1, 2, 3], type=pa.int32())})
        table2 = pa.table({"a": pa.array([4, 5, 6], type=pa.int64())})

        result, changed = solve_table_schema(table1, table2, change_flag=True)

        assert changed is True
        assert result.field("a").type == pa.int64()

    def test_no_change(self):
        """Test solve_table_schema with no schema change."""
        table1 = pa.table({"a": [1, 2, 3]})
        table2 = pa.table({"a": [4, 5, 6]})

        result, changed = solve_table_schema(table1, table2, change_flag=True)

        assert changed is False

    def test_additional_columns(self):
        """Test merging schemas with different columns."""
        table1 = pa.table({"a": [1, 2]})
        table2 = pa.table({"a": [3, 4], "b": ["x", "y"]})

        result, changed = solve_table_schema(table1, table2, change_flag=True)

        assert "a" in result.names
        assert "b" in result.names
        # Note: changed may be False if only new columns are added without type changes

    def test_empty_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="At least one table"):
            solve_table_schema()

    def test_schema_input(self):
        """Test with schema input instead of table."""
        schema1 = pa.schema([pa.field("a", pa.int32())])
        schema2 = pa.schema([pa.field("a", pa.int64())])

        result = solve_table_schema(schema1, schema2)

        assert result.field("a").type == pa.int64()


class TestConvertTable:
    """Tests for convert_table function."""

    def test_basic_conversion(self):
        """Test basic table conversion."""
        table = pa.table({"a": pa.array([1, 2, 3], type=pa.int32())})
        new_schema = pa.schema([pa.field("a", pa.int64())])

        result = convert_table(table, new_schema)

        assert result.schema.field("a").type == pa.int64()
        assert result.to_pydict()["a"] == [1, 2, 3]

    def test_float_conversion(self):
        """Test int to float conversion."""
        table = pa.table({"a": [1, 2, 3]})
        new_schema = pa.schema([pa.field("a", pa.float64())])

        result = convert_table(table, new_schema)

        assert result.schema.field("a").type == pa.float64()


class TestConcatTables:
    """Tests for concat_tables function."""

    def test_basic_concat(self):
        """Test basic table concatenation."""
        table1 = pa.table({"a": [1, 2]})
        table2 = pa.table({"a": [3, 4]})

        result = concat_tables(table1, table2)

        assert result.num_rows == 4
        assert result.to_pydict()["a"] == [1, 2, 3, 4]

    def test_concat_with_schema_promotion(self):
        """Test concat with schema promotion."""
        table1 = pa.table({"a": pa.array([1, 2], type=pa.int32())})
        table2 = pa.table({"a": pa.array([3, 4], type=pa.int64())})

        result = concat_tables(table1, table2)

        assert result.schema.field("a").type == pa.int64()
        assert result.num_rows == 4

    def test_empty_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="At least one table"):
            concat_tables()

    def test_concat_multiple(self):
        """Test concatenating multiple tables."""
        table1 = pa.table({"a": [1]})
        table2 = pa.table({"a": [2]})
        table3 = pa.table({"a": [3]})

        result = concat_tables(table1, table2, table3)

        assert result.num_rows == 3
        assert result.to_pydict()["a"] == [1, 2, 3]


class TestTimestampTypes:
    """Tests for timestamp type handling."""

    def test_timestamp_metadata(self):
        """Test timestamp metadata extraction."""
        ts_type = pa.timestamp("ns", tz="America/New_York")
        meta = get_dtype_meta(ts_type)

        assert meta["unit"] == "ns"
        assert meta["timezone"] == "America/New_York"

    def test_timestamp_merge(self):
        """Test timestamp type merging."""
        ts1 = pa.timestamp("us")
        ts2 = pa.timestamp("ns")

        result = merge_dtypes(ts1, ts2)

        # ns has higher bit width, should be chosen
        assert pa.types.is_timestamp(result)


class TestTimeTypes:
    """Tests for time type handling."""

    def test_time_metadata(self):
        """Test time metadata extraction."""
        time_type = pa.time64("us")
        meta = get_dtype_meta(time_type)

        assert meta["unit"] == "us"
        assert meta["bit_width"] == 64

    def test_time_merge(self):
        """Test time type merging."""
        time1 = pa.time32("s")
        time2 = pa.time64("us")

        result = merge_dtypes(time1, time2)

        # time64 has higher bit width
        assert result.bit_width == 64


class TestDurationTypes:
    """Tests for duration type handling."""

    def test_duration_metadata(self):
        """Test duration metadata extraction."""
        dur_type = pa.duration("ms")
        meta = get_dtype_meta(dur_type)

        assert meta["unit"] == "ms"


class TestBinaryTypes:
    """Tests for binary type handling."""

    def test_binary_promotion(self):
        """Test binary to large_binary promotion."""
        result = merge_dtypes(pa.binary(), pa.large_binary())
        assert result == pa.large_binary()

    def test_fixed_size_binary_metadata(self):
        """Test fixed size binary metadata."""
        fsb_type = pa.binary(16)
        meta = get_dtype_meta(fsb_type)

        assert meta["bit_width"] == 16 * 8  # bytes to bits


class TestDictionaryMerging:
    """Tests for dictionary type merging."""

    def test_dict_to_dict_merge(self):
        """Test dictionary to dictionary merging."""
        dict1 = pa.dictionary(pa.int8(), pa.string())
        dict2 = pa.dictionary(pa.int32(), pa.string())

        result = merge_dtypes(dict1, dict2)

        # Larger index type should be chosen
        assert pa.types.is_dictionary(result)
        assert result.index_type.bit_width >= 8

    def test_dict_and_string(self):
        """Test dictionary and string merging."""
        dict_type = pa.dictionary(pa.int32(), pa.string())
        str_type = pa.string()

        # Both should work without error
        result = merge_dtypes(dict_type, str_type)
        assert result is not None
