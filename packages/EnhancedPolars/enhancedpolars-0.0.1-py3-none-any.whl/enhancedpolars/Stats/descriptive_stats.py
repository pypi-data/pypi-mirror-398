"""
Polars Descriptive Statistics Module

This module provides efficient polars expression generators for comprehensive
statistical calculations over grouped columns, including descriptive statistics,
quantiles, correlations, and auto-detection of appropriate statistics by data type.
"""

import polars as pl
from typing import Dict, List, Union, Optional, Any, Literal
from dataclasses import dataclass, field
import numpy as np


@dataclass
class StatsConfig:
    """Configuration class for statistical calculations."""

    # Basic statistics
    include_length: bool = True
    include_count: bool = True
    include_mean: bool = True
    include_std: bool = True
    include_median: bool = True
    include_mad: bool = True  # Median Absolute Deviation
    mad_scale: float = 1.0  # Scale factor for MAD (1.0 = raw MAD, 1.4826 ≈ std equivalent)
    include_min: bool = True
    include_max: bool = True
    include_n_unique: bool = True
    include_unique_values: bool = False  # List of unique values (use with caution for high cardinality)
    include_value_counts: bool = False  # Value counts (frequency of each unique value)
    max_unique_values: Optional[int] = 100  # Limit for unique values/value_counts, None = unlimited

    # Quantiles to calculate
    quantiles: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])

    # Advanced statistics
    include_variance: bool = False
    include_skewness: bool = False
    include_kurtosis: bool = False
    include_sum: bool = False
    include_range: bool = False
    include_iqr: bool = False  # Interquartile Range
    include_autocorrelation: bool = False  # Autocorrelation with lag
    autocorr_lags: List[int] = field(default_factory=lambda: [1])  # Lag periods for autocorrelation

    # Null handling
    include_null_count: bool = False
    include_null_percentage: bool = False

    # Custom prefix for column names
    prefix: str = ""
    suffix: str = ""

    # Decimal precision for quantile naming
    quantile_precision: int = 0  # 0 means auto-detect

    # Mixed-length result handling
    explode_lists: bool = False  # If True, explode list results to separate rows


def safe_combine_expressions(
    df: Union[pl.DataFrame, pl.LazyFrame],
    expression_groups: List[List[pl.Expr]],
    explode_lists: bool = False
) -> Union[pl.DataFrame, pl.LazyFrame]:
    """
    Safely combine expressions that may return different numbers of rows.

    This function handles the common scenario where some expressions return
    single values (like mean, count) while others return lists/arrays
    (like unique_values, value_counts) that may have different lengths.

    Parameters:
    -----------
    df : pl.DataFrame or pl.LazyFrame
        Source dataframe
    expression_groups : List[List[pl.Expr]]
        Groups of expressions to combine
    explode_lists : bool
        If True, explode list columns to separate rows

    Returns:
    --------
    pl.DataFrame or pl.LazyFrame
        Combined result handling mixed-length expressions
    """
    # Combine all expressions
    all_expressions = []
    for group in expression_groups:
        all_expressions.extend(group)

    # Execute the expressions
    if isinstance(df, pl.LazyFrame):
        result = df.select(all_expressions)
        if explode_lists:
            # Find list columns and explode them
            schema = result.collect_schema()
            list_columns = [col for col, dtype in schema.items()
                          if str(dtype).startswith('List[')]
            if list_columns:
                for col in list_columns:
                    result = result.explode(col)
        return result
    else:
        result = df.select(all_expressions)
        if explode_lists:
            # Find list columns and explode them
            list_columns = [col for col, dtype in result.schema.items()
                          if str(dtype).startswith('List[')]
            if list_columns:
                for col in list_columns:
                    result = result.explode(col)
        return result


def generate_comprehensive_stats(
    column: Union[str, List[str]],
    config: Optional[StatsConfig] = None,
    custom_expressions: Optional[Dict[str, pl.Expr]] = None
) -> List[pl.Expr]:
    """
    Generate comprehensive statistical expressions for polars columns.

    This function creates an efficient set of polars expressions that calculate
    various descriptive statistics, quantiles, and custom metrics for given
    column(s), optimized for use with group_by operations.

    The returned expressions work with both eager DataFrames and lazy LazyFrames,
    as they return polars expressions that are evaluated when the query is executed.

    Parameters:
    -----------
    column : str or List[str]
        Column name(s) to calculate statistics for
    config : StatsConfig, optional
        Configuration object specifying which statistics to include
    custom_expressions : Dict[str, pl.Expr], optional
        Dictionary of custom expressions with alias names as keys

    Returns:
    --------
    List[pl.Expr]
        List of polars expressions for statistical calculations

    Examples:
    ---------
    >>> import polars as pl
    >>>
    >>> # Works with eager DataFrames
    >>> df = pl.DataFrame({
    ...     "group": ["A", "A", "B", "B", "C", "C"],
    ...     "value": [1, 2, 3, 4, 5, 6],
    ...     "price": [10.5, 20.3, 30.1, 40.7, 50.2, 60.8]
    ... })
    >>>
    >>> # Single column
    >>> stats_exprs = generate_comprehensive_stats("value")
    >>> result = df.group_by("group").agg(stats_exprs)
    >>>
    >>> # Multiple columns
    >>> stats_exprs = generate_comprehensive_stats(["value", "price"])
    >>> result = df.group_by("group").agg(stats_exprs)
    >>>
    >>> # Also works with lazy LazyFrames
    >>> lazy_df = pl.LazyFrame({
    ...     "group": ["A", "A", "B", "B", "C", "C"],
    ...     "value": [1, 2, 3, 4, 5, 6],
    ...     "price": [10.5, 20.3, 30.1, 40.7, 50.2, 60.8]
    ... })
    >>> stats_exprs = generate_comprehensive_stats("value")
    >>> result = lazy_df.group_by("group").agg(stats_exprs).collect()
    >>>
    >>> # With custom configuration
    >>> config = StatsConfig(
    ...     quantiles=[0.25, 0.50, 0.75],
    ...     include_skewness=True,
    ...     prefix="val_"
    ... )
    >>> stats_exprs = generate_comprehensive_stats("value", config)
    >>> result = df.group_by("group").agg(stats_exprs)
    >>>
    >>> # With custom expressions
    >>> custom_exprs = {
    ...     "value_squared_mean": pl.col("value").pow(2).mean(),
    ...     "value_log_std": pl.col("value").log().std(),
    ...     "price_value_ratio": pl.col("price") / pl.col("value")
    ... }
    >>> stats_exprs = generate_comprehensive_stats("value", custom_expressions=custom_exprs)
    >>> result = df.group_by("group").agg(stats_exprs)
    """
    if config is None:
        config = StatsConfig()

    if custom_expressions is None:
        custom_expressions = {}

    # Handle list of columns by recursively calling for each column
    if isinstance(column, list):
        all_expressions = []
        for col_name in column:
            col_expressions = generate_comprehensive_stats(col_name, config, None)
            all_expressions.extend(col_expressions)

        # Add custom expressions once at the end
        for alias, expr in custom_expressions.items():
            all_expressions.append(expr.alias(alias))

        return all_expressions

    # Single column processing
    col_name = column
    col_expr = pl.col(col_name)
    expressions = []

    # Helper function to create alias
    def make_alias(stat_name: str) -> str:
        return f"{config.prefix}{col_name}_{stat_name}{config.suffix}"

    # Basic count and length statistics
    if config.include_length:
        expressions.append(pl.len().alias(make_alias("length")))

    if config.include_count:
        expressions.append(col_expr.count().alias(make_alias("count")))

    if config.include_null_count:
        expressions.append(col_expr.null_count().alias(make_alias("null_count")))

    if config.include_null_percentage:
        expressions.append(
            (col_expr.null_count() / pl.len() * 100).alias(make_alias("null_pct"))
        )

    # Central tendency
    if config.include_mean:
        expressions.append(col_expr.mean().alias(make_alias("mean")))

    if config.include_median:
        expressions.append(col_expr.median().alias(make_alias("median")))

    # Variability measures
    if config.include_std:
        expressions.append(col_expr.std().alias(make_alias("std")))

    if config.include_variance:
        expressions.append(col_expr.var().alias(make_alias("variance")))

    if config.include_mad:
        # Median Absolute Deviation with optional scaling
        # Scale factor of 1.4826 makes MAD equivalent to standard deviation for normal distributions
        expressions.append(
            ((col_expr - col_expr.median()).abs().median() * config.mad_scale).alias(make_alias("mad"))
        )

    # Range statistics
    if config.include_min:
        expressions.append(col_expr.min().alias(make_alias("min")))

    if config.include_max:
        expressions.append(col_expr.max().alias(make_alias("max")))

    if config.include_range:
        expressions.append(
            (col_expr.max() - col_expr.min()).alias(make_alias("range"))
        )

    if config.include_sum:
        expressions.append(col_expr.sum().alias(make_alias("sum")))

    # Quantiles
    if config.quantiles:
        for q in config.quantiles:
            if 0 <= q <= 1:
                # Format quantile name consistently
                if config.quantile_precision == 0:
                    # Auto-detect precision - use consistent formatting
                    q_percent = q * 100
                    if q_percent == int(q_percent):
                        # Whole percentages: q01, q05, q25, q50, etc.
                        q_name = f"q{int(q_percent):02d}"
                    else:
                        # Decimal percentages: q1_5, q2_5, etc.
                        q_name = f"q{q_percent:.10f}".rstrip('0').rstrip('.').replace('.', '_')
                else:
                    # Use specified precision
                    q_name = f"q{q * 100:.{config.quantile_precision}f}".replace('.', '_')

                expressions.append(col_expr.quantile(q).alias(make_alias(q_name)))

    # Interquartile range (if quartiles are included)
    if config.include_iqr and (0.25 in config.quantiles and 0.75 in config.quantiles):
        expressions.append(
            (col_expr.quantile(0.75) - col_expr.quantile(0.25)).alias(make_alias("iqr"))
        )

    # Uniqueness
    if config.include_n_unique:
        expressions.append(col_expr.n_unique().alias(make_alias("n_unique")))

    if config.include_unique_values:
        # Get unique values (optionally limited to prevent memory issues)
        # Use aggregation to ensure single value return in all contexts
        if config.max_unique_values is not None:
            unique_expr = (
                col_expr.unique()
                .head(config.max_unique_values)
                .implode()  # Always return as list to ensure single value
                .alias(make_alias("unique_values"))
            )
        else:
            unique_expr = col_expr.unique().implode().alias(make_alias("unique_values"))
        expressions.append(unique_expr)

    if config.include_value_counts:
        # Get value counts as a dictionary directly using map_elements
        def value_counts_to_dict(input_data):
            if input_data is None:
                return {}

            # Handle polars Series (which is what imploded value_counts actually returns)
            if hasattr(input_data, 'to_list'):
                # Convert Series to list
                data_list = input_data.to_list()
            elif isinstance(input_data, list):
                data_list = input_data
            else:
                return {}

            # Convert list of structs to dictionary
            result = {}
            for item in data_list:
                if isinstance(item, dict):
                    # Handle struct format: {col_name: value, "count": count}
                    if col_name in item and 'count' in item:
                        result[item[col_name]] = item['count']
                    # Handle alternative struct format where fields might be named differently
                    elif len(item) == 2:
                        keys = list(item.keys())
                        if 'count' in keys:
                            value_key = [k for k in keys if k != 'count'][0]
                            result[item[value_key]] = item['count']
                        else:
                            # Assume first is value, second is count
                            value_key, count_key = keys
                            result[item[value_key]] = item[count_key]
            return result

        if config.max_unique_values is not None:
            value_counts_expr = (
                col_expr.value_counts()
                .head(config.max_unique_values)
                .implode()  # Ensure it's aggregated properly
                .map_elements(value_counts_to_dict, return_dtype=pl.Object)
                .alias(make_alias("value_counts"))
            )
        else:
            value_counts_expr = (
                col_expr.value_counts()
                .implode()  # Ensure it's aggregated properly
                .map_elements(value_counts_to_dict, return_dtype=pl.Object)
                .alias(make_alias("value_counts"))
            )
        expressions.append(value_counts_expr)

    # Advanced statistics (approximations for grouped data)
    if config.include_skewness:
        # Approximate skewness using moment-based formula
        mean_expr = col_expr.mean()
        std_expr = col_expr.std()
        skew_expr = (
            ((col_expr - mean_expr) / std_expr).pow(3).mean()
        ).alias(make_alias("skewness"))
        expressions.append(skew_expr)

    if config.include_kurtosis:
        # Approximate kurtosis using moment-based formula
        mean_expr = col_expr.mean()
        std_expr = col_expr.std()
        kurt_expr = (
            ((col_expr - mean_expr) / std_expr).pow(4).mean() - 3
        ).alias(make_alias("kurtosis"))
        expressions.append(kurt_expr)

    # Autocorrelation (for time series data)
    if config.include_autocorrelation:
        for lag in config.autocorr_lags:
            if lag > 0:
                # Calculate autocorrelation at specified lag
                # autocorr = correlation(x[t], x[t-lag])
                autocorr_expr = pl.corr(
                    col_expr,
                    col_expr.shift(lag)
                ).alias(make_alias(f"autocorr_lag{lag}"))
                expressions.append(autocorr_expr)

    # Add custom expressions
    for alias, expr in custom_expressions.items():
        expressions.append(expr.alias(alias))

    return expressions


def generate_autocorrelation_stats(
    column: str,
    lags: List[int],
    prefix: str = "autocorr_"
) -> List[pl.Expr]:
    """
    Generate autocorrelation expressions for multiple lag periods.

    Autocorrelation measures the linear relationship between a time series
    and a delayed version of itself. Useful for detecting patterns, seasonality,
    and trend persistence in time series data.

    Parameters:
    -----------
    column : str
        Column name to calculate autocorrelations for
    lags : List[int]
        List of lag periods to calculate autocorrelations for
    prefix : str
        Prefix for autocorrelation column names

    Returns:
    --------
    List[pl.Expr]
        List of autocorrelation expressions

    Examples:
    ---------
    >>> # Calculate autocorrelations at lags 1, 2, 5, 10
    >>> autocorr_exprs = generate_autocorrelation_stats("price", [1, 2, 5, 10])
    >>> result = df.group_by("stock").agg(autocorr_exprs)
    >>>
    >>> # Daily, weekly, monthly autocorrelations for daily data
    >>> autocorr_exprs = generate_autocorrelation_stats("sales", [1, 7, 30])
    >>> result = df.select(autocorr_exprs)
    """
    expressions = []
    col_expr = pl.col(column)

    for lag in lags:
        if lag > 0:
            # Calculate autocorrelation: corr(x[t], x[t-lag])
            autocorr_expr = pl.corr(
                col_expr,
                col_expr.shift(lag)
            ).alias(f"{prefix}{column}_lag{lag}")
            expressions.append(autocorr_expr)
        elif lag == 0:
            # Autocorrelation at lag 0 is always 1 (perfect correlation with itself)
            autocorr_expr = pl.lit(1.0).alias(f"{prefix}{column}_lag0")
            expressions.append(autocorr_expr)

    return expressions


def generate_correlation_stats(
    columns: List[str],
    prefix: str = "corr_"
) -> List[pl.Expr]:
    """
    Generate pairwise correlation expressions for multiple columns.

    Parameters:
    -----------
    columns : List[str]
        List of column names to calculate correlations for
    prefix : str
        Prefix for correlation column names

    Returns:
    --------
    List[pl.Expr]
        List of correlation expressions

    Examples:
    ---------
    >>> corr_exprs = generate_correlation_stats(["value", "price", "quantity"])
    >>> result = df.group_by("group").agg(corr_exprs)
    """
    expressions = []

    # Convert to expressions
    col_exprs = [pl.col(col) for col in columns]

    # Generate pairwise correlations
    for i in range(len(col_exprs)):
        for j in range(i + 1, len(col_exprs)):
            corr_expr = pl.corr(col_exprs[i], col_exprs[j]).alias(
                f"{prefix}{columns[i]}_{columns[j]}"
            )
            expressions.append(corr_expr)

    return expressions


def generate_window_stats(
    column: str,
    window_size: int,
    config: Optional[StatsConfig] = None
) -> List[pl.Expr]:
    """
    Generate rolling window statistical expressions.

    Parameters:
    -----------
    column : str
        Column name to calculate rolling statistics for
    window_size : int
        Size of the rolling window
    config : StatsConfig, optional
        Configuration for which statistics to include

    Returns:
    --------
    List[pl.Expr]
        List of rolling window expressions

    Examples:
    ---------
    >>> rolling_exprs = generate_window_stats("value", window_size=3)
    >>> result = df.with_columns(rolling_exprs)
    """
    if config is None:
        config = StatsConfig()

    # Convert column to expression
    col_expr = pl.col(column)
    base_name = column

    expressions = []

    def make_alias(stat_name: str) -> str:
        return f"{config.prefix}{base_name}_rolling_{window_size}_{stat_name}{config.suffix}"

    # Rolling statistics
    if config.include_mean:
        expressions.append(
            col_expr.rolling_mean(window_size).alias(make_alias("mean"))
        )

    if config.include_std:
        expressions.append(
            col_expr.rolling_std(window_size).alias(make_alias("std"))
        )

    if config.include_min:
        expressions.append(
            col_expr.rolling_min(window_size).alias(make_alias("min"))
        )

    if config.include_max:
        expressions.append(
            col_expr.rolling_max(window_size).alias(make_alias("max"))
        )

    if config.include_median:
        expressions.append(
            col_expr.rolling_median(window_size).alias(make_alias("median"))
        )

    if config.quantiles:
        for q in config.quantiles:
            if 0 <= q <= 1:
                q_name = f"q{int(q * 100):02d}"
                expressions.append(
                    col_expr.rolling_quantile(q, window_size=window_size).alias(make_alias(q_name))
                )

    return expressions


# Convenience functions for common use cases
def quick_stats(column: Union[str, List[str]]) -> List[pl.Expr]:
    """Generate basic statistics quickly."""
    config = StatsConfig(
        quantiles=[0.25, 0.50, 0.75],
        include_variance=False,
        include_skewness=False,
        include_kurtosis=False,
        include_sum=False,
        include_range=False
    )
    return generate_comprehensive_stats(column, config)


def full_stats(column: Union[str, List[str]]) -> List[pl.Expr]:
    """Generate comprehensive statistics including advanced metrics."""
    config = StatsConfig(
        quantiles=[0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99],
        include_variance=True,
        include_skewness=True,
        include_kurtosis=True,
        include_sum=True,
        include_range=True,
        include_iqr=True,
        include_null_count=True,
        include_null_percentage=True
    )
    return generate_comprehensive_stats(column, config)


# Intelligent auto-stats functions
def get_column_appropriate_stats(
    df: Union[pl.DataFrame, pl.LazyFrame],
    columns: Optional[List[str]] = None,
    prefix: str = "",
    numeric_config: Optional[StatsConfig] = None,
    numeric_quantiles: Optional[List[float]] = None,
    datetime_config: Optional[StatsConfig] = None,
    string_config: Optional[StatsConfig] = None,
    categorical_config: Optional[StatsConfig] = None,
    boolean_config: Optional[StatsConfig] = None,
    other_config: Optional[StatsConfig] = None
) -> Dict[str, List[pl.Expr]]:
    """
    Automatically determine appropriate statistics for each column based on data type.

    Parameters:
    -----------
    df : pl.DataFrame or pl.LazyFrame
        DataFrame to analyze
    columns : List[str], optional
        Specific columns to analyze. If None, analyzes all columns
    prefix : str
        Prefix for column names in results
    numeric_config : StatsConfig, optional
        Override configuration for numeric columns (Int, Float types)
    datetime_config : StatsConfig, optional
        Override configuration for datetime columns (Date, Datetime, Time, Duration)
    string_config : StatsConfig, optional
        Override configuration for string columns (Utf8)
    categorical_config : StatsConfig, optional
        Override configuration for categorical columns
    boolean_config : StatsConfig, optional
        Override configuration for boolean columns
    other_config : StatsConfig, optional
        Override configuration for other/unknown column types

    Returns:
    --------
    Dict[str, List[pl.Expr]]
        Dictionary mapping column names to appropriate statistical expressions

    Examples:
    ---------
    >>> df = pl.DataFrame({
    ...     "id": [1, 2, 3],
    ...     "name": ["Alice", "Bob", "Charlie"],
    ...     "value": [10.5, 20.3, 30.1],
    ...     "date": ["2023-01-01", "2023-01-02", "2023-01-03"]
    ... }).with_columns(pl.col("date").str.strptime(pl.Date))
    >>>
    >>> # Use defaults
    >>> stats_by_col = get_column_appropriate_stats(df)
    >>>
    >>> # Override numeric column config
    >>> custom_numeric = StatsConfig(quantiles=[0.25, 0.5, 0.75], include_skewness=False)
    >>> stats_by_col = get_column_appropriate_stats(df, numeric_config=custom_numeric)
    >>>
    >>> # Apply different stats to different column types
    >>> for col_name, exprs in stats_by_col.items():
    ...     result = df.select(exprs)
    """
    # Get column information
    schema = df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema
    if columns is None:
        columns = list(schema.keys())

    stats_by_column = {}

    for col_name in columns:
        dtype = schema[col_name]

        if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                     pl.Float32, pl.Float64]:
            # Numeric columns: all statistics make sense
            if numeric_config is not None:
                config = numeric_config
                # Update prefix if it wasn't set in the override config
                if not config.prefix:
                    config.prefix = prefix
            else:
                config = StatsConfig(
                    quantiles=numeric_quantiles or [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99],
                    include_variance=True,
                    include_skewness=True,
                    include_kurtosis=True,
                    include_sum=True,
                    include_range=True,
                    include_iqr=True,
                    include_null_count=True,
                    include_null_percentage=True,
                    prefix=prefix
                )
            stats_by_column[col_name] = generate_comprehensive_stats(col_name, config)

        elif dtype in [pl.Date, pl.Datetime, pl.Time, pl.Duration]:
            # Datetime columns: min, max, range, counts (no mean, std, etc.)
            if datetime_config is not None:
                config = datetime_config
                # Update prefix if it wasn't set in the override config
                if not config.prefix:
                    config.prefix = prefix
            else:
                config = StatsConfig(
                    quantiles=[],  # No quantiles for datetime
                    include_mean=False,
                    include_std=False,
                    include_median=False,
                    include_mad=False,
                    include_variance=False,
                    include_skewness=False,
                    include_kurtosis=False,
                    include_sum=False,
                    include_range=True,
                    include_iqr=False,
                    include_null_count=True,
                    include_null_percentage=True,
                    prefix=prefix
                )
            stats_by_column[col_name] = generate_comprehensive_stats(col_name, config)

        elif dtype in [pl.Utf8, pl.Categorical] or str(dtype).startswith('Categorical'):
            # String/Categorical columns: unique counts, mode, length stats

            # Determine which config to use
            if str(dtype).startswith('Categorical') and categorical_config is not None:
                config = categorical_config
                # Update prefix if it wasn't set in the override config
                if not config.prefix:
                    config.prefix = prefix
            elif dtype == pl.Utf8 and string_config is not None:
                config = string_config
                # Update prefix if it wasn't set in the override config
                if not config.prefix:
                    config.prefix = prefix
            elif categorical_config is not None and str(dtype).startswith('Categorical'):
                config = categorical_config
                if not config.prefix:
                    config.prefix = prefix
            elif string_config is not None and dtype == pl.Utf8:
                config = string_config
                if not config.prefix:
                    config.prefix = prefix
            else:
                # Use default configuration
                config = StatsConfig(
                    quantiles=[],  # No quantiles for strings
                    include_mean=False,
                    include_std=False,
                    include_median=False,
                    include_mad=False,
                    include_min=False,  # Min/max for strings can be confusing
                    include_max=False,
                    include_variance=False,
                    include_skewness=False,
                    include_kurtosis=False,
                    include_sum=False,
                    include_range=False,
                    include_iqr=False,
                    include_n_unique=True,
                    include_unique_values=True,  # Show actual unique values for categorical
                    include_value_counts=True,  # Show value counts for categorical
                    max_unique_values=50,  # Limit for categorical, None = unlimited
                    include_null_count=True,
                    include_null_percentage=True,
                    prefix=prefix
                )

            # Add string-specific expressions
            col_expr = pl.col(col_name)
            string_stats = generate_comprehensive_stats(col_name, config)

            # Add string length statistics
            def make_alias(stat_name: str) -> str:
                return f"{config.prefix}{col_name}_{stat_name}"

            # For categorical, use categories for length operations (much more efficient)
            if str(dtype).startswith('Categorical'):
                # For categorical, we calculate length stats on the categories themselves
                # This is much more efficient than casting each value to string
                string_stats.extend([
                    col_expr.cat.get_categories().str.len_chars().mean().alias(make_alias("avg_char_length")),
                    col_expr.cat.get_categories().str.len_chars().min().alias(make_alias("min_char_length")),
                    col_expr.cat.get_categories().str.len_chars().max().alias(make_alias("max_char_length")),
                    col_expr.mode().first().alias(make_alias("mode"))  # Most common value
                ])
            else:
                # For regular strings, calculate length stats on actual values
                string_stats.extend([
                    col_expr.str.len_chars().mean().alias(make_alias("avg_char_length")),
                    col_expr.str.len_chars().min().alias(make_alias("min_char_length")),
                    col_expr.str.len_chars().max().alias(make_alias("max_char_length")),
                    col_expr.mode().first().alias(make_alias("mode"))  # Most common value
                ])

            stats_by_column[col_name] = string_stats

        elif dtype == pl.Boolean:
            # Boolean columns: counts, true/false ratios
            if boolean_config is not None:
                # User provided custom boolean config - use comprehensive stats
                config = boolean_config
                if not config.prefix:
                    config.prefix = prefix
                stats_by_column[col_name] = generate_comprehensive_stats(col_name, config)
            else:
                # Use default boolean-specific logic
                col_expr = pl.col(col_name)

                def make_alias(stat_name: str) -> str:
                    return f"{prefix}{col_name}_{stat_name}"

                boolean_stats = [
                    col_expr.count().alias(make_alias("count")),
                    col_expr.null_count().alias(make_alias("null_count")),
                    col_expr.sum().alias(make_alias("true_count")),  # Count of True values
                    (col_expr.count() - col_expr.sum()).alias(make_alias("false_count")),
                    (col_expr.sum() / col_expr.count()).alias(make_alias("true_ratio")),
                    col_expr.n_unique().alias(make_alias("n_unique"))
                ]

                stats_by_column[col_name] = boolean_stats

        else:
            # For other/unknown types, use basic stats
            if other_config is not None:
                config = other_config
                # Update prefix if it wasn't set in the override config
                if not config.prefix:
                    config.prefix = prefix
            else:
                config = StatsConfig(
                    quantiles=[],
                    include_mean=False,
                    include_std=False,
                    include_median=False,
                    include_mad=False,
                    include_min=False,
                    include_max=False,
                    include_variance=False,
                    include_skewness=False,
                    include_kurtosis=False,
                    include_sum=False,
                    include_range=False,
                    include_iqr=False,
                    include_n_unique=True,
                    include_null_count=True,
                    include_null_percentage=True,
                    prefix=prefix
                )
            stats_by_column[col_name] = generate_comprehensive_stats(col_name, config)

    return stats_by_column


def generate_smart_stats(
    df: Union[pl.DataFrame, pl.LazyFrame],
    group_by: Optional[Union[str, List[str]]] = None,
    columns: Optional[List[str]] = None,
    prefix: str = "",
    numeric_config: Optional[StatsConfig] = None,
    datetime_config: Optional[StatsConfig] = None,
    string_config: Optional[StatsConfig] = None,
    categorical_config: Optional[StatsConfig] = None,
    boolean_config: Optional[StatsConfig] = None,
    other_config: Optional[StatsConfig] = None,
    numeric_quantiles: Optional[List[float]] = None,
    stack_results: bool = True,
    return_type: Literal['dataframe', 'dictionary'] = 'dataframe'
) -> pl.DataFrame | Dict[str, Any]:
    """
    Generate appropriate statistics for all columns based on their data types,
    optionally grouped by specified columns.

    Parameters:
    -----------
    df : pl.DataFrame or pl.LazyFrame
        DataFrame to analyze
    group_by : str or List[str], optional
        Column(s) to group by before calculating statistics
    columns : List[str], optional
        Specific columns to analyze. If None, analyzes all non-grouping columns
    prefix : str
        Prefix for column names in results
    numeric_config : StatsConfig, optional
        Override configuration for numeric columns (Int, Float types)
    datetime_config : StatsConfig, optional
        Override configuration for datetime columns (Date, Datetime, Time, Duration)
    string_config : StatsConfig, optional
        Override configuration for string columns (Utf8)
    categorical_config : StatsConfig, optional
        Override configuration for categorical columns
    boolean_config : StatsConfig, optional
        Override configuration for boolean columns
    other_config : StatsConfig, optional
        Override configuration for other/unknown column types
    stack_results: bool, optional
        Whether to stack results where the column name is in the first column and the statistics for it are in the remaining columns

    Returns:
    --------
    pl.DataFrame or pl.LazyFrame
        DataFrame with appropriate statistics for each column type

    Examples:
    ---------
    >>> df = pl.DataFrame({
    ...     "group": ["A", "A", "B", "B"],
    ...     "name": ["Alice", "Bob", "Charlie", "David"],
    ...     "value": [10.5, 20.3, 30.1, 40.7],
    ...     "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
    ...     "active": [True, False, True, True]
    ... }).with_columns(pl.col("date").str.strptime(pl.Date))
    >>>
    >>> # Analyze all columns
    >>> result = generate_smart_stats(df)
    >>>
    >>> # Analyze with grouping
    >>> result = generate_smart_stats(df, group_by="group")
    >>>
    >>> # Analyze specific columns
    >>> result = generate_smart_stats(df, columns=["value", "date"])
    >>>
    >>> # Use custom configurations for different column types
    >>> custom_numeric = StatsConfig(quantiles=[0.25, 0.5, 0.75], include_skewness=False)
    >>> result = generate_smart_stats(df, numeric_config=custom_numeric)
    """
    # Get appropriate statistics for each column
    stats_by_column = get_column_appropriate_stats(
        df,
        columns,
        prefix,
        numeric_config=numeric_config,
        datetime_config=datetime_config,
        string_config=string_config,
        categorical_config=categorical_config,
        boolean_config=boolean_config,
        other_config=other_config,
        numeric_quantiles=numeric_quantiles,
    )

    # Exclude grouping columns from analysis
    if group_by is not None:
        if isinstance(group_by, str):
            group_cols = [group_by]
        else:
            group_cols = group_by

        # Remove grouping columns from stats
        for group_col in group_cols:
            if group_col in stats_by_column:
                del stats_by_column[group_col]

    # Flatten all expressions
    all_expressions = []
    for expressions in stats_by_column.values():
        all_expressions.extend(expressions)

    # Apply grouping if specified
    if group_by is not None:
        if isinstance(df, pl.LazyFrame):
            result = df.group_by(group_by).agg(all_expressions)
        else:
            result = df.group_by(group_by).agg(all_expressions)
    else:
        # No grouping - calculate stats for entire dataset
        # Use dummy grouping to ensure list aggregations work correctly
        if isinstance(df, pl.LazyFrame):
            result = df.with_columns(pl.lit(1).alias("_dummy_group")).group_by("_dummy_group").agg(all_expressions).select(pl.exclude("_dummy_group"))
        else:
            result = df.with_columns(pl.lit(1).alias("_dummy_group")).group_by("_dummy_group").agg(all_expressions).select(pl.exclude("_dummy_group"))

     # Collect result if it's a LazyFrame for processing
    if isinstance(result, pl.LazyFrame):
        result = result.collect()

    # Stack results if requested
    if stack_results and len(stats_by_column) > 0:
        # Get all stat column names (excluding group_by columns if present)
        group_cols = []
        if group_by is not None:
            if isinstance(group_by, str):
                group_cols = [group_by]
            else:
                group_cols = list(group_by)


        # Get all columns that are statistics (not grouping columns)
        stat_columns = [col for col in result.columns if col not in group_cols]

        # Create a mapping of original column names to their stat columns
        column_to_stats = {}
        for col_name in stats_by_column.keys():
            col_stats = []
            for stat_col in stat_columns:
                # Check if this stat column belongs to this original column
                if stat_col.startswith(f"{prefix}{col_name}_") or stat_col == f"{prefix}{col_name}":
                    col_stats.append(stat_col)
            if col_stats:
                column_to_stats[col_name] = col_stats

        # Stack the results
        stacked_dfs = []
        for col_name, stat_cols in column_to_stats.items():
            # Create a dataframe for this column's stats
            if group_cols:
                # Include group columns
                col_df = result.select(group_cols + stat_cols)
                # Add column name
                col_df = col_df.with_columns(pl.lit(col_name).alias("column"))
                # Rename stat columns to remove the column prefix
                rename_dict = {}
                for stat_col in stat_cols:
                    # Remove prefix and column name from stat column name
                    new_name = stat_col
                    if prefix:
                        new_name = new_name.replace(prefix, "", 1)
                    if new_name.startswith(f"{col_name}_"):
                        new_name = new_name[len(col_name) + 1:]
                    rename_dict[stat_col] = new_name
                col_df = col_df.rename(rename_dict)
            else:
                # No group columns
                col_df = result.select(stat_cols)
                # Add column name
                col_df = col_df.with_columns(pl.lit(col_name).alias("column"))
                # Rename stat columns
                rename_dict = {}
                for stat_col in stat_cols:
                    new_name = stat_col
                    if prefix:
                        new_name = new_name.replace(prefix, "", 1)
                    if new_name.startswith(f"{col_name}_"):
                        new_name = new_name[len(col_name) + 1:]
                    rename_dict[stat_col] = new_name
                col_df = col_df.rename(rename_dict)

            stacked_dfs.append(col_df)

        if stacked_dfs:
            # Concatenate all column dataframes
            # Use diagonal_relaxed to handle type differences
            result = pl.concat(stacked_dfs, how="diagonal_relaxed")

            # Reorder columns to put 'column' first after group columns
            if group_cols:
                other_cols = [c for c in result.columns if c not in group_cols + ["column"]]
                result = result.select(group_cols + ["column"] + other_cols)
            else:
                other_cols = [c for c in result.columns if c != "column"]
                result = result.select(["column"] + other_cols)

    if return_type == 'dataframe':
        return result

    # Helper function to convert value_counts records to dictionary
    def convert_value_counts_to_dict(value_counts_list, original_col_name):
        """Convert value_counts list of dicts to a simple dict mapping value -> count"""
        if not isinstance(value_counts_list, list) or not value_counts_list:
            return value_counts_list

        # Check if this looks like value_counts output
        if len(value_counts_list) > 0:
            first_item = value_counts_list[0]
            if isinstance(first_item, dict) and 'count' in first_item:
                # Find the value column (should be the original column name)
                value_key = None
                for key in first_item.keys():
                    if key != 'count':
                        value_key = key
                        break

                if value_key:
                    # Convert to simple dict: {value: count, ...}
                    return {item[value_key]: item['count'] for item in value_counts_list}

        return value_counts_list

    # Handle dictionary return type
    result_dict = {}

    # Determine if we have grouping columns
    group_cols = []
    if group_by is not None:
        if isinstance(group_by, str):
            group_cols = [group_by]
        else:
            group_cols = list(group_by)

    if stack_results and 'column' in result.columns:
        # Stacked results: rows represent different columns
        if group_cols:
            # With grouping: {group_value: {column_name: {'stat_name': value, ...}}}
            for row in result.iter_rows(named=True):
                # Extract group key (single value or tuple for multiple group columns)
                if len(group_cols) == 1:
                    group_key = row[group_cols[0]]
                else:
                    group_key = tuple(row[group_col] for group_col in group_cols)

                # Initialize group dict if not exists
                if group_key not in result_dict:
                    result_dict[group_key] = {}

                # Get column name and create its stats dict
                col_name = row['column']
                result_dict[group_key][col_name] = {}

                # Extract all stats for this column (exclude group cols and 'column')
                for stat_col, value in row.items():
                    if stat_col not in group_cols + ['column']:
                        result_dict[group_key][col_name][stat_col] = value
        else:
            # Without grouping: {column_name: {'stat_name': value, ...}}
            for row in result.iter_rows(named=True):
                col_name = row['column']
                result_dict[col_name] = {}

                # Extract all stats for this column (exclude 'column')
                for stat_col, value in row.items():
                    if stat_col != 'column':
                        result_dict[col_name][stat_col] = value
    else:
        # Non-stacked results: columns contain stats with prefixes
        if group_cols:
            # With grouping: {group_value: {column_name: {'stat_name': value, ...}}}
            for row in result.iter_rows(named=True):
                # Extract group key (single value or tuple for multiple group columns)
                if len(group_cols) == 1:
                    group_key = row[group_cols[0]]
                else:
                    group_key = tuple(row[group_col] for group_col in group_cols)

                # Initialize group dict if not exists
                if group_key not in result_dict:
                    result_dict[group_key] = {}

                # Process each column's statistics
                for col_name in stats_by_column.keys():
                    if col_name not in result_dict[group_key]:
                        result_dict[group_key][col_name] = {}

                    # Extract stats for this column
                    for stat_col in row.keys():
                        if stat_col not in group_cols:
                            # Remove prefix and column name to get stat name
                            stat_name = stat_col
                            if prefix:
                                stat_name = stat_name.replace(prefix, "", 1)
                            if stat_name.startswith(f"{col_name}_"):
                                clean_stat_name = stat_name[len(col_name) + 1:]
                                value = row[stat_col]
                                result_dict[group_key][col_name][clean_stat_name] = value
                            elif stat_name == col_name:
                                # Handle case where stat column name is just the column name
                                result_dict[group_key][col_name][stat_name] = row[stat_col]
        else:
            # Without grouping: {column_name: {'stat_name': value, ...}}
            # Should only have one row since no grouping
            if len(result) > 0:
                row = result.row(0, named=True)

                # Process each column's statistics
                for col_name in stats_by_column.keys():
                    result_dict[col_name] = {}

                    # Extract stats for this column
                    for stat_col, value in row.items():
                        # Remove prefix and column name to get stat name
                        stat_name = stat_col
                        if prefix:
                            stat_name = stat_name.replace(prefix, "", 1)
                        if stat_name.startswith(f"{col_name}_"):
                            clean_stat_name = stat_name[len(col_name) + 1:]
                            value = row.get(stat_col, value)
                            result_dict[col_name][clean_stat_name] = value
                        elif stat_name == col_name:
                            # Handle case where stat column name is just the column name
                            result_dict[col_name][stat_name] = value

    return result_dict
