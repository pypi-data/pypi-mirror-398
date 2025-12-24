
import pyarrow as pa
from typing import Dict, Any, Tuple
from CoreUtilities.core_types import CoreDataType


def get_dtype_meta(dt: pa.DataType) -> Dict[str, Any]:
    info = {"arrow_type": str(dt), "id": dt.id, "bit_width": None, "signed": None,
            "precision": None, "scale": None, "unit": None, "timezone": None,
            "value_type": None, "key_type": None, "fields": None, 'core_data_type': None,
            'dtype': dt}

    if pa.types.is_integer(dt):
        info["bit_width"] = dt.bit_width
        info["signed"] = dt.bit_width > 0 and not pa.types.is_unsigned_integer(dt)
        info["core_data_type"] = CoreDataType.INTEGER

    elif _is_float_helper(dt):
        info["precision"] = 'HALF' if pa.types.is_float16(dt) else 'SINGLE' if pa.types.is_float32(dt) else 'DOUBLE'
        info["bit_width"] = dt.bit_width
        info["core_data_type"] = CoreDataType.FLOAT

    elif pa.types.is_decimal(dt):
        info["precision"] = dt.precision
        info["scale"] = dt.scale
        info["bit_width"] = dt.bit_width
        info["core_data_type"] = CoreDataType.DECIMAL

    elif pa.types.is_timestamp(dt):
        info["unit"] = dt.unit
        info["timezone"] = dt.tz
        info["bit_width"] = dt.bit_width
        info["core_data_type"] = CoreDataType.DATETIME

    elif pa.types.is_time(dt):
        info["unit"] = dt.unit
        info["bit_width"] = dt.bit_width
        info["core_data_type"] = CoreDataType.TIME

    elif pa.types.is_duration(dt):
        info["unit"] = dt.unit
        info["bit_width"] = dt.bit_width
        info["core_data_type"] = CoreDataType.TIMEDELTA

    elif pa.types.is_interval(dt):
        info["unit"] = dt.unit
        info["bit_width"] = dt.bit_width
        info["core_data_type"] = CoreDataType.TIMEDELTA

    elif pa.types.is_fixed_size_binary(dt):
        info["bit_width"] = dt.byte_width * 8
        info["core_data_type"] = CoreDataType.BYTES

    elif pa.types.is_list(dt) or pa.types.is_large_list(dt):
        info["value_type"] = get_dtype_meta(dt.value_type)
        info["core_data_type"] = CoreDataType.LIST

    elif pa.types.is_fixed_size_list(dt):
        info["value_type"] = get_dtype_meta(dt.value_type)
        info["list_size"] = dt.list_size
        info["core_data_type"] = CoreDataType.LIST

    elif pa.types.is_struct(dt):
        info["fields"] = {f.name: get_dtype_meta(f.type) for f in dt}
        info["core_data_type"] = CoreDataType.OBJECT

    elif pa.types.is_map(dt):
        info["key_type"] = get_dtype_meta(dt.key_type)
        info["value_type"] = get_dtype_meta(dt.item_type)
        info["core_data_type"] = CoreDataType.DICT

    elif pa.types.is_dictionary(dt):
        info["key_type"] = get_dtype_meta(dt.index_type)
        info["value_type"] = get_dtype_meta(dt.value_type)
        info["core_data_type"] = CoreDataType.DICT

    elif hasattr(pa.types, "is_uuid") and pa.types.is_uuid(dt): # type: ignore
        info["bit_width"] = 128   # fixed at 16 bytes
        info["core_data_type"] = CoreDataType.UUID

    return info

def _is_float_helper(dtype: pa.DataType) -> bool:
    return pa.types.is_floating(dtype) or pa.types.is_float64(dtype)


def get_meta_for_table(table: pa.Table) -> Dict[str, Any]:
    return {
        "num_rows": table.num_rows,
        "num_columns": table.num_columns,
        "schema": get_schema_meta(table.schema),
        "columns": {name: get_dtype_meta(col.type) for name, col in zip(table.column_names, table.columns)}
    }

def get_schema_meta(schema: pa.Schema) -> Dict[str, Any]:
    return {
        "names": schema.names,
        "types": [get_dtype_meta(field.type) for field in schema],
    }

def merge_dtypes(*dtypes: pa.DataType) -> pa.DataType:
    """
    Determine the smallest compatible dtype from a sequence of PyArrow data types.
    
    Compatible upgrades:
    - int8/int16/int32 -> int64
    - int8/int16/int32/int64 -> float32/float64
    - float32 -> float64  
    - categorical -> utf8
    
    Args:
        *dtypes: Variable number of PyArrow DataType objects
        
    Returns:
        The smallest PyArrow DataType that can accommodate all input types
        
    Raises:
        ValueError: If no dtypes are provided
        TypeError: If dtypes are incompatible
    """
    if not dtypes:
        raise ValueError("At least one dtype must be provided")
    
    if len(dtypes) == 1:
        return dtypes[0]
    
    # Start with the first dtype and merge with each subsequent one
    result = dtypes[0]
    for dtype in dtypes[1:]:
        result = _merge_two_dtypes(result, dtype)
    
    return result


def _merge_two_dtypes(old_type: pa.DataType, new_type: pa.DataType) -> pa.DataType:
    """
    Helper function to merge two PyArrow data types.
    """
    # Same type - no upgrade needed
    if old_type.equals(new_type):
        return old_type
        
    # Integer to larger integer
    if pa.types.is_integer(old_type) and pa.types.is_integer(new_type):
        old_bits = old_type.bit_width
        new_bits = new_type.bit_width
        return new_type if new_bits >= old_bits else old_type
    
    # Integer to float
    if pa.types.is_integer(old_type) and _is_float_helper(new_type):
        return new_type
    elif _is_float_helper(old_type) and pa.types.is_integer(new_type):
        return old_type
        
    # Float to larger float
    if _is_float_helper(old_type) and _is_float_helper(new_type):
        old_bits = old_type.bit_width
        new_bits = new_type.bit_width
        return new_type if new_bits >= old_bits else old_type
    
    # Decimals
    if pa.types.is_decimal(old_type) and pa.types.is_decimal(new_type):
        old_precision = old_type.precision
        new_precision = new_type.precision
        old_scale = old_type.scale
        new_scale = new_type.scale
        if new_precision >= old_precision and new_scale >= old_scale:
            return new_type
        elif old_precision >= new_precision and old_scale >= new_scale:
            return old_type
        else:
            raise TypeError(f"Incompatible decimal schema upgrade from {old_type} to {new_type}")
    elif pa.types.is_decimal(old_type) and _is_float_helper(new_type):
        return new_type
    elif _is_float_helper(old_type) and pa.types.is_decimal(new_type):
        return old_type
    elif pa.types.is_decimal(old_type) and pa.types.is_integer(new_type):
        return old_type
    elif pa.types.is_integer(old_type) and pa.types.is_decimal(new_type):
        return new_type
        
    # Categorical to string
    if pa.types.is_dictionary(old_type) and pa.types.is_string(new_type):
        return old_type
    elif pa.types.is_string(old_type) and pa.types.is_dictionary(new_type):
        return new_type
    
    # Categorical to larger categorical
    if pa.types.is_dictionary(old_type) and pa.types.is_dictionary(new_type):
        old_bits = old_type.index_type.bit_width
        new_bits = new_type.index_type.bit_width
        return new_type if new_bits >= old_bits else old_type
    
    # String to larger string (e.g., large_utf8)
    if pa.types.is_string(old_type) and pa.types.is_large_string(new_type):
        return new_type
    elif pa.types.is_large_string(old_type) and pa.types.is_string(new_type):
        return old_type
    
    # binary to larger binary (e.g., large_binary)
    if pa.types.is_binary(old_type) and pa.types.is_large_binary(new_type):
        return new_type
    elif pa.types.is_large_binary(old_type) and pa.types.is_binary(new_type):
        return old_type
    
    # Date to larger date/time
    if pa.types.is_date(old_type) and pa.types.is_timestamp(new_type):
        return new_type
    elif pa.types.is_timestamp(old_type) and pa.types.is_date(new_type):
        return old_type
    elif pa.types.is_date(old_type) and pa.types.is_date(new_type):
        old_bits = old_type.bit_width
        new_bits = new_type.bit_width
        return new_type if new_bits >= old_bits else old_type
    elif pa.types.is_timestamp(old_type) and pa.types.is_timestamp(new_type):
        old_bits = old_type.bit_width
        new_bits = new_type.bit_width
        return new_type if new_bits >= old_bits else old_type
    elif pa.types.is_time(old_type) and pa.types.is_time(new_type):
        old_bits = old_type.bit_width
        new_bits = new_type.bit_width
        return new_type if new_bits >= old_bits else old_type

    raise TypeError(f"Incompatible schema upgrade from {old_type} to {new_type}")


def solve_table_schema(*tables: pa.Table | pa.Schema, change_flag: bool = False) -> pa.Schema | Tuple[pa.Schema, bool]:
    """
    Solve the schema for a set of PyArrow tables by merging their schemas.
    """
    if not tables:
        raise ValueError("At least one table must be provided")

    # Start with the schema of the first table
    merged_schema = tables[0].schema if isinstance(tables[0], pa.Table) else tables[0]
    changed: bool = False
    for table in tables[1:]:
        new_schema = table.schema if isinstance(table, pa.Table) else table
        try:
            fields = []
            for field in merged_schema:
                base_name = field.name
                base_type = field.type
                
                if base_name in new_schema.names:
                    new_field = new_schema.field(base_name)
                    new_type = new_field.type
                    final_type = _merge_two_dtypes(old_type=base_type, new_type=new_type)

                    changed = (final_type != base_type) or changed or (new_type != base_type) or (new_field.nullable != field.nullable)

                    fields.append(pa.field(base_name, final_type, nullable=field.nullable or new_field.nullable, metadata=field.metadata))

                else:
                    changed = True
                    fields.append(field)

            for field in new_schema:
                if field.name not in merged_schema.names:
                    fields.append(field)
            merged_schema = pa.schema(fields, metadata=merged_schema.metadata)
        except Exception as e:
            print(e)
            raise e
            merged_schema = pa.unify_schemas(*[merged_schema, new_schema])

    return (merged_schema, changed) if change_flag else merged_schema


def convert_table(table: pa.Table, schema: pa.Schema) -> pa.Table:
    """
    Convert a PyArrow table to a new schema by applying type promotions.
    """
    new_columns = []
    for i, column in enumerate(table.columns):
        old_type = column.type
        new_type = schema[i].type
        merged_type = _merge_two_dtypes(old_type, new_type)
        new_columns.append(table[i].cast(merged_type))
    return pa.Table.from_arrays(new_columns, schema=schema)


def concat_tables(*tables: pa.Table) -> pa.Table:
    """
    Concatenate multiple PyArrow tables into a single table.
    """
    if not tables:
        raise ValueError("At least one table must be provided")

    # Solve the schema for the concatenated table
    merged_schema = solve_table_schema(*tables)

    # Convert each table to the merged schema
    converted_tables = [convert_table(table, merged_schema) for table in tables]

    # Concatenate the converted tables
    return pa.concat_tables(converted_tables)