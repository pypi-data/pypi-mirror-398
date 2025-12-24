"""
Polars SQL Extension Module

This module provides high-performance SQL database upload functionality for Polars DataFrames.
It includes optimized bulk insert operations, automatic table creation, and intelligent data type mapping
across multiple database dialects.

Key Features:
- High-performance bulk inserts with chunking and batching
- Automatic table creation using SQL specifications
- Intelligent data type conversion and validation
- Support for multiple SQL dialects (Oracle, PostgreSQL, SQL Server, MySQL, SQLite)
- Comprehensive error handling and transaction management
- Memory-efficient processing for large datasets

Author: DataScience_ToolBox
Created: July 2025
Version: 2.0.0 - Refactored for native Polars support
License: MIT
"""

from typing import Tuple, Dict, Any, Literal, Optional, List, Callable, Union, cast, Iterator, TYPE_CHECKING
import re
from math import ceil
import time

import polars as pl

# SQLUtilities is an optional dependency
try:
    from sqlutilities import DatabaseConnection, SQLDialect, COLUMNDTYPE, SQL_TABLE
    SQLUTILITIES_AVAILABLE = True
except ImportError:
    SQLUTILITIES_AVAILABLE = False
    # Define placeholder types for type checking when sqlutilities is not installed
    DatabaseConnection = None  # type: ignore
    SQLDialect = None  # type: ignore
    COLUMNDTYPE = None  # type: ignore
    SQL_TABLE = None  # type: ignore

if TYPE_CHECKING:
    from sqlutilities import DatabaseConnection, SQLDialect, COLUMNDTYPE, SQL_TABLE

from .base import UniversalPolarsDataFrameExtension
from .epl import EnhancedPolars

# Import tqdm for progress bars with fallback
try:
    from tqdm import tqdm as TqdmClass  # type: ignore
    TQDM_AVAILABLE = True
except ImportError:
    class TqdmClass:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.total = kwargs.get('total', 0)
            self.n = 0
        def update(self, n=1):
            self.n += n
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    TQDM_AVAILABLE = False

# Configure logging with fallback
from CoreUtilities import get_logger, LogLevel
logger = get_logger(
    'polars_to_sql',
    level=LogLevel.INFO,
    include_performance=True,
    include_emoji=True
)

def log_with_emoji(level: str, message: str, emoji: str = "") -> None:
    if hasattr(logger, level):
        getattr(logger, level)(message, emoji=emoji)
    else:
        getattr(logger, level)(message)


class PolarsSQLExtension(UniversalPolarsDataFrameExtension):
    """
    High-performance SQL upload extension for Polars DataFrames.

    This extension provides optimized database upload functionality with automatic
    table creation, intelligent data type mapping, and bulk insert operations
    optimized for different database dialects.

    Inherits from UniversalPolarsDataFrameExtension to leverage standard
    DataFrame properties like height, length, columns, schema, and is_lazy.
    """

    def __init__(self, df: pl.DataFrame | pl.LazyFrame):
        super().__init__(df)

    def _iter_chunks(
        self,
        chunk_size: int,
        total_rows: int
    ) -> Iterator[pl.DataFrame]:
        """
        Yield chunks of data, collecting lazily for LazyFrames.

        For LazyFrames, only one chunk is materialized in memory at a time,
        preventing OOM errors for large datasets.

        Parameters
        ----------
        chunk_size : int
            Number of rows per chunk.
        total_rows : int
            Total number of rows to process.

        Yields
        ------
        pl.DataFrame
            Chunks of the DataFrame.
        """
        n_chunks = (total_rows + chunk_size - 1) // chunk_size

        for i in range(n_chunks):
            start_idx = i * chunk_size
            rows_in_chunk = min(chunk_size, total_rows - start_idx)

            if self.is_lazy:
                # For LazyFrame: collect only this chunk
                lf = cast(pl.LazyFrame, self._df)
                yield lf.slice(start_idx, rows_in_chunk).collect()
            else:
                # For DataFrame: slice without full copy
                df = cast(pl.DataFrame, self._df)
                yield df.slice(start_idx, rows_in_chunk)

    def to_sql(
        self,
        connection: DatabaseConnection, # type: ignore
        table_name: str,
        schema_name: Optional[str] = None,
        if_exists: Literal['fail', 'replace', 'append'] = 'append',
        chunk_size: Optional[int] = None,
        method: Literal['auto', 'bulk', 'batch', 'single'] = 'auto',
        primary_key: Optional[Union[str, List[str]]] = None,
        identity_column: Optional[str] = None,
        identity_seed: int = 1,
        identity_increment: int = 1,
        non_nullable: Optional[Union[str, List[str]]] = None,
        infer_specific: bool = True,
        downcast_floats: bool = True,
        safety_threshold: Optional[float] = None,
        use_fixed_char_length: bool = False,
        timezone_aware: bool = True,
        min_char_bytes: int = 1,
        time_precision: Literal['second', 'millisecond', 'microsecond', 'nanosecond', 'ms', 'us', 'ns', 'auto'] = 'second',
        on_conflict: Optional[str] = None,
        validate_data: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        show_progress: bool = True,
        sample_rows: Optional[int] = None,
        inference_confidence: float = 1.0,
        use_native: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Upload Polars DataFrame to SQL database with high-performance bulk operations.

        This method provides optimized database upload with automatic table creation,
        intelligent data type mapping, and efficient bulk insert operations tailored
        for different database dialects.

        Parameters
        ----------
        connection : DatabaseConnection
            Active database connection using RobustConnection for transaction management.
        table_name : str
            Name of the target database table.
        schema_name : str, optional
            Database schema name. If None, uses connection default.
        if_exists : {'fail', 'replace', 'append'}, default 'append'
            How to behave if the table already exists:
            - 'fail': Raise a ValueError if table exists
            - 'replace': Drop the table before creating (recreate)
            - 'append': Append data to existing table or create if not exists
        chunk_size : int, optional
            Number of rows to insert per batch. If None, uses dialect-optimized defaults.
        method : {'auto', 'bulk', 'batch', 'single'}, default 'auto'
            Insert method to use:
            - 'auto': Automatically select best method based on dialect and data size
            - 'bulk': Use bulk insert operations (fastest for large datasets)
            - 'batch': Use batched inserts with prepared statements
            - 'single': Insert rows individually (slowest, most compatible)
        primary_key : str or List[str], optional
            Column name(s) to be designated as primary key(s).
        identity_column : str, optional
            Column name to be designated as identity/autoincrement column.
        identity_seed : int, default 1
            Starting value for identity/autoincrement column.
        identity_increment : int, default 1
            Increment value for identity/autoincrement column.
        non_nullable : str or List[str], optional
            Column name(s) that should be marked as NOT NULL.
        infer_specific : bool, default True
            Whether to perform detailed data analysis for optimal SQL types.
        downcast_floats : bool, default True
            Whether to downcast floating-point types when possible to save space.
        safety_threshold : float, optional
            Safety margin for numeric precision calculations (0.0-1.0).
        use_fixed_char_length : bool, default False
            Whether to use fixed-length character types (CHAR vs VARCHAR).
        timezone_aware : bool, default True
            Whether datetime types should include timezone information.
        min_char_bytes : int, default 1
            Minimum number of bytes to allocate for character columns.
        time_precision : str, default 'second'
            Precision level for time-based data types.
        on_conflict : str, optional
            Conflict resolution strategy for primary key violations.
        validate_data : bool, default True
            Whether to validate data types and convert before insertion.
        progress_callback : callable, optional
            Callback function to report upload progress.
        show_progress : bool, default True
            Whether to display a tqdm progress bar during data upload.
        sample_rows : int, optional
            Number of rows to use for SQL type inference.
        inference_confidence : float, default 1.0
            Confidence level for type inference (0.0-1.0). Lower values sample fewer
            rows for faster inference at the cost of accuracy.
        use_native : bool, default False
            If True, use Polars' native `write_database` method wrapped in a transaction
            for safety. This is faster but provides less control over type mapping and
            table creation. When True, most other parameters are ignored except
            connection, table_name, schema_name, and if_exists.
        **kwargs
            Additional arguments passed to the transaction manager (or to Polars'
            write_database when use_native=True).

        Returns
        -------
        Dict[str, Any]
            Upload statistics and results.

        Examples
        --------
        >>> import polars as pl
        >>> df = pl.DataFrame({
        ...     'id': [1, 2, 3],
        ...     'name': ['Alice', 'Bob', 'Charlie'],
        ...     'salary': [50000.50, 60000.75, 55000.00]
        ... })
        >>> result = df.epl.to_sql(
        ...     connection=conn,
        ...     table_name='employees',
        ...     schema_name='hr',
        ...     if_exists='replace',
        ...     primary_key='id'
        ... )
        """
        # Check if sqlutilities is available
        if not SQLUTILITIES_AVAILABLE:
            raise ImportError(
                "sqlutilities is required for SQL operations but is not installed. "
                "Install it with: pip install sqlutilities"
            )

        start_time = time.time()

        # Handle native Polars write_database path
        if use_native:
            return self._execute_native_write(
                connection=connection,
                table_name=table_name,
                schema_name=schema_name,
                if_exists=if_exists,
                start_time=start_time,
                **kwargs
            )

        # Validate all input parameters
        self._validate_upload_parameters(connection, table_name, method, chunk_size)

        # Get dialect information
        dialect = connection.dialect
        log_with_emoji('info', f"Starting SQL upload to {dialect.name_value} database", "🚀")

        # Get height using the base class property (works for both DataFrame and LazyFrame)
        total_rows = self.height

        # Handle empty DataFrame case
        if total_rows == 0:
            log_with_emoji('warning', "DataFrame is empty, nothing to upload", "⚠️")
            return self._create_empty_result()

        # Determine optimal chunk size and method
        if chunk_size is None:
            chunk_size = self._get_optimal_chunk_size(connection, total_rows, method)

        if method == 'auto':
            method = self._get_optimal_method(connection, total_rows)  # type: ignore

        log_with_emoji('info', f"Using method: {method}, chunk_size: {chunk_size}", "⚙️")

        # Create SQL_TABLE instance to check table existence
        sql_table = SQL_TABLE(table_name=table_name, connection=connection, schema=schema_name) # type: ignore
        table_exists = sql_table.exists()

        # Determine if we need to generate SQL specification
        skip_sql_spec = if_exists == 'append' and table_exists

        if skip_sql_spec:
            log_with_emoji('info', f"Table {sql_table.full_table_name} exists, skipping SQL specification generation for append mode", "⏭️")
            sql_table.populate_definition_from_existing()
            log_with_emoji('info', "Populated table definition with existing column information", "✅")
            table_created = False
            table_replaced = False
        else:
            # Generate SQL table specification
            # For LazyFrames, this analyzes each column individually without collecting the entire dataset
            log_with_emoji('info', "Generating SQL table specification", "📋")

            if sample_rows is not None and sample_rows > 0 and total_rows > sample_rows:
                log_with_emoji('info', f"Using sample of {sample_rows} rows for type inference (out of {total_rows} total rows)", "🎯")

            sql_spec = self._get_sql_specification(
                dialect=dialect,
                table_name=table_name,
                schema_name=schema_name,
                primary_key=primary_key,
                identity_column=identity_column,
                identity_seed=identity_seed,
                identity_increment=identity_increment,
                non_nullable=non_nullable,
                infer_specific=infer_specific,
                downcast_floats=downcast_floats,
                safety_threshold=safety_threshold,
                use_fixed_char_length=use_fixed_char_length,
                timezone_aware=timezone_aware,
                min_char_bytes=min_char_bytes,
                time_precision=time_precision,
                sample_rows=sample_rows,
                inference_confidence=inference_confidence
            )

            # Create table using SQL_TABLE's built-in if_exists functionality
            log_with_emoji('info', f"Creating/managing table {sql_table.full_table_name}", "🏗️")
            create_result = sql_table.create_table_from_dataframe(
                df=sql_spec.to_pandas(),
                if_exists=if_exists
            )

            table_created = bool(create_result) if if_exists != 'replace' else True
            table_replaced = if_exists == 'replace'

        # Execute the appropriate insert strategy
        # For LazyFrames, this iterates through chunks, collecting one at a time
        try:
            rows_inserted, chunks_processed = self._execute_insert_strategy(
                sql_table=sql_table,
                method=method,
                chunk_size=chunk_size,
                total_rows=total_rows,
                on_conflict=on_conflict,
                progress_callback=progress_callback,
                dialect=dialect,
                show_progress=show_progress,
                validate_data=validate_data
            )
        except Exception as e:
            log_with_emoji('error', f"Data insertion failed: {str(e)}", "💥")
            raise RuntimeError(f"Data insertion failed: {str(e)}")

        # Calculate performance metrics and gather results
        execution_time, insert_rate = self._calculate_performance_metrics(start_time, rows_inserted)
        table_info = self._get_table_info_safely(sql_table)

        # Create and return results
        results = self._create_results_dict(
            rows_inserted, total_rows, table_created, table_replaced,
            chunks_processed, execution_time, insert_rate, method, chunk_size, table_info
        )

        log_with_emoji(
            'info',
            f"Upload completed: {rows_inserted}/{total_rows} rows in {execution_time:.2f}s "
            f"({insert_rate:.0f} rows/sec)",
            "🎉"
        )

        return results

    def _get_sql_specification(
        self,
        dialect: SQLDialect, # type: ignore
        table_name: str,
        schema_name: Optional[str] = None,
        primary_key: Optional[Union[str, List[str]]] = None,
        identity_column: Optional[str] = None,
        identity_seed: int = 1,
        identity_increment: int = 1,
        non_nullable: Optional[Union[str, List[str]]] = None,
        infer_specific: bool = True,
        downcast_floats: bool = False,
        safety_threshold: Optional[float] = None,
        use_fixed_char_length: bool = False,
        timezone_aware: bool = True,
        min_char_bytes: int = 1,
        time_precision: Literal['second', 'millisecond', 'microsecond', 'nanosecond', 'ms', 'us', 'ns', 'auto'] = 'second',
        sample_rows: Optional[int] = None,
        inference_confidence: float = 1.0
    ) -> pl.DataFrame:
        """
        Generate SQL table specification from the DataFrame/LazyFrame.

        Uses EnhancedPolars.infer_dtypes to analyze columns. For LazyFrames, this
        collects each column individually, avoiding materializing the entire dataset
        into memory at once.

        Parameters
        ----------
        dialect : SQLDialect
            Target SQL database dialect.
        table_name : str
            Name of the target database table.
        schema_name : str, optional
            Database schema name.
        primary_key : str or List[str], optional
            Column name(s) for primary key.
        identity_column : str, optional
            Column name for identity/autoincrement.
        identity_seed : int, default 1
            Starting value for identity column.
        identity_increment : int, default 1
            Increment value for identity column.
        non_nullable : str or List[str], optional
            Columns that should be NOT NULL.
        infer_specific : bool, default True
            Whether to infer specific SQL types.
        downcast_floats : bool, default False
            Whether to downcast floats.
        safety_threshold : float, optional
            Safety margin for precision.
        use_fixed_char_length : bool, default False
            Whether to use CHAR instead of VARCHAR.
        timezone_aware : bool, default True
            Whether datetime should include timezone.
        min_char_bytes : int, default 1
            Minimum bytes for character columns.
        time_precision : str, default 'second'
            Precision for time types.
        sample_rows : int, optional
            Number of rows to sample for type inference. If None, analyzes all rows.

        Returns
        -------
        pl.DataFrame
            Specification DataFrame with columns: FieldName, Datatype, SchemaName,
            TableName, isRequired, isPrimaryKey, isIdentity, identitySeed, identityIncrement
        """
        # Use EnhancedPolars.infer_dtypes for type analysis
        # This handles LazyFrames by collecting columns individually
        col_metadata = cast(Dict[str, Any], EnhancedPolars.infer_dtypes(
            self._df,
            attempt_downcast=downcast_floats,
            attempt_numeric_to_datetime=False,
            confidence=inference_confidence,
            n=sample_rows,
            sample_strat='first' if sample_rows else 'random',
            collect_precision_scale=infer_specific,
            return_df=False  # Returns Dict[str, Any]
        ))

        # Map metadata to SQL types using COLUMNDTYPE.get_optimal_type_for_data
        dtype_dict: Dict[str, str] = {}
        for col_name, meta in col_metadata.items():
            # Get the inferred core type
            inferred_meta = meta.get('inferred_meta', meta)
            core_type = inferred_meta.get('core_data_type')

            # Get optimal COLUMNDTYPE based on metadata
            optimal_dtype, size_spec = COLUMNDTYPE.get_optimal_type_for_data( # type: ignore
                core_type=core_type,
                dialect=dialect,
                min_value=meta.get('min_value'),
                max_value=meta.get('max_value'),
                precision=meta.get('precision'),
                scale=meta.get('scale'),
                max_length=meta.get('max_byte_length'),
                timezone_aware=timezone_aware,
                use_fixed_length=use_fixed_char_length,
                safety_threshold=safety_threshold,
                time_precision=time_precision,
                min_char_bytes=min_char_bytes
            )

            # Convert to SQL string
            dtype_dict[col_name] = COLUMNDTYPE.to_sql_string( # type: ignore
                datatype=optimal_dtype,
                target_dialect=dialect,
                size_spec=size_spec
            )

        # Create specification DataFrame
        field_names = list(dtype_dict.keys())
        datatypes = list(dtype_dict.values())

        base = pl.DataFrame({
            'FieldName': field_names,
            'Datatype': datatypes,
            'SchemaName': [schema_name] * len(field_names),
            'TableName': [table_name] * len(field_names),
            'isRequired': [False] * len(field_names),
            'userGuidance': [None] * len(field_names),
            'isPrimaryKey': [False] * len(field_names),
            'isIdentity': [False] * len(field_names),
            'identitySeed': [None] * len(field_names),
            'identityIncrement': [None] * len(field_names)
        })

        # Process primary key and non-nullable columns
        pkl: List[str] = primary_key if isinstance(primary_key, list) else [primary_key] if isinstance(primary_key, str) else []
        nnl: List[str] = non_nullable if isinstance(non_nullable, list) else [non_nullable] if isinstance(non_nullable, str) else []

        # Update isRequired for non-nullable and primary key columns
        nn_fields = pkl + nnl
        if nn_fields:
            base = base.with_columns(
                pl.when(pl.col('FieldName').is_in(nn_fields))
                .then(pl.lit(True))
                .otherwise(pl.col('isRequired'))
                .alias('isRequired')
            )

        # Update isPrimaryKey
        if pkl:
            base = base.with_columns(
                pl.when(pl.col('FieldName').is_in(pkl))
                .then(pl.lit(True))
                .otherwise(pl.col('isPrimaryKey'))
                .alias('isPrimaryKey')
            )

        # Handle identity column
        if identity_column:
            if identity_column in field_names:
                base = base.with_columns([
                    pl.when(pl.col('FieldName') == identity_column)
                    .then(pl.lit(True))
                    .otherwise(pl.col('isIdentity'))
                    .alias('isIdentity'),
                    pl.when(pl.col('FieldName') == identity_column)
                    .then(pl.lit(True))
                    .otherwise(pl.col('isRequired'))
                    .alias('isRequired'),
                    pl.when(pl.col('FieldName') == identity_column)
                    .then(pl.lit(identity_seed))
                    .otherwise(pl.col('identitySeed'))
                    .alias('identitySeed'),
                    pl.when(pl.col('FieldName') == identity_column)
                    .then(pl.lit(identity_increment))
                    .otherwise(pl.col('identityIncrement'))
                    .alias('identityIncrement')
                ])
            else:
                # Identity column doesn't exist, add it
                identity_datatype = self._get_identity_datatype(dialect)
                identity_row = pl.DataFrame({
                    'FieldName': [identity_column],
                    'Datatype': [identity_datatype],
                    'SchemaName': [schema_name],
                    'TableName': [table_name],
                    'isRequired': [True],
                    'userGuidance': [None],
                    'isPrimaryKey': [identity_column in pkl],
                    'isIdentity': [True],
                    'identitySeed': [identity_seed],
                    'identityIncrement': [identity_increment]
                })
                base = pl.concat([identity_row, base])

        return base

    def _get_identity_datatype(self, dialect: SQLDialect) -> str: # type: ignore
        """Get the appropriate identity column datatype for the dialect."""
        dialect_name = dialect.name_value.upper()
        if dialect_name in ['POSTGRESQL', 'POSTGRES']:
            return 'SERIAL'
        elif dialect_name == 'ORACLE':
            return 'NUMBER'
        else:
            return 'INTEGER'

    def _prepare_data_for_insertion(
        self,
        df: pl.DataFrame,
        sql_table: Any,
        dialect: SQLDialect # type: ignore
    ) -> pl.DataFrame:
        """
        Prepare DataFrame for database insertion with type conversion.

        Parameters
        ----------
        df : pl.DataFrame
            Source DataFrame to prepare.
        sql_table : SQL_TABLE
            SQL table instance with column metadata.
        dialect : SQLDialect
            Target database dialect.

        Returns
        -------
        pl.DataFrame
            DataFrame prepared for database insertion.
        """
        log_with_emoji('info', "Preparing data for database insertion", "🔧")

        # Get column metadata from SQL_TABLE definition
        column_metadata = self._get_column_metadata_from_table(sql_table)

        # Build expressions for all columns - more efficient than extracting series
        formatted_exprs = [
            format_column_expr_for_sql(
                col_name=col_name,
                column_specification=str(column_metadata[col_name]),
                dialect=dialect
            ).alias(col_name) if col_name in column_metadata else pl.col(col_name)
            for col_name in df.columns
        ]

        result = df.select(formatted_exprs)

        log_with_emoji('info', f"Data preparation completed for {len(df.columns)} columns", "✅")
        return result

    def _get_column_metadata_from_table(self, sql_table: Any) -> Dict[str, COLUMNDTYPE]: # type: ignore
        """Extract COLUMNDTYPE metadata from SQL_TABLE's definition."""
        column_metadata = {}
        if hasattr(sql_table, 'definition') and hasattr(sql_table.definition, 'columns'):
            for column_def in sql_table.definition.columns:
                if hasattr(column_def, 'name') and hasattr(column_def, 'data_type'):
                    column_metadata[column_def.name] = column_def.data_type
        return column_metadata

    def _validate_upload_parameters(
        self,
        connection: DatabaseConnection, # type: ignore
        table_name: str,
        method: str,
        chunk_size: Optional[int]
    ) -> None:
        """Validate upload parameters and raise appropriate errors."""
        # Check if the connection is a DatabaseConnection from the sqlutilities package. This will simultananously check its type and prevent it from being accessed if not imported.
        if not callable(getattr(connection, "_retrieve_credentials_from_secrets", None)):
            raise ValueError("connection must be a DatabaseConnection instance")

        if not hasattr(connection, 'is_connected') or not connection.is_connected:
            raise RuntimeError("Database connection is not active")

        if not table_name or not isinstance(table_name, str):
            raise ValueError("table_name must be a non-empty string")

        if len(table_name.strip()) == 0:
            raise ValueError("table_name cannot be empty or whitespace only")

        valid_methods = ['auto', 'bulk', 'batch', 'single']
        if method not in valid_methods:
            raise ValueError(f"method must be one of {valid_methods}, got '{method}'")

        if chunk_size is not None and (not isinstance(chunk_size, int) or chunk_size <= 0):
            raise ValueError("chunk_size must be a positive integer")

    def _get_optimal_chunk_size(
        self,
        connection: DatabaseConnection, # type: ignore
        total_rows: int,
        method: str
    ) -> int:
        """Determine optimal chunk size from connection's driver info."""
        driver_info = connection.current_driver
        base_size = driver_info.get('optimal_chunk_size', 1000) if driver_info else 1000

        if method == 'single':
            return 1
        elif method == 'bulk' and total_rows > 100000:
            return min(base_size * 2, 10000)
        elif method == 'batch' and total_rows < 1000:
            return min(base_size, max(total_rows // 4, 10))
        else:
            return base_size

    def _get_optimal_method(
        self,
        connection: DatabaseConnection, # type: ignore
        total_rows: int
    ) -> Literal['bulk', 'batch', 'single']:
        """Determine optimal insert method based on driver info and data size."""
        driver_info = connection.current_driver
        # Use driver's optimal_chunk_size as batch_max threshold heuristic
        batch_max = driver_info.get('optimal_chunk_size', 5000) * 2 if driver_info else 10000

        if total_rows <= 1:
            return 'single'
        elif total_rows <= batch_max:
            return 'batch'
        else:
            return 'bulk'

    def _execute_insert_strategy(
        self,
        sql_table: Any,
        method: str,
        chunk_size: int,
        total_rows: int,
        on_conflict: Optional[str],
        progress_callback: Optional[Callable[[int, int], None]],
        dialect: Optional[SQLDialect], # type: ignore
        show_progress: bool,
        validate_data: bool = True
    ) -> Tuple[int, int]:
        """
        Execute the appropriate insert strategy based on method.

        For LazyFrames, chunks are collected one at a time to avoid
        materializing the entire dataset into memory.
        """
        method_configs = {
            'bulk': {'emoji': '⚡', 'description': 'bulk insert method'},
            'batch': {'emoji': '📦', 'description': 'batch insert method'},
            'single': {'emoji': '🔄', 'description': 'single insert method'}
        }

        config = method_configs.get(method)
        if not config:
            raise ValueError(f"Unknown insert method: {method}")

        log_with_emoji('info', f"Using {config['description']}", config['emoji'])

        columns = self.columns
        rows_inserted = 0
        chunks_processed = 0

        # Prepare insert statement
        insert_statement = sql_table.prepare_insert_statement(
            columns=columns,
            insert_mode='insert'
        )

        actual_chunk_size = 1 if method == 'single' else chunk_size

        # Setup progress bar
        display_table_name = self._get_display_table_name(sql_table)
        progress_bar = None
        if show_progress and TQDM_AVAILABLE:
            progress_bar = TqdmClass(
                total=total_rows,
                desc=f"Uploading to {display_table_name}",
                unit="rows",
                unit_scale=True,
                leave=True
            )

        try:
            # Iterate through chunks - for LazyFrames, each chunk is collected individually
            for df_chunk in self._iter_chunks(actual_chunk_size, total_rows):
                # Validate and prepare data for insertion if requested
                if validate_data:
                    assert dialect is not None, "dialect is required for data validation"
                    df_chunk = self._prepare_data_for_insertion(df_chunk, sql_table, dialect=dialect)

                # Convert chunk to list of lists using rows() to preserve Python types
                # (datetime, bool, None) instead of to_numpy().tolist() which loses type info
                chunk_data = [list(row) for row in df_chunk.rows()]

                try:
                    chunk_rows_inserted = self._process_chunk(
                        method=method,
                        sql_table=sql_table,
                        chunk_data=chunk_data,
                        columns=columns,
                        insert_statement=insert_statement,
                        on_conflict=on_conflict,
                        dialect=dialect
                    )

                    rows_inserted += chunk_rows_inserted
                    chunks_processed += 1

                    if progress_bar:
                        progress_bar.update(chunk_rows_inserted)

                    if progress_callback:
                        progress_callback(rows_inserted, total_rows)

                except Exception as e:
                    method_name = config['description'].replace(' method', '')
                    log_with_emoji('error', f"{method_name.title()} insert failed for chunk {chunks_processed + 1}: {str(e)}", "💥")
                    raise

        finally:
            if progress_bar:
                progress_bar.close()

        return rows_inserted, chunks_processed

    def _process_chunk(
        self,
        method: str,
        sql_table: Any,
        chunk_data: List[List[Any]],
        columns: List[str],
        insert_statement: Optional[Dict],
        on_conflict: Optional[str],
        dialect: Optional[SQLDialect] # type: ignore
    ) -> int:
        """Unified chunk processor for all insert methods."""
        if not insert_statement:
            insert_statement = sql_table.prepare_insert_statement(
                columns=columns,
                insert_mode='insert'
            )

        if not insert_statement:
            raise ValueError(f"Failed to prepare insert statement for {method} method")

        insert_sql = insert_statement['sql']

        if method == 'bulk':
            inserted = sql_table.connection.bulk_insert(
                sql=insert_sql,
                data=chunk_data,
                chunk_size=None,
                on_conflict=on_conflict
            )
            return inserted

        elif method == 'batch':
            parameter_style = insert_statement.get('parameter_style', 'format')
            formatted_data = self._format_data_for_parameters(chunk_data, columns, parameter_style, dialect)
            sql_table.connection.execute_many(insert_sql, formatted_data)
            return len(formatted_data)

        elif method == 'single':
            parameter_style = insert_statement.get('parameter_style', 'format')
            rows_inserted = 0
            for row_values in chunk_data:
                formatted_params = self._format_data_for_parameters([row_values], columns, parameter_style, dialect)
                if formatted_params:
                    sql_table.connection.execute_query(insert_sql, formatted_params[0] if isinstance(formatted_params, list) else formatted_params)
                    rows_inserted += 1
            return rows_inserted

        else:
            raise ValueError(f"Unknown insert method: {method}")

    def _format_data_for_parameters(
        self,
        data: List[List[Any]],
        columns: List[str],
        parameter_style: str,
        dialect: Optional[SQLDialect] # type: ignore
    ) -> List[Union[Dict[str, Any], Tuple[Any, ...]]]:
        """Format data for database driver consumption."""
        if not data:
            return []

        use_dict = False
        if dialect and hasattr(dialect, 'parameter_format_preference'):
            if dialect.parameter_format_preference == 'dict':  # type: ignore
                use_dict = True
        elif parameter_style in ('named', 'pyformat'):
            use_dict = True

        if use_dict:
            return [dict(zip(columns, row)) for row in data]
        else:
            return [tuple(row) for row in data]

    def _get_display_table_name(self, sql_table: Any) -> str:
        """Extract just the table name for display purposes."""
        table_name = getattr(sql_table, 'table_name', 'unknown')
        if '.' in table_name:
            table_name = table_name.split('.')[-1]
        table_name = table_name.strip('"').strip("'").strip('`').strip('[').strip(']')
        return table_name

    def _calculate_performance_metrics(self, start_time: float, rows_inserted: int) -> Tuple[float, float]:
        """Calculate execution time and insert rate."""
        execution_time = time.time() - start_time
        insert_rate = rows_inserted / execution_time if execution_time > 0 else 0
        return execution_time, insert_rate

    def _get_table_info_safely(self, sql_table: Any) -> Optional[Any]:
        """Safely retrieve table information with error handling."""
        try:
            return sql_table.get_table_info()
        except Exception as e:
            log_with_emoji('warning', f"Could not retrieve table info: {str(e)}", "⚠️")
            return None

    def _create_empty_result(self) -> Dict[str, Any]:
        """Create result dictionary for empty DataFrame case."""
        return {
            'rows_inserted': 0,
            'total_rows': 0,
            'table_created': False,
            'table_replaced': False,
            'chunks_processed': 0,
            'execution_time': 0.0,
            'insert_rate': 0.0,
            'method_used': 'none',
            'chunk_size_used': 0,
            'table_info': None
        }

    def _create_results_dict(
        self,
        rows_inserted: int,
        total_rows: int,
        table_created: bool,
        table_replaced: bool,
        chunks_processed: int,
        execution_time: float,
        insert_rate: float,
        method: str,
        chunk_size: int,
        table_info: Optional[Any]
    ) -> Dict[str, Any]:
        """Create the results dictionary with all upload statistics."""
        return {
            'rows_inserted': rows_inserted,
            'total_rows': total_rows,
            'table_created': table_created,
            'table_replaced': table_replaced,
            'chunks_processed': chunks_processed,
            'execution_time': execution_time,
            'insert_rate': insert_rate,
            'method_used': method,
            'chunk_size_used': chunk_size,
            'table_info': table_info
        }

    def _execute_native_write(
        self,
        connection: DatabaseConnection, # type: ignore
        table_name: str,
        schema_name: Optional[str],
        if_exists: Literal['fail', 'replace', 'append'],
        start_time: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute native Polars write_database wrapped in a transaction.

        This method provides a simpler, faster path using Polars' built-in
        write_database functionality while ensuring safety through transaction
        wrapping.

        Parameters
        ----------
        connection : DatabaseConnection
            Active database connection.
        table_name : str
            Name of the target database table.
        schema_name : str, optional
            Database schema name.
        if_exists : {'fail', 'replace', 'append'}
            How to behave if the table already exists.
        start_time : float
            Start time for performance tracking.
        **kwargs
            Additional arguments passed to Polars' write_database.

        Returns
        -------
        Dict[str, Any]
            Upload statistics and results.
        """
        log_with_emoji('info', "Using native Polars write_database method", "🔌")

        # Get total rows
        total_rows = self.height

        # Handle empty DataFrame
        if total_rows == 0:
            log_with_emoji('warning', "DataFrame is empty, nothing to upload", "⚠️")
            return self._create_empty_result()

        # Build the full table name
        full_table_name = f"{schema_name}.{table_name}" if schema_name else table_name

        # Build connection URI from DatabaseConnection (use connectorx_uri)
        connection_uri = connection.connectorx_uri

        # Collect DataFrame if lazy
        df = cast(pl.LazyFrame, self._df).collect() if self.is_lazy else cast(pl.DataFrame, self._df)

        # Execute within a transaction for safety using context manager
        try:
            with connection.transaction():
                # Use Polars native write_database
                df.write_database(
                    table_name=full_table_name,
                    connection=connection_uri,
                    if_table_exists=if_exists,
                    **kwargs
                )

            rows_inserted = total_rows
            log_with_emoji('info', f"Native write completed: {rows_inserted} rows", "✅")

        except Exception as e:
            log_with_emoji('error', f"Native write failed, transaction rolled back: {str(e)}", "💥")
            raise RuntimeError(f"Native write_database failed: {str(e)}")

        # Calculate performance metrics
        execution_time = time.time() - start_time
        insert_rate = rows_inserted / execution_time if execution_time > 0 else 0

        log_with_emoji(
            'info',
            f"Upload completed: {rows_inserted} rows in {execution_time:.2f}s "
            f"({insert_rate:.0f} rows/sec)",
            "🎉"
        )

        return {
            'rows_inserted': rows_inserted,
            'total_rows': total_rows,
            'table_created': if_exists in ('replace', 'fail'),
            'table_replaced': if_exists == 'replace',
            'chunks_processed': 1,
            'execution_time': execution_time,
            'insert_rate': insert_rate,
            'method_used': 'native',
            'chunk_size_used': total_rows,
            'table_info': None
        }


# ============================================================================
# Series-level helper functions
# ============================================================================

def format_column_expr_for_sql(
    col_name: str,
    column_specification: str,
    dialect: SQLDialect,  # noqa: ARG001 - kept for API consistency and future dialect-specific formatting  # type: ignore
    truncation_indicator: str = "..."
) -> pl.Expr:
    """
    Create a Polars expression to format a column for SQL insertion.

    Parameters
    ----------
    col_name : str
        The name of the column to format.
    column_specification : str
        SQL column type specification (e.g., 'VARCHAR(100)', 'INTEGER').
    dialect : SQLDialect
        Target database dialect (reserved for future dialect-specific formatting).
    truncation_indicator : str, default "..."
        String to append when truncating values to indicate data loss.

    Returns
    -------
    pl.Expr
        Expression that formats the column for SQL insertion.
    """
    _ = dialect  # Reserved for future dialect-specific formatting
    col = pl.col(col_name)
    spec_parts = re.search(r'([A-Za-z_\s0-9]+)\(([A-Za-z,\s0-9]+)\)', column_specification)

    base_type: str = spec_parts.group(1).strip().upper() if spec_parts else column_specification.strip().upper()
    parameters = [x.strip() for x in spec_parts.group(2).strip().split(',')] if spec_parts else []

    # Handle string types with length constraints
    if any(t in base_type for t in ['VARCHAR', 'CHAR', 'TEXT', 'NVARCHAR', 'NCHAR']):
        result = col.cast(pl.Utf8)
        if len(parameters) == 1 and parameters[0].lower() != 'max':
            try:
                max_len = int(parameters[0])
                if max_len > 0:
                    indicator_len = len(truncation_indicator)
                    # Truncate with indicator if string exceeds max_len
                    result = pl.when(result.str.len_chars() > max_len).then(
                        result.str.slice(0, max_len - indicator_len) + pl.lit(truncation_indicator)
                    ).otherwise(result)
            except ValueError:
                pass
        return result

    # Handle integer types
    if any(t in base_type for t in ['INT', 'BIGINT', 'SMALLINT', 'TINYINT', 'NUMBER']):
        return col.cast(pl.Int64)

    # Handle float/decimal types
    if any(t in base_type for t in ['FLOAT', 'DOUBLE', 'REAL', 'DECIMAL', 'NUMERIC', 'BINARY_DOUBLE']):
        return col.cast(pl.Float64)

    # Handle datetime types
    if any(t in base_type for t in ['DATETIME', 'TIMESTAMP', 'DATE', 'TIME']):
        if 'DATE' in base_type and 'TIME' not in base_type:
            return col.cast(pl.Date)
        if 'TIME' in base_type and 'DATE' not in base_type and 'STAMP' not in base_type:
            return col.cast(pl.Time)
        return col.cast(pl.Datetime)

    # Handle boolean types
    if any(t in base_type for t in ['BOOL', 'BIT']):
        return col.cast(pl.Boolean)

    # Handle binary types
    if any(t in base_type for t in ['BLOB', 'BINARY', 'BYTEA', 'VARBINARY']):
        return col.cast(pl.Binary)

    # Default: return as-is
    return col
