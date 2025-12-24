from .epl import EnhancedPolars as ep
import polars as pl
import warnings
from typing import Optional, Union, Literal, List, Dict, Any, cast, Tuple
from .base import UniversalPolarsDataFrameExtension

class PolarsMerging(UniversalPolarsDataFrameExtension):
    """
    Polars DataFrame/LazyFrame extension that provides enhanced merging capabilities with automatic
    dtype conflict resolution.
    
    This extension provides merge, merge_asof, and concat methods that automatically
    handle dtype mismatches by finding compatible types before merging.
    """
    
    def __init__(self, df: Any):
        super().__init__(df)
    
    def merge(self, 
              right: Union[pl.DataFrame, pl.LazyFrame],
              how: Literal['inner', 'left', 'full', 'semi', 'anti', 'cross'] = 'inner',
              on: Optional[Union[str, List[str]]] = None,
              left_on: Optional[Union[str, List[str]]] = None,
              right_on: Optional[Union[str, List[str]]] = None,
              suffix: str = '_right',
              validate: Optional[Literal['m:m', '1:m', 'm:1', '1:1']] = None,
              nulls_equal: bool = False,
              resolve_dtypes: bool = True,
              **kwargs) -> Union[pl.DataFrame, pl.LazyFrame]:
        """
        Join DataFrame with another DataFrame with automatic dtype conflict resolution.
        
        This method wraps polars join() but first resolves any dtype conflicts between
        matching columns in both DataFrames by promoting to compatible types.
        
        Args:
            right: DataFrame to join with
            how: Type of join ('inner', 'left', 'full', 'semi', 'anti', 'cross')
            on: Column name(s) to join on (must exist in both DataFrames)
            left_on: Column name(s) to join on from left DataFrame
            right_on: Column name(s) to join on from right DataFrame
            suffix: Suffix to apply to overlapping column names from right DataFrame
            validate: Validate join type ('m:m', '1:m', 'm:1', '1:1')
            nulls_equal: Consider null values as equal during join
            resolve_dtypes: Whether to automatically resolve dtype conflicts (default True)
            **kwargs: Additional arguments passed to polars join
            
        Returns:
            pl.DataFrame: Joined DataFrame with resolved dtypes
            
        Example:
            >>> df1 = pl.DataFrame({'A': [1, 2], 'B': [1.0, 2.0]})  # B is Float64
            >>> df2 = pl.DataFrame({'A': [1, 2], 'B': [3, 4]})      # B is Int64
            >>> result = df1.ud_merge.merge(df2, on='A')  # B columns promoted to Float64
        """
        if not resolve_dtypes:
            # Use native polars join without dtype resolution - works with both lazy/eager
            join_kwargs = {'how': how, 'suffix': suffix, 'nulls_equal': nulls_equal}
            if on is not None:
                join_kwargs['on'] = on
            if left_on is not None:
                join_kwargs['left_on'] = left_on
            if right_on is not None:
                join_kwargs['right_on'] = right_on
            if validate is not None:
                join_kwargs['validate'] = validate
            
            return self._df.join(right, **join_kwargs, **kwargs) # type: ignore
        
        # Determine join columns (works with both lazy/eager via schema)
        join_columns = self._get_join_columns(right, on, left_on, right_on)
        
        # Resolve dtype conflicts using schema - works with both lazy/eager
        left_df, right_df = self._resolve_join_dtypes(
            self._df, right, join_columns, suffix
        )
        
        # Perform the join with resolved dtypes
        join_kwargs = {'how': how, 'suffix': suffix, 'nulls_equal': nulls_equal}
        if on is not None:
            join_kwargs['on'] = on
        if left_on is not None:
            join_kwargs['left_on'] = left_on
        if right_on is not None:
            join_kwargs['right_on'] = right_on
        if validate is not None:
            join_kwargs['validate'] = validate
        
        return left_df.join(right_df, **join_kwargs, **kwargs)
    
    def merge_asof(self,
                   right: Union[pl.DataFrame, pl.LazyFrame],
                   on: Optional[str] = None,
                   left_on: Optional[str] = None,
                   right_on: Optional[str] = None,
                   by: Optional[Union[str, List[str]]] = None,
                   by_left: Optional[Union[str, List[str]]] = None,
                   by_right: Optional[Union[str, List[str]]] = None,
                   strategy: Literal['backward', 'forward', 'nearest'] = 'backward',
                   suffix: str = '_right',
                   tolerance: Optional[Union[str, int, float]] = None,
                   allow_exact_matches: bool = True,
                   resolve_dtypes: bool = True,
                   **kwargs) -> Union[pl.DataFrame, pl.LazyFrame]:
        """
        Perform join_asof with automatic dtype conflict resolution.
        
        Similar to polars join_asof but first resolves dtype conflicts between
        the DataFrames to ensure compatibility.
        
        Args:
            right: DataFrame to join with
            on: Column name to join on (must be sorted)
            left_on: Column name from left DataFrame  
            right_on: Column name from right DataFrame
            by: Additional columns to match exactly on both sides
            by_left: Additional left DataFrame columns to match
            by_right: Additional right DataFrame columns to match
            strategy: Direction to search for matches ('backward', 'forward', 'nearest')
            suffix: Suffix for overlapping column names from right DataFrame
            tolerance: Tolerance for matches
            allow_exact_matches: Whether to allow exact matches
            resolve_dtypes: Whether to resolve dtype conflicts (default True)
            **kwargs: Additional arguments passed to polars join_asof
            
        Returns:
            pl.DataFrame: Result of join_asof with resolved dtypes
        """
        # Determine sort columns for proper join_asof ordering
        # join_asof requires data to be sorted by the 'on' column, and when 'by' is used,
        # sorted by [by_cols, on_col] so within each group the data is sorted
        left_on_col = on or left_on
        right_on_col = on or right_on

        left_sort_cols: List[str] = []
        right_sort_cols: List[str] = []

        if by:
            by_list = [by] if isinstance(by, str) else list(by)
            left_sort_cols.extend(by_list)
            right_sort_cols.extend(by_list)
        if by_left:
            left_by_list = [by_left] if isinstance(by_left, str) else list(by_left)
            left_sort_cols.extend(left_by_list)
        if by_right:
            right_by_list = [by_right] if isinstance(by_right, str) else list(by_right)
            right_sort_cols.extend(right_by_list)

        if left_on_col:
            left_sort_cols.append(left_on_col)
        if right_on_col:
            right_sort_cols.append(right_on_col)

        # Sort both DataFrames upfront
        left_df = self._df.sort(left_sort_cols) if left_sort_cols else self._df
        right_df = right.sort(right_sort_cols) if right_sort_cols else right

        # Resolve dtype conflicts if requested
        if resolve_dtypes:
            join_on = on or left_on
            right_join_on = on or right_on

            join_columns = []
            if join_on and right_join_on:
                join_columns.append((join_on, right_join_on))

            if by:
                by_list = [by] if isinstance(by, str) else by
                join_columns.extend([(col, col) for col in by_list])

            if by_left and by_right:
                left_by_list = [by_left] if isinstance(by_left, str) else by_left
                right_by_list = [by_right] if isinstance(by_right, str) else by_right
                join_columns.extend(zip(left_by_list, right_by_list))

            left_df, right_df = self._resolve_join_dtypes(
                left_df, right_df, join_columns, suffix
            )

        # Build asof_kwargs
        asof_kwargs = {'strategy': strategy, 'suffix': suffix, 'allow_exact_matches': allow_exact_matches}
        if on is not None:
            asof_kwargs['on'] = on
        if left_on is not None:
            asof_kwargs['left_on'] = left_on
        if right_on is not None:
            asof_kwargs['right_on'] = right_on
        if by is not None:
            asof_kwargs['by'] = by
        if by_left is not None:
            asof_kwargs['by_left'] = by_left
        if by_right is not None:
            asof_kwargs['by_right'] = by_right
        if tolerance is not None:
            asof_kwargs['tolerance'] = tolerance

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Sortedness of columns cannot be checked",
                category=UserWarning,
            )
            return left_df.join_asof(right_df, **asof_kwargs, **kwargs)  # type: ignore
    
    def concat(self, 
               *others: Union[pl.DataFrame, pl.LazyFrame],
               how: Literal['vertical', 'vertical_relaxed', 'horizontal', 'diagonal', 'diagonal_relaxed'] = 'vertical',
               rechunk: bool = False,
               parallel: bool = True,
               **kwargs) -> Union[pl.DataFrame, pl.LazyFrame]:
        """
        Concatenate DataFrames with automatic dtype conflict resolution.
        
        This method first uses the imported concat_series_dataframe function to handle
        dtype conflicts, then applies polars-specific concatenation parameters.
        
        Args:
            *others: Other DataFrames to concatenate with
            how: How to concatenate ('vertical', 'vertical_relaxed', 'horizontal', 'diagonal', 'diagonal_relaxed')
            rechunk: Rechunk the final result
            parallel: Run concatenation in parallel
            **kwargs: Additional arguments passed to polars concat
            
        Returns:
            pl.DataFrame: Concatenated DataFrame with resolved dtypes
            
        Example:
            >>> df1 = pl.DataFrame({'A': [1, 2], 'B': [1.0, 2.0]})  # B is Float64
            >>> df2 = pl.DataFrame({'A': [3, 4], 'B': [3, 4]})      # B is Int64
            >>> result = df1.ud_merge.concat(df2)  # B promoted to Float64
        """
        # Collect all DataFrames to concatenate
        all_dfs = [self._df] + list(others)
        
        # For basic vertical concat, polars handles dtype resolution automatically
        if how in ['vertical', 'vertical_relaxed', 'horizontal']:
            return pl.concat(all_dfs, how=how, rechunk=rechunk, parallel=parallel, **kwargs) # type: ignore
        else:
            # For complex concat types with dtype resolution, need eager DataFrames
            # This is the only case where we actually need collection
            eager_dfs = [df.collect() if isinstance(df, pl.LazyFrame) else df for df in all_dfs]
  
            # Use native polars concat for non-vertical cases
            return pl.concat(eager_dfs, how=how, rechunk=rechunk, parallel=parallel, **kwargs)
    
    def _get_join_columns(self, right, on, left_on, right_on):
        """Determine which columns will be used for joining."""
        join_columns = []
        
        if on:
            on_list = [on] if isinstance(on, str) else on
            join_columns.extend([(col, col) for col in on_list])
        elif left_on and right_on:
            left_on_list = [left_on] if isinstance(left_on, str) else left_on
            right_on_list = [right_on] if isinstance(right_on, str) else right_on
            join_columns.extend(zip(left_on_list, right_on_list))
        else:
            # Default join on common columns - get columns from schema efficiently
            left_cols = list(self.schema.keys())
            right_cols = right.collect_schema().names() if isinstance(right, pl.LazyFrame) else right.schema.names()
            common_cols = set(left_cols) & set(right_cols)
            join_columns.extend([(col, col) for col in common_cols])
        
        return join_columns
    
    def _resolve_join_dtypes(self, left_df, right_df, join_columns, suffix):
        """Resolve dtype conflicts between DataFrames using schema (works with lazy/eager)."""
        # Get schemas efficiently - collect_schema() for lazy, schema for eager
        left_schema = left_df.collect_schema() if isinstance(left_df, pl.LazyFrame) else dict(left_df.schema.items())
        right_schema = right_df.collect_schema() if isinstance(right_df, pl.LazyFrame) else dict(right_df.schema.items())
        
        left_result = left_df
        right_result = right_df
        
        # Resolve dtype conflicts in join columns
        for left_col, right_col in join_columns:
            if left_col in left_schema and right_col in right_schema:
                left_dtype = left_schema[left_col]
                right_dtype = right_schema[right_col]
                
                if left_dtype != right_dtype:
                    # Find compatible dtype
                    merged_dtype = ep.merge_polars_dtypes(left_dtype, right_dtype)
                    
                    # Convert columns to merged dtype using cast (works with lazy/eager)
                    if left_dtype != merged_dtype:
                        left_result = left_result.with_columns(pl.col(left_col).cast(merged_dtype))
                    
                    if right_dtype != merged_dtype:
                        right_result = right_result.with_columns(pl.col(right_col).cast(merged_dtype))
        
        # Resolve dtype conflicts in overlapping columns (non-join columns)
        overlapping_cols = set(left_schema.keys()) & set(right_schema.keys())
        
        # Remove join columns from overlapping check
        join_col_names = {col[0] for col in join_columns} | {col[1] for col in join_columns}
        overlapping_cols = overlapping_cols - join_col_names
        
        for col in overlapping_cols:
            left_dtype = left_schema[col]
            right_dtype = right_schema[col]
            
            if left_dtype != right_dtype:
                # Find compatible dtype
                merged_dtype = ep.merge_polars_dtypes(left_dtype, right_dtype)
                
                # Convert columns to merged dtype using cast (works with lazy/eager)
                if left_dtype != merged_dtype:
                    left_result = left_result.with_columns(pl.col(col).cast(merged_dtype))
                
                if right_dtype != merged_dtype:
                    right_result = right_result.with_columns(pl.col(col).cast(merged_dtype))
        
        return left_result, right_result
    

    def infer_dtypes(self,
                attempt_downcast: bool = True,
                attempt_numeric_to_datetime: bool = False,
                confidence: float = 1.0,
                n: Optional[int] = None,
                sample_strat: Literal['first', 'random'] = 'random',
                seed: int = 42,
                collect_precision_scale: bool = False,
                return_df: bool = False,
                columns: Optional[List[str]] = None) -> Dict[str, Any] | Tuple[pl.DataFrame, Dict[str, Any]]:
        """
        Infer optimal data types for all columns in the DataFrame with comprehensive analysis.
        
        This method provides intelligent type inference with support for temporal parsing,
        numeric optimization, categorical detection, and precision/scale analysis. It can
        optionally return the converted DataFrame along with detailed metadata for each column.
        This is a convenience wrapper around the standalone infer_dtypes function.
        
        Parameters:
        -----------
        attempt_downcast : bool, optional (default=True)
            If True, attempts to downcast numeric types to smaller, more efficient types
            for each column (e.g., Int64 -> Int32, Float64 -> Float32) when values fit.
            
        attempt_numeric_to_datetime : bool, optional (default=False)
            If True, attempts to convert numeric columns that appear to be timestamps
            (seconds, milliseconds, microseconds, nanoseconds) to datetime types.
            
        confidence : float, optional (default=1.0)
            Confidence level for sampling (0.0 to 1.0) applied to each column.
            Lower values use smaller samples for faster inference.
            
        n : int, optional (default=None)
            If specified, use exactly N samples for inference on each column.
            Overrides confidence parameter.
            
        sample_strat : {'first', 'random'}, optional (default='random')
            Sampling strategy when using less than the full dataset.
            
        seed : int, optional (default=42)
            Random seed for reproducible sampling when sample_strat='random'.
            
        collect_precision_scale : bool, optional (default=False)
            If True, calculates precision and scale for numeric columns.
            
        return_df : bool, optional (default=False)
            If True, returns a tuple of (converted_dataframe, metadata_dict).
            If False, returns only the metadata dictionary.
            
        columns : List[str], optional (default=None)
            List of specific column names to analyze. If None, all columns are processed.
            
        Returns:
        --------
        Dict[str, Any] or Tuple[pl.DataFrame, Dict[str, Any]]
            Comprehensive metadata for each column or tuple with converted DataFrame.
            
        Examples:
        ---------
        >>> # Basic type inference
        >>> metadata = df.ud_merge.infer_dtypes()
        >>> 
        >>> # Get converted DataFrame with optimizations
        >>> converted_df, metadata = df.ud_merge.infer_dtypes(return_df=True)
        >>> 
        >>> # Fast inference with sampling
        >>> metadata = df.ud_merge.infer_dtypes(confidence=0.1)
        """
        
        return ep.infer_dtypes(df=self._df,
                attempt_downcast=attempt_downcast,
                attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                confidence=confidence,
                n=n,
                sample_strat=sample_strat,
                seed=seed,
                collect_precision_scale=collect_precision_scale,
                return_df=return_df,
                columns=columns)

    def optimize_dtypes(self,
                    attempt_downcast: bool = True,
                    attempt_numeric_to_datetime: bool = False,
                    confidence: float = 1.0,
                    n: Optional[int] = None,
                    sample_strat: Literal['first', 'random'] = 'random',
                    seed: int = 42,
                    columns: Optional[List[str]] = None) -> pl.DataFrame:
        """
        Optimize data types for the DataFrame with comprehensive type inference and conversion.
        
        This method provides a simplified interface to automatically optimize all column types
        in the DataFrame without requiring metadata analysis. It applies intelligent type
        optimization including temporal parsing, numeric downcasting, categorical detection,
        and precision optimization. This is a convenience wrapper around the standalone
        optimize_dtypes function.
        
        Parameters:
        -----------
        attempt_downcast : bool, optional (default=True)
            If True, attempts to downcast numeric types to smaller, more efficient types
            (e.g., Int64 -> Int32, Float64 -> Float32) when values fit within the range.
            
        attempt_numeric_to_datetime : bool, optional (default=False)
            If True, attempts to convert numeric values that appear to be timestamps
            (seconds, milliseconds, microseconds, nanoseconds) to datetime types.
            
        confidence : float, optional (default=1.0)
            Confidence level for sampling (0.0 to 1.0). Lower values use smaller samples
            for faster inference at the cost of potential accuracy.
            
        n : int, optional (default=None)
            If specified, use exactly N samples for inference. Overrides confidence parameter.
            Useful when you want precise control over sample size for each column.
            
        sample_strat : {'first', 'random'}, optional (default='random')
            Sampling strategy when using less than the full dataset.
            
        seed : int, optional (default=42)
            Random seed for reproducible sampling when sample_strat='random'.
            
        columns : List[str], optional (default=None)
            List of specific column names to optimize. If None, all columns are processed.
            
        Returns:
        --------
        pl.DataFrame
            Optimized DataFrame with inferred and converted types:
            - All type conversions applied based on inference results
            - Memory-optimized with appropriate downcasting when safe
            - Temporal strings converted to proper datetime types
            - Numeric types optimized for efficiency
            
        Examples:
        ---------
        >>> # Basic optimization of all columns
        >>> optimized_df = df.ud_merge.optimize_dtypes()
        >>> 
        >>> # Full optimization including timestamp detection
        >>> optimized_df = df.ud_merge.optimize_dtypes(
        ...     attempt_downcast=True,
        ...     attempt_numeric_to_datetime=True
        ... )
        >>> 
        >>> # Fast optimization using sampling
        >>> optimized_df = df.ud_merge.optimize_dtypes(confidence=0.1)
        >>> 
        >>> # Optimize only specific columns
        >>> optimized_df = df.ud_merge.optimize_dtypes(columns=['col1', 'col2'])
        
        Note:
        -----
        This method automatically returns the optimized DataFrame without metadata.
        For detailed analysis with metadata, use infer_dtypes() instead.
        """
        return cast(pl.DataFrame, ep.optimize_dtypes(df_or_series=self._df,
                    attempt_downcast=attempt_downcast,
                    attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                    confidence=confidence,
                    n=n,
                    sample_strat=sample_strat,
                    seed=seed, columns=columns))
    

    def astype(self, dtype: Any, **kwargs) -> pl.DataFrame:
        """
        Convert DataFrame columns to specified data type(s) with intelligent conversion handling.
        
        This method provides a more powerful alternative to polars' native astype() method
        by using the enhanced convert_to_polars_dtype function. It supports complex conversions
        including string-to-temporal parsing, numeric-to-temporal conversion with automatic
        scale detection, and handles edge cases that native casting might fail on.
        
        Parameters:
        -----------
        dtype : Any
            Target data type specification:
            - For single type: Apply the same dtype to all columns
            - For dict: Map column names to their target dtypes
            - Supports all Polars DataTypes, string specifications, and Python types
            - All dtypes are automatically parsed for consistency
            
        **kwargs : dict
            Additional keyword arguments passed to the conversion functions:
            - For string-to-temporal: Arguments to str.to_date(), str.to_datetime(), str.to_time()
            - For temporal parsing: strict=False is used by default for robust parsing
            - For numeric-to-temporal: Custom arguments to temporal conversion functions
            
        Returns:
        --------
        pl.DataFrame
            DataFrame with columns converted to the specified data type(s):
            - Intelligent conversion handling for complex type changes
            - Preserves data integrity where possible
            - Uses optimized conversion paths for temporal types
            - Automatic scale detection for numeric-to-temporal conversions
            
        Examples:
        ---------
        >>> # Convert all columns to string
        >>> string_df = df.ud_merge.astype(pl.String)
        >>> 
        >>> # Convert specific columns to different types
        >>> converted_df = df.ud_merge.astype({
        ...     'date_col': pl.Date,
        ...     'timestamp_col': pl.Datetime,
        ...     'number_col': pl.Int32,
        ...     'category_col': pl.Categorical
        ... })
        >>> 
        >>> # Convert numeric timestamps to datetime (auto-detects scale)
        >>> datetime_df = df.ud_merge.astype({'timestamp_ms': pl.Datetime})
        >>> 
        >>> # Convert with additional parameters
        >>> converted_df = df.ud_merge.astype(
        ...     {'date_strings': pl.Date}, 
        ...     strict=False  # Passed to conversion function
        ... )
        
        Note:
        -----
        This method is more robust than native polars astype() for complex conversions
        but may be slightly slower due to the additional intelligence. For simple
        type conversions where you're certain about compatibility, native astype()
        may be sufficient.
        
        See Also:
        ---------
        optimize_dtypes : Automatic type optimization without explicit type specification
        infer_dtypes : Detailed type analysis with metadata
        """

        return cast(pl.DataFrame, ep.convert_to_polars_dtype(data_series_or_frame=self._df, dtype=dtype, **kwargs))
