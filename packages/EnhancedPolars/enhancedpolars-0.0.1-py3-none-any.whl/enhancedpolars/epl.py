
import polars as pl
pl.Config.set_tbl_cols(30)
pl.Config.set_tbl_width_chars(300)
import numpy as np
import pandas as pd
import pyarrow as pa
import os
import io as io_module
from pathlib import Path
import json
from typing import Optional, cast, List, Literal, Dict, Tuple, Any, Set, Type, Union
from tqdm import tqdm
import re
from copy import deepcopy
from dateutil import parser
from datetime import datetime
import numpy as np
import logging
from CoreUtilities.core_types import CoreDataType
from CoreUtilities.serialization import XSer
from CoreUtilities import find_files
from CoreUtilities import SignedFile
from CoreUtilities.strings import remove_illegal_characters
from CoreUtilities import generate_random_sequence
from .io import PolarsIO

# Optional sqlutilities import
try:
    from sqlutilities import read_sql, DatabaseConnection
    SQLUTILITIES_AVAILABLE = True
except ImportError:
    SQLUTILITIES_AVAILABLE = False
    read_sql = None
    DatabaseConnection = None

# BatchedCsvReader location varies by Polars version
csv_ret_type = Union[pl.DataFrame, pl.LazyFrame, Any]  # Any covers BatchedCsvReader

dt_options =  Literal["TEXT", "UUID", "TINYINT", "SMALLINT", "BIGINT", "INTEGER", "FLOAT", "DATE", "DATETIME", "TIME", "BOOLEAN", "JSON", "XML"]

class EnhancedPolars:
    """Drop-in replacement for polars with custom constructors."""

    def __getattr__(self, name):
        """Delegate all unknown attributes to the real polars module."""
        return getattr(pl, name)
    
    @staticmethod
    def cleanup(df: pl.DataFrame | pl.LazyFrame | pl.Series,
                optimize_types: bool = True,
                type_inference_confidence: float = 0.6,
                attempt_numeric_to_datetime: bool = False,
                clean_column_names: bool = True,
                desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase', 'capitalize', 'casefold', 'preserve'] = 'preserve') -> pl.DataFrame | pl.LazyFrame | pl.Series:

        # Track if input was LazyFrame to preserve type
        was_lazy = isinstance(df, pl.LazyFrame)

        if clean_column_names and not(isinstance(df, pl.Series)):
            df = df.rename({x: remove_illegal_characters(x, case=desired_column_name_case, preserve_decimals=True) for x in (df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema).names()})

        if optimize_types:
            df = EnhancedPolars.optimize_dtypes(df, confidence=type_inference_confidence, attempt_numeric_to_datetime=attempt_numeric_to_datetime)

        # Convert back to LazyFrame if input was LazyFrame
        if was_lazy and isinstance(df, pl.DataFrame):
            df = df.lazy()

        return df

    @staticmethod
    def _read_file_with_signature_check(
        fp: Path,
        verify: bool = True,
        decryption_key: Optional[bytes] = None,
        decryption_password: Optional[str] = None
    ) -> Tuple[Optional[bytes], Optional[Any], bool]:
        """
        Read file content, auto-detecting if it's signed.

        Returns:
            Tuple of (data_bytes, header, was_signed)
            - If signed/encrypted: (bytes, header_or_None, True)
            - If not signed: (None, None, False) - caller should use normal read path
        """
        is_signed = SignedFile.is_signed(fp)
        needs_decrypt = decryption_key is not None or decryption_password is not None

        if not is_signed and not needs_decrypt:
            return (None, None, False)

        try:
            result = SignedFile.read(
                path=fp,
                verify=verify,
                allow_unsigned=False,
                decryption_key=decryption_key,
                decryption_password=decryption_password,
                return_header=True
            )
            data, header = cast(Tuple[bytes, Any], result)
            return (data, header, True)
        except Exception:
            # If reading as signed fails, return None to trigger normal read
            return (None, None, False)

    @staticmethod
    def _read_parquet(fp: Path | str, mode: Literal['eager', 'lazy',] = 'lazy',
                 recursive: bool = True, hive_partitioning: bool = True, # recognize key=value/ folders
                 filter_parquet_only: bool = True,
                 glob: bool = True,
                 verify: bool = True,
                 decryption_key: Optional[bytes] = None,
                 decryption_password: Optional[str] = None,
                 **kwargs) -> Union[pl.DataFrame, pl.LazyFrame, Tuple[pl.DataFrame, Any]]:
        if isinstance(fp, str):
            fp = Path(fp)

        # For single files, check if it's a signed file
        if fp.is_file():
            data, header, was_signed = EnhancedPolars._read_file_with_signature_check(
                fp, verify=verify, decryption_key=decryption_key, decryption_password=decryption_password
            )
            if was_signed and data is not None:
                df = pl.read_parquet(io_module.BytesIO(data), **kwargs)
                return (df, header)

        if fp.is_dir():
            return pl.scan_parquet(((fp / '**' / '*.parquet') if recursive else (fp / '*.parquet')) if not filter_parquet_only else list(fp.glob("**/*.parquet" if recursive else "*.parquet")),
                                   hive_partitioning=hive_partitioning, glob=glob, **kwargs)
        elif mode == 'eager':
            return pl.read_parquet(fp, **kwargs)

        return pl.scan_parquet(fp, **kwargs)
    
    @staticmethod
    def read_parquet(fp: Path | str, mode: Literal['eager', 'lazy',] = 'lazy',
                     recursive: bool = True, hive_partitioning: bool = True, # recognize key=value/ folders
                     glob: bool = True,
                     filter_parquet_only: bool = True,
                     optimize_types: bool = True,
                     type_inference_confidence: float = 0.6,
                     clean_column_names: bool = True,
                     desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                       'capitalize', 'casefold', 'preserve'] = 'preserve',
                     attempt_numeric_to_datetime: bool = False,
                     verify: bool = True,
                     decryption_key: Optional[bytes] = None,
                     decryption_password: Optional[str] = None,
                     return_header: bool = False,
                     **kwargs) -> Union[pl.DataFrame, pl.LazyFrame, Tuple[pl.DataFrame, Any], Tuple[pl.LazyFrame, Any], pl.Series]:

        result = EnhancedPolars._read_parquet(fp, mode=mode, recursive=recursive, filter_parquet_only=filter_parquet_only,
                                              hive_partitioning=hive_partitioning, glob=glob,
                                              verify=verify,
                                              decryption_key=decryption_key, decryption_password=decryption_password,
                                              **kwargs)

        # _read_parquet returns tuple (df, header) for single files (signed or not), or LazyFrame for directories
        if isinstance(result, tuple):
            df, header = result
        else:
            df = result
            header = None
        df = cast(pl.DataFrame | pl.LazyFrame | pl.Series, EnhancedPolars.cleanup(df,
                                    optimize_types=optimize_types,
                                    type_inference_confidence=type_inference_confidence,
                                    clean_column_names=clean_column_names,
                                    attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                                    desired_column_name_case=desired_column_name_case))
        if return_header and isinstance(result, tuple):
            return cast(pl.DataFrame, df), header
        return df

    @staticmethod
    def _read_csv(fp: Path | str | List[Path | str],
                 mode: Literal['eager', 'lazy',] = 'lazy',
                 batch_size: Optional[int] = None,
                 recursive: bool = True,
                 filter_csv_only: bool = True,
                 verify: bool = True,
                 decryption_key: Optional[bytes] = None,
                 decryption_password: Optional[str] = None,
                 **kwargs) -> csv_ret_type: # type: ignore
        if isinstance(fp, str):
            fp = Path(fp)

        # For single files, check if it's a signed file
        if isinstance(fp, Path) and fp.is_file():
            data, header, was_signed = EnhancedPolars._read_file_with_signature_check(
                fp, verify=verify, decryption_key=decryption_key, decryption_password=decryption_password
            )
            if was_signed and data is not None:
                csv_content = data.decode('utf-8') if isinstance(data, bytes) else str(data)

                # Extract dtype info from signed file header (if signed via PolarsIO.to_csv)
                schema_override: Optional[Dict[str, Any]] = None
                if header and isinstance(header, dict):
                    dtypes_str = header.get('dtypes')
                    if dtypes_str:
                        try:
                            schema_override = json.loads(dtypes_str) if isinstance(dtypes_str, str) else dtypes_str
                        except (json.JSONDecodeError, ValueError):
                            pass

                df = pl.read_csv(io_module.StringIO(csv_content), comment_prefix='#', **kwargs)

                if schema_override:
                    try:
                        df = df.cast({col: PolarsIO._parse_dtype_string(dtype_str) for col, dtype_str in schema_override.items()})
                    except Exception:
                        pass

                # Return header without dtypes (just user header if present)
                user_header = header.get('header') if header and isinstance(header, dict) else None
                return (df, user_header)

        if isinstance(fp, Path):
            if fp.is_dir():
                return pl.scan_csv(fp if not filter_csv_only else list(fp.glob("**/*.csv" if recursive else "*.csv")), **kwargs)
            elif fp.is_file() and isinstance(kwargs.get('dtypes'), type(None)):
                with open(fp, 'r') as f:
                    first_line = f.readline()
                    if first_line.startswith("# dtypes:"):
                        kwargs['dtypes'] = json.loads(first_line[len("# dtypes:"):].strip())
                        kwargs['comment_char'] = "#"
                if mode == 'eager':
                    if isinstance(batch_size, int):
                        return pl.read_csv_batched(fp, batch_size=batch_size, **kwargs)
                    return pl.read_csv(fp, **kwargs)
        return pl.scan_csv(cast(List[str] | List[Path], fp), **kwargs)

    @staticmethod
    def read_csv(fp: Path | str | List[Path | str],
                 mode: Literal['eager', 'lazy',] = 'lazy',
                 batch_size: Optional[int] = None,
                 recursive: bool = True,
                 filter_csv_only: bool = True,
                 optimize_types: bool = True,
                 type_inference_confidence: float = 0.6,
                 clean_column_names: bool = True,
                 desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                   'capitalize', 'casefold', 'preserve'] = 'preserve',
                 attempt_numeric_to_datetime: bool = False,
                 verify: bool = True,
                 decryption_key: Optional[bytes] = None,
                 decryption_password: Optional[str] = None,
                 return_header: bool = False,
                 **kwargs):

        result = EnhancedPolars._read_csv(fp, mode=mode, batch_size=batch_size, recursive=recursive,
                                          filter_csv_only=filter_csv_only,
                                          verify=verify,
                                          decryption_key=decryption_key, decryption_password=decryption_password,
                                          **kwargs)

        # _read_csv returns tuple (df, header) for single files (signed or not), or LazyFrame for directories
        if isinstance(result, tuple):
            df, header = result
        else:
            df = result
            header = None
        df = cast(pl.DataFrame | pl.LazyFrame | pl.Series, EnhancedPolars.cleanup(df,
                                    optimize_types=optimize_types,
                                    type_inference_confidence=type_inference_confidence,
                                    clean_column_names=clean_column_names,
                                    attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                                    desired_column_name_case=desired_column_name_case))
        if return_header and isinstance(result, tuple):
            return cast(pl.DataFrame, df), header
        return df

    @staticmethod
    def _read_ipc(fp: Path | str, mode: Literal['eager', 'lazy', 'stream'] = 'lazy',
                  recursive: bool = True,
                  filter_ipc_only: bool = True,
                  verify: bool = True,
                  decryption_key: Optional[bytes] = None,
                  decryption_password: Optional[str] = None,
                  **kwargs) -> Union[pl.DataFrame, pl.LazyFrame, Tuple[pl.DataFrame, Any]]:
        if isinstance(fp, str):
            fp = Path(fp)

        # For single files, check if it's a signed file
        if fp.is_file():
            data, header, was_signed = EnhancedPolars._read_file_with_signature_check(
                fp, verify=verify, decryption_key=decryption_key, decryption_password=decryption_password
            )
            if was_signed and data is not None:
                df = pl.read_ipc(io_module.BytesIO(data), **kwargs)
                return (df, header)

        if fp.is_dir():
            return pl.scan_ipc(fp if not filter_ipc_only else list(fp.glob("**/*.ipc" if recursive else "*.ipc")), **kwargs)
        elif mode == 'stream':
            return pl.read_ipc_stream(fp, **kwargs)
        elif mode == 'eager':
            return pl.read_ipc(fp, **kwargs)
        return pl.scan_ipc(fp, **kwargs)

    @staticmethod
    def read_ipc(fp: Path | str, mode: Literal['eager', 'lazy', 'stream'] = 'lazy',
                 recursive: bool = True,
                 filter_ipc_only: bool = True,
                 optimize_types: bool = True,
                 type_inference_confidence: float = 0.6,
                 clean_column_names: bool = True,
                 desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                   'capitalize', 'casefold', 'preserve'] = 'preserve',
                 attempt_numeric_to_datetime: bool = False,
                 verify: bool = True,
                 decryption_key: Optional[bytes] = None,
                 decryption_password: Optional[str] = None,
                 return_header: bool = False,
                 **kwargs):

        result = EnhancedPolars._read_ipc(fp, mode=mode, recursive=recursive, filter_ipc_only=filter_ipc_only,
                                          verify=verify,
                                          decryption_key=decryption_key, decryption_password=decryption_password,
                                          **kwargs)

        # _read_ipc returns tuple (df, header) for single files (signed or not), or LazyFrame for directories
        if isinstance(result, tuple):
            df, header = result
        else:
            df = result
            header = None
        df = cast(pl.DataFrame | pl.LazyFrame | pl.Series, EnhancedPolars.cleanup(df,
                                    optimize_types=optimize_types,
                                    type_inference_confidence=type_inference_confidence,
                                    clean_column_names=clean_column_names,
                                    attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                                    desired_column_name_case=desired_column_name_case))
        if return_header and isinstance(result, tuple):
            return cast(pl.DataFrame, df), header
        return df

    @staticmethod
    def _read_delta(fp: Path | str, mode: Literal['eager', 'lazy'] = 'lazy',
                   recursive: bool = True, filter_delta_only: bool = True, **kwargs) -> pl.DataFrame | pl.LazyFrame:
        if isinstance(fp, str):
            fp = Path(fp)
        if fp.is_dir():
            return pl.scan_delta(fp if not filter_delta_only else list(fp.glob("**/*.delta" if recursive else "*.delta")), **kwargs)
        elif mode == 'eager':
            return pl.read_delta(fp, **kwargs)
        return pl.scan_delta(fp, **kwargs)

    @staticmethod
    def read_delta(fp: Path | str, mode: Literal['eager', 'lazy'] = 'lazy',
                  recursive: bool = True,
                  filter_delta_only: bool = True,
                  optimize_types: bool = True,
                  type_inference_confidence: float = 0.6,
                  clean_column_names: bool = True,
                  desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                        'capitalize', 'casefold', 'preserve'] = 'preserve',
                  attempt_numeric_to_datetime: bool = False,
                  **kwargs):
        return EnhancedPolars.cleanup(EnhancedPolars._read_delta(fp, mode=mode, recursive=recursive, filter_delta_only=filter_delta_only, **kwargs),
                                       optimize_types=optimize_types,
                                       type_inference_confidence=type_inference_confidence,
                                       clean_column_names=clean_column_names,
                                       desired_column_name_case=desired_column_name_case,
                                       attempt_numeric_to_datetime=attempt_numeric_to_datetime)

    @staticmethod
    def _read_ndjson(fp: Path | str, mode: Literal['eager', 'lazy'] = 'lazy',
                     recursive: bool = True,
                     filter_ndjson_only: bool = True,
                     **kwargs) -> pl.DataFrame | pl.LazyFrame:
        if isinstance(fp, str):
            fp = Path(fp)
        if fp.is_dir():
            return pl.scan_ndjson(fp if not filter_ndjson_only else list(fp.glob("**/*.ndjson" if recursive else "*.ndjson")), **kwargs)
        elif mode == 'eager':
            return pl.read_ndjson(fp, **kwargs)
        return pl.scan_ndjson(fp, **kwargs)
    
    @staticmethod
    def read_ndjson(fp: Path | str, mode: Literal['eager', 'lazy'] = 'lazy',
                   recursive: bool = True,
                   filter_ndjson_only: bool = True,
                   optimize_types: bool = True,
                   type_inference_confidence: float = 0.6,
                   clean_column_names: bool = True,
                   desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                         'capitalize', 'casefold', 'preserve'] = 'preserve',
                   attempt_numeric_to_datetime: bool = False,
                   **kwargs):
        return EnhancedPolars.cleanup(EnhancedPolars._read_ndjson(fp, mode=mode, recursive=recursive, filter_ndjson_only=filter_ndjson_only, **kwargs),
                                       optimize_types=optimize_types,
                                       type_inference_confidence=type_inference_confidence,
                                       clean_column_names=clean_column_names,
                                       desired_column_name_case=desired_column_name_case,
                                       attempt_numeric_to_datetime=attempt_numeric_to_datetime)

    @staticmethod
    def _from_data(df: pl.DataFrame | pl.LazyFrame | pd.DataFrame | pa.Table | np.ndarray | dict | list | str, **kwargs) -> pl.DataFrame | pl.Series:
        if isinstance(df, (pl.DataFrame, pl.LazyFrame)):
            return df # type: ignore
        elif isinstance(df, pd.DataFrame):
            return pl.from_pandas(df, **kwargs)
        elif isinstance(df, pa.Table):
            return pl.from_arrow(df, **kwargs)
        elif isinstance(df, np.ndarray):
            return pl.from_numpy(df, **kwargs)
        elif isinstance(df, dict):
            return pl.from_dict(df, **kwargs)
        elif isinstance(df, list):
            return pl.from_records(df, **kwargs)
        elif isinstance(df, str):
            return pl.from_repr(cast(str, df), **kwargs)
        try:
            import dask.dataframe as dd # type: ignore[import]
            if isinstance(df, dd.DataFrame):
                return pl.from_pandas(df.compute(), **kwargs)
        except ImportError:
            pass
        raise TypeError(f"Unsupported data type: {type(df)}")
    

    @staticmethod
    def from_data(df: pl.DataFrame | pl.LazyFrame | pd.DataFrame | pa.Table | np.ndarray | dict | list | str,
                 optimize_types: bool = True,
                   type_inference_confidence: float = 0.6,
                   clean_column_names: bool = True,
                   desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                         'capitalize', 'casefold', 'preserve'] = 'preserve',
                   attempt_numeric_to_datetime: bool = False,
                   **kwargs) -> pl.DataFrame | pl.Series:
        return cast(pl.DataFrame | pl.Series, EnhancedPolars.cleanup(EnhancedPolars._from_data(df, **kwargs),
                                       optimize_types=optimize_types,
                                       type_inference_confidence=type_inference_confidence,
                                       clean_column_names=clean_column_names,
                                       desired_column_name_case=desired_column_name_case,
                                       attempt_numeric_to_datetime=attempt_numeric_to_datetime))

    @staticmethod
    def bit_width(dtp) -> int | None:
        if dtp.is_numeric() and (result := re.search(r"(\d+)$", str(dtp))) is not None:
            return int(result.group(0))
    
    @staticmethod
    def get_dtype_meta(dt: pl.DataType) -> Dict[str, Any]:
        info = {"polars_type": str(dt), "bit_width": None, "signed": None,
                "precision": None, "scale": None, "unit": None, "timezone": None,
                "value_type": None, "key_type": None, "fields": None, 'core_data_type': None,
                'dtype': str(dt)}

        if dt.is_numeric():
            info['bit_width'] = EnhancedPolars.bit_width(dt)
            info['signed'] = dt.is_signed_integer()
            info['core_data_type'] = CoreDataType.INTEGER if dt.is_integer() else CoreDataType.FLOAT if dt.is_float() else CoreDataType.DECIMAL if dt.is_decimal() else CoreDataType.NUMERIC
            info['precision'] = "SINGLE" if dt == pl.Float32 else "DOUBLE" if dt == pl.Float64 else dt.precision if hasattr(dt, 'precision') else None # type: ignore
            info["scale"] = dt.scale if hasattr(dt, 'scale') else None # type: ignore
     
        # Boolean type
        elif dt == pl.Boolean:
            info["bit_width"] = 1
            info["core_data_type"] = CoreDataType.BOOLEAN

        # String types
        elif dt == pl.String:
            info["core_data_type"] = CoreDataType.STRING
        elif hasattr(pl, 'Utf8') and dt == pl.Utf8:
            # Utf8 is an alias for String in newer Polars versions
            info["core_data_type"] = CoreDataType.STRING
        elif dt == pl.Categorical:
            info["core_data_type"] = CoreDataType.CATEGORICAL
        elif hasattr(pl, 'Enum') and dt == pl.Enum:
            info["core_data_type"] = CoreDataType.CATEGORICAL
            if hasattr(dt, 'categories'):
                info["categories"] = dt.categories # type: ignore

        # Binary type
        elif dt == pl.Binary:
            info["core_data_type"] = CoreDataType.BYTES

     

        # Temporal types
        elif dt == pl.Date:
            info["bit_width"] = 32
            info["core_data_type"] = CoreDataType.DATE
        elif dt == pl.Time:
            info["core_data_type"] = CoreDataType.TIME
        elif str(dt).startswith('Datetime') or dt == pl.Datetime:
            info["unit"] = dt.time_unit if hasattr(dt, 'time_unit') else None # type: ignore
            info["timezone"] = dt.time_zone if hasattr(dt, 'time_zone') else None # type: ignore
            info["core_data_type"] = CoreDataType.DATETIME
        elif str(dt).startswith('Duration') or dt == pl.Duration:
            info["unit"] = dt.time_unit if hasattr(dt, 'time_unit') else None # type: ignore
            info["core_data_type"] = CoreDataType.TIMEDELTA

        # Container types
        elif str(dt).startswith('List') or dt == pl.List:
            info["value_type"] = get_dtype_meta(dt.inner) if hasattr(dt, 'inner') else None # type: ignore
            info["core_data_type"] = CoreDataType.LIST
        elif str(dt).startswith('Array') or dt == pl.Array:
            info["value_type"] = get_dtype_meta(dt.inner) if hasattr(dt, 'inner') else None # type: ignore
            info["array_width"] = dt.width if hasattr(dt, 'width') else None # type: ignore
            info["core_data_type"] = CoreDataType.ARRAY
        elif str(dt).startswith('Struct') or dt == pl.Struct:
            info["fields"] = {field.name: get_dtype_meta(field.dtype) for field in dt.fields} if hasattr(dt, 'fields') else None # type: ignore
            info["core_data_type"] = CoreDataType.OBJECT

        # Null type
        elif dt == pl.Null:
            info["core_data_type"] = CoreDataType.NONE_TYPE

        # Object type (fallback)
        elif hasattr(pl, 'Object') and dt == pl.Object:
            info["core_data_type"] = CoreDataType.OBJECT
        
        # Unknown type - special Polars type for undetermined types
        elif hasattr(pl, 'Unknown') and dt == pl.Unknown:
            info["core_data_type"] = CoreDataType.ANY
        
        # Check for UUID as string representation
        # UUID might be stored as String or Binary in Polars
        elif str(dt).lower() == 'uuid':
            info["core_data_type"] = CoreDataType.UUID
            info["bit_width"] = 128  # UUID is 128 bits
        
        # Unknown type
        else:
            info["core_data_type"] = CoreDataType.OBJECT

        return info

    @staticmethod
    def get_meta_for_dataframe(df: pl.DataFrame) -> Dict[str, Any]:
        """
        Extract metadata for a Polars DataFrame.
        """
        return {
            "num_rows": df.height,
            "num_columns": df.width,
            "schema": EnhancedPolars.get_schema_meta(df.schema),
            "columns": {name: EnhancedPolars.get_dtype_meta(dtype) for name, dtype in df.schema.items()}
        }

    @staticmethod
    def get_schema_meta(schema: Dict[str, pl.DataType]) -> Dict[str, Any]:
        """
        Extract metadata for a Polars schema.
        """
        return {
            "names": list(schema.keys()),
            "types": [EnhancedPolars.get_dtype_meta(dtype) for dtype in schema.values()],
        }


    @staticmethod
    def _is_float_helper(dtype: pl.DataType) -> bool:
        """
        Helper function to check if dtype is a float type.
        """
        return (dtype in (pl.Float32, pl.Float64)) or dtype.is_float()

    @staticmethod
    def _is_integer_helper(dtype: pl.DataType) -> bool:
        """
        Helper function to check if dtype is an integer type.
        """
        int_types = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]
        # Add Int128 if available
        if hasattr(pl, 'Int128'):
            int_types.append(pl.Int128)
        return (dtype in int_types) or dtype.is_integer()

    @staticmethod
    def _is_temporal_helper(dtype: pl.DataType) -> bool:
        """
        Helper function to check if dtype is a temporal type.
        """
        return (dtype in (pl.Date, pl.Time, pl.Datetime, pl.Duration)) or dtype.is_temporal()

    @staticmethod
    def _is_string_helper(dtype: pl.DataType) -> bool:
        """
        Helper function to check if dtype is a string type.
        """
        string_types = [pl.String, pl.Categorical, pl.Enum]
        # Add Utf8 if available (alias for String)
        if hasattr(pl, 'Utf8'):
            string_types.append(pl.Utf8)
        return dtype in string_types

    @staticmethod
    def _is_special_type_helper(dtype: pl.DataType) -> bool:
        """
        Helper function to check if dtype is a special/complex/container type.
        """
        # Container/complex types
        if (str(dtype).startswith('List') or 
            str(dtype).startswith('Array') or 
            str(dtype).startswith('Struct')):
            return True
        
        # Unknown types
        special_types = []
        if hasattr(pl, 'Unknown'):
            special_types.append(pl.Unknown)
        
        # Check for UUID in string representation
        if str(dtype).lower() == 'uuid' or 'uuid' in str(dtype).lower():
            return True
        
        return dtype in special_types if special_types else False

    @staticmethod
    def infer_numeric_temporal_scale(series: pl.Series, target_type: str = "datetime") -> Literal["d", "s", "ms", "us", "ns"]:
        """
        Infer the time scale/unit of numeric values based on their magnitude.
        
        Args:
            series: Numeric series to analyze
            target_type: Type of temporal data ("datetime", "date", "time", "duration")
            
        Returns:
            Inferred time unit: "d", "s", "ms", "us", or "ns"
        """
        max_val: float | int = cast(float | int, series.max())
        
        if max_val is None:
            return "us"  # Default to microseconds
        
        # Cast to float for comparison to avoid type errors
        max_val_float = float(max_val)
        
        if target_type == "date":
            # Date-specific thresholds
            if max_val_float < 100_000:  # Likely days since epoch
                return "d"
            elif max_val_float < 10_000_000_000:  # Likely seconds
                return "s"
            elif max_val_float < 10_000_000_000_000:  # Likely milliseconds
                return "ms"
            else:  # Likely microseconds or nanoseconds
                return "us"
                
        elif target_type == "datetime":
            # Datetime-specific thresholds
            if max_val_float < 10_000_000_000:  # Likely seconds
                return "s"
            elif max_val_float < 10_000_000_000_000:  # Likely milliseconds
                return "ms"
            elif max_val_float < 10_000_000_000_000_000:  # Likely microseconds
                return "us"
            else:  # Likely nanoseconds
                return "ns"
                
        elif target_type == "time":
            # Time-specific thresholds (values within a day)
            if max_val_float <= 86_400:  # Seconds in a day
                return "s"
            elif max_val_float <= 86_400_000:  # Milliseconds in a day
                return "ms"
            elif max_val_float <= 86_400_000_000:  # Microseconds in a day
                return "us"
            else:  # Nanoseconds in a day
                return "ns"
                
        elif target_type == "duration":
            # Duration-specific thresholds (context-dependent)
            if max_val_float < 1_000:  # Small values, likely seconds
                return "s"
            elif max_val_float < 1_000_000:  # Likely milliseconds
                return "ms"
            elif max_val_float < 1_000_000_000:  # Likely microseconds
                return "us"
            else:  # Likely nanoseconds
                return "ns"
        
        return "us"  # Default fallback

    @staticmethod
    def convert_numeric_to_temporal(series: pl.Series, target_dtype: pl.DataType, inferred_scale: Literal["d", "s", "ms", "us", "ns"] | None = None) -> pl.Series:
        """
        Convert numeric series to temporal type with proper scale handling.
        
        Args:
            series: Numeric series to convert
            target_dtype: Target temporal data type
            inferred_scale: Optional pre-inferred scale, otherwise will be inferred
            
        Returns:
            Converted series with temporal type
        """
        if target_dtype == pl.Datetime or str(target_dtype).startswith('Datetime'):
            scale = inferred_scale or EnhancedPolars.infer_numeric_temporal_scale(series, "datetime")
            # Type assertion for literal type
            scale = cast(Literal["d", "s", "ms", "us", "ns"], scale)
            target_time_unit = target_dtype.time_unit if hasattr(target_dtype, 'time_unit') else 'us' # type: ignore
            time_zone = target_dtype.time_zone if hasattr(target_dtype, 'time_zone') else None # type: ignore
            
            # Convert using inferred scale
            result = pl.from_epoch(series, time_unit=scale)
            
            # Convert to target time unit if different
            if scale != target_time_unit:
                result = result.dt.cast_time_unit(target_time_unit)
            
            # Add timezone if specified
            if time_zone:
                result = result.dt.replace_time_zone(time_zone)
                
            return result
            
        elif target_dtype == pl.Date or str(target_dtype).startswith('Date'):
            scale = inferred_scale or EnhancedPolars.infer_numeric_temporal_scale(series, "date")
            # Type assertion for literal type
            scale = cast(Literal["d", "s", "ms", "us", "ns"], scale)
            return pl.from_epoch(series, time_unit=scale).cast(pl.Date)
            
        elif target_dtype == pl.Time or str(target_dtype).startswith('Time'):
            # Time type in Polars ALWAYS expects nanoseconds since midnight
            # Need to convert input to nanoseconds before casting
            scale = inferred_scale or EnhancedPolars.infer_numeric_temporal_scale(series, "time")
            
            # Convert to nanoseconds since midnight
            if scale == "s":
                # Seconds to nanoseconds
                ns_series = series * 1_000_000_000
            elif scale == "ms":
                # Milliseconds to nanoseconds
                ns_series = series * 1_000_000
            elif scale == "us":
                # Microseconds to nanoseconds
                ns_series = series * 1_000
            elif scale == "ns":
                # Already in nanoseconds
                ns_series = series
            else:  # "d" shouldn't happen for time, but handle it
                # Days don't make sense for time, but handle gracefully
                ns_series = series
            
            return ns_series.cast(target_dtype)
            
        elif target_dtype == pl.Duration or str(target_dtype).startswith('Duration'):
            # Duration conversion - much simpler approach
            try:
                # Try direct cast first
                return series.cast(target_dtype)
            except:
                # If that fails, infer the scale
                scale = inferred_scale or EnhancedPolars.infer_numeric_temporal_scale(series, "duration")
                target_time_unit = target_dtype.time_unit if hasattr(target_dtype, 'time_unit') else 'us' # type: ignore
                
                # Convert to target unit scale
                conversion_factors = {
                    ("s", "ns"): 1_000_000_000,
                    ("s", "us"): 1_000_000,
                    ("s", "ms"): 1_000,
                    ("ms", "ns"): 1_000_000,
                    ("ms", "us"): 1_000,
                    ("us", "ns"): 1_000,
                    ("ns", "us"): 0.001,
                    ("ns", "ms"): 0.000001,
                    ("us", "ms"): 0.001,
                    ("ms", "s"): 0.001,
                    ("us", "s"): 0.000001,
                    ("ns", "s"): 0.000000001,
                }
                
                # Apply conversion if needed
                if scale != target_time_unit and (scale, target_time_unit) in conversion_factors:
                    factor = conversion_factors[(scale, target_time_unit)]
                    series = series * factor
                
                # Cast to duration
                return series.cast(target_dtype)
        
        else:
            # Fallback to direct cast
            return series.cast(target_dtype)

    @staticmethod
    def merge_polars_dtypes(*dtypes: pl.DataType) -> pl.DataType:
        """
        Determine the smallest compatible dtype from a sequence of Polars data types.
        
        Compatible upgrades:
        - Int8/Int16/Int32 -> Int64
        - Int8/Int16/Int32/Int64 -> Float32/Float64
        - Float32 -> Float64  
        - Categorical -> String
        
        Args:
            *dtypes: Variable number of Polars DataType objects
            
        Returns:
            The smallest Polars DataType that can accommodate all input types
            
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
            result = EnhancedPolars._merge_two_polars_dtypes(result, dtype)
        
        return result

    @staticmethod
    def _merge_two_polars_dtypes(old_type: pl.DataType, new_type: pl.DataType) -> pl.DataType:
        """
        Helper function to merge two Polars data types.
        """
        # Same type - no upgrade needed
        if old_type == new_type:
            return old_type
            
        # Handle special types
        if EnhancedPolars._is_special_type_helper(old_type) or EnhancedPolars._is_special_type_helper(new_type):
            # If one is Unknown, use the other
            if hasattr(pl, 'Unknown'):
                if old_type == pl.Unknown:
                    return new_type
                elif new_type == pl.Unknown:
                    return old_type
            # If both are special, prefer the first one
            return old_type
        
        # Handle UUID types - treat as String for compatibility
        if 'uuid' in str(old_type).lower() or 'uuid' in str(new_type).lower():
            # If one is UUID and other is string, use string
            if EnhancedPolars._is_string_helper(old_type) or EnhancedPolars._is_string_helper(new_type):
                return pl.String()
            # If both are UUID, keep as is
            return old_type
        
        # Integer to larger integer
        if EnhancedPolars._is_integer_helper(old_type) and EnhancedPolars._is_integer_helper(new_type):
            old_meta = EnhancedPolars.get_dtype_meta(old_type)
            new_meta = EnhancedPolars.get_dtype_meta(new_type)
            old_bits = old_meta["bit_width"]
            new_bits = new_meta["bit_width"]
            old_signed = old_meta["signed"]
            new_signed = new_meta["signed"]

            if old_signed == new_signed:
                return new_type if new_bits >= old_bits else old_type
            elif old_signed:
                # old is signed, new is unsigned
                if old_bits >= new_bits:
                    return old_type
                else:
                    return getattr(pl, f'Int{new_bits * 2}', pl.Int64)() if new_bits * 2 <= 128 else pl.Int128()
            else:
                # old is unsigned, new is signed
                if new_bits > old_bits:
                    return new_type
                else:
                    return getattr(pl, f'Int{old_bits * 2}', pl.Int64)() if old_bits * 2 <= 128 else pl.Int128()

        # Integer to float
        if EnhancedPolars._is_integer_helper(old_type) and EnhancedPolars._is_float_helper(new_type):
            return new_type
        elif EnhancedPolars._is_float_helper(old_type) and EnhancedPolars._is_integer_helper(new_type):
            return old_type
            
        # Float to larger float
        if EnhancedPolars._is_float_helper(old_type) and EnhancedPolars._is_float_helper(new_type):
            old_meta = EnhancedPolars.get_dtype_meta(old_type)
            new_meta = EnhancedPolars.get_dtype_meta(new_type)
            old_bits = old_meta["bit_width"]
            new_bits = new_meta["bit_width"]
            return new_type if new_bits >= old_bits else old_type
        
        # Categorical/Enum to String (including Utf8)
        string_types = [pl.String]
        if hasattr(pl, 'Utf8'):
            string_types.append(pl.Utf8)
        
        if old_type in (pl.Categorical, pl.Enum) and new_type in string_types:
            return old_type
        elif old_type in string_types and new_type in (pl.Categorical, pl.Enum):
            return new_type
        
        # Handle Utf8 and String compatibility (they're essentially the same)
        if hasattr(pl, 'Utf8'):
            if (hasattr(pl, 'Utf8') and old_type == pl.Utf8) and new_type == pl.String:
                return new_type  # Prefer String over Utf8
            elif old_type == pl.String and (hasattr(pl, 'Utf8') and new_type == pl.Utf8):
                return old_type  # Prefer String over Utf8
        
        # Datetime precision compatibility
        if (old_type == pl.Datetime or str(old_type).startswith('Datetime')) and (new_type == pl.Datetime or str(new_type).startswith('Datetime')):
            # Both are datetime types, merge to the LOWER precision (minimum safe dtype)
            old_unit = getattr(old_type, 'time_unit', 'us')
            new_unit = getattr(new_type, 'time_unit', 'us')
            
            # Precision hierarchy: s < ms < us < ns (lower value = lower precision)
            unit_hierarchy = {'s': 0, 'ms': 1, 'us': 2, 'ns': 3}
            
            # Choose the lower precision (safer for both)
            if unit_hierarchy.get(old_unit, 2) <= unit_hierarchy.get(new_unit, 2):
                return old_type
            else:
                return new_type
        
        # Date/Time compatibility
        if (old_type == pl.Date or str(old_type).startswith('Date')) and (new_type == pl.Datetime or str(new_type).startswith('Datetime')):
            return old_type
        elif (old_type == pl.Datetime or str(old_type).startswith('Datetime')) and (new_type == pl.Date or str(new_type).startswith('Date')):
            return new_type

        # If we can't find a compatible upgrade, return the more general type
        if old_type == pl.Object or new_type == pl.Object:
            return pl.Object()
        
        # For truly incompatible types, fall back to String as the most general compatible type
        return pl.String()

    @staticmethod
    def convert_to_polars_dtype(data_series_or_frame: pl.Series | pl.DataFrame | pl.LazyFrame,
                            dtype: Any, **kwargs) -> pl.Series | pl.DataFrame:
        """
        Convert a Polars Series, DataFrame, or LazyFrame to specified data type(s) with intelligent conversion handling.
        
        This function provides comprehensive type conversion capabilities including string-to-temporal parsing,
        numeric-to-temporal conversion, temporal-to-numeric conversion, and direct type casting. It handles
        complex conversions that go beyond simple casting, such as parsing datetime strings with format
        detection and converting Unix timestamps to datetime objects.
        
        Parameters:
        -----------
        data_series_or_frame : pl.Series, pl.DataFrame, or pl.LazyFrame
            The Polars data structure to convert. LazyFrames are automatically collected to DataFrames
            before processing to enable column-wise operations.
            
        dtype : Any
            Target data type specification:
            - For Series: A single Polars DataType (e.g., pl.Int32, pl.Datetime, pl.String)
            - For DataFrame/LazyFrame: A dictionary mapping column names to target dtypes
            - If dict is not provided for DataFrame, the same dtype is applied to all columns
            - All dtypes are automatically parsed through parse_dtype() for consistency
            
        **kwargs : dict
            Additional keyword arguments passed to specific conversion functions:
            - For string-to-temporal: Arguments to str.to_date(), str.to_datetime(), str.to_time()
            - For temporal parsing: strict=False is used by default for robust parsing
            - For numeric-to-temporal: Custom arguments to temporal conversion functions
            
        Returns:
        --------
        pl.Series or pl.DataFrame
            Converted data structure with the specified data type(s):
            - Series input returns converted Series with target dtype
            - DataFrame/LazyFrame input returns DataFrame with converted columns
            - Original data structure if conversion is unnecessary (same dtype)
            - All conversions preserve data integrity where possible
            
        Raises:
        -------
        TypeError
            If input is not a Polars Series, DataFrame, or LazyFrame
            
        ValueError
            If specified column name is not found in DataFrame
            If string-to-duration conversion fails due to format incompatibility
            
        AssertionError
            If dtype for Series conversion is not a valid Polars DataType
            
        Examples:
        ---------
        >>> import polars as pl
        >>> 
        >>> # Convert Series from string to date
        >>> date_series = pl.Series(['2023-01-01', '2023-01-02', '2023-01-03'])
        >>> converted = convert_to_polars_dtype(date_series, pl.Date)
        >>> print(converted.dtype)  # Date
        >>> 
        >>> # Convert Series with datetime strings to datetime with timezone
        >>> dt_series = pl.Series(['2023-01-01 12:00:00', '2023-01-02 13:30:00'])
        >>> converted = convert_to_polars_dtype(dt_series, pl.Datetime(time_unit='ms', time_zone='UTC'))
        >>> 
        >>> # Convert numeric timestamps to datetime (auto-detects milliseconds)
        >>> timestamp_series = pl.Series([1640995200000, 1640995260000, 1640995320000])
        >>> converted = convert_to_polars_dtype(timestamp_series, pl.Datetime)
        >>> 
        >>> # Convert DataFrame with multiple column types
        >>> df = pl.DataFrame({
        ...     'dates': ['2023-01-01', '2023-01-02'],
        ...     'numbers': [1.0, 2.0],
        ...     'categories': ['A', 'B']
        ... })
        >>> converted_df = convert_to_polars_dtype(df, {
        ...     'dates': pl.Date,
        ...     'numbers': pl.Int32,
        ...     'categories': pl.Categorical
        ... })
        >>> 
        >>> # Apply same dtype to all columns in DataFrame
        >>> string_df = pl.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        >>> all_string = convert_to_polars_dtype(string_df, pl.String)
        >>> 
        >>> # Convert LazyFrame (automatically collected)
        >>> lazy_df = pl.LazyFrame({'values': [1.0, 2.0, 3.0]})
        >>> converted_df = convert_to_polars_dtype(lazy_df, pl.Int32)
        >>> print(type(converted_df))  # <class 'polars.DataFrame'>
        
        Conversion Capabilities:
        ------------------------
        1. **String-to-Temporal**: Intelligent parsing of date/datetime/time strings
        - Automatic format detection for common patterns
        - Timezone-aware datetime conversion
        - Robust parsing with strict=False by default
        
        2. **Numeric-to-Temporal**: Unix timestamp conversion with scale detection
        - Automatic unit inference (seconds, milliseconds, microseconds, nanoseconds)
        - Support for date, datetime, time, and duration target types
        - Preserves precision and timezone information
        
        3. **Temporal-to-Numeric**: Convert temporal types to numeric representations
        - Date to days since epoch
        - Datetime to microsecond timestamps
        - Time to microseconds since midnight
        - Duration to total microseconds
        
        4. **Direct Casting**: Standard type conversions for compatible types
        - Numeric type conversions (int ↔ float, upcasting/downcasting)
        - String/categorical conversions
        - Container type conversions (List, Struct)
        
        5. **Complex Type Handling**: Support for nested and special types
        - List and Array types with inner type specification
        - Struct types with field-level conversion
        - Categorical and Enum types
        
        Performance Notes:
        ------------------
        - Early return for same-type conversions (no processing overhead)
        - LazyFrame collection only when necessary
        - Column-wise processing for DataFrames (memory efficient)
        - Leverages native Polars conversion methods where possible
        - Automatic fallback to direct casting for unsupported conversions
        
        See Also:
        ---------
        parse_dtype : Parse and normalize dtype specifications
        convert_numeric_to_temporal : Specialized numeric-to-temporal conversion
        infer_numeric_temporal_scale : Infer temporal scale from numeric data
        merge_polars_dtypes : Merge multiple dtypes for compatibility
        """
        if isinstance(data_series_or_frame, pl.Series):
            dtype = EnhancedPolars.parse_dtype(dtype)
            assert isinstance(dtype, pl.DataType), "dtype must be a Polars DataType when converting a Series"
            curr_dtype: pl.DataType = data_series_or_frame.dtype

            # If types are the same, return as-is
            if curr_dtype == dtype:
                return data_series_or_frame
            
            # String to temporal conversions
            elif EnhancedPolars._is_string_helper(curr_dtype) and EnhancedPolars._is_temporal_helper(dtype):
                if dtype == pl.Date or str(dtype).startswith('Date'):
                    # Try to parse string as date
                    return data_series_or_frame.str.to_date(strict=False, **kwargs)
                elif dtype == pl.Datetime or str(dtype).startswith('Datetime'):
                    # Parse string as datetime
                    time_unit = dtype.time_unit if hasattr(dtype, 'time_unit') else 'us' # type: ignore
                    time_zone = dtype.time_zone if hasattr(dtype, 'time_zone') else None # type: ignore
                    return data_series_or_frame.str.to_datetime(
                        time_unit=time_unit,
                        time_zone=time_zone,
                        strict=False,
                        **kwargs
                    )
                elif dtype == pl.Time or str(dtype).startswith('Time'):
                    # Parse string as time
                    return data_series_or_frame.str.to_time(strict=False, **kwargs)
                elif dtype == pl.Duration or str(dtype).startswith('Duration'):
                    # For duration, we need to handle special parsing
                    time_unit = dtype.time_unit if hasattr(dtype, 'time_unit') else 'us' # type: ignore
                    # Try to cast directly, may need custom parsing logic
                    try:
                        return data_series_or_frame.cast(dtype)
                    except:
                        # If direct cast fails, try parsing as timedelta string
                        # This would need custom implementation based on string format
                        raise ValueError(f"Cannot convert string to duration type {dtype}")
            
            # Numeric to temporal conversions
            elif (EnhancedPolars._is_integer_helper(curr_dtype) or EnhancedPolars._is_float_helper(curr_dtype)) and EnhancedPolars._is_temporal_helper(dtype):
                # Use the new helper function for clean conversion
                return EnhancedPolars.convert_numeric_to_temporal(data_series_or_frame, dtype)
            
            # Temporal to numeric conversions
            elif EnhancedPolars._is_temporal_helper(curr_dtype) and (EnhancedPolars._is_integer_helper(dtype) or EnhancedPolars._is_float_helper(dtype)):
                if curr_dtype == pl.Date or str(curr_dtype).startswith('Date'):
                    # Convert date to numeric (days since epoch)
                    # Use dt.epoch for date to get days
                    return data_series_or_frame.dt.epoch(time_unit='d').cast(dtype)
                elif curr_dtype == pl.Datetime or str(curr_dtype).startswith('Datetime'):
                    # Convert datetime to numeric (timestamp)
                    return data_series_or_frame.dt.epoch(time_unit='us').cast(dtype)
                elif curr_dtype == pl.Time or str(curr_dtype).startswith('Time'):
                    # Convert time to numeric (microseconds since midnight)
                    microseconds = (
                        data_series_or_frame.dt.hour() * 3_600_000_000 +
                        data_series_or_frame.dt.minute() * 60_000_000 +
                        data_series_or_frame.dt.second() * 1_000_000 +
                        data_series_or_frame.dt.microsecond()
                    )
                    return microseconds.cast(dtype)
                elif curr_dtype == pl.Duration or str(curr_dtype).startswith('Duration'):
                    # Convert duration to numeric
                    return data_series_or_frame.dt.total_microseconds().cast(dtype)
            
            # Default case: try direct cast
            else:
                return data_series_or_frame.cast(dtype)
            
            # This should never be reached, but ensures all paths return
            return data_series_or_frame.cast(dtype)

        elif isinstance(data_series_or_frame, (pl.DataFrame, pl.LazyFrame)):
            if isinstance(data_series_or_frame, pl.LazyFrame):
                data_series_or_frame = data_series_or_frame.collect()

            if not isinstance(dtype, dict):
                dtype = {col: dtype for col, _ in data_series_or_frame.schema.items()}

            dtype = {col: EnhancedPolars.parse_dtype(dtype=dtype[col]) for col in dtype}

            # Start with the original dataframe
            result = data_series_or_frame
            
            # Convert each specified column
            for col_name, target_dtype in dtype.items():
                if col_name not in result.columns:
                    raise ValueError(f"Column '{col_name}' not found in DataFrame")
                
                # Convert the column using the Series conversion logic
                converted_series = EnhancedPolars.convert_to_polars_dtype(result[col_name], target_dtype)
                
                # Replace the column in the dataframe
                # Handle both Series and DataFrame returns from recursive call
                if isinstance(converted_series, pl.Series):
                    result = result.with_columns(converted_series.alias(col_name))
                else:
                    logging.warning(f"Expected a Series after conversion, got {type(converted_series)}")
                    # This shouldn't happen, but handle it gracefully
                    result = result.with_columns(converted_series[col_name].alias(col_name))
            
            return result
        
        else:
            raise TypeError("Input must be a Polars Series or DataFrame")
    
    @staticmethod
    def merge_schemas(*schemas, change_flag: bool = False) -> Dict[str, pl.DataType] | Tuple[Dict[str, pl.DataType], bool]:
        """
        Merge multiple Polars schemas into a single schema with compatible dtypes.
        
        Args:
            *schemas: Variable number of schema dictionaries (column name -> dtype)
            
        Returns:
            Merged schema dictionary with compatible dtypes
            
        Raises:
            ValueError: If no schemas provided
            TypeError: If schemas are not dictionaries
        """
        if not schemas:
            raise ValueError("At least one schema must be provided")
        
        merged_schema: Dict[str, pl.DataType] = {}
        changed: bool = False
        for i, schema in enumerate(schemas):
            if not isinstance(schema, dict):
                raise TypeError("Each schema must be a dictionary")
            
            for col, dtype in schema.items():
                dtype = EnhancedPolars.parse_dtype(dtype)
                
                if col in merged_schema:
                    # Merge the existing dtype with the new one
                    merged_schema[col] = EnhancedPolars.merge_polars_dtypes(merged_schema[col], dtype)
                    if merged_schema[col] != dtype:
                        changed = True
                else:
                    merged_schema[col] = dtype
                    if i > 0:
                        changed = True
        
        return (merged_schema, changed) if change_flag else merged_schema
    @staticmethod
    def concat_series_dataframe(*dataframe_or_series) -> pl.Series | pl.DataFrame:
        """
        Concatenate Polars Series or DataFrame objects with automatic dtype/schema merging.
        
        Handles safe type mismatches by finding the smallest compatible dtype that can
        accommodate all input types (e.g., int16 vs int32 -> int32).
        
        Args:
            *dataframe_or_series: Variable number of Series or DataFrame objects
            
        Returns:
            Concatenated Series or DataFrame with merged types
            
        Raises:
            ValueError: If no inputs provided
            TypeError: If mixing Series and DataFrames, or if types are incompatible
        """
        if not dataframe_or_series:
            raise ValueError("At least one Series or DataFrame must be provided")
        
        # If all inputs are Series, concatenate them with dtype merging
        if all(isinstance(df, pl.Series) for df in dataframe_or_series):
            # Find the merged dtype for all series
            merged_dtype = EnhancedPolars.merge_polars_dtypes(*[s.dtype for s in dataframe_or_series])
            
            # Cast all series to the merged dtype
            casted_series = []
            for series in dataframe_or_series:
                if series.dtype != merged_dtype:
                    # Use our convert function for complex conversions
                    casted = EnhancedPolars.convert_to_polars_dtype(series, merged_dtype)
                    casted_series.append(casted)
                else:
                    casted_series.append(series)
            
            # Now concatenate the casted series
            return pl.concat(casted_series)

        # If all inputs are DataFrames, concatenate them with schema merging
        if all(isinstance(df, (pl.DataFrame, pl.LazyFrame)) for df in dataframe_or_series):
            if len(dataframe_or_series) == 1:
                return dataframe_or_series[0]
            
            # Get all unique column names
            merged_schema: Dict[str, pl.DataType] = cast(Dict[str, pl.DataType],
                                                         EnhancedPolars.merge_schemas(*[df.schema for df in dataframe_or_series],
                                                                                 change_flag=False))

            # Align all dataframes to have the same columns and dtypes
            aligned_dfs = []
            for df in dataframe_or_series:
                # Start with the current dataframe
                aligned_df = df
                _len: int = cast(pl.LazyFrame, df.select(pl.count())).collect().item() if isinstance(df, pl.LazyFrame) else len(df)
                
                # Add missing columns with nulls
                for col in merged_schema.keys():
                    if col not in df.columns:
                        # Add column with nulls of the merged dtype
                        null_series = pl.Series(col, [None] * _len, dtype=merged_schema[col])
                        aligned_df = aligned_df.with_columns(null_series)
                
                # Cast existing columns to merged dtypes
                for col in df.columns:
                    if df.schema[col] != merged_schema[col]:
                        # Use our convert function for complex conversions
                        converted = EnhancedPolars.convert_to_polars_dtype((df.select(col).collect() if isinstance(df, pl.LazyFrame) else df)[col], merged_schema[col])
                        # converted is a Series, so we can use alias
                        if isinstance(converted, pl.Series):
                            aligned_df = aligned_df.with_columns(converted.alias(col))
                        else:
                            # This shouldn't happen since we're passing a Series to convert_to_polars_dtype
                            aligned_df = aligned_df.with_columns(converted[col].alias(col))
                
                # Ensure columns are in consistent order
                aligned_df = aligned_df.select(merged_schema.keys())
                aligned_dfs.append(aligned_df)
            
            # Now concatenate the aligned dataframes
            return pl.concat(aligned_dfs, how='vertical')

        # If we reach here, it means we have a mix of Series and DataFrames
        raise TypeError("Cannot concatenate mixed Polars Series and DataFrame objects")

    @staticmethod
    def optimize_dtypes(df_or_series: pl.DataFrame | pl.Series | pl.LazyFrame,
                        attempt_downcast: bool = True,
                        attempt_numeric_to_datetime: bool = False,
                        confidence: float = 1.0,
                        n: Optional[int] = None,
                        sample_strat: Literal['first', 'random'] = 'random',
                        seed: int = 42,
                        columns: Optional[List[str]]= None) -> pl.Series | pl.DataFrame:
        """
        Optimize data types for a Polars Series, DataFrame, or LazyFrame with comprehensive type inference.
        
        This function provides a simplified interface to the comprehensive type inference capabilities
        of `infer_dtype` and `infer_dtypes`, automatically returning the optimized data structure
        without metadata. It applies intelligent type optimization including temporal parsing,
        numeric downcasting, categorical detection, and precision optimization.
        
        Parameters:
        -----------
        df_or_series : pl.DataFrame, pl.Series, or pl.LazyFrame
            The Polars data structure to optimize. LazyFrames are automatically collected
            for processing and returned as DataFrames.
            
        attempt_downcast : bool, optional (default=True)
            If True, attempts to downcast numeric types to smaller, more efficient types
            (e.g., Int64 -> Int32, Float64 -> Float32) when values fit within the range.
            Provides memory optimization with no loss of data.
            
        attempt_numeric_to_datetime : bool, optional (default=False)
            If True, attempts to convert numeric values that appear to be timestamps
            (seconds, milliseconds, microseconds, nanoseconds) to datetime types.
            Uses intelligent magnitude-based detection for temporal units.
            
        confidence : float, optional (default=1.0)
            Confidence level for sampling (0.0 to 1.0). Lower values use smaller samples
            for faster inference at the cost of potential accuracy.
            - 1.0: Use entire dataset (slowest, most accurate)
            - 0.1-0.5: Good for large datasets with uniform distribution
            - 0.01-0.1: Very fast, suitable for quick previews
            
        n : int, optional (default=None)
            If specified, use exactly N samples for inference. Overrides confidence parameter.
            Useful when you want precise control over sample size for each column.
            
        sample_strat : {'first', 'random'}, optional (default='random')
            Sampling strategy when using less than the full dataset:
            - 'first': Use the first n samples from each column
            - 'random': Use random sampling with specified seed
            
        seed : int, optional (default=42)
            Random seed for reproducible sampling when sample_strat='random'.
            Ensures consistent results across multiple runs.
            
        columns : List[str], optional (default=None)
            List of specific column names to optimize. If None, all columns in the
            DataFrame/LazyFrame are processed. For Series input, this parameter is ignored.
            Useful for selective optimization of only certain columns in large datasets.
            
        Returns:
        --------
        pl.Series or pl.DataFrame
            Optimized data structure with inferred and converted types:
            - Series input returns optimized Series
            - DataFrame/LazyFrame input returns optimized DataFrame
            - All type conversions applied based on inference results
            - Memory-optimized with appropriate downcasting when safe
            
        Examples:
        ---------
        >>> import polars as pl
        >>> 
        >>> # Optimize a Series with string dates
        >>> dates_series = pl.Series(['2023-01-01', '2023-01-02', '2023-01-03'])
        >>> optimized_series = optimize_dtypes(dates_series)
        >>> print(optimized_series.dtype)  # pl.Date
        >>> 
        >>> # Optimize a DataFrame with mixed types
        >>> df = pl.DataFrame({
        ...     'dates': ['2023-01-01', '2023-01-02', '2023-01-03'],
        ...     'numbers': [1.0, 2.0, 3.0],  # Float64 that could be Int64
        ...     'categories': ['A', 'B', 'A'],
        ...     'timestamps': [1640995200000, 1640995260000, 1640995320000]  # milliseconds
        ... })
        >>> 
        >>> # Basic optimization with downcasting
        >>> optimized_df = optimize_dtypes(df)
        >>> 
        >>> # Full optimization including numeric-to-datetime conversion
        >>> fully_optimized = optimize_dtypes(
        ...     df, 
        ...     attempt_downcast=True,
        ...     attempt_numeric_to_datetime=True
        ... )
        >>> 
        >>> # Fast optimization on large DataFrame using 10% sample
        >>> large_df = pl.DataFrame({'col1': range(1000000), 'col2': ['text'] * 1000000})
        >>> optimized_fast = optimize_dtypes(large_df, confidence=0.1)
        >>> 
        >>> # Optimize LazyFrame (automatically collected)
        >>> lazy_df = pl.LazyFrame({'values': [1.0, 2.0, 3.0]})
        >>> optimized_df = optimize_dtypes(lazy_df)  # Returns DataFrame
        >>> 
        >>> # Selective optimization of specific columns only
        >>> mixed_df = pl.DataFrame({
        ...     'dates': ['2023-01-01', '2023-01-02'],
        ...     'numbers': [1.0, 2.0],
        ...     'text': ['hello', 'world'],
        ...     'categories': ['A', 'B']
        ... })
        >>> # Only optimize the 'dates' and 'numbers' columns
        >>> partial_optimized = optimize_dtypes(mixed_df, columns=['dates', 'numbers'])
        
        Performance Notes:
        ------------------
        - Automatically optimizes processing: only applies full inference to string/object columns
        - For known numeric/temporal types, uses fast paths unless attempt_downcast=True
        - Sampling is applied per-column, so large DataFrames benefit significantly
        - Memory efficient: processes one column at a time
        - LazyFrames are collected only for columns that need analysis
        - Returns immediately for already-optimal types when appropriate
        
        Type Optimization Strategy:
        ---------------------------
        1. **Fast Path**: For clearly typed columns, apply only downcasting if requested
        2. **String/Object Columns**: Apply full inference pipeline with temporal parsing
        3. **Categorical Detection**: Convert appropriate string columns to categorical
        4. **Numeric Downcasting**: Safely reduce memory usage with smaller integer/float types
        5. **Temporal Recognition**: Parse timestamps and datetime strings intelligently
        6. **Memory Optimization**: Choose most efficient representation for each data type
        
        See Also:
        ---------
        infer_dtype : Single-column type inference with detailed metadata
        infer_dtypes : Multi-column type inference with detailed metadata
        convert_to_polars_dtype : Direct type conversion with specific target types
        """
        if isinstance(df_or_series, pl.Series):
            return cast(Tuple[pl.Series, Dict[str, Any]], EnhancedPolars.infer_dtype(df_or_series, attempt_downcast=attempt_downcast,
                            attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                            confidence=confidence, n=n, sample_strat=sample_strat, seed=seed,
                            return_series=True))[0]

        return cast(Tuple[pl.DataFrame, Dict[str, Any]], EnhancedPolars.infer_dtypes(df_or_series, attempt_downcast=attempt_downcast,
                            attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                            confidence=confidence, n=n, sample_strat=sample_strat, seed=seed,
                            return_df=True, columns=columns))[0]

    @staticmethod
    def infer_dtypes(df: pl.DataFrame | pl.LazyFrame,
                    attempt_downcast: bool = True,
                    attempt_numeric_to_datetime: bool = False,
                    confidence: float = 1.0,
                    n: Optional[int] = None,
                    sample_strat: Literal['first', 'random'] = 'random',
                    seed: int = 42,
                    collect_precision_scale: bool = False,
                    return_df: bool = False,
                    columns: Optional[List] = None) -> Dict[str, Any] | Tuple[pl.DataFrame, Dict[str, Any]]:
        """
        Infer optimal data types for all columns in a Polars DataFrame with comprehensive analysis.
        
        This function applies intelligent type inference to every column in a DataFrame,
        with support for temporal parsing, numeric optimization, categorical detection,
        and precision/scale analysis. It can optionally return the converted DataFrame
        along with detailed metadata for each column.
        
        Parameters:
        -----------
        df : pl.DataFrame or pl.LazyFrame
            The Polars DataFrame or LazyFrame to analyze and optionally convert.
            
        attempt_downcast : bool, optional (default=True)
            If True, attempts to downcast numeric types to smaller, more efficient types
            for each column (e.g., Int64 -> Int32, Float64 -> Float32) when values fit.
            
        attempt_numeric_to_datetime : bool, optional (default=False)
            If True, attempts to convert numeric columns that appear to be timestamps
            (seconds, milliseconds, microseconds, nanoseconds) to datetime types.
            
        confidence : float, optional (default=1.0)
            Confidence level for sampling (0.0 to 1.0) applied to each column.
            Lower values use smaller samples for faster inference.
            - 1.0: Use entire series for each column (slowest, most accurate)
            - 0.1-0.5: Good for large datasets with uniform distribution
            - 0.01-0.1: Very fast, suitable for quick previews
            
        n : int, optional (default=None)
            If specified, use exactly N samples for inference on each column.
            Overrides confidence parameter.
            
        sample_strat : {'first', 'random'}, optional (default='random')
            Sampling strategy when using less than the full dataset:
            - 'first': Use the first n samples from each column
            - 'random': Use random sampling with specified seed
            
        seed : int, optional (default=42)
            Random seed for reproducible sampling when sample_strat='random'.
            
        collect_precision_scale : bool, optional (default=False)
            If True, calculates precision and scale for numeric columns, useful for
            database schema generation or decimal type optimization.
            
        return_df : bool, optional (default=False)
            If True, returns a tuple of (converted_dataframe, metadata_dict).
            If False, returns only the metadata dictionary.
            
        columns : List[str], optional (default=None)
            List of specific column names to analyze and optimize. If None, all columns
            in the DataFrame/LazyFrame are processed. Useful for selective analysis of
            only certain columns in large datasets to improve performance.
            
        Returns:
        --------
        Dict[str, Any] or Tuple[pl.DataFrame, Dict[str, Any]]
            If return_df=False: Dictionary mapping column names to their metadata including:
            - For each column: same structure as infer_dtype() return value
            - 'core_data_type': CoreDataType enum value
            - 'inferred_meta': Metadata for the inferred/converted type
            - 'n_levels': Number of unique values
            - 'min_value', 'max_value': For numeric/temporal columns
            - 'temporal_format', 'temporal_type': For string->datetime conversions
            - 'precision', 'scale': If collect_precision_scale=True
            - 'category_levels': List of categories if categorical
            
            If return_df=True: Tuple of (converted_dataframe, metadata_dict)
            
        Examples:
        ---------
        >>> import polars as pl
        >>> 
        >>> # Create a mixed-type DataFrame
        >>> df = pl.DataFrame({
        ...     'dates': ['2023-01-01', '2023-01-02', '2023-01-03'],
        ...     'numbers': [1.0, 2.0, 3.0],  # Float64 that could be Int64
        ...     'categories': ['A', 'B', 'A'],
        ...     'timestamps': [1640995200000, 1640995260000, 1640995320000]  # milliseconds
        ... })
        >>> 
        >>> # Basic type inference for all columns
        >>> metadata = infer_dtypes(df)
        >>> for col, meta in metadata.items():
        ...     print(f"{col}: {meta['inferred_meta']['core_data_type']}")
        >>> 
        >>> # Get converted DataFrame with all optimizations
        >>> converted_df, metadata = infer_dtypes(
        ...     df, 
        ...     attempt_downcast=True,
        ...     attempt_numeric_to_datetime=True,
        ...     return_df=True
        ... )
        >>> 
        >>> # Fast inference on large DataFrame using 10% sample
        >>> large_df = pl.DataFrame({'col1': range(1000000), 'col2': ['text'] * 1000000})
        >>> metadata = infer_dtypes(large_df, confidence=0.1)
        >>> 
        >>> # Precision and scale analysis for all numeric columns
        >>> df_decimal = pl.DataFrame({
        ...     'prices': [123.45, 67.890, 1.23],
        ...     'quantities': [100, 250, 75]
        ... })
        >>> metadata = infer_dtypes(df_decimal, collect_precision_scale=True)
        >>> for col, meta in metadata.items():
        ...     if 'precision' in meta:
        ...         print(f"{col}: Precision={meta['precision']}, Scale={meta['scale']}")
        >>> 
        >>> # Selective analysis of specific columns only
        >>> mixed_df = pl.DataFrame({
        ...     'dates': ['2023-01-01', '2023-01-02'],
        ...     'numbers': [1.0, 2.0],
        ...     'text': ['hello', 'world'],
        ...     'categories': ['A', 'B']
        ... })
        >>> # Only analyze the 'dates' and 'numbers' columns
        >>> selective_metadata = infer_dtypes(mixed_df, columns=['dates', 'numbers'])
        >>> print(list(selective_metadata.keys()))  # ['dates', 'numbers']
        
        Performance Notes:
        ------------------
        - Automatically optimizes processing: only applies full inference to string/object columns
        - For known numeric/temporal types, uses fast metadata extraction unless attempt_downcast=True
        - Sampling is applied per-column, so large DataFrames benefit significantly
        - LazyFrame inputs are automatically collected for the columns that need analysis
        - Early exits for columns that don't need complex inference
        - Memory efficient: processes one column at a time rather than loading all data
        
        Type Inference Strategy:
        ------------------------
        1. **Fast Path**: For clearly typed columns (numeric, boolean, etc.), extract metadata without inference
        2. **String/Object Columns**: Apply full inference pipeline with temporal parsing, numeric conversion
        3. **Categorical Detection**: Convert high-cardinality string columns to categorical
        4. **Numeric Optimization**: Downcast to smaller types when safe
        5. **Temporal Recognition**: Parse timestamps and datetime strings intelligently
        """
        if (return_df or collect_precision_scale or attempt_downcast or attempt_numeric_to_datetime):
            col_meta: Dict[str, Any] = {}
            cols: List[pl.Series] = []

            for name, dtype in (df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema).items():
                if columns is not None and name not in columns:
                    if return_df:
                        cols.append(df[name] if isinstance(df, pl.DataFrame) else df.select(name).collect()[name])
                    continue
                _tp = EnhancedPolars.infer_dtype(df[name] if isinstance(df, pl.DataFrame) else df.select(name).collect()[name],
                                            attempt_downcast=attempt_downcast, attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                                            confidence=confidence, n=n, sample_strat=sample_strat, seed=seed, collect_precision_scale=collect_precision_scale,
                                            return_series=return_df)
                if isinstance(_tp, tuple):
                    col_meta[name] = _tp[1]
                    cols.append(cast(pl.Series, _tp[0]))
                else:
                    col_meta[name] = _tp

            if return_df:
                return pl.DataFrame(cols), col_meta

            return col_meta
        
        else:
            col_meta: Dict[str, Any] = {}
            for col, dtype in df.schema.items():
                meta = EnhancedPolars.get_dtype_meta(dtype)

                if (meta['core_data_type'] not in [CoreDataType.OBJECT, CoreDataType.STRING]):
                    col_meta[col] = meta
                else:
                    col_meta[col] = EnhancedPolars.infer_dtype(df[col] if isinstance(df, pl.DataFrame) else df.select(col).collect()[col],
                                            attempt_downcast=attempt_downcast, attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                                            confidence=confidence, n=n, sample_strat=sample_strat, seed=seed, collect_precision_scale=collect_precision_scale,
                                            return_series=return_df)
                    
            return col_meta

    @staticmethod
    def get_temporal_string_format(series: pl.Series, max_samples: int = 100) -> Dict[str, Optional[str]]:
        """
        Get the temporal string format for a Polars Series.

        Args:
            series (pl.Series): The input Series.

        Returns:
            Tuple[Optional[str], Optional[str]]: The inferred temporal string format and its type, or (None, None) if not applicable.
        """
        #  Common datetime formats to try
        COMMON_FORMATS = {
                            # --- DATE ---
                            "%Y-%m-%d": "DATE",
                            "%Y/%m/%d": "DATE",
                            "%Y.%m.%d": "DATE",
                            "%Y%m%d": "DATE",
                            "%d-%m-%Y": "DATE",
                            "%d/%m/%Y": "DATE",
                            "%d.%m.%Y": "DATE",
                            "%d%m%Y": "DATE",
                            "%m-%d-%Y": "DATE",
                            "%m/%d/%Y": "DATE",
                            "%m.%d.%Y": "DATE",
                            "%m%d%Y": "DATE",
                            "%d-%m-%y": "DATE",
                            "%d/%m/%y": "DATE",
                            "%m-%d-%y": "DATE",
                            "%m/%d/%y": "DATE",
                            "%y-%m-%d": "DATE",
                            "%y/%m/%d": "DATE",
                            "%d %b %Y": "DATE",
                            "%d %B %Y": "DATE",
                            "%b %d, %Y": "DATE",
                            "%B %d, %Y": "DATE",

                            # --- TIME ---
                            "%H:%M": "TIME",
                            "%H:%M:%S": "TIME",
                            "%H:%M:%S.%f": "TIME",
                            "%I:%M %p": "TIME",
                            "%I:%M:%S %p": "TIME",

                            # --- DATETIME ---
                            "%Y-%m-%d %H:%M": "DATETIME",
                            "%Y-%m-%d %H:%M:%S": "DATETIME",
                            "%Y-%m-%d %H:%M:%S.%f": "DATETIME",
                            "%d/%m/%Y %H:%M": "DATETIME",
                            "%d/%m/%Y %H:%M:%S": "DATETIME",
                            "%m/%d/%Y %H:%M": "DATETIME",
                            "%m/%d/%Y %H:%M:%S": "DATETIME",
                            "%Y-%m-%d %I:%M %p": "DATETIME",
                            "%Y-%m-%d %I:%M:%S %p": "DATETIME",
                            "%m/%d/%Y %I:%M %p": "DATETIME",
                            "%m/%d/%Y %I:%M:%S %p": "DATETIME",
                            "%d/%m/%Y %I:%M %p": "DATETIME",
                            "%d/%m/%Y %I:%M:%S %p": "DATETIME",
                            "%Y-%m-%d %H:%M:%S%z": "DATETIME",
                            "%Y-%m-%d %H:%M:%S %z": "DATETIME",
                            "%Y-%m-%dT%H:%M:%S%z": "DATETIME",
                            "%Y-%m-%dT%H:%M:%S.%f%z": "DATETIME",
                            "%Y-%m-%dT%H:%M:%S": "DATETIME",
                            "%Y-%m-%dT%H:%M:%S.%f": "DATETIME",
                            "%d %b %Y %H:%M:%S": "DATETIME",
                            "%d %B %Y %H:%M:%S": "DATETIME",
                            "%b %d, %Y %H:%M:%S": "DATETIME",
                            "%B %d, %Y %H:%M:%S": "DATETIME",
                        }
        # Take up to 100 unique, non-null samples
        samples = (
            series.drop_nulls()
            .unique()
            .head(max_samples)
            .to_list()
        )
        
        if not samples:
            return {"temporal_format": None, "temporal_type": None}

        sample_formats: Set[str] = set()
        sample_types: Set[str] = set()
        for i, val in enumerate(samples):
            found_format = False
            for fmt, _tp in COMMON_FORMATS.items():
                    try:
                        datetime.strptime(val, fmt)  # raises if incompatible
                        sample_formats.add(fmt)
                        sample_types.add(_tp)
                        found_format = True
                        break  # Stop at the first matching format
                    except Exception:
                        continue
            if not found_format:
                try:
                    parser.parse(val)
                    return {'temporal_format': 'MIXED', 'temporal_type': "DATETIME"}
                except Exception:
                        continue
            
        if (len(sample_formats) == 1) and (len(sample_types) == 1):
            return {'temporal_format': sample_formats.pop(), 'temporal_type': sample_types.pop()}
        elif (len(sample_formats) > 1) or (len(sample_types) > 1):
            return {'temporal_format': '|'.join(sorted(sample_formats)), 'temporal_type': '|'.join(sorted(sample_types))}
        return {'temporal_format': None, 'temporal_type': None}

    @staticmethod
    def infer_dtype(series: pl.Series,
                    attempt_downcast: bool = True,
                    attempt_numeric_to_datetime: bool = False,
                    confidence: float = 1.0,
                    n: Optional[int] = None,
                    sample_strat: Literal['first', 'random'] = 'random',
                    seed: int = 42,
                    collect_precision_scale: bool = False,
                    cardinality_threshold: float = 0.5,
                    return_series: bool = False) -> Dict[str, Any] | Tuple[pl.Series, Dict[str, Any]]: # type: ignore
            """
            Infer the optimal data type for a Polars Series with comprehensive type detection and optimization.
            
            This function provides intelligent type inference with support for temporal parsing,
            numeric optimization, categorical detection, and precision/scale analysis. It includes
            sampling capabilities for performance on large datasets and can optionally return
            the converted series along with metadata.
            
            Parameters:
            -----------
            series : pl.Series
                The Polars Series to analyze and optionally convert.
                
            attempt_downcast : bool, optional (default=True)
                If True, attempts to downcast numeric types to smaller, more efficient types
                (e.g., Int64 -> Int32, Float64 -> Float32) when values fit within the range.
                
            attempt_numeric_to_datetime : bool, optional (default=False)
                If True, attempts to convert numeric values that appear to be timestamps
                (seconds, milliseconds, microseconds, nanoseconds) to datetime types.
                
            confidence : float, optional (default=1.0)
                Confidence level for sampling (0.0 to 1.0). Lower values use smaller samples
                for faster inference at the cost of potential accuracy.
                - 1.0: Use entire series (slowest, most accurate)
                - 0.1-0.5: Good for large datasets with uniform distribution
                - 0.01-0.1: Very fast, suitable for quick previews
                
            n : int, optional (default=None)
                If specified, use exactly N samples for inference. Overrides confidence parameter.
                Useful when you want precise control over sample size.
                
            sample_strat : {'first', 'random'}, optional (default='random')
                Sampling strategy when using less than the full dataset:
                - 'first': Use the first n samples
                - 'random': Use random sampling with specified seed
                
            seed : int, optional (default=42)
                Random seed for reproducible sampling when sample_strat='random'.
                
            collect_precision_scale : bool, optional (default=False)
                If True, calculates precision and scale for numeric types, useful for
                database schema generation or decimal type optimization.
                
            cardinality_threshold : float, optional (default=0.5)
                Threshold for categorical conversion. If unique values / total values
                is below this ratio, string columns are converted to categorical.
                
            return_series : bool, optional (default=False)
                If True, returns a tuple of (converted_series, metadata).
                If False, returns only the metadata dictionary.
                
            Returns:
            --------
            Dict[str, Any] or Tuple[pl.Series, Dict[str, Any]]
                If return_series=False: Dictionary containing type metadata including:
                - 'core_data_type': CoreDataType enum value
                - 'inferred_meta': Metadata for the inferred/converted type
                - 'n_levels': Number of unique values
                - 'min_value', 'max_value': For numeric/temporal types
                - 'temporal_format', 'temporal_type': For string->datetime conversions
                - 'precision', 'scale': If collect_precision_scale=True
                - 'category_levels': List of categories if categorical
                
                If return_series=True: Tuple of (converted_series, metadata_dict)
                
            Examples:
            ---------
            >>> import polars as pl
            >>> 
            >>> # Basic type inference
            >>> series = pl.Series(['2023-01-01', '2023-01-02', '2023-01-03'])
            >>> meta = infer_dtype(series)
            >>> print(meta['inferred_meta']['core_data_type'])  # CoreDataType.DATETIME
            >>> 
            >>> # Fast inference on large dataset using 10% sample
            >>> large_series = pl.Series(range(1000000))
            >>> meta = infer_dtype(large_series, confidence=0.1)
            >>> 
            >>> # Get converted series with downcasting
            >>> series = pl.Series([1.0, 2.0, 3.0])  # Float64
            >>> converted_series, meta = infer_dtype(series, attempt_downcast=True, return_series=True)
            >>> # converted_series is now Int64
            >>> 
            >>> # Numeric to datetime conversion
            >>> timestamp_series = pl.Series([1640995200000, 1640995260000])  # milliseconds
            >>> meta = infer_dtype(timestamp_series, attempt_numeric_to_datetime=True)
            >>> 
            >>> # Precision and scale analysis
            >>> decimal_series = pl.Series([123.45, 67.890, 1.23])
            >>> meta = infer_dtype(decimal_series, collect_precision_scale=True)
            >>> print(f"Precision: {meta['precision']}, Scale: {meta['scale']}")
            
            Performance Notes:
            ------------------
            - For series > 10,000 rows, confidence < 1.0 is recommended for string/object types
            - Numeric types often exit early without full scans due to optimization
            - String parsing benefits most from sampling
            - Temporal string parsing uses intelligent format detection with common patterns
            - Early exits for known types when attempt_downcast=False
            """
            # Initialize cache if needed
            # Early exit for known numeric types that don't need inference
            meta = EnhancedPolars.get_dtype_meta(series.dtype)

            if (meta['core_data_type'] not in [CoreDataType.OBJECT, CoreDataType.STRING]) and not (attempt_downcast):
                return (series, meta) if return_series else meta
            
            if meta['core_data_type'] in [CoreDataType.CATEGORICAL]:
                # Get information for the underling categories
                series_u = pl.Series(series.cat.get_categories())
                meta['n_levels'] = series_u.len()
                meta['category_levels'] = series_u.to_list()
                inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
            else:
                series_u = (series.filter(series.is_not_nan() & series.is_not_null()) if meta['core_data_type'] in [CoreDataType.FLOAT] else series.filter(series.is_not_null())).unique()
                inferred_meta = deepcopy(meta)
                meta['n_levels'] = series_u.len()
            meta['percent_null'] = series.is_null().mean() if meta['core_data_type'] in [CoreDataType.CATEGORICAL] else (((series.len() - series_u.len()) / series.len() * 100) if series.len() > 0 else 0.0)

            n_samples: int = min(max([n if isinstance(n, int) and n > 0 else int(series_u.len() * confidence), 100]), series_u.len())

            if n_samples == 0:
                return (series, meta) if return_series else meta

            if n_samples < series_u.len():
                series_u = series_u.sample(n=n_samples, seed=seed) if sample_strat == 'random' else series_u.head(n_samples)

            if (meta['core_data_type'] in [CoreDataType.OBJECT, CoreDataType.STRING]):
                # Calculate max byte length for string sizing
                non_null_strings = series.filter(series.is_not_null())
                if non_null_strings.len() > 0:
                    meta['max_byte_length'] = non_null_strings.str.len_bytes().max()
                else:
                    meta['max_byte_length'] = 0

                # Check if is a datetime/date/time/duration string
                meta.update(EnhancedPolars.get_temporal_string_format(series_u))
                if (meta.get('temporal_format') == 'MIXED') or ('|' in (meta.get('temporal_format') or '')):
                    col_name: str = series_u.name
                    try:
                        _t = series_u.to_frame().select(
                                    pl.col(col_name).map_batches(
                                        lambda batch: [parser.parse(x) for x in batch], # Nulls already filtered out
                                        return_dtype=pl.Datetime
                                    ).alias(col_name)
                                )[col_name]
                        assert _t.is_not_null().all()
                        series_u = _t

                        if return_series:
                            _t = series.to_frame().select(
                                    pl.col(col_name).map_batches(
                                        lambda batch: [parser.parse(x) if x is not None else None for x in batch], # Nulls not already filtered out
                                        return_dtype=pl.Datetime
                                    ).alias(col_name)
                                )[col_name]
                            assert _t.is_not_null().sum() == series.is_not_null().sum()
                            series = _t
                            inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                        else:
                            inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
                    except Exception as e:
                        # If not all is converted say that it is not a temporal type
                        meta['temporal_type'] = None
                        meta['temporal_format'] = None
                elif '|' not in (meta.get('temporal_format') or '|'):
                    fmt: str = meta['temporal_format']
                    tp_str: str = meta['temporal_type']
                    tp = pl.Date if tp_str == 'DATE' else pl.Time if tp_str == 'TIME' else pl.Datetime
                    try:
                        series_u = series_u.str.strptime(tp, fmt, strict=True)
                        if return_series:
                            series = series.str.strptime(tp, fmt, strict=True)
                            inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                        else:
                            inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
                    except Exception as e:
                        # If not all is converted say that it is not a temporal type
                        meta['temporal_type'] = None
                        meta['temporal_format'] = None
                
                if meta.get('temporal_format') is None:
                    # Check for timedelta
                    series_u = EnhancedPolars.to_timedelta_polars(series_u)
                    if series_u.dtype == pl.Duration:
                        if return_series:
                            series = EnhancedPolars.to_timedelta_polars(series)
                            if series.dtype == pl.Duration:
                                inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                        else:
                            inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)

                if inferred_meta['core_data_type'] in [CoreDataType.OBJECT, CoreDataType.STRING]:
                    # Check for numeric conversion from string
                    try:
                        series_u = series_u.cast(pl.Float64)
                        if return_series:
                            series = series.cast(pl.Float64)
                            inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                        else:
                            inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
                        attempt_downcast = True # if it is parsed from string it could be a integer, don't know yet
                    except Exception as e:
                        pass

            if (inferred_meta['core_data_type'] in [CoreDataType.FLOAT, CoreDataType.INTEGER]):
                if attempt_downcast or attempt_numeric_to_datetime:
                    meta['min_value'] = cast(int | float, series.min() if return_series else series_u.min())
                    meta['max_value'] = cast(int | float, series.max() if return_series else series_u.max())

                if attempt_numeric_to_datetime and (inferred_meta['core_data_type'] in [CoreDataType.INTEGER, CoreDataType.FLOAT]):
                    candidates = [
                        ("s", (1e9, 2e9), "ms"),        # seconds -> convert to ms by * 1000
                        ("ms", (1e12, 2e12), "ms"),     # milliseconds -> use ms directly
                        ("us", (1e15, 2e15), "us"),     # microseconds -> use us directly  
                        ("ns", (1e18, 2e18), "ns"),     # nanoseconds -> use ns directly
                    ]
                    for unit, (low, high), pl_unit in candidates:
                        if meta['min_value'] > low and meta['max_value'] < high:
                            try:
                                if unit == "s":
                                    # Convert seconds to milliseconds
                                    series_u_converted = (series_u * 1000).cast(pl.Datetime(pl_unit))  # type: ignore
                                    if return_series:
                                        series = (series * 1000).cast(pl.Datetime(pl_unit))  # type: ignore
                                        inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                                    else:
                                        inferred_meta = EnhancedPolars.get_dtype_meta(series_u_converted.dtype)
                                    series_u = series_u_converted
                                else:
                                    # Use the values directly
                                    series_u = series_u.cast(pl.Datetime(pl_unit))  # type: ignore
                                    if return_series:
                                        series = series.cast(pl.Datetime(pl_unit))  # type: ignore
                                        inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                                    else:
                                        inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
                                break
                            except Exception:
                                pass

                if (inferred_meta['core_data_type'] in [CoreDataType.FLOAT, CoreDataType.INTEGER]) and attempt_downcast:
                    # attempt int conversion first, don't need to filter nans for series_u since they have been removed already
                    finite: bool = series.filter(series.is_not_nan() & series.is_not_null()).is_finite().all() if return_series else series_u.is_finite().all()
                    if finite:
                        # Check if all values are whole numbers (no fractional parts)
                        is_whole = (series_u == series_u.round(0)).all()
                        if is_whole:
                            series_u = series_u.cast(pl.Int64)
                            if return_series:
                                series = series.cast(pl.Int64)
                                inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                            else:
                                inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
    
                    if EnhancedPolars._is_integer_helper(series_u.dtype):
                        # check unsigned candidates first if all values >= 0
                        if meta['min_value'] >= 0:
                            if (meta['max_value'] <= 255) and (series_u.dtype != pl.UInt8):
                                series_u = series_u.cast(pl.UInt8)
                                if return_series:
                                    series = series.cast(pl.UInt8)
                            elif (meta['max_value'] <= 65535) and (series_u.dtype != pl.UInt16):
                                series_u = series_u.cast(pl.UInt16)
                                if return_series:
                                    series = series.cast(pl.UInt16)
                            elif (meta['max_value'] <= 4294967295) and (series_u.dtype != pl.UInt32):
                                series_u = series_u.cast(pl.UInt32)
                                if return_series:
                                    series = series.cast(pl.UInt32)      
                        else:
                            if (-128 <= meta['min_value']) and (meta['max_value'] <= 127) and (series_u.dtype != pl.Int8):
                                series_u = series_u.cast(pl.Int8)
                                if return_series:
                                    series = series.cast(pl.Int8)
                            elif (-32768 <= meta['min_value']) and (meta['max_value'] <= 32767) and (series_u.dtype != pl.Int16):
                                series_u = series_u.cast(pl.Int16)
                                if return_series:
                                    series = series.cast(pl.Int16)
                            elif (-2147483648 <= meta['min_value']) and (meta['max_value'] <= 2147483647) and (series_u.dtype != pl.Int32):
                                series_u = series_u.cast(pl.Int32)
                                if return_series:
                                    series = series.cast(pl.Int32)

                    if EnhancedPolars._is_float_helper(series_u.dtype):
                        # Try Float32 if it round-trips
                        s32 = (series if return_series else series_u).cast(pl.Float32)
                        if (s32.cast(pl.Float64) == (series if return_series else series_u)).all():  
                            if return_series:
                                series = s32
                                series_u = series_u.cast(pl.Float32)
                            else:
                                series_u = s32

                if collect_precision_scale:
                    scale_expr = (
                                    (pl.col(series.name) - pl.col(series.name).floor())
                                    .abs()
                                    .cast(pl.Utf8)
                                    .str.len_chars() - 2
                                    ).alias("scale")

                    prec_expr = (
                                    pl.col(series.name).cast(pl.Utf8)
                                    .str.replace_all(r"[-.]", "")
                                    .str.len_chars()
                                ).alias("precision")

                    # Apply via select
                    _tp = series.to_frame().select([prec_expr, scale_expr]).max()
                    meta['precision'] = max(_tp['precision'].item(), 0)
                    meta['scale'] = max(_tp['scale'].item(), 0)

            if (inferred_meta['core_data_type'] in [CoreDataType.DATETIME]):

                if attempt_downcast:
                    # Check for date downcast (only for DATETIME, not TIME)
                    if (inferred_meta['core_data_type'] == CoreDataType.DATETIME and 
                        pl.select(((series if return_series else series_u).dt.time() == pl.time(0, 0, 0)).all()).item()):
                        if return_series:
                            series = series.dt.date()
                            inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                        else:
                            series_u = series_u.dt.date()
                            inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
                    else:
                        _s = (series if return_series else series_u)
                        if inferred_meta['core_data_type'] == CoreDataType.DATETIME:
                            # For Datetime, test different time units
                            for unit in ["ms", "us", "ns"]:  # test in increasing precision
                                down = _s.cast(pl.Datetime(unit)) # type: ignore
                                up   = down.cast(_s.dtype)
                                if up.equals(_s):
                                    if return_series:
                                        series = down
                                        inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                                    else:
                                        series_u = down
                                        inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
                                    break

            if inferred_meta['core_data_type'] in [CoreDataType.OBJECT, CoreDataType.STRING]:
                # Final check for categorical
                if (meta['n_levels'] / series.len() if series.len() > 0 else 0.0) <= cardinality_threshold:
                    series_u = series_u.cast(pl.Categorical)
                    if return_series:
                        series = series.cast(pl.Categorical)
                        inferred_meta = EnhancedPolars.get_dtype_meta(series.dtype)
                        meta['category_levels'] = series.cat.get_categories().to_list()
                    else:
                        inferred_meta = EnhancedPolars.get_dtype_meta(series_u.dtype)
                        meta['category_levels'] = series_u.cat.get_categories().to_list()

            meta['inferred_meta'] = inferred_meta

            return (series, meta) if return_series else meta

    @staticmethod
    def to_timedelta_polars(s: pl.Series, unit: Literal['ns', 'us', 'ms'] = "ms") -> pl.Series:
        """
        Convert a Polars string Series with pandas-style timedelta strings
        (e.g. '1d', '40m', '2h30m', '01:23:45', '500ms') into a Polars Duration.
        Non-matching values -> null.
        """
        # Regex that broadly validates a timedelta-like string (case-insensitive)
        TIMEDELTA_REGEX = re.compile(
            r"^("
            r"(\d+d)?"
            r"(\d+h)?"
            r"(\d+m)?"
            r"(\d+s)?"
            r"(\d+ms)?"
            r"(\d+(us|µs))?"
            r"(\d+ns)?"
            r"|"
            r"\d{1,2}:\d{2}(:\d{2})?"   # HH:MM[:SS]
            r")$", re.IGNORECASE
        )

        # Step 1: mask valid candidates
        valid_mask = [bool(TIMEDELTA_REGEX.match(str(x))) for x in s.to_list()]
        nnull_mask_sum = s.is_not_null().sum()
        
        if sum(valid_mask) != nnull_mask_sum:
            return s
        elif nnull_mask_sum == 0:
            return s
        
        s_masked = s.to_frame().with_columns(
            pl.when(pl.Series(valid_mask))
            .then(pl.col(s.name))
            .otherwise(None)
            .alias(s.name)
        )

        # Step 2: extract components without lookahead (case-insensitive)
        df = s_masked.with_columns([
            pl.col(s.name).str.extract(r"(?i)(\d+)d", 1).cast(pl.Int64, strict=False).fill_null(0).alias("days"),
            pl.col(s.name).str.extract(r"(?i)(\d+)h", 1).cast(pl.Int64, strict=False).fill_null(0).alias("hours"),
            pl.col(s.name).str.extract(r"(?i)(\d+)m([^a-zA-Z]|$)", 1).cast(pl.Int64, strict=False).fill_null(0).alias("minutes"),
            pl.col(s.name).str.extract(r"(?i)(\d+)s([^a-zA-Z]|$)", 1).cast(pl.Int64, strict=False).fill_null(0).alias("seconds"),
            pl.col(s.name).str.extract(r"(?i)(\d+)ms", 1).cast(pl.Int64, strict=False).fill_null(0).alias("milliseconds"),
            pl.col(s.name).str.extract(r"(?i)(\d+)(us|µs)", 1).cast(pl.Int64, strict=False).fill_null(0).alias("microseconds"),
            pl.col(s.name).str.extract(r"(?i)(\d+)ns", 1).cast(pl.Int64, strict=False).fill_null(0).alias("nanoseconds"),

            # HH:MM:SS (optional seconds)
            pl.col(s.name).str.extract(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", 1).cast(pl.Int64, strict=False).fill_null(0).alias("hms_h"),
            pl.col(s.name).str.extract(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", 2).cast(pl.Int64, strict=False).fill_null(0).alias("hms_m"),
            pl.col(s.name).str.extract(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", 3).cast(pl.Int64, strict=False).fill_null(0).alias("hms_s"),
        ])

        # Step 3: combine to ns
        df = df.with_columns(
            (
                pl.col("days") * 86_400_000_000_000 +
                (pl.col("hours") + pl.col("hms_h")) * 3_600_000_000_000 +
                (pl.col("minutes") + pl.col("hms_m")) * 60_000_000_000 +
                (pl.col("seconds") + pl.col("hms_s")) * 1_000_000_000 +
                pl.col("milliseconds") * 1_000_000 +
                pl.col("microseconds") * 1_000 +
                pl.col("nanoseconds")
            ).alias("delta_ns")
        )

        return df.with_columns(
            pl.col("delta_ns").cast(pl.Duration(unit)).alias(s.name)
        )[s.name]

    @staticmethod
    def _numpy_dtype_to_polars(dtype: np.dtype) -> pl.DataType:
        """Convert a numpy dtype to a Polars DataType."""
        numpy_to_polars: Dict[np.dtype, pl.DataType] = {
            np.dtype('int8'): pl.Int8(),
            np.dtype('int16'): pl.Int16(),
            np.dtype('int32'): pl.Int32(),
            np.dtype('int64'): pl.Int64(),
            np.dtype('uint8'): pl.UInt8(),
            np.dtype('uint16'): pl.UInt16(),
            np.dtype('uint32'): pl.UInt32(),
            np.dtype('uint64'): pl.UInt64(),
            np.dtype('float16'): pl.Float32(),
            np.dtype('float32'): pl.Float32(),
            np.dtype('float64'): pl.Float64(),
            np.dtype('bool'): pl.Boolean(),
            np.dtype('object'): pl.String(),
            np.dtype('str'): pl.String(),
        }

        # Direct lookup
        if dtype in numpy_to_polars:
            return numpy_to_polars[dtype]

        # Handle datetime64
        if np.issubdtype(dtype, np.datetime64):
            unit_str = np.datetime_data(dtype)[0]
            unit_map: Dict[str, Literal['ns', 'us', 'ms']] = {'ns': 'ns', 'us': 'us', 'ms': 'ms', 's': 'us'}
            return pl.Datetime(unit_map.get(unit_str, 'us'))

        # Handle timedelta64
        if np.issubdtype(dtype, np.timedelta64):
            unit_str = np.datetime_data(dtype)[0]
            unit_map_dur: Dict[str, Literal['ns', 'us', 'ms']] = {'ns': 'ns', 'us': 'us', 'ms': 'ms', 's': 'us'}
            return pl.Duration(unit_map_dur.get(unit_str, 'us'))

        # Handle string types
        if dtype.kind == 'U' or dtype.kind == 'S':
            return pl.String()

        raise ValueError(f"Unsupported numpy dtype: {dtype}")

    @staticmethod
    def _arrow_dtype_to_polars(dtype: Any) -> pl.DataType:
        """Convert a PyArrow DataType to a Polars DataType."""
        import pyarrow as pa

        arrow_to_polars: Dict[Any, pl.DataType] = {
            pa.int8(): pl.Int8(),
            pa.int16(): pl.Int16(),
            pa.int32(): pl.Int32(),
            pa.int64(): pl.Int64(),
            pa.uint8(): pl.UInt8(),
            pa.uint16(): pl.UInt16(),
            pa.uint32(): pl.UInt32(),
            pa.uint64(): pl.UInt64(),
            pa.float16(): pl.Float32(),
            pa.float32(): pl.Float32(),
            pa.float64(): pl.Float64(),
            pa.bool_(): pl.Boolean(),
            pa.string(): pl.String(),
            pa.large_string(): pl.String(),
            pa.utf8(): pl.String(),
            pa.large_utf8(): pl.String(),
            pa.binary(): pl.Binary(),
            pa.large_binary(): pl.Binary(),
            pa.date32(): pl.Date(),
            pa.date64(): pl.Date(),
            pa.null(): pl.Null(),
        }

        # Direct lookup
        if dtype in arrow_to_polars:
            return arrow_to_polars[dtype]

        # Handle timestamp types
        if pa.types.is_timestamp(dtype):
            unit: Literal['ns', 'us', 'ms'] = dtype.unit if dtype.unit in ('ns', 'us', 'ms') else 'us'
            tz = dtype.tz
            return pl.Datetime(unit, tz)

        # Handle duration types
        if pa.types.is_duration(dtype):
            dur_unit: Literal['ns', 'us', 'ms'] = dtype.unit if dtype.unit in ('ns', 'us', 'ms') else 'us'
            return pl.Duration(dur_unit)

        # Handle time types
        if pa.types.is_time32(dtype) or pa.types.is_time64(dtype):
            return pl.Time()

        # Handle decimal types
        if pa.types.is_decimal(dtype):
            return pl.Decimal(dtype.precision, dtype.scale)

        # Handle list types
        if pa.types.is_list(dtype) or pa.types.is_large_list(dtype):
            inner = EnhancedPolars._arrow_dtype_to_polars(dtype.value_type)
            return pl.List(inner)

        # Fallback to string representation parsing
        raise ValueError(f"Unsupported PyArrow dtype: {dtype}")

    @staticmethod
    def parse_dtype(dtype: str | Type | np.dtype | Any) -> pl.DataType:
        """
        Parse a dtype specification to a Polars DataType with comprehensive support for multiple formats.
        
        This function handles conversion from various dtype representations including:
        - Pandas dtypes and extension types  
        - PyArrow dtypes
        - NumPy dtypes
        - Python builtin types
        - String representations of all the above
        - Parquet logical types
        
        Parameters:
        -----------
        dtype : str, Type, np.dtype, or Any
            The dtype specification to parse. Can be:
            - String names like 'int64', 'float32', 'datetime64[ns]', 'string', 'category'
            - Python builtin types like int, float, str, bool
            - NumPy dtypes like np.int64, np.float32, np.datetime64
            - Pandas dtypes like pd.Int64Dtype(), pd.StringDtype()
            - PyArrow dtypes like pa.int64(), pa.string()
            - Complex string specifications like 'datetime64[ns, UTC]', 'decimal(10,2)'
            
        Returns:
        --------
        pl.DataType
            The corresponding Polars DataType
            
        Raises:
        ------
        ValueError
            If the dtype cannot be parsed or is not supported
            
        Examples:
        ---------
        >>> # Basic types
        >>> parse_dtype('int64')  # pl.Int64
        >>> parse_dtype(int)      # pl.Int64  
        >>> parse_dtype('string') # pl.String
        >>> 
        >>> # Complex temporal types
        >>> parse_dtype('datetime64[ns]')      # pl.Datetime('ns')
        >>> parse_dtype('datetime64[ms, UTC]') # pl.Datetime('ms', 'UTC')
        >>> 
        >>> # Pandas extension types
        >>> parse_dtype('Int64')     # pl.Int64 (nullable pandas int)
        >>> parse_dtype('string')    # pl.String (pandas string)
        >>> parse_dtype('category')  # pl.Categorical
        >>> 
        >>> # Decimal types
        >>> parse_dtype('decimal(10,2)')  # pl.Decimal(10, 2)
        >>> parse_dtype('decimal128(5)')  # pl.Decimal(5, 0)
        """
        # Handle None or already Polars types
        if dtype is None or isinstance(dtype, type(None)):
            return pl.Null()
        if isinstance(dtype, pl.DataType):
            return dtype
            
        # Handle NumPy dtypes first
        if isinstance(dtype, np.dtype):
            try:
                return EnhancedPolars._numpy_dtype_to_polars(dtype)
            except Exception:
                # Fall through to string parsing for unsupported numpy types
                dtype = str(dtype)
        
        # Handle Python builtin types
        if isinstance(dtype, type):
            builtin_map = {
                int: pl.Int64(),
                float: pl.Float64(),
                str: pl.String(),
                bool: pl.Boolean(),
                bytes: pl.Binary(),
                list: pl.List(pl.String()),  # Default to list of strings
                dict: pl.Struct([]),         # Empty struct
            }
            if dtype in builtin_map:
                return builtin_map[dtype]
            else:
                # Try to convert class name to string for further parsing
                dtype = dtype.__name__
        
        # Handle PyArrow types (if available)
        if hasattr(dtype, '__module__') and 'pyarrow' in str(dtype.__module__):
            try:
                import pyarrow as pa
                # Convert PyArrow to Polars
                if isinstance(dtype, pa.DataType):
                    return EnhancedPolars._arrow_dtype_to_polars(dtype)
            except ImportError:
                pass
            except Exception:
                # Fall through to string parsing
                dtype = str(dtype)
        
        # Handle Pandas types (if available)
        try:
            import pandas as pd
            if hasattr(pd, 'api') and hasattr(pd.api, 'types'):
                # Check if it's a pandas extension dtype
                if hasattr(dtype, 'name') and not isinstance(dtype, str):
                    dtype_name = dtype.name
                else:
                    dtype_name = str(dtype)
                    
                # Handle pandas extension types
                pandas_extension_map = {
                    'Int8': pl.Int8(),
                    'Int16': pl.Int16(), 
                    'Int32': pl.Int32(),
                    'Int64': pl.Int64(),
                    'UInt8': pl.UInt8(),
                    'UInt16': pl.UInt16(),
                    'UInt32': pl.UInt32(), 
                    'UInt64': pl.UInt64(),
                    'Float32': pl.Float32(),
                    'Float64': pl.Float64(),
                    'boolean': pl.Boolean(),
                    'string': pl.String(),
                    'category': pl.Categorical(),
                }
                
                if dtype_name in pandas_extension_map:
                    return pandas_extension_map[dtype_name]
        except ImportError:
            pass
        
        # String parsing for complex types
        if isinstance(dtype, str):
            dtype_str = dtype.lower().strip()
            
            # Basic integer types
            if dtype_str in ['int8', 'i1']:
                return pl.Int8()
            elif dtype_str in ['int16', 'i2']:
                return pl.Int16()
            elif dtype_str in ['int32', 'i4', 'int']:
                return pl.Int32()
            elif dtype_str in ['int64', 'i8', 'long']:
                return pl.Int64()
            elif dtype_str in ['uint8', 'u1']:
                return pl.UInt8()
            elif dtype_str in ['uint16', 'u2']:
                return pl.UInt16()
            elif dtype_str in ['uint32', 'u4']:
                return pl.UInt32()
            elif dtype_str in ['uint64', 'u8']:
                return pl.UInt64()
                
            # Float types
            elif dtype_str in ['float16', 'f2', 'half']:
                return pl.Float32()  # Polars doesn't have Float16, use Float32
            elif dtype_str in ['float32', 'f4', 'float', 'single']:
                return pl.Float32()
            elif dtype_str in ['float64', 'f8', 'double']:
                return pl.Float64()
                
            # Boolean
            elif dtype_str in ['bool', 'boolean', '?']:
                return pl.Boolean()
                
            # String types
            elif dtype_str in ['str', 'string', 'object', 'text', 'utf8']:
                return pl.String()
            elif dtype_str in ['category', 'categorical']:
                return pl.Categorical()
                
            # Binary
            elif dtype_str in ['bytes', 'binary']:
                return pl.Binary()
                
            # Date and time types
            elif dtype_str in ['date', 'date32']:
                return pl.Date()
            elif dtype_str in ['time', 'time64']:
                return pl.Time()
                
            # Complex datetime parsing
            elif dtype_str.startswith('datetime') or dtype_str.startswith('timestamp'):
                # Parse datetime64[unit, tz] format
                
                # Match patterns like 'datetime64[ns]', 'datetime64[ms, UTC]', 'timestamp[us, tz=UTC]'
                dt_pattern = r'(?:datetime64|timestamp)\[([^,\]]+)(?:,\s*(?:tz=)?([^\]]+))?\]'
                match = re.search(dt_pattern, dtype_str)
                
                if match:
                    unit = match.group(1).strip()
                    tz = match.group(2).strip() if match.group(2) else None
                    
                    # Map units (Polars only supports ns, us, ms)
                    unit_map = {
                        'ns': 'ns',
                        'us': 'us', 
                        'μs': 'us',
                        'ms': 'ms',
                        's': 'ms',  # Convert seconds to milliseconds for Polars
                        'seconds': 'ms',
                        'milliseconds': 'ms',
                        'microseconds': 'us',
                        'nanoseconds': 'ns'
                    }
                    
                    polars_unit = unit_map.get(unit, 'us')
                    
                    if tz and tz.lower() not in ['none', 'null']:
                        if polars_unit == 'ns':
                            return pl.Datetime('ns', tz)
                        elif polars_unit == 'us':
                            return pl.Datetime('us', tz)
                        else:  # ms
                            return pl.Datetime('ms', tz)
                    else:
                        if polars_unit == 'ns':
                            return pl.Datetime('ns')
                        elif polars_unit == 'us':
                            return pl.Datetime('us')
                        else:  # ms
                            return pl.Datetime('ms')
                else:
                    # Default datetime
                    return pl.Datetime('us')
                    
            # Duration/timedelta types
            elif dtype_str.startswith('timedelta') or dtype_str.startswith('duration'):
                # Parse timedelta64[unit] format
                td_pattern = r'(?:timedelta64|duration)\[([^\]]+)\]'
                match = re.search(td_pattern, dtype_str)
                
                if match:
                    unit = match.group(1).strip()
                    # Map units (Polars only supports ns, us, ms)
                    unit_map = {
                        'ns': 'ns',
                        'us': 'us',
                        'μs': 'us', 
                        'ms': 'ms',
                        's': 'ms',  # Convert seconds to milliseconds for Polars
                        'seconds': 'ms',
                        'milliseconds': 'ms',
                        'microseconds': 'us',
                        'nanoseconds': 'ns'
                    }
                    polars_unit = unit_map.get(unit, 'us')
                    
                    if polars_unit == 'ns':
                        return pl.Duration('ns')
                    elif polars_unit == 'us':
                        return pl.Duration('us')
                    else:  # ms
                        return pl.Duration('ms')
                else:
                    return pl.Duration('us')
                    
            # Decimal types
            elif dtype_str.startswith('decimal'):
                # Parse decimal(precision, scale) format
                decimal_pattern = r'decimal(?:128|64|32)?\s*\(\s*(\d+)\s*(?:,\s*(\d+))?\s*\)'
                match = re.search(decimal_pattern, dtype_str)
                
                if match:
                    precision = int(match.group(1))
                    scale = int(match.group(2)) if match.group(2) else 0
                    return pl.Decimal(precision, scale)
                else:
                    # Default decimal
                    return pl.Decimal(10, 2)
                    
            # List/Array types
            elif dtype_str.startswith('list') or dtype_str.startswith('array'):
                # Parse list[dtype] or array[dtype] format
                container_pattern = r'(?:list|array)\[([^\]]+)\]'
                match = re.search(container_pattern, dtype_str)
                
                if match:
                    inner_dtype_str = match.group(1).strip()
                    inner_dtype = EnhancedPolars.parse_dtype(inner_dtype_str)
                    return pl.List(inner_dtype)
                else:
                    return pl.List(pl.String())
                    
            # Struct types
            elif dtype_str.startswith('struct'):
                # For now, return empty struct - could be enhanced to parse field definitions
                return pl.Struct([])
                
            # Null type
            elif dtype_str in ['null', 'none', 'void']:
                return pl.Null()
                
            # Try numpy dtype parsing as fallback
            else:
                try:
                    numpy_dtype = np.dtype(dtype_str)
                    return EnhancedPolars._numpy_dtype_to_polars(numpy_dtype)
                except (TypeError, ValueError):
                    pass
        
        # Final fallback - try to convert via numpy if possible
        try:
            if hasattr(dtype, 'dtype') and not isinstance(dtype, str):
                # Pandas Series/Index/Array with dtype attribute
                return EnhancedPolars.parse_dtype(dtype.dtype)
            elif hasattr(dtype, 'type') and not isinstance(dtype, str):
                # NumPy scalar with type attribute
                return EnhancedPolars.parse_dtype(dtype.type)
            else:
                # Try numpy conversion
                numpy_dtype = np.dtype(dtype)
                return EnhancedPolars._numpy_dtype_to_polars(numpy_dtype)
        except Exception:
            pass
        
        # If all else fails, raise an error
        raise ValueError(f"Cannot parse dtype: {dtype} (type: {type(dtype)})")

    @staticmethod
    def read_data(fp_query: Path | str, mode: Literal['eager', 'lazy'] = 'lazy',
                 file_type: Optional[Literal['.csv', '.parquet', '.json', '.ndjson', '.ipc', 'd.elta']] = None,
                 pattern: Optional[str] = None,
                 strict_type_scan_enforcement: bool = True,
                 recursive: bool = True,
                 merge_results: bool = True,
                 optimize_types: bool = True,
                 type_inference_confidence: float = 0.6,
                 clean_column_names: bool = True,
                 desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                   'capitalize', 'casefold', 'preserve'] = 'preserve',
                 **kwargs) -> pl.DataFrame | pl.LazyFrame | Dict[Path, pl.DataFrame | pl.LazyFrame] | Any:
        
        res = EnhancedPolars._read_data(fp_query=fp_query, mode=mode, file_type=file_type, pattern=pattern,
                                        strict_type_scan_enforcement=strict_type_scan_enforcement,
                                        optimize_types=optimize_types, clean_column_names=clean_column_names,
                                        desired_column_name_case=desired_column_name_case,
                                         type_inference_confidence=type_inference_confidence,
                                        recursive=recursive, merge_results=merge_results, **kwargs)
        
        assert isinstance(res, tuple) and (len(res) == 2), f'Found length {len(res)} with types {[type(r) for r in res]}' # type: ignore
        df, status = res

        if status == 1:
            return EnhancedPolars.cleanup(df,
                                        optimize_types=optimize_types, type_inference_confidence=type_inference_confidence,
                                        clean_column_names=clean_column_names, desired_column_name_case=desired_column_name_case)

        return df

    @staticmethod
    def _read_data(fp_query: Path | str, mode: Literal['eager', 'lazy'] = 'lazy',
                 file_type: Optional[Literal['.csv', '.parquet', '.json', '.ndjson', '.ipc', 'd.elta']] = None,
                 pattern: Optional[str] = None,
                 strict_type_scan_enforcement: bool = True,
                 recursive: bool = True,
                 merge_results: bool = True,
                 optimize_types: bool = True,
                 type_inference_confidence: float = 0.6,
                 clean_column_names: bool = True,
                 desired_column_name_case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase',
                                                   'capitalize', 'casefold', 'preserve'] = 'preserve',
                 attempt_numeric_to_datetime: bool = False,
                 **kwargs) -> pl.DataFrame | pl.LazyFrame | Dict[Path, pl.DataFrame | pl.LazyFrame] | Any:
         if isinstance(fp_query, str):
             if os.path.exists(fp_query):
                 fp_query = Path(fp_query)
             elif (('connection' in kwargs) or ('uri' in kwargs)):
                return EnhancedPolars._read_sql(query=fp_query, **kwargs)
             else:
                 raise FileNotFoundError(f"File or directory not found: {fp_query}")
            
         if isinstance(fp_query, Path):
             if fp_query.is_dir():
                 if file_type in ['.csv', '.tsv']:
                    return EnhancedPolars.read_csv(fp_query, mode=mode, recursive=recursive, filter_csv_only=strict_type_scan_enforcement, type_inference_confidence=type_inference_confidence,
                                                   optimize_types=optimize_types, clean_column_names=clean_column_names, desired_column_name_case=desired_column_name_case,
                                                    attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif file_type == '.parquet':
                    return EnhancedPolars.read_parquet(fp_query, mode=mode, recursive=recursive, filter_parquet_only=strict_type_scan_enforcement, type_inference_confidence=type_inference_confidence,
                                                        optimize_types=optimize_types, clean_column_names=clean_column_names, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif file_type == '.ipc':
                     return EnhancedPolars.read_ipc(fp_query, mode=mode, recursive=recursive, filter_ipc_only=strict_type_scan_enforcement, type_inference_confidence=type_inference_confidence,
                                                     optimize_types=optimize_types, clean_column_names=clean_column_names, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif file_type == '.delta':
                     return EnhancedPolars.read_delta(fp_query, mode=mode, recursive=recursive, filter_delta_only=strict_type_scan_enforcement, type_inference_confidence=type_inference_confidence,
                                                       optimize_types=optimize_types, clean_column_names=clean_column_names, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif file_type in ['.ndjson']:
                     return EnhancedPolars.read_ndjson(fp_query, mode=mode, recursive=recursive, filter_ndjson_only=strict_type_scan_enforcement, type_inference_confidence=type_inference_confidence,
                                                        optimize_types=optimize_types, clean_column_names=clean_column_names, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif pattern is not None:
                     files: List[Path] = find_files(directory=fp_query, pattern=pattern, file_type=file_type, recursive=recursive, mode='file')
                     if len(files) == 0:
                         raise FileNotFoundError(f"No files found in directory: {fp_query} matching pattern: {pattern}, kwargs: {kwargs}")
                     results: Dict[Path, pl.DataFrame | pl.LazyFrame] = {f: cast(pl.DataFrame | pl.LazyFrame, EnhancedPolars.read_data(fp_query=f, mode=mode, optimize_types=optimize_types, type_inference_confidence=type_inference_confidence,
                                                                                                                                       clean_column_names=clean_column_names, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                                                                                                                                         **kwargs)) for f in tqdm(files, desc="Reading files")}

                     if merge_results:
                         if all([isinstance(v, (pl.DataFrame, pl.LazyFrame)) for v in results.values()]):
                             return cast(pl.DataFrame | pl.LazyFrame, EnhancedPolars.concat_series_dataframe(*results.values())), 1
                         else:
                             logging.warning('Not all of the results were loadable as DataFrame or LazyFrame, returning dict of results instead.')

                     return results, 1
                 else:
                     raise ValueError(f"file_type or pattern must be specified when reading from a directory: {fp_query}")
             elif fp_query.is_file():
                 if fp_query.name.endswith(('.csv', '.tsv')):
                    if ('sep' not in kwargs) and fp_query.name.endswith('.tsv'):
                        kwargs['sep'] = '\t'
                    return EnhancedPolars.read_csv(fp_query, mode=mode, optimize_types=optimize_types, clean_column_names=clean_column_names,
                                                    type_inference_confidence=type_inference_confidence, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif fp_query.name.endswith(('.parquet', '.parq', '.pq')):
                    return EnhancedPolars.read_parquet(fp_query, mode=mode, optimize_types=optimize_types, clean_column_names=clean_column_names,
                                                        type_inference_confidence=type_inference_confidence, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif fp_query.name.endswith(('.xlsx', '.xls')):
                     return pl.read_excel(fp_query, **kwargs), 0
                 elif fp_query.name.endswith(('.ipc', '.feather')):
                     try:
                        return EnhancedPolars.read_ipc(fp_query, mode=mode, optimize_types=optimize_types, clean_column_names=clean_column_names,
                                                        type_inference_confidence=type_inference_confidence, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                     except Exception as e:
                         try:
                             return pl.from_pandas(pd.read_feather(fp_query, **kwargs)), 0
                         except Exception as e2:
                             raise ValueError(f"Error reading IPC/Feather file with Polars and Pandas: {e}, {e2}")
                 elif fp_query.name.endswith(('.arrow')):
                     return pl.read_ipc(fp_query, **kwargs), 0
                 elif fp_query.name.endswith(('.avro')):
                     return pl.read_avro(fp_query, **kwargs), 0
                 elif fp_query.name.endswith(('.delta')):
                     return EnhancedPolars.read_delta(fp_query, mode=mode, optimize_types=optimize_types, clean_column_names=clean_column_names,
                                                       type_inference_confidence=type_inference_confidence, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif fp_query.name.endswith(('.json', '.jsonl')):
                     try:
                         return pl.read_json(fp_query, **kwargs), 0
                     except Exception as e:
                         try:
                             with open(fp_query, 'r') as f:
                                 data = json.load(f)
                             logging.warning("Falling back to json.load and returning dict/list")
                             return data, -1
                         except Exception as e2:
                             raise ValueError(f"Error reading JSON file with Polars and json.load: {e}, {e2}") 
                 elif fp_query.name.endswith(('.ndjson')):
                     return EnhancedPolars.read_ndjson(fp_query, mode=mode, optimize_types=optimize_types, clean_column_names=clean_column_names,
                                                        type_inference_confidence=type_inference_confidence, desired_column_name_case=desired_column_name_case, attempt_numeric_to_datetime=attempt_numeric_to_datetime, **kwargs), 1
                 elif fp_query.name.endswith(('.txt', '.sql')):
                     with open(fp_query, 'r') as f:
                         data = f.read()
                         if fp_query.name.endswith('.sql') and (('connection' in kwargs) or ('uri' in kwargs)):
                            return EnhancedPolars._read_sql(query=data, **kwargs)

                         return data, -1
                 elif fp_query.name.endswith(('.yaml', '.yml')):
                    import yaml
                    with open(fp_query, 'r') as f:
                        data = yaml.safe_load(f)
                    return data, -1
                 elif fp_query.name.endswith(('.pkl', '.pickle')):
                     import pickle
                     return pickle.load(open(fp_query, 'rb')), -1
                 elif fp_query.name.endswith(('.joblib')):
                     import joblib
                     return joblib.load(fp_query), -1
                 elif fp_query.name.endswith(('.json_aes', '.yaml_aes', '.yml_aes')):
                     return SignedFile.read(path=str(fp_query), **kwargs), -1
                 elif fp_query.name.endswith(('.h5', '.hdf5')):
                     return pl.from_pandas(pd.read_hdf(fp_query, **kwargs)), 0
                 elif fp_query.name.endswith(('.ods', '.odf')):
                     return pl.read_ods(fp_query, **kwargs), 0

         raise ValueError(f"Unsupported file extension: {fp_query.name}")

    @staticmethod
    def _read_sql(query: str, **kwargs) -> Tuple[pl.DataFrame, int]:
        if 'connection' in kwargs:
            # Check if the connection is a DatabaseConnection from the sqlutilities package. This will simultananously check its type and prevent it from being accessed if not imported.
            if callable(getattr(kwargs['connection'], "_retrieve_credentials_from_secrets", None)):
                return cast(pl.DataFrame, read_sql(query=query, output_format='polars', **kwargs)), 0 # type: ignore
            return pl.read_database(query=query, **kwargs), 0
        elif 'uri' in kwargs:
            return pl.read_database_uri(query=query, **kwargs), 0
        raise ValueError("Either 'connection' or 'uri' must be provided in kwargs to read SQL data.")
    
    @staticmethod
    def to_partitioned_parquet(
        df: pd.DataFrame | pl.DataFrame | pl.LazyFrame,
        root_path: str | Path,
        partition_cols: List[str],
        schema_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        overwrite_config: bool = False,
        schema_metadata: Optional[Dict[str, Any]] = None,
        column_metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Converts a Pandas or Polars DataFrame to a partitioned PyArrow Parquet dataset
        with granular, column-level schema control.

        This function allows overriding individual field parameters (e.g., 'type',
        'nullable', 'metadata') by dynamically calling the appropriate methods on
        the PyArrow Field object.

        Args:
            df (Union[pd.DataFrame, pl.DataFrame]):
                The input DataFrame to convert.
            root_path (str):
                The root directory where the partitioned dataset will be saved.
            partition_cols (List[str]):
                A list of column names to partition the dataset by. The order
                of columns determines the directory hierarchy.
            schema_overrides (Optional[Dict[str, Dict[str, Any]]], optional):
                A dictionary mapping column names to another dictionary of properties
                to override. Keys should match the suffix of `pa.Field.with_*`
                methods (e.g., 'type', 'nullable', 'metadata').
                Example: {'col_a': {'nullable': False, 'type': pa.int32()}}
                Defaults to None.
            **kwargs:
                Additional keyword arguments to be passed directly to
                pyarrow.parquet.write_to_dataset(). For example,
                `existing_data_behavior='overwrite_or_ignore'`.
        """
        if not isinstance(df, (pd.DataFrame, pl.DataFrame, pl.LazyFrame)):
            raise TypeError("Input 'df' must be a Pandas or Polars DataFrame.")

        if isinstance(df, pd.DataFrame):
            df = pl.from_pandas(df)

        PolarsIO(df).to_partitioned_parquet(root_path=root_path,
                                            partition_cols=partition_cols,
                                            schema_overrides=schema_overrides,
                                            overwrite_config=overwrite_config,
                                            schema_metadata=schema_metadata,
                                            column_metadata=column_metadata,
                                            **kwargs)

    @staticmethod
    def read_schema_metadata(root_path: str | Path, regex: Optional[str] = None, keys: Optional[List[str] | str] = None, **find_files_kwargs) -> Any:
        if isinstance(regex, str):
            dirs: List[Path] = find_files(directory=root_path, pattern=regex, pattern_type='regex', mode='directory', **find_files_kwargs)
            assert len(dirs) == 1, f"Expected exactly one directory matching regex '{regex}', found {len(dirs)}: {dirs}."
            root_path = dirs[0]
        metadata_path = os.path.join(root_path, '_dataset_metadata.json')
        assert os.path.exists(metadata_path), f"Metadata file not found at {metadata_path}"
        out: Dict[str, Any] = XSer.safe_load(metadata_path)['__schema_metadata__']
        if isinstance(keys, str):
            return out[keys] # type: ignore
        elif isinstance(keys, list):
            return {k: out[k] for k in keys if k in out} # type: ignore
        return out

    @staticmethod
    def generate_random_data(n: int,
                                    dtypes: Optional[List[dt_options] | dt_options] = None,
                                    percent_null: float = 0.2,
                                    seed: Optional[int] = 20) -> pl.DataFrame:
        if isinstance(dtypes, str):
            dtypes = [dtypes]
        elif isinstance(dtypes, list):
            if not all(isinstance(dt, str) for dt in dtypes):
                raise TypeError("All elements in 'dtypes' list must be strings.")
        else:
            dtypes = [ "TEXT", "UUID", "TINYINT", "SMALLINT", "BIGINT", "INTEGER",
                        "FLOAT", "DATE", "DATETIME", "TIME", "BOOLEAN",
                        "JSON", "XML"
                     ]
        if not isinstance(seed, int):
            seed = 20
        if seed <= 0:
            raise ValueError("'seed' must be a positive integer.")
        
        assert isinstance(n, int) and n > 0, "'n' must be a positive integer."

        return pl.DataFrame({dtype: generate_random_sequence(
                            dtype=dtype,
                            n=n,
                            percent_null=percent_null,
                            seed=seed) for dtype in dtypes})
    

    @staticmethod
    def save_data(obj: Any,
                  out_path: str | Path,
                  **kwargs) -> bool:
        
        if isinstance(out_path, str):
            out_path = Path(out_path)
        
        if out_path.name.endswith(('.csv', '.tsv')):
            if 'separator' not in kwargs and out_path.name.endswith('.tsv'):
                kwargs['separator'] = '\t'
            PolarsIO(EnhancedPolars.from_data(obj)).to_csv(out_path, **kwargs) # type: ignore
            return True
        elif out_path.name.endswith(('.parquet', '.parq', '.pq')):
             if 'partition_cols' in kwargs:
                 PolarsIO(EnhancedPolars.from_data(obj)).to_partitioned_parquet(root_path=out_path, **kwargs) # type: ignore
             else:
                 PolarsIO(EnhancedPolars.from_data(obj)).to_parquet(out_path, **kwargs) # type: ignore
             return True
        elif out_path.name.endswith(('.xlsx', '.xls')):
            PolarsIO(EnhancedPolars.from_data(obj)).to_excel(out_path, **kwargs) # type: ignore
            return True
        elif out_path.name.endswith(('.ipc', '.feather')):
            PolarsIO(EnhancedPolars.from_data(obj)).to_ipc(out_path, **kwargs) # type: ignore
            return True
        elif out_path.name.endswith(('.arrow')):
            PolarsIO(EnhancedPolars.from_data(obj)).to_arrow(out_path, **kwargs) # type: ignore
            return True
        elif out_path.name.endswith(('.avro')):
            PolarsIO(EnhancedPolars.from_data(obj)).to_avro(out_path, **kwargs) # type: ignore
            return True
        elif out_path.name.endswith(('.delta')):
            PolarsIO(EnhancedPolars.from_data(obj)).to_delta(out_path, **kwargs) # type: ignore
            return True
        elif out_path.name.endswith(('.json', '.jsonl')):
            if isinstance(obj, (pl.DataFrame, pl.LazyFrame, pd.DataFrame)):
                PolarsIO(EnhancedPolars.from_data(obj)).to_json(out_path, **kwargs) # type: ignore
            else:
                XSer.safe_dump(obj, out_fp=out_path, target='json', **kwargs)
            return True
        elif out_path.name.endswith(('.ndjson')):
            PolarsIO(EnhancedPolars.from_data(obj)).to_ndjson(out_path, **kwargs) # type: ignore
            return True
        elif out_path.name.endswith(('.txt', '.sql')):
            with open(out_path, 'w') as f:
               f.write(str(obj))
            return True
        elif out_path.name.endswith(('.yaml', '.yml')):
            XSer.safe_dump(obj, out_fp=out_path, target='yaml', **kwargs)
            return True
        elif out_path.name.endswith(('.pkl', '.pickle')):
            import pickle
            pickle.dump(obj, open(out_path, 'wb'))
            return True
        elif out_path.name.endswith(('.joblib')):
            import joblib
            joblib.dump(obj, filename=out_path) 
            return True
        elif out_path.name.endswith(('.h5', '.hdf5')):
            if isinstance(obj, (pl.DataFrame, pl.LazyFrame)):
                obj = (obj.collect() if isinstance(obj, pl.LazyFrame) else obj).to_pandas()
            assert isinstance(obj, pd.DataFrame), f"Expected Pandas DataFrame for HDF5 output, got {type(obj)}"
            obj.to_hdf(out_path, **kwargs)
            return True
        elif out_path.name.endswith(('.ods', '.odf')):
            PolarsIO(EnhancedPolars.from_data(obj)).to_ods(out_path, **kwargs) # type: ignore
            return True
        else:
            raise ValueError(f"Unsupported file extension: {out_path.suffix}")