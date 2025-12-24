import polars as pl
from typing import Any, Callable, Dict, List, Optional, Union, Literal, cast, Tuple
from .interpolation import PolarsInterpolationUtils, PolarsDataFrameInterpolationExtension
from .base import UniversalPolarsDataFrameExtension



class PolarsUniversalGroupBy(UniversalPolarsDataFrameExtension):
    """
    A wrapper around a Polars GroupBy object to provide a more flexible,
    pandas-like API for grouped operations.
    """
    def __init__(self, df: pl.DataFrame | pl.LazyFrame, group_by_cols: List[str]):
        super().__init__(df)
        self._group_by_cols = group_by_cols
        # Unpack list to avoid Polars treating it as expressions (breaks map_groups)
        self._grouped = df.group_by(*group_by_cols)

    def agg(self, *aggs: Union[pl.Expr, Dict[str, Union[str, List[str]]]], **named_aggs: pl.Expr) -> pl.DataFrame | pl.LazyFrame:
        """
        Perform standard Polars aggregations with support for pandas-style dictionary syntax.

        Supports both Polars-style expressions and pandas-style dictionary aggregation.

        Parameters
        ----------
        *aggs : pl.Expr or dict
            Polars expressions or dictionary mapping column names to aggregation functions.
            Dictionary values can be single strings or lists of aggregation function names.
        **named_aggs : pl.Expr
            Named aggregation expressions using keyword arguments.

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            DataFrame with aggregated results.

        Examples
        --------
        Polars style::

            .agg(
                pl.col('value').mean().alias('mean_value'),
                max_value=pl.col('value').max()
            )

        Pandas style (dictionary)::

            .agg({'col1': 'mean', 'col2': 'max', 'col3': ['mean', 'max']})
        """
        # Handle dictionary-style aggregation (pandas-like)
        if len(aggs) == 1 and isinstance(aggs[0], dict) and not named_aggs:
            agg_dict = aggs[0]
            expressions = []
            
            for col_name, agg_funcs in agg_dict.items():
                # Handle single aggregation
                if isinstance(agg_funcs, str):
                    agg_funcs = [agg_funcs]
                
                alias_dict: Dict[str, str] = {'nunique': 'n_unique', 'size': 'len'}
                # Handle multiple aggregations for same column
                for agg_func in agg_funcs:
                    try:
                        expr = getattr(pl.col(col_name), alias_dict.get(agg_func, agg_func))().alias(f"{col_name}_{agg_func}" if len(agg_funcs) > 1 else col_name)
                    except AttributeError:
                        raise ValueError(f"Aggregation function '{agg_func}' not supported for column '{col_name}'")
                    
                    expressions.append(expr)
            
            return self._grouped.agg(*expressions)
        
        # Use standard Polars aggregation for expressions
        return self._grouped.agg(*aggs, **named_aggs)

    def apply(self, func: Callable[[pl.DataFrame], pl.DataFrame]) -> pl.DataFrame | pl.LazyFrame:
        """
        Apply a custom function to each group sub-DataFrame.

        This is a wrapper around the powerful but more verbose .map_groups() method.

        Parameters
        ----------
        func : callable
            A function that takes a DataFrame and returns a DataFrame.

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            Result of applying the function to each group.
        """
        return self._grouped.map_groups(func) # type: ignore

    def _apply_window_expr(self, exprs: List[pl.Expr]) -> pl.DataFrame | pl.LazyFrame:
        """Internal helper to apply expressions in a window context."""
        return self._df.with_columns([expr.over(self._group_by_cols) for expr in exprs])

    def interpolate(self,
                   columns: Optional[Union[List[str], str]] = None,
                   by: Optional[str] = None,
                   method: str = 'linear',
                   **kwargs) -> pl.DataFrame | pl.LazyFrame:
        """
        Apply custom interpolation logic over each group.

        Parameters
        ----------
        columns : str, list of str, or None, optional
            Column(s) to interpolate. If None, applies to all columns.
        by : str, optional
            Index column for interpolation ordering.
        method : str, default 'linear'
            Interpolation method to use.
        **kwargs : dict
            Additional keyword arguments passed to the interpolation function.

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            DataFrame with interpolated values.
        """
        # Handle columns parameter
        if columns is None:
            cols = self.columns
        elif isinstance(columns, str):
            cols = [columns]
        else:
            cols = columns
            
        # Filter out index and group columns
        by_cols = [by] if by is not None else []
        group_cols = self._group_by_cols if isinstance(self._group_by_cols, list) else [self._group_by_cols] if self._group_by_cols else []
        exclude_set = set(by_cols + group_cols)
        filtered_cols = [col for col in cols if col not in exclude_set]
        
        # Use the centralized expression builder instead of trying to access DataFrame namespace on column
        interp_expr = [
            PolarsInterpolationUtils.build_interpolation_expr(
                df=self._df, col_name=col, by=by, method=method, **kwargs
            ) for col in filtered_cols
        ]
        return self._apply_window_expr(interp_expr)

    def ffill(self, columns: Optional[Union[List[str], str]] = None, limit: Optional[int] = None, limit_area: Optional[Literal['inside', 'outside']] = None) -> pl.DataFrame | pl.LazyFrame:
        """Forward fills nulls in one or more columns with group awareness."""
        if columns is None:
            columns = [col for col in self.columns if col not in self._group_by_cols]
        elif isinstance(columns, str):
            columns = [columns]
            
        # Create temporary DataFrame helper to access expression builders
        df_helper = PolarsDataFrameInterpolationExtension(self._df)
        fill_exprs = [df_helper._build_ffill_expr(c, limit=limit, limit_area=limit_area).over(self._group_by_cols) for c in columns]
        return self._df.with_columns(fill_exprs)

    def bfill(self, columns: Optional[Union[List[str], str]] = None, limit: Optional[int] = None, limit_area: Optional[Literal['inside', 'outside']] = None) -> pl.DataFrame | pl.LazyFrame:
        """Backward fills nulls in one or more columns with group awareness."""
        if columns is None:
            columns = [col for col in self.columns if col not in self._group_by_cols]
        elif isinstance(columns, str):
            columns = [columns]
            
        # Create temporary DataFrame helper to access expression builders
        df_helper = PolarsDataFrameInterpolationExtension(self._df)
        fill_exprs = [df_helper._build_bfill_expr(c, limit=limit, limit_area=limit_area).over(self._group_by_cols) for c in columns]
        return self._df.with_columns(fill_exprs)

    def fillna(self,
               value: Any = None,
               strategy: Optional[Literal['forward', 'backward', 'min', 'max', 'mean', 'zero', 'one']] = None,
               limit: Optional[int] = None,
               matches_supertype: bool = True,
               columns: Optional[Union[List[str], str]] = None) -> pl.DataFrame | pl.LazyFrame:
        """
        Fill null values in one or more columns with group awareness.

        Parameters
        ----------
        value : any, optional
            Literal value to use for null replacement.
        strategy : {'forward', 'backward', 'min', 'max', 'mean', 'zero', 'one'}, optional
            Strategy for null replacement.
        limit : int, optional
            Maximum number of consecutive nulls to fill.
        matches_supertype : bool, default True
            Ensure replacement values match the column's supertype.
        columns : str, list of str, or None, optional
            Columns to apply filling to. If None, applies to all columns.

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            DataFrame with filled null values.
        """
        if columns is None:
            columns = [col for col in self._df.columns if col not in self._group_by_cols]
        elif isinstance(columns, str):
            columns = [columns]
            
        if value is not None:
            # Direct value replacement with group awareness
            fill_exprs = [pl.col(c).fill_null(value).over(self._group_by_cols) for c in columns]
        elif strategy is not None:
            # Strategy-based filling with group awareness
            fill_exprs = []
            for c in columns:
                if strategy == 'forward':
                    df_helper = PolarsDataFrameInterpolationExtension(self._df)
                    expr = df_helper._build_ffill_expr(c, limit=limit).over(self._group_by_cols)
                elif strategy == 'backward':
                    df_helper = PolarsDataFrameInterpolationExtension(self._df)
                    expr = df_helper._build_bfill_expr(c, limit=limit).over(self._group_by_cols)
                elif strategy == 'mean':
                    expr = pl.col(c).fill_null(pl.col(c).mean().over(self._group_by_cols))
                elif strategy == 'min':
                    expr = pl.col(c).fill_null(pl.col(c).min().over(self._group_by_cols))
                elif strategy == 'max':
                    expr = pl.col(c).fill_null(pl.col(c).max().over(self._group_by_cols))
                elif strategy == 'zero':
                    expr = pl.col(c).fill_null(0)
                elif strategy == 'one':
                    expr = pl.col(c).fill_null(1)
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")
                fill_exprs.append(expr)
        else:
            raise ValueError("Either 'value' or 'strategy' must be provided")
            
        return self._df.with_columns(fill_exprs)

    def ewm(self, column: str, alpha: Optional[float] = None, com: Optional[float] = None, 
            span: Optional[int] = None, half_life: Optional[float] = None, adjust: bool = True, 
            min_periods: int = 1, ignore_nulls: bool = True, **aggregations: str) -> pl.DataFrame | pl.LazyFrame:
        """
        Performs exponential weighted moving calculations with a user-friendly interface.
        
        Args:
            column: The column to apply EWM calculations to
            alpha: Smoothing factor (0 < alpha <= 1). Mutually exclusive with com, span, half_life.
            com: Center of mass. Mutually exclusive with alpha, span, half_life.
            span: Span. Mutually exclusive with alpha, com, half_life.
            half_life: Half-life. Mutually exclusive with alpha, com, span.
            adjust: Whether to use bias adjustment.
            min_periods: Minimum number of observations required to have a value.
            ignore_nulls: Whether to ignore null values.
            **aggregations: Named aggregation functions. Supported: 'mean', 'std', 'var'
            
        Example:
            .ewm('temperature', alpha=0.3, temp_smooth='mean', temp_volatility='std')
            .ewm('price', span=10, price_smooth='mean', adjust=False)
            .ewm('volume', com=5, vol_mean='mean', vol_std='std', min_periods=3)
        """
        # Validate that only one smoothing parameter is provided
        smoothing_params = [alpha, com, span, half_life]
        non_none_params = [p for p in smoothing_params if p is not None]
        
        if len(non_none_params) == 0:
            alpha = 0.5  # Default value
        elif len(non_none_params) > 1:
            raise ValueError("Only one of alpha, com, span, or half_life should be specified")
        
        # Map user-friendly names to Polars EWM methods
        ewm_methods = {
            'mean': 'ewm_mean',
            'std': 'ewm_std', 
            'var': 'ewm_var'
        }
        
        # Build kwargs for the EWM method
        ewm_kwargs = {
            'adjust': adjust,
            'min_periods': min_periods,
            'ignore_nulls': ignore_nulls
        }
        
        # Add the appropriate smoothing parameter
        if alpha is not None:
            ewm_kwargs['alpha'] = alpha
        elif com is not None:
            ewm_kwargs['com'] = com
        elif span is not None:
            ewm_kwargs['span'] = span
        elif half_life is not None:
            ewm_kwargs['half_life'] = half_life
        
        ewm_exprs = []
        for alias_name, agg_type in aggregations.items():
            if agg_type not in ewm_methods:
                available = ', '.join(ewm_methods.keys())
                raise ValueError(f"Unsupported EWM aggregation '{agg_type}'. Available: {available}")
            
            # Get the Polars method name
            polars_method = ewm_methods[agg_type]
            
            # Build the expression with all kwargs
            expr = getattr(pl.col(column), polars_method)(**ewm_kwargs).alias(alias_name)
            ewm_exprs.append(expr)
        
        return self._apply_window_expr(ewm_exprs)

    def resample(
        self,
        time_column: str,
        every: str,
        period: Optional[str] = None,
        offset: Optional[str] = None,
        include_boundaries: bool = False,
        closed: Literal['left', 'right', 'both', 'none'] = 'left',
        label: Literal['left', 'right', 'datapoint'] = 'left',
        start_by: Literal['window', 'datapoint', 'monday'] = 'window',
        **aggs: pl.Expr
    ) -> pl.DataFrame | pl.LazyFrame:
        """
        Downsamples time-series data by a given time interval for each group.
        This is a complete wrapper for the native `group_by_dynamic`.

        Args:
            time_column: The column to use as the time index.
            every: The interval of the windows.
            period: The duration of the windows (e.g., '2h' window every '1h'). Defaults to `every`.
            offset: An offset to shift the window.
            truncate: Truncates the time column to the `every` interval.
            include_boundaries: Whether to include window start and end times in the output.
            closed: Which side of the interval is closed ('left', 'right', 'both', 'none').
            label: Which boundary to use as the label ('left' or 'right').
            start_by: How to determine the start of the first window ('window', 'datapoint', 'monday').
            **aggs: The aggregations to perform on each window.
        """
        # The period defaults to the 'every' interval if not specified
        dynamic_period = period if period is not None else every

        # Ensure expressions have proper aliases
        agg_expressions = []
        for name, expr in aggs.items():
            if isinstance(expr, pl.Expr):
                # Check if expression already has an alias
                expr_str = str(expr)
                if '.alias(' in expr_str:
                    # Expression already has alias, use it directly
                    agg_expressions.append(expr)
                else:
                    # Add alias based on the dictionary key
                    agg_expressions.append(expr.alias(name))
            else:
                # Not an expression, wrap it
                agg_expressions.append(expr)
        
        return self._df.group_by_dynamic(
            time_column,
            every=every,
            period=dynamic_period,
            offset=offset,
            include_boundaries=include_boundaries,
            closed=closed,
            group_by=self._group_by_cols,
            start_by=start_by,
            label=label
        ).agg(agg_expressions)

    def upsample(self, time_column, every) -> pl.DataFrame | pl.LazyFrame:
        """
        Upsamples the time series to a higher frequency by creating a regular time grid.
        
        Args:
            time_column: The datetime column to use for upsampling
            every: The frequency for the new time grid (e.g., '1m', '30s')
        """
        # Get the min and max time for each group
        time_bounds = self._df.group_by(self._group_by_cols).agg(
            pl.min(time_column).alias("min_time"), 
            pl.max(time_column).alias("max_time")
        )
        
        # Create the time grid for each group
        time_grid = time_bounds.with_columns(
            pl.struct(["min_time", "max_time"]).map_elements(
                lambda row: pl.datetime_range(row["min_time"], row["max_time"], every, eager=True),
                return_dtype=pl.List(pl.Datetime)
            ).alias(time_column)
        ).drop("min_time", "max_time").explode(time_column)
        
        # Join with original data
        return time_grid.join(self._df, on=self._group_by_cols + [time_column], how="left") # type: ignore

    def process_time_series_v2(self, **kwargs) -> pl.DataFrame | pl.LazyFrame:
        """
        Process time series data with grouping.
        Delegates to the DataFrame's ud_groupby.process_time_series_v2 method with the groupby columns pre-configured.
        """
        # Ensure group_by parameter uses our groupby columns
        kwargs['group_by'] = self._group_by_cols
        # Call the DataFrame's extension method
        return self._df.epl.process_time_series_v2(**kwargs) # type: ignore
    
    def __getattr__(self, name: str):
        """
        Delegate missing methods to the native polars GroupBy object.
        This allows access to all native polars groupby methods like max(), min(), mean(), etc.
        """
        if hasattr(self._grouped, name):
            attr = getattr(self._grouped, name)
            if callable(attr):
                return attr
            else:
                return attr
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class UniversalPolarsDataFrameGroupByExtension(UniversalPolarsDataFrameExtension):
    def __init__(self, df: pl.DataFrame):
        super().__init__(df)

    def __call__(self, *group_by_cols: str) -> PolarsUniversalGroupBy:
        """
        Creates a SmartGroupBy object.

        Usage:
            df.epl('group1', 'group2').agg(...)
        """
        return PolarsUniversalGroupBy(self._df, list(group_by_cols))
