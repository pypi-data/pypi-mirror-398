import polars as pl
from pyarrow import dataset as ds
from pyarrow import parquet as pq
import pyarrow as pa
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
import io as io_module
from typing import List, Optional, Dict, Any, cast, Tuple, Literal
import logging
from CoreUtilities import XSer, SignedFile
from .pyarrow_typing import solve_table_schema
from CoreUtilities import debug_inputs
from .base import UniversalPolarsDataFrameExtension

# Type alias for time units
TimeUnit = Literal["ns", "us", "ms"]


class PolarsIO(UniversalPolarsDataFrameExtension):

    def __init__(self, df: pl.DataFrame | pl.LazyFrame):
        super().__init__(df)


    def to_partitioned_parquet(
        self,
        root_path: str | Path,
        partition_cols: List[str] | str,
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
        if not partition_cols:
            raise ValueError("'partition_cols' cannot be empty.")

        df = cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)

        if isinstance(partition_cols, str):
            partition_cols = [partition_cols]

        og_config: Dict[str, Any] = cast(Dict[str, Any], debug_inputs(function=PolarsIO.to_partitioned_parquet, kwargs=locals()))
        for k in ['self', 'overwrite_config', 'schema_metadata']:
            og_config.pop(k, None)
        og_config['__schema_metadata__'] = schema_metadata

        config_path = os.path.join(root_path, '_dataset_metadata.json')
        needs_validation: bool = False
        schema_modified: bool = False

        if os.path.exists(config_path) and not overwrite_config:
            # Dataset exists, load config
            config = XSer.safe_load(config_path)

            # Use loaded config. User-provided args are ignored.
            if partition_cols is not None or schema_overrides is not None:
                logging.warning("Warning: Dataset config already exists. Ignoring user-provided "
                    "'partition_cols' and 'schema_overrides'.")
            partition_cols = config['partition_cols']
            schema_overrides = config['schema_overrides']
            column_metadata = config['column_metadata']
            needs_validation = True
            # preserve initial special schema metadata in the event of an overwrite due to upcasting of schema
            og_config['__schema_metadata__'] = config.get('__schema_metadata__', {})

        schema_overrides = schema_overrides or {}
        if isinstance(column_metadata, dict):
            for col_name, metadata in column_metadata.items():
                if col_name in schema_overrides:
                    if 'metadata' in schema_overrides[col_name]:
                        # Merge existing metadata with new metadata
                        schema_overrides[col_name]['metadata'] = {**schema_overrides[col_name]['metadata'], **metadata}
                    else:
                        schema_overrides[col_name]['metadata'] = metadata
                else:
                    schema_overrides[col_name] = {'metadata': metadata}
        if len(schema_overrides) > 0:
            for col_name, metadata in schema_overrides.items():
                if 'metadata' in metadata:
                    metadata['metadata'] = XSer.safe_dump(metadata['metadata'], target='parquet_dataset_metadata')

        missing_cols = set(partition_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"The following partition columns are missing from the DataFrame: {missing_cols}"
            )

        table = df.to_arrow()


        # --- Schema Override Logic ---
        final_schema = table.schema
        if schema_overrides:
            for col_name, overrides in schema_overrides.items():
                try:
                    field_index = final_schema.get_field_index(col_name)
                    updated_field = final_schema.field(field_index)

                    # Dynamically apply overrides using getattr
                    for param, value in overrides.items():
                        method_name = f"with_{param}"
                        if hasattr(updated_field, method_name):
                            method = getattr(updated_field, method_name)
                            try:
                                updated_field = method(value)
                            except Exception as e:
                                logging.error(f"  - Error applying override '{param}' to '{col_name}' with value: {value}: {e}")
                                raise
                        else:
                            logging.warning(f"  - Warning: Invalid override parameter '{param}' for column '{col_name}'. Skipping.")

                    final_schema = final_schema.set(field_index, updated_field)
                    logging.debug(f"  - Applied overrides to '{col_name}'.")
                    schema_modified = True
                except KeyError:
                    logging.warning(f"  - Warning: Column '{col_name}' in schema_overrides not found in DataFrame. Skipping.")

        files_to_replace: List[str | Path] = []
        if needs_validation:
            # Schema validation: Check for conflicts between existing and new data
            try:
                # Get existing dataset schema
                files_to_replace = [str(p) for p in Path(root_path).rglob("*.parquet")]
                final_schema, schema_modified = cast(Tuple[pa.Schema, bool], solve_table_schema(ds.dataset(files_to_replace, format="parquet").schema, final_schema, change_flag=True))

                if schema_modified:
                    logging.info("Schema changes detected during validation.")

                    existing_data = pl.scan_parquet(
                                    os.path.join(root_path, '**/*.parquet'), hive_partitioning=True,
                                    glob=True,
                                    allow_missing_columns=True # safe way to read all exisitng data
                                ).collect().to_arrow().cast(target_schema=final_schema)

                    table = pa.concat_tables([table.select([field.name for field in final_schema if field.name in table.column_names]).cast(target_schema=final_schema), existing_data])
                else:
                    files_to_replace = []
                    table = table.select([field.name for field in final_schema if field.name in table.column_names]).cast(target_schema=final_schema)

            except Exception as e:
                logging.error(f"Schema validation/mergine failed: {e}")
                raise e
        else:
            table = table.cast(target_schema=final_schema)

        os.makedirs(root_path, exist_ok=True)
        pq.write_to_dataset(
            table,
            root_path=root_path,
            partition_cols=partition_cols,
            schema=final_schema,
            existing_data_behavior=kwargs.pop('existing_data_behavior', 'overwrite_or_ignore'),
            **kwargs,
        )
        for f in files_to_replace:
            if os.path.exists(f):
                os.remove(f)

        if not os.path.exists(config_path) or overwrite_config or schema_modified:
            XSer.safe_dump(obj=og_config, target='json', out_fp=config_path)
            pq.write_metadata(final_schema, where=os.path.join(root_path, "_common_metadata"))

    def to_csv(
        self,
        fp: str | Path,
        signed: bool = False,
        encryption_key: Optional[bytes] = None,
        encryption_password: Optional[str] = None,
        signature_header: Optional[Any] = None,
        signature_as_comment: bool = False,
        **kwargs
    ):
        """
        Write the DataFrame to a CSV file.

        Parameters
        ----------
        fp : str | Path
            The file path to write the CSV to.
        write_header : bool, optional
            If True (default), include dtype information as a comment header.
        signed : bool, optional
            If True, write as a signed file with cryptographic integrity verification.
            Default is False.
        encryption_key : bytes, optional
            Fernet encryption key. Implies signed=True.
        encryption_password : str, optional
            Password for encryption. Implies signed=True.
        signature_header : Any, optional
            Optional metadata to store in the signed file header.
        signature_as_comment : bool, optional
            If True and signed, write signature as a comment line readable by
            standard CSV readers. Cannot be used with encryption. Default is False.
        **kwargs : keyword arguments
            Additional arguments passed to the Polars CSV writer.
        """
        # Encryption implies signing
        if encryption_key is not None or encryption_password is not None:
            signed = True

        if signed:
            df = cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)
            buffer = io_module.BytesIO()

            if not signature_header:
                signature_header = {}
            else:
                signature_header = {'header': signature_header}
            
            signature_header['dtypes'] = json.dumps({k: str(v) for k, v in df.schema.items()})

            df.write_csv(buffer, **kwargs)

            SignedFile.write(
                path=fp,
                data=buffer.getvalue(),
                encryption_key=encryption_key,
                encryption_password=encryption_password,
                signature_as_comment=signature_as_comment,
                header=signature_header
            )

        elif self.is_lazy:
            cast(pl.LazyFrame, self._df).sink_csv(fp, **kwargs)
        else:
            cast(pl.DataFrame, self._df).write_csv(fp, **kwargs)

    def to_parquet(
        self,
        fp: str | Path,
        partition_cols: Optional[List[str] | str] = None,
        signed: bool = False,
        encryption_key: Optional[bytes] = None,
        encryption_password: Optional[str] = None,
        signature_header: Optional[Any] = None,
        **kwargs
    ):
        """
        Write the DataFrame to a Parquet file.

        Parameters
        ----------
        fp : str | Path
            The file path to write the Parquet to.
        partition_cols : List[str] | str, optional
            Column(s) to partition by. If provided, writes a partitioned dataset.
        signed : bool, optional
            If True, write as a signed file with cryptographic integrity verification.
            Default is False. Not compatible with partition_cols or lazy sink.
        encryption_key : bytes, optional
            Fernet encryption key. Implies signed=True.
        encryption_password : str, optional
            Password for encryption. Implies signed=True.
        signature_header : Any, optional
            Optional metadata to store in the signed file header.
        **kwargs : keyword arguments
            Additional arguments passed to the Polars Parquet writer.
        """
        # Encryption implies signing
        if encryption_key is not None or encryption_password is not None:
            signed = True

        if signed:
            if partition_cols is not None:
                raise ValueError("signed=True is not compatible with partition_cols")

            df = cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)
            buffer = io_module.BytesIO()
            df.write_parquet(buffer, **kwargs)

            SignedFile.write(
                path=fp,
                data=buffer.getvalue(),
                encryption_key=encryption_key,
                encryption_password=encryption_password,
                header=signature_header
            )
        elif isinstance(partition_cols, (str, list)):
            self.to_partitioned_parquet(fp, partition_cols=partition_cols, **kwargs)
        elif self.is_lazy:
            cast(pl.LazyFrame, self._df).sink_parquet(fp, **kwargs)
        else:
            cast(pl.DataFrame, self._df).write_parquet(fp, **kwargs)

    def to_ipc(
        self,
        fp: str | Path,
        stream: bool = False,
        signed: bool = False,
        encryption_key: Optional[bytes] = None,
        encryption_password: Optional[str] = None,
        signature_header: Optional[Any] = None,
        **kwargs
    ):
        """
        Write the DataFrame to an IPC (Arrow) file.

        Parameters
        ----------
        fp : str | Path
            The file path to write the IPC file to.
        stream : bool, optional
            If True, write as IPC stream format. Default is False.
        signed : bool, optional
            If True, write as a signed file with cryptographic integrity verification.
            Default is False. Not compatible with lazy sink.
        encryption_key : bytes, optional
            Fernet encryption key. Implies signed=True.
        encryption_password : str, optional
            Password for encryption. Implies signed=True.
        signature_header : Any, optional
            Optional metadata to store in the signed file header.
        **kwargs : keyword arguments
            Additional arguments passed to the Polars IPC writer.
        """
        # Encryption implies signing
        if encryption_key is not None or encryption_password is not None:
            signed = True

        if signed:
            df = cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)
            buffer = io_module.BytesIO()

            if stream:
                df.write_ipc_stream(buffer, **kwargs)
            else:
                df.write_ipc(buffer, **kwargs)

            SignedFile.write(
                path=fp,
                data=buffer.getvalue(),
                encryption_key=encryption_key,
                encryption_password=encryption_password,
                header=signature_header
            )
        elif stream:
            (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).write_ipc_stream(fp, **kwargs)
        elif self.is_lazy:
            cast(pl.LazyFrame, self._df).sink_ipc(fp, **kwargs)
        else:
            cast(pl.DataFrame, self._df).write_ipc(fp, **kwargs)

    def to_avro(self,
                fp: str | Path,
                **kwargs):

        (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).write_avro(fp, **kwargs)

    def to_excel(self,
                 fp: str | Path,
                 **kwargs):

        (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).write_excel(fp, **kwargs)

    def to_ndjson(self,
                  fp: str | Path,
                  **kwargs):

        if self.is_lazy:
            cast(pl.LazyFrame, self._df).sink_ndjson(fp, **kwargs)
        else:
            cast(pl.DataFrame, self._df).write_ndjson(fp, **kwargs)

    def to_json(self,
                fp: str | Path,
                **kwargs):

         (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).write_json(fp, **kwargs)

    def to_hdf(self,
               fp: str | Path,
               **kwargs):
       (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).to_pandas().to_hdf(fp, **kwargs)

    def to_pandas(self) -> pd.DataFrame:
        return (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).to_pandas()

    def to_numpy(self) -> np.ndarray:
        return (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).to_numpy()

    def to_arrow(self) -> pa.Table:
        return (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).to_arrow()

    def to_list(self) -> list:
        return self.to_numpy().tolist()

    def to_dict(self, **kwargs) -> dict:
        return (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).to_dict(**kwargs)

    def to_delta(self,
                 fp: str | Path,
                 **kwargs):
        (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).write_delta(fp, **kwargs)

    def to_records(self, **kwargs) -> pl.Series:
        return (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).to_series(**kwargs)

    def to_iceberg(self,
                  fp: str | Path,
                  **kwargs):
        (cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)).write_iceberg(fp, **kwargs)

    # =========================================================================
    # Signed File Utilities
    # =========================================================================

    @staticmethod
    def verify_signed_file(
        fp: str | Path,
        decryption_key: Optional[bytes] = None,
        decryption_password: Optional[str] = None
    ) -> bool:
        """
        Verify the cryptographic integrity of a signed file.

        Parameters
        ----------
        fp : str | Path
            Path to the signed file.
        decryption_key : bytes, optional
            Fernet decryption key for encrypted files.
        decryption_password : str, optional
            Password for encrypted files.

        Returns
        -------
        bool
            True if verification succeeds.

        Raises
        ------
        ValueError
            If verification fails due to corruption, tampering, or wrong key.
        """
        return SignedFile.verify(
            path=fp,
            decryption_key=decryption_key,
            decryption_password=decryption_password
        )

    @staticmethod
    def _parse_dtype_string(dtype_str: str) -> pl.DataType:
        """
        Parse a dtype string back to a Polars DataType.

        Parameters
        ----------
        dtype_str : str
            String representation of a Polars dtype (e.g., "Int64", "String").

        Returns
        -------
        pl.DataType
            The corresponding Polars data type.
        """
        dtype_mapping: Dict[str, pl.DataType] = {
            "Int8": pl.Int8(),
            "Int16": pl.Int16(),
            "Int32": pl.Int32(),
            "Int64": pl.Int64(),
            "UInt8": pl.UInt8(),
            "UInt16": pl.UInt16(),
            "UInt32": pl.UInt32(),
            "UInt64": pl.UInt64(),
            "Float32": pl.Float32(),
            "Float64": pl.Float64(),
            "Boolean": pl.Boolean(),
            "String": pl.String(),
            "Utf8": pl.Utf8(),
            "Date": pl.Date(),
            "Time": pl.Time(),
            "Null": pl.Null(),
            "Binary": pl.Binary(),
        }

        if dtype_str in dtype_mapping:
            return dtype_mapping[dtype_str]

        # Handle Datetime with timezone
        if dtype_str.startswith("Datetime"):
            import re
            tu_match = re.search(r"time_unit='([^']+)'", dtype_str)
            tu: TimeUnit = cast(TimeUnit, tu_match.group(1)) if tu_match else "us"

            if "time_zone=" in dtype_str and "time_zone=None" not in dtype_str:
                tz_match = re.search(r"time_zone='([^']+)'", dtype_str)
                tz = tz_match.group(1) if tz_match else None
                return pl.Datetime(time_unit=tu, time_zone=tz)
            else:
                return pl.Datetime(time_unit=tu)

        # Handle Duration
        if dtype_str.startswith("Duration"):
            import re
            tu_match = re.search(r"time_unit='([^']+)'", dtype_str)
            tu = cast(TimeUnit, tu_match.group(1)) if tu_match else "us"
            return pl.Duration(time_unit=tu)

        # Default to String for unknown types
        return pl.String()
