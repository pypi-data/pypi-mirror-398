import datetime as dt
from typing import Callable, Iterable, Optional, Union, Tuple, cast, List, Any, Literal

import polars as pl
import pandas as pd

TimeDeltaLike = Union[dt.timedelta, int, float, None | str]  # int/float -> seconds

def aggregate_connected_segments(
    frame: Union[pl.DataFrame, pl.LazyFrame],
    *,
    start_col: str,
    end_col: str,
    by: Optional[Union[str, Iterable[str]]] = None,
    tolerance: TimeDeltaLike = None,
    agg_fn: Optional[Union[
        Callable[[pl.DataFrame], Union[pl.Series, dict, pl.DataFrame]],  # DataFrame function
        dict[str, pl.Expr],  # Expression dict
        Callable[[], dict[str, pl.Expr]]  # Expression generator
    ]] = None,
    compute_union_duration: bool = True,
    return_labels: bool = False,
) -> pl.DataFrame | pl.LazyFrame | Tuple[pl.DataFrame, pl.DataFrame]:
    """
    Partition intervals into connected components using tolerance-augmented overlap,
    then aggregate each component (per group if `by` given) with a user function.

    Connectivity rule (within each group):
        start_i belongs to the current component iff
        start_i <= max_seen_end_plus_tol
    where max_seen_end_plus_tol is the cumulative max of (end + tolerance).

    Parameters
    ----------
    frame : pl.DataFrame | pl.LazyFrame
    start_col, end_col : str
        Temporal columns (Date or Datetime). If Date and tolerance has sub-day seconds,
        the columns are cast to Datetime for correct resolution.
    by : str | Iterable[str] | None
        Optional grouping keys.
    tolerance : timedelta | int | float | None
        Connectivity slack. int/float interpreted as seconds. None -> 0 seconds.
        Used *only* to decide connectivity; the final reported `end` is not padded.
    agg_fn : callable | dict[str, pl.Expr] | None
        Aggregation function for non-time columns. Can be:
        - A callable taking a DataFrame and returning Series/dict/DataFrame (eager evaluation)
        - A dict mapping column names to Polars expressions (stays lazy)
        - A callable returning a dict of expressions (stays lazy)
        For lazy evaluation with expressions, the expressions will be evaluated
        with .over(by + ["_cc"]) where "_cc" is the internal component label.
    compute_union_duration : bool
        If True, compute the true covered time of the component (union of intervals,
        without tolerance) as `union_duration`.
    return_labels : bool
        If True, also return a DataFrame mapping each original row to its component id.

    Returns
    -------
    If agg_fn is None and input is LazyFrame: returns LazyFrame with columns
        [*by, start_col, end_col, n_segments].
    Otherwise returns an eager DataFrame with:
        [*by, start_col, end_col, n_segments, (optional union_duration), (agg_fn outputs)]
    """
    # --- normalize inputs ---
    by = [by] if isinstance(by, str) else (list(by) if by else [])
    tol = (dt.timedelta(0) if tolerance is None
           else tolerance if isinstance(tolerance, dt.timedelta)
           else pd.to_timedelta(tolerance).to_pytimedelta() if isinstance(tolerance, str)
           else dt.timedelta(seconds=float(tolerance)))
    if tol < dt.timedelta(0):
        raise ValueError("tolerance must be non-negative")

    is_lazy = isinstance(frame, pl.LazyFrame) or hasattr(frame, 'collect')
    lf = frame if is_lazy else frame.lazy()

    # Ensure consistent temporal resolution if needed
    # Use collect_schema() to avoid performance warning
    schema = lf.collect_schema()
    s_dtype = schema[start_col]
    e_dtype = schema[end_col]
    need_dt_cast = (
        (str(s_dtype) == "Date" or str(e_dtype) == "Date")
        and tol.total_seconds() % 86400 != 0
    )
    lf = lf.with_columns(
        **({
            start_col: pl.col(start_col).cast(pl.Datetime),
            end_col: pl.col(end_col).cast(pl.Datetime),
        } if need_dt_cast else {})
    )

    # --- label connected components via sweep-line ---
    # Sort within groups by start; maintain running max of (end + tol) over window
    def over(expr: pl.Expr) -> pl.Expr:
        return expr.over(by) if by else expr

    # Build connected components using sweep-line algorithm
    # We need to materialize the _cc column as an actual column (not expression)
    # to use it with map_groups later
    lf_lab = (
        lf
        .filter(pl.all_horizontal(pl.col(start_col).is_not_null(), pl.col(end_col).is_not_null()))
        .with_columns(_end_ext = pl.col(end_col) + pl.lit(tol))
        .sort(by + [start_col] if by else [start_col])
        .with_columns(
            _prev_max_ext = over(pl.col("_end_ext").cum_max().shift(1))
        )
        .with_columns(
            _is_new = (
                pl.col("_prev_max_ext").is_null() |
                (pl.col(start_col) > pl.col("_prev_max_ext"))
            ).cast(pl.Int64)
        )
        .with_columns(_cc = over(pl.col("_is_new").cum_sum()))
        .drop(["_is_new", "_prev_max_ext", "_end_ext"])
    )

    # Check if agg_fn is expression-based (can stay lazy)
    is_expr_based = False
    expr_aggs = {}
    
    if agg_fn is not None:
        # Check if it's a dict of expressions
        if isinstance(agg_fn, dict):
            is_expr_based = all(isinstance(v, pl.Expr) for v in agg_fn.values())
            if is_expr_based:
                expr_aggs = agg_fn
        # Check if it's a callable that returns expressions
        elif callable(agg_fn):
            try:
                # Try calling with no args to see if it returns expressions
                test_result = agg_fn() # type: ignore
                if isinstance(test_result, dict) and all(isinstance(v, pl.Expr) for v in test_result.values()):
                    is_expr_based = True
                    expr_aggs = test_result
            except (TypeError, Exception):
                # It's a DataFrame-based function
                is_expr_based = False
    
    # If we can stay lazy (no DataFrame function, no union duration needed)
    # We can return lazy even if input was eager, as long as we're using expressions
    if (agg_fn is None or is_expr_based) and not compute_union_duration:
        # Build base aggregations
        base_aggs = [
            pl.col(start_col).min().alias(start_col),
            pl.col(end_col).max().alias(end_col),
            pl.len().alias("n_segments"),
        ]
        
        # Add user expression aggregations
        for name, expr in expr_aggs.items():
            base_aggs.append(expr.alias(name))
        
        out_lazy = (
            lf_lab
            .group_by(by + ["_cc"])
            .agg(base_aggs)
            .drop("_cc")
            .sort(by + [start_col] if by else [start_col])
        )
        return out_lazy

    # Collect for eager operations (required for union duration or DataFrame-based agg)
    df_lab = cast(pl.LazyFrame, lf_lab).collect()

    # Define aggregation function that returns a DataFrame
    def aggregate_group(group_df: pl.DataFrame) -> pl.DataFrame:
        # Remove the _cc column for processing
        chunk = group_df.drop("_cc") if "_cc" in group_df.columns else group_df
        
        # Get start and end times
        starts = chunk[start_col].to_list()
        ends = chunk[end_col].to_list()
        
        if not starts:
            return pl.DataFrame()
        
        # Include grouping columns in result
        result = {}
        for col in by:
            if col in chunk.columns:
                result[col] = chunk[col][0]
        
        result.update({
            start_col: min(starts),
            end_col: max(ends),
            "n_segments": len(starts),
        })
        
        # Compute union duration if requested
        if compute_union_duration:
            # Sort intervals and merge overlapping ones
            intervals = sorted(zip(starts, ends))
            merged = []
            for s, e in intervals:
                if not merged or s > merged[-1][1]:
                    merged.append([s, e])
                else:
                    merged[-1][1] = max(merged[-1][1], e)
            
            union_td = dt.timedelta(0)
            for s, e in merged:
                union_td += (e - s)
            result["union_duration"] = union_td
        
        # Apply user aggregation function if provided
        if agg_fn is not None:
            if callable(agg_fn):
                # Handle callable aggregation functions
                user_out = agg_fn(chunk) # type: ignore
                if isinstance(user_out, pl.Series):
                    result[user_out.name or "agg"] = user_out.item()
                elif isinstance(user_out, dict):
                    result.update(user_out)
                elif isinstance(user_out, pl.DataFrame):
                    if user_out.height != 1:
                        raise ValueError("agg_fn must return a single row")
                    for c in user_out.columns:
                        result[c] = user_out[c][0]
                else:
                    raise TypeError("agg_fn must return a Series, dict, or 1-row DataFrame")
            elif isinstance(agg_fn, dict):
                # Handle dictionary aggregations (e.g., {'col': 'first'})
                for col, agg_method in agg_fn.items():
                    if col in chunk.columns:
                        if agg_method == 'first': # type: ignore
                            result[col] = chunk[col].drop_nulls().first() if chunk[col].drop_nulls().len() > 0 else chunk[col].first()
                        elif agg_method == 'last': # type: ignore
                            result[col] = chunk[col].drop_nulls().last() if chunk[col].drop_nulls().len() > 0 else chunk[col].last()
                        elif agg_method == 'mean': # type: ignore
                            result[col] = chunk[col].mean() # type: ignore
                        elif agg_method == 'sum': # type: ignore
                            result[col] = chunk[col].sum()
                        elif agg_method == 'min': # type: ignore
                            result[col] = chunk[col].min()
                        elif agg_method == 'max': # type: ignore
                            result[col] = chunk[col].max()
                        elif agg_method == 'count': # type: ignore
                            result[col] = chunk[col].len()
                        else:
                            # For other string methods, try to get the method from the Series
                            if hasattr(chunk[col], agg_method): # type: ignore
                                method = getattr(chunk[col], agg_method) # type: ignore
                                if callable(method):
                                    result[col] = method()
                                else:
                                    result[col] = method
                            else:
                                raise ValueError(f"Unknown aggregation method: {agg_method}")
            else:
                raise TypeError("agg_fn must be callable or a dictionary mapping column names to aggregation methods")
        
        return pl.DataFrame([result])
    
    # Group by the component labels and apply aggregation
    # Use explicit column names to avoid expression issues
    if by:
        df_comp = df_lab.group_by(*by, "_cc", maintain_order=True).map_groups(aggregate_group)
    else:
        df_comp = df_lab.group_by("_cc", maintain_order=True).map_groups(aggregate_group)
    
    # Clean up and sort
    df_comp = df_comp.drop("_cc", strict=False).sort(by + [start_col] if by else [start_col])
    
    if return_labels:
        labels = df_lab.select(by + ["_cc"])
        return df_comp, labels
    
    return df_comp


def add_time_boundaries(
    data_structure: pl.LazyFrame | pl.DataFrame,
    dt_name: str,
    start: Optional[pl.LazyFrame | pl.DataFrame | dt.datetime] = None,
    end: Optional[pl.LazyFrame | pl.DataFrame | dt.datetime] = None,
    id_name: Optional[str] = None,
    label_name: Optional[str] = None,
    value_name: Optional[Union[str, List[str]]] = None,
    start_fill_value: Optional[Any] = None,
    end_fill_value: Optional[Any] = None,
    meta_cols: Optional[List[str]] = None,
    inclusive: Literal['both', 'left', 'right', 'neither'] = 'both',
    trim: bool = True
) -> pl.LazyFrame | pl.DataFrame:
    """
    Add start and end time boundary rows to time series data with specified fill values.
    
    This function creates new rows at specified start and/or end time points and adds them
    to the existing data. It supports both single time series and multi-ID datasets, with
    optional cross-joining for label-based (long-format) data structures.
    
    Parameters
    ----------
    data_structure : pl.LazyFrame | pl.DataFrame
        The input time series data.
        
    dt_name : str
        Column name containing datetime values. This column must exist in data_structure.
        
    start : pl.LazyFrame | pl.DataFrame | dt.datetime | None, optional
        Start time boundary specification:
        - datetime.datetime: Single start time (requires id_name=None)
        - UniversalDataSeries: Start times with id_name as index, converted to DataFrame
        - UniversalDataFrame: Must contain id_name and dt_name columns, or 'start_xxx'/'end_xxx' columns
        - None: No start boundary added
        
    end : pl.LazyFrame | pl.DataFrame | dt.datetime | None, optional
        End time boundary specification:
        - datetime.datetime: Single end time (requires id_name=None)
        - UniversalDataSeries: End times with id_name as index, converted to DataFrame  
        - UniversalDataFrame: Must contain id_name and dt_name columns
        - None: No end boundary added (unless inferred from start DataFrame with 'start_xxx'/'end_xxx')
        
    id_name : str, optional
        Column name that identifies different time series groups. Required when start/end
        are UniversalDataFrame or UniversalDataSeries. Must be None for single datetime inputs.
        
    label_name : str, optional
        Column name for categorical labels in long-format data. If provided, boundary rows
        are cross-joined with all unique values in this column to create entries for each label.
        
    value_name : str or List[str], optional
        Column name(s) to fill with boundary values. If None, all columns except id_name,
        dt_name, and label_name are used as value columns.
        
    start_fill_value : Any, optional
        Value to assign to value columns in start boundary rows. If None, columns are
        not filled (may contain NaN).
        
    end_fill_value : Any, optional
        Value to assign to value columns in end boundary rows. If None, columns are
        not filled (may contain NaN).
        
    trim : bool, default True
        Whether to apply merge_asof filtering to trim data outside boundaries.
        Only applies when id_name is specified and fill values are provided.
        - With start: filters data to start from boundary times (direction='forward')
        - With end: filters data to end at boundary times (direction='backward')
    inclusive : {'both', 'left', 'right', 'neither'}, default 'both'
        Inclusion rule for merge_asof when trimming data:
        - 'both': include rows equal to boundary times
        - 'left': include rows equal to start boundary only
        - 'right': include rows equal to end boundary only
        - 'neither': exclude rows equal to boundary times
        
    Returns
    -------
    pl.LazyFrame | pl.DataFrame
        Original data concatenated with new boundary rows.
        
    Examples
    --------
    Add single start/end boundaries:
    
    >>> import pandas as pd
    >>> from datetime import datetime
    >>> df = UniversalDataFrame(pd.DataFrame({
    ...     'timestamp': pd.date_range('2023-01-02', periods=3, freq='D'),
    ...     'value': [10, 20, 30]
    ... }))
    >>> result = add_time_boundaries(
    ...     df,
    ...     dt_name='timestamp',
    ...     start=datetime(2023, 1, 1),
    ...     end=datetime(2023, 1, 5),
    ...     start_fill_value=0,
    ...     end_fill_value=0
    ... )
    >>> # Result: 5 rows with boundary rows at 2023-01-01 and 2023-01-05
    
    Add boundaries for multiple time series:
    
    >>> df = UniversalDataFrame(pd.DataFrame({
    ...     'id': ['A', 'A', 'B', 'B'],
    ...     'timestamp': pd.to_datetime(['2023-01-02', '2023-01-03', 
    ...                                 '2023-01-02', '2023-01-04']),
    ...     'value': [10, 20, 15, 25]
    ... }))
    >>> start_df = UniversalDataFrame(pd.DataFrame({
    ...     'id': ['A', 'B'],
    ...     'timestamp': pd.to_datetime(['2023-01-01', '2023-01-01'])
    ... }))
    >>> result = add_time_boundaries(
    ...     df,
    ...     dt_name='timestamp',
    ...     start=start_df,
    ...     id_name='id',
    ...     start_fill_value=0
    ... )
    >>> # Result: 6 rows with start boundaries added for each ID
    
    Handle long-format data with labels:
    
    >>> df = UniversalDataFrame(pd.DataFrame({
    ...     'id': ['A', 'A'],
    ...     'timestamp': pd.to_datetime(['2023-01-02', '2023-01-03']),
    ...     'metric': ['temp', 'temp'],
    ...     'value': [20.5, 22.1]
    ... }))
    >>> result = add_time_boundaries(
    ...     df,
    ...     dt_name='timestamp',
    ...     start=datetime(2023, 1, 1),
    ...     id_name='id',
    ...     label_name='metric',
    ...     start_fill_value=0
    ... )
    >>> # Result: Cross-join creates start boundary for each unique metric value
    
    Use DataFrame with start_xxx/end_xxx columns:
    
    >>> ranges_df = UniversalDataFrame(pd.DataFrame({
    ...     'id': ['A', 'B'],
    ...     'start_xxx': pd.to_datetime(['2023-01-01', '2023-01-01']),
    ...     'end_xxx': pd.to_datetime(['2023-01-05', '2023-01-06'])
    ... }))
    >>> result = add_time_boundaries(
    ...     df,
    ...     dt_name='timestamp',
    ...     start=ranges_df,  # end is automatically inferred
    ...     id_name='id',
    ...     start_fill_value=0,
    ...     end_fill_value=999
    ... )
    
    Notes
    -----
    - Input UniversalDataSeries is automatically converted to DataFrame with reset index
    - Boundary rows are created by concatenating original data with new boundary DataFrames
    - When label_name is specified, boundaries are cross-joined with all unique label values
    - The trim parameter uses merge_asof to filter data relative to boundary times
    - Value columns are automatically determined if value_name is None
    - Always returns UniversalDataFrame, even for UniversalDataSeries input
    
    Raises
    ------
    TypeError
        If data_structure is not UniversalDataFrame or UniversalDataSeries
    ValueError  
        If id_name is not None when using single datetime start/end
        If required columns are missing from DataFrame inputs
    AssertionError
        If parameter combinations are invalid or required columns don't exist
    """
    # Validate input types
    if not isinstance(data_structure, (pl.LazyFrame, pl.DataFrame)):
        raise TypeError("data_structure must be pl.LazyFrame or pl.DataFrame")

    if isinstance(label_name, str):
        assert label_name in data_structure.columns, f"label_name '{label_name}' not found in data structure" # type: ignore
        assert data_structure[label_name].is_not_null().all(), "label_name column must not contain null values" # type: ignore
        label_levels: List[str] = data_structure[label_name].unique().to_list() # type: ignore
    else:
        assert label_name is None, "label_name must be a string or None"
        label_levels: List[str] = []

    assert isinstance(dt_name, str), "dt_name must be a string"

    if value_name is None:
        # Use all non-ID, non-datetime columns
        if isinstance(data_structure, pl.LazyFrame):
            all_columns = data_structure.collect_schema().names()
        else:
            all_columns = data_structure.columns
        value_columns = [col for col in all_columns if col not in [id_name, dt_name, label_name]]
    elif isinstance(value_name, str):
        value_columns = [value_name]
    elif isinstance(value_name, list):
        value_columns = value_name
    else:
        raise TypeError("value_name must be a string, list of strings, or None")


    meta_cols_f: List[str] = meta_cols if isinstance(meta_cols, list) else []

    # Build boundaries DataFrame from start/end inputs
    boundaries = None
    
    # Process start boundary
    if start is not None:
        if isinstance(start, dt.datetime):
            assert len(meta_cols_f) == 0, "meta_cols must be empty when using single datetime start"
            assert id_name is None, "id_name must be None for single datetime start"
            boundaries = pl.DataFrame({'_BOUNDARY_START_': [start]})
            
        elif isinstance(start, (pl.LazyFrame, pl.DataFrame)):
            if isinstance(start, pl.LazyFrame):
                start = start.collect()
            assert id_name is not None, "id_name must be specified if start is a UniversalDataFrame"
            assert all([col in start.columns for col in meta_cols_f]) or (len(meta_cols_f) == 0), f"start DataFrame must contain '{meta_cols_f}' columns if they are provided"
            
            # Handle start_xxx/end_xxx special case
            if dt_name not in start.columns:
                assert any(col in start.columns for col in ['start_xxx', 'end_xxx']), f'Either "start_xxx" or "end_xxx" must be present in the start DataFrame; available columns are {start.columns}'
                cols_to_select = [id_name] + [col for col in ['start_xxx', 'end_xxx'] if col in start.columns] + meta_cols_f
                boundaries = start[cols_to_select]
                # Only rename columns that exist
                rename_dict = {}
                if 'start_xxx' in boundaries.columns:
                    rename_dict['start_xxx'] = '_BOUNDARY_START_'
                if 'end_xxx' in boundaries.columns:
                    rename_dict['end_xxx'] = '_BOUNDARY_END_'
                boundaries = boundaries.rename(rename_dict)
            else:
                assert dt_name in start.columns, f"start DataFrame must contain '{dt_name}' column"
                boundaries = start[[id_name, dt_name] + meta_cols_f].rename({dt_name: '_BOUNDARY_START_'})

    # Process end boundary
    if end is not None:
        if isinstance(end, dt.datetime):
            assert len(meta_cols_f) == 0, "meta_cols must be empty when using single datetime end"
            assert id_name is None, "id_name must be None for single datetime end"
            if isinstance(boundaries, pl.DataFrame):
                boundaries = boundaries.with_columns(pl.lit(end).alias('_BOUNDARY_END_'))
            else:
                boundaries = pl.DataFrame({'_BOUNDARY_END_': [end]})

        elif isinstance(end, (pl.LazyFrame, pl.DataFrame)):
            if isinstance(end, pl.LazyFrame):
                end = end.collect()
            assert id_name is not None, "id_name must be specified if end is a UniversalDataFrame"
            assert all([col in end.columns for col in meta_cols_f]) or (len(meta_cols_f) == 0), f"end DataFrame must contain '{meta_cols_f}' columns if they are provided"
            
            if dt_name in end.columns:
                end_df = end[[id_name, dt_name] + meta_cols_f].rename({dt_name: '_BOUNDARY_END_'})
            elif any([x in end.columns for x in ['start_xxx', 'end_xxx']]):
                cols_to_select = [id_name] + [col for col in ['start_xxx', 'end_xxx'] if col in end.columns] + meta_cols_f
                end_df = end[cols_to_select]
                # Only rename columns that exist
                rename_dict = {}
                if 'start_xxx' in end_df.columns:
                    rename_dict['start_xxx'] = '_BOUNDARY_START_'
                if 'end_xxx' in end_df.columns:
                    rename_dict['end_xxx'] = '_BOUNDARY_END_'
                end_df = end_df.rename(rename_dict)
            else:
                raise ValueError(f"end DataFrame must contain either '{dt_name}' or 'start_xxx'/'end_xxx' columns; available columns are {end.columns}")
            
            if isinstance(boundaries, pl.DataFrame):
                assert isinstance(end_df, pl.DataFrame) # for the linter
                if end_df[id_name].n_unique() < end_df.shape[0]:
                    boundaries = pl.concat([boundaries, end_df], how='vertical')
                else:
                    boundaries = boundaries.join(end_df, on=[id_name] + meta_cols_f, how='inner')
            else:
                boundaries = end_df

    # Apply fill values to boundaries DataFrame
    fill_df = None
    if boundaries is not None:
        if id_name is not None:
            # Get unique values from data_structure for filtering
            if isinstance(data_structure, pl.LazyFrame):
                unique_ids = data_structure.select(pl.col(id_name).unique()).collect()[id_name].to_list()
            else:
                unique_ids = data_structure[id_name].unique().to_list()
            boundaries = boundaries.filter(pl.col(id_name).is_in(unique_ids)) # type: ignore
        for k, f_v in {'start': start_fill_value, 'end': end_fill_value}.items():
            # Check if this boundary type exists in the boundaries DataFrame
            boundary_col = '_BOUNDARY_START_' if k == 'start' else '_BOUNDARY_END_'
            if boundary_col in boundaries.columns: # type: ignore
                # Only drop the opposite boundary column if it exists
                drop_col = '_BOUNDARY_START_' if k == 'end' else '_BOUNDARY_END_'
                if drop_col in boundaries.columns:
                    tp_df: pl.DataFrame = boundaries.clone().drop(drop_col).rename({boundary_col: dt_name})
                else:
                    tp_df: pl.DataFrame = boundaries.clone().rename({boundary_col: dt_name})
                
                # If label_levels exist, expand tp_df to include all label levels
                if label_levels and label_name:
                    # Create a DataFrame with all label levels
                    if id_name is not None:
                        # For each unique combination of id_name and meta_cols, add all label levels
                        group_cols = [id_name] + meta_cols_f if meta_cols_f else [id_name]
                        group_cols = [col for col in group_cols if col in tp_df.columns]
                        
                        if group_cols:
                            # Get unique combinations of grouping columns
                            unique_groups = tp_df.select(group_cols).unique()
                            # Create cross product with label levels
                            label_df = pl.DataFrame({label_name: label_levels})
                            tp_df = unique_groups.join(label_df, how='cross')
                            # Add back the datetime and other columns from original tp_df
                            drop_col = '_BOUNDARY_START_' if k == 'end' else '_BOUNDARY_END_'
                            boundary_df = boundaries.clone()
                            if drop_col in boundary_df.columns:
                                boundary_df = boundary_df.drop(drop_col)
                            tp_df = tp_df.join(boundary_df.rename({boundary_col: dt_name}),
                                              on=group_cols, how='left')
                        else:
                            # No grouping columns, just add label levels
                            tp_df = tp_df.with_columns(pl.lit(label_levels[0]).alias(label_name))
                            for label in label_levels[1:]:
                                label_row = tp_df.clone()
                                label_row = label_row.with_columns(pl.lit(label).alias(label_name))
                                tp_df = pl.concat([tp_df, label_row], how='vertical')
                    else:
                        # No id_name, expand for all label levels
                        base_df = tp_df.clone()
                        tp_df = base_df.with_columns(pl.lit(label_levels[0]).alias(label_name))
                        for label in label_levels[1:]:
                            label_row = base_df.clone()
                            label_row = label_row.with_columns(pl.lit(label).alias(label_name))
                            tp_df = pl.concat([tp_df, label_row], how='vertical')
                
                # Ensure all columns from data_structure exist in tp_df with correct types
                # Get schema from data_structure
                if isinstance(data_structure, pl.LazyFrame):
                    data_schema = data_structure.collect_schema()
                else:
                    data_schema = data_structure.schema
                
                tp_df_cols = tp_df.columns if isinstance(tp_df, pl.DataFrame) else tp_df.collect_schema().names()
                
                # Add missing columns with null values but correct data types
                for col_name, col_dtype in data_schema.items():
                    if col_name not in tp_df_cols:
                        tp_df = tp_df.with_columns(pl.lit(None, dtype=col_dtype).alias(col_name))
                
                # Apply fill value only if provided
                if f_v is not None:
                    tp_df = tp_df.with_columns([pl.lit(f_v).alias(col) for col in value_columns])
                
                # Reorder columns to match data_structure, but keep additional columns (like meta_cols)
                if isinstance(data_structure, pl.LazyFrame):
                    data_cols_ordered = data_structure.collect_schema().names()
                else:
                    data_cols_ordered = data_structure.columns
                
                # Get current tp_df columns
                tp_df_current_cols = tp_df.columns if isinstance(tp_df, pl.DataFrame) else tp_df.collect_schema().names()
                
                # Keep columns in data_structure order, then append any extra columns from tp_df
                extra_cols = [col for col in tp_df_current_cols if col not in data_cols_ordered]
                final_column_order = data_cols_ordered + extra_cols
                tp_df = tp_df.select(final_column_order)
                    
                if fill_df is None:
                    fill_df = tp_df
                else:
                    fill_df = pl.concat([fill_df, tp_df], how='vertical')
            

    # Apply trimming by filtering the original data to stay within boundaries
    if trim and boundaries is not None:
        # Join with data on id_name, then filter by time ranges
        if id_name is not None:
            # Convert boundaries to LazyFrame if data_structure is LazyFrame
            if isinstance(data_structure, pl.LazyFrame):
                boundaries_for_join = boundaries.lazy()
            else:
                boundaries_for_join = boundaries
            merged_data = data_structure.join(boundaries_for_join, on=id_name, how='inner') # type: ignore
        else:
            merged_data = data_structure
            assert boundaries.shape[0] == 1, "When id_name is None, boundaries must contain exactly one row"
            for col in boundaries.columns:
                merged_data = merged_data.with_columns(pl.lit(boundaries[col].item()).alias(col))
        
        # Filter to keep only rows within time boundaries
        conditions = []
        
        # Get column names appropriately for LazyFrame or DataFrame
        if isinstance(merged_data, pl.LazyFrame):
            merged_cols = merged_data.collect_schema().names()
        else:
            merged_cols = merged_data.columns
        
        # Check merged_data columns, not boundaries columns
        # Apply inclusive parameter to determine comparison operators
        if '_BOUNDARY_START_' in merged_cols:
            if inclusive in ['both', 'left']:
                conditions.append(pl.col(dt_name) >= pl.col('_BOUNDARY_START_'))
            else:
                conditions.append(pl.col(dt_name) > pl.col('_BOUNDARY_START_'))
        
        if '_BOUNDARY_END_' in merged_cols:
            if inclusive in ['both', 'right']:
                conditions.append(pl.col(dt_name) <= pl.col('_BOUNDARY_END_'))
            else:
                conditions.append(pl.col(dt_name) < pl.col('_BOUNDARY_END_'))
        
        if conditions:
            mask = conditions[0] if len(conditions) == 1 else conditions[0] & conditions[1]
            filtered_data = merged_data.filter(mask)
            # Drop boundary columns
            if isinstance(filtered_data, pl.LazyFrame):
                filtered_cols = filtered_data.collect_schema().names()
            else:
                filtered_cols = filtered_data.columns
            drop_cols = [col for col in ['_BOUNDARY_START_', '_BOUNDARY_END_'] if col in filtered_cols]
            data_structure = filtered_data.drop(drop_cols)
        else:
            data_structure = merged_data
        
    if fill_df is None:
        return data_structure
    else:
        # Ensure both DataFrames are of the same type for concatenation
        if isinstance(data_structure, pl.LazyFrame):
            fill_df_for_concat = fill_df.lazy() if isinstance(fill_df, pl.DataFrame) else fill_df
        else:
            fill_df_for_concat = fill_df.collect() if isinstance(fill_df, pl.LazyFrame) else fill_df
        return pl.concat([data_structure, fill_df_for_concat], how='vertical') # type: ignore