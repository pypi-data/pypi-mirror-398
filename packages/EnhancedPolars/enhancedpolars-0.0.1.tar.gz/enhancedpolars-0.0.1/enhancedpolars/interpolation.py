import polars as pl
from typing import Literal, List, Optional, Any, Callable, Dict, Tuple, Union, Sequence, cast, Iterable
import numpy as np
from collections import Counter
from pathlib import Path
import datetime as dt

# Add parent directory to path for enhanced logging import
from CoreUtilities import get_logger, LogLevel
from .time_integration import aggregate_connected_segments as ag_segs, TimeDeltaLike, add_time_boundaries as atb
from .base import UniversalPolarsDataFrameExtension


# Initialize logger for this module
logger = get_logger("interpolation_polars", level=LogLevel.TRACE, include_emoji=True)



# --- SciPy Prerequisite Check ---
try:
    from scipy.interpolate import (
        BarycentricInterpolator, # type: ignore
        KroghInterpolator, # type: ignore
        PchipInterpolator, # type: ignore
        CubicSpline, # type: ignore
        Akima1DInterpolator # type: ignore
    )
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Define dummy classes if SciPy is not available so the code can still be parsed
    class BarycentricInterpolator: pass
    class KroghInterpolator: pass
    class PchipInterpolator: pass
    class CubicSpline: pass
    class Akima1DInterpolator: pass


class PolarsInterpolationUtils:
    """
    Shared utility class for all Polars interpolation operations.
    
    This eliminates code duplication between DataFrame, GroupBy, and Series extensions
    by providing common methods that can be used across all contexts.
    """
    
    @staticmethod
    def create_null_or_nan_expr(df: pl.DataFrame | pl.LazyFrame, col_name: str) -> pl.Expr:
        """
        Create a dtype-safe null or NaN detection expression using schema context.
        
        Args:
            df: DataFrame containing the column (for schema access)
            col_name: Name of the column to check
            
        Returns:
            Expression that safely checks for null OR NaN (for float types only)
        """
        col_dtype = (df.collect_schema() if hasattr(df, 'collect') else df.schema)[col_name]
        col_expr = pl.col(col_name)
        
        if col_dtype.is_float():
            return col_expr.is_null() | col_expr.is_nan()
        else:
            return col_expr.is_null()
    
    @staticmethod
    def build_ffill_expr(df: pl.DataFrame | pl.LazyFrame, col_name: str, limit: Optional[int] = None, 
                        limit_area: Optional[str] = None) -> pl.Expr:
        """
        Build forward fill expression with dtype-safe null/NaN detection.
        
        Args:
            df: DataFrame containing the column (for schema access)
            col_name: Name of the column to fill
            limit: Maximum number of consecutive nulls to fill
            limit_area: Restricts filling to 'inside' or 'outside' first/last valid values
            
        Returns:
            Expression for forward filling with proper dtype safety
        """
        c = pl.col(col_name)
        is_null_or_nan_expr = PolarsInterpolationUtils.create_null_or_nan_expr(df=df, col_name=col_name)
        
        # Convert NaN to null for float columns, then apply forward_fill
        col_dtype = (df.collect_schema() if hasattr(df, 'collect') else df.schema)[col_name]
        if col_dtype.is_float():
            # For float columns, first convert NaN to null, then forward fill
            c_normalized = pl.when(c.is_nan()).then(None).otherwise(c)
            ffilled_expr = c_normalized.forward_fill(limit=limit)
        else:
            # For non-float columns, use native forward_fill directly
            ffilled_expr = c.forward_fill(limit=limit)

        if limit_area is None:
            return ffilled_expr

        # Find the row number of the first non-null value
        first_valid_idx = (~is_null_or_nan_expr).arg_true().first()
        row_nr = pl.int_range(0, pl.len())

        if limit_area == 'inside':
            fill_mask = is_null_or_nan_expr & (row_nr > first_valid_idx)
            return pl.when(fill_mask).then(ffilled_expr).otherwise(c)
        elif limit_area == 'outside':
            fill_mask = is_null_or_nan_expr & (row_nr < first_valid_idx)
            return pl.when(fill_mask).then(ffilled_expr).otherwise(c)
        else:
            raise ValueError("`limit_area` must be either 'inside' or 'outside'")
    
    @staticmethod
    def build_bfill_expr(df: pl.DataFrame | pl.LazyFrame, col_name: str, limit: Optional[int] = None, 
                        limit_area: Optional[str] = None) -> pl.Expr:
        """
        Build backward fill expression with dtype-safe null/NaN detection.
        
        Args:
            df: DataFrame containing the column (for schema access)
            col_name: Name of the column to fill
            limit: Maximum number of consecutive nulls to fill
            limit_area: Restricts filling to 'inside' or 'outside' first/last valid values
            
        Returns:
            Expression for backward filling with proper dtype safety
        """
        c = pl.col(col_name)
        is_null_or_nan_expr = PolarsInterpolationUtils.create_null_or_nan_expr(df=df, col_name=col_name)
        
        # Convert NaN to null for float columns, then apply backward_fill  
        col_dtype = (df.collect_schema() if hasattr(df, 'collect') else df.schema)[col_name]
        if col_dtype.is_float():
            # For float columns, first convert NaN to null, then backward fill
            c_normalized = pl.when(c.is_nan()).then(None).otherwise(c)
            bfilled_expr = c_normalized.backward_fill(limit=limit)
        else:
            # For non-float columns, use native backward_fill directly
            bfilled_expr = c.backward_fill(limit=limit)

        if limit_area is None:
            return bfilled_expr

        # Find the row number of the last non-null value
        last_valid_idx = (~is_null_or_nan_expr).arg_true().last()
        row_nr = pl.int_range(0, pl.len())

        if limit_area == 'inside':
            fill_mask = is_null_or_nan_expr & (row_nr < last_valid_idx)
            return pl.when(fill_mask).then(bfilled_expr).otherwise(c)
        elif limit_area == 'outside':
            fill_mask = is_null_or_nan_expr & (row_nr > last_valid_idx)
            return pl.when(fill_mask).then(bfilled_expr).otherwise(c)
        else:
            raise ValueError("`limit_area` must be either 'inside' or 'outside'")
    
        
    @staticmethod
    def build_interpolation_expr(df: pl.DataFrame | pl.LazyFrame, 
                               col_name: str, 
                               by: Optional[str] = None,
                               method: str = 'linear',
                               order: Optional[int] = None, 
                               limit: Optional[int] = None,
                               limit_area: Optional[Literal['inside', 'outside']] = None,
                               limit_direction: Optional[Literal['forward', 'backward', 'both']] = None,
                               value: Optional[Any] = None,
                               strategy: Optional[str] = None,
                               **kwargs) -> pl.Expr:
        """
        Centralized expression builder for ALL fill/interpolation operations.
        
        Args:
            df: DataFrame containing the columns (for schema access)
            col_name: Name of the column to process
            method: Method to use - can be interpolation method ('linear', 'nearest', etc.) or fill method ('ffill', 'bfill', 'fillna')
            by: Name of the column to use as x-coordinate (required for interpolation methods)
            order: Order/degree for polynomial methods
            limit: Maximum number of consecutive NaN values to process
            limit_area: Whether to limit to 'inside' or 'outside' existing values
            limit_direction: Direction for limiting ('forward', 'backward', 'both')
            value: Fill value (for fillna method)
            strategy: Fill strategy (for fillna method with strategy)
            **kwargs: Additional arguments passed to interpolators
            
        Returns:
            Expression for the specified operation with proper dtype safety
        """
        c = pl.col(col_name)
        
        # Handle fill operations (ffill, bfill, fillna)
        if method == 'ffill':
            return PolarsInterpolationUtils.build_ffill_expr(df=df, col_name=col_name, limit=limit, limit_area=limit_area)
        elif method == 'bfill':
            return PolarsInterpolationUtils.build_bfill_expr(df=df, col_name=col_name, limit=limit, limit_area=limit_area)
        elif method == 'fillna':
            if value is not None:
                return c.fill_null(value)
            elif strategy is not None:
                valid_strategies = ['forward', 'backward', 'min', 'max', 'mean', 'zero']
                if strategy not in valid_strategies:
                    raise ValueError(f"Unknown strategy: {strategy}. Valid: {valid_strategies}")
                from typing import cast
                return c.fill_null(strategy=cast(Any, strategy))
            else:
                raise ValueError("Either 'value' or 'strategy' required for fillna")
        
        # Handle interpolation operations (require 'by' parameter)
        if by is None:
            raise ValueError("'by' parameter required for interpolation methods")
        
        x = pl.col(by)
        
        # Create dtype-safe null/NaN detection expressions
        is_null_or_nan_expr = PolarsInterpolationUtils.create_null_or_nan_expr(df=df, col_name=col_name)
        is_not_null_or_nan_expr = ~is_null_or_nan_expr

        # --- Native methods ---
        if method in ('linear', 'time', 'slinear', 'nearest', 'zero'):
            logger.debug(f"⚡ Using native Polars interpolation method: {method}")
            
            if method == 'zero':
                logger.trace("🔬 Using zero-order hold (forward fill)")
                # Use proper null/NaN handling for float columns
                return PolarsInterpolationUtils.build_ffill_expr(df=df, col_name=col_name, limit=limit, limit_area=limit_area)
            
            elif method in ('linear', 'time', 'slinear'):
                logger.trace(f"🔬 Building linear interpolation expression", metadata={'method': method})
                
                # Check if column needs dtype conversion for interpolation compatibility
                col_dtype = (df.collect_schema() if hasattr(df, 'collect') else df.schema)[col_name]
                needs_conversion = col_dtype in [pl.Int8, pl.Int16, pl.UInt8, pl.UInt16]
                
                working_col = c  # Default to original column
                if needs_conversion:
                    logger.debug(f"🔧 Column {col_name} needs dtype conversion from {col_dtype} for interpolation")
                    # Convert column to compatible dtype within the expression
                    if col_dtype in [pl.Int8, pl.Int16]:
                        working_col = c.cast(pl.Int32)
                        logger.trace(f"🔧 Converting {col_name} from {col_dtype} to Int32")
                    elif col_dtype in [pl.UInt8, pl.UInt16]:
                        working_col = c.cast(pl.UInt32)
                        logger.trace(f"🔧 Converting {col_name} from {col_dtype} to UInt32")
                
                if by is not None:
                    # Use native polars interpolate_by when index column is specified
                    interpolated = working_col.interpolate_by(by)
                    logger.trace("✅ Using native .interpolate_by() method")
                else:
                    # Use native polars interpolate when no index column
                    interpolated = working_col.interpolate(method='linear') 
                    logger.trace("✅ Using native .interpolate() method")
                logger.trace("✅ Linear interpolation expression built successfully")
                
            elif method == 'nearest':
                logger.trace("🔬 Building nearest neighbor interpolation expression")
                if by is not None:
                    # For nearest with by column, use native polars nearest
                    interpolated = c.interpolate(method='nearest')
                else:
                    # Use native nearest interpolation  
                    interpolated = c.interpolate(method='nearest')
                logger.trace("✅ Nearest neighbor interpolation expression built")
            
            # For linear/time/slinear, the native methods already handle extrapolation correctly
            # No additional extrapolation handling needed
            
            # Apply limits directly in the expression (will be handled at DataFrame level)
            final_interpolated = interpolated
            
            # Apply limit_area constraints 
            if limit_area is not None:
                # Note: limit_area is handled at the DataFrame level after expression evaluation
                pass
            
            # Apply limit_direction constraints
            if limit_direction == 'forward':
                # Use forward fill only with proper null/NaN handling
                final_interpolated = PolarsInterpolationUtils.build_ffill_expr(df=df, col_name=col_name, limit=limit, limit_area=limit_area)
            elif limit_direction == 'backward':
                # Use backward fill only with proper null/NaN handling
                final_interpolated = PolarsInterpolationUtils.build_bfill_expr(df=df, col_name=col_name, limit=limit, limit_area=limit_area)
            # 'both' is default - no change needed
            
            # Apply consecutive limit
            if limit is not None:
                # Note: limit is handled at the DataFrame level after expression evaluation
                pass
            
            return pl.when(is_null_or_nan_expr).then(final_interpolated).otherwise(c)

        # --- SciPy-based Methods ---
        if not SCIPY_AVAILABLE:
            logger.error(f"❌ SciPy not available for method '{method}'")
            raise ImportError(f"Method '{method}' requires SciPy. Please run: pip install scipy")

        logger.debug(f"🧪 Using SciPy-based interpolation method: {method}")

        if method == 'quadratic': order = 2
        elif method == 'cubic': order = 3
            
        if method in ('polynomial', 'barycentric', 'krogh', 'quadratic', 'cubic') and order is None:
            logger.error(f"❌ Order parameter required for method '{method}'")
            raise ValueError(f"Method '{method}' requires the 'order' parameter.")
            
        logger.trace(f"🔬 Prepared SciPy method: {method}, order: {order}, kwargs: {kwargs}")

        def _apply_scipy_interp(series: Sequence[pl.Series]) -> pl.Series:
            x_series, y_series = series[0], series[1]
            
            # Use the Series namespace for safe dtype checking
            is_null_mask = y_series.epl.isnull() # type: ignore
            
            null_count = is_null_mask.sum()
            total_count = len(y_series)
            logger.trace(f"🔬 Processing series: {null_count}/{total_count} null values")
            
            if not is_null_mask.any(): 
                logger.trace("✅ No null values found, returning original series")
                return y_series

            x_known, y_known = x_series.filter(~is_null_mask).to_numpy(), y_series.filter(~is_null_mask).to_numpy()
            x_interp = x_series.filter(is_null_mask).to_numpy()

            min_points = order + 1 if order is not None else 2
            logger.trace(f"🔬 Data validation: {len(y_known)} known points, need ≥{min_points}")
            
            if len(y_known) < min_points:
                logger.error(f"❌ Insufficient data points: {len(y_known)} < {min_points}")
                raise ValueError(f"Not enough data points ({len(y_known)}) for '{method}' interpolation. Need at least {min_points} points.")
            
            # Check for duplicate x values which cause scipy interpolation to fail
            unique_x_count = len(np.unique(x_known))
            if unique_x_count < len(x_known):
                logger.error(f"❌ Duplicate x values detected: {len(x_known)} total, {unique_x_count} unique")
                raise ValueError(f"Duplicate x values detected for '{method}' interpolation. SciPy interpolation requires distinct x values.")
            
            try:
                logger.trace(f"🔬 Selecting interpolator class for method: {method}")
                # Select the interpolator class
                InterpolatorClass = {
                    'polynomial': BarycentricInterpolator, 'barycentric': BarycentricInterpolator,
                    'quadratic': BarycentricInterpolator, 'cubic': BarycentricInterpolator,
                    'spline': Akima1DInterpolator, 'akima': Akima1DInterpolator,
                    'krogh': KroghInterpolator,
                    'pchip': PchipInterpolator,
                    'cubicspline': CubicSpline,
                }[method]

                logger.trace(f"🔬 Creating {InterpolatorClass.__name__} with {len(x_known)} points")
                # Unpack **kwargs directly into the SciPy constructor
                interpolator = InterpolatorClass(x_known, y_known, **kwargs)
                y_interp = interpolator(x_interp)
                logger.trace(f"✅ SciPy interpolation completed: interpolated {len(x_interp)} values")
                
                # Create a full-length series with interpolated values at null positions
                result = y_series.clone()
                null_indices = is_null_mask.arg_true().to_numpy()
                for i, interp_val in enumerate(y_interp):
                    result = result.scatter(null_indices[i], interp_val)
                
                return result
            
            except Exception as e:
                logger.error(f"❌ SciPy interpolation failed for method '{method}': {str(e)}")
                raise RuntimeError(f"SciPy interpolation failed for method '{method}': {str(e)}") from e

        return pl.map_batches([x, c], _apply_scipy_interp, return_dtype=pl.Float64)



class PolarsDataFrameInterpolationExtension(UniversalPolarsDataFrameExtension):
    def __init__(self, df: Union[pl.DataFrame, pl.LazyFrame]):
        super().__init__(df)

    def add_time_boundaries(
        self,
        dt_name: str,
        start: Optional[pl.LazyFrame | pl.DataFrame | dt.datetime] = None,
        end: Optional[pl.LazyFrame | pl.DataFrame | dt.datetime] = None,
        id_name: Optional[str] = None,
        label_name: Optional[str] = None,
        value_name: Optional[Union[str, List[str]]] = None,
        start_fill_value: Optional[Any] = None,
        end_fill_value: Optional[Any] = None,
        meta_cols: Optional[List[str]] = None,
        trim: bool = True,
        inclusive: Literal['both', 'left', 'right', 'neither'] = 'both',
    ) -> pl.LazyFrame | pl.DataFrame:
            return atb(data_structure=self._df,
                        dt_name=dt_name,
                        start=start,
                        end=end,
                        id_name=id_name,
                        label_name=label_name,
                        value_name=value_name,
                        start_fill_value=start_fill_value,
                        end_fill_value=end_fill_value,
                        meta_cols=meta_cols,
                        inclusive=inclusive,
                        trim=trim
                    )

    def _build_ffill_expr(self, col_name: str, limit: Optional[int] = None, limit_area: Optional[str] = None) -> pl.Expr:
        """Build forward fill expression using shared utility."""
        return PolarsInterpolationUtils.build_ffill_expr(df=self._df, col_name=col_name, limit=limit, limit_area=limit_area)

    def _build_bfill_expr(self, col_name: str, limit: Optional[int] = None, limit_area: Optional[str] = None) -> pl.Expr:
        """Build backward fill expression using shared utility."""
        return PolarsInterpolationUtils.build_bfill_expr(df=self._df, col_name=col_name, limit=limit, limit_area=limit_area)

    def _build_interpolation_expr(self, col_name: str, by: str, method: str, order: Optional[int] = None, **kwargs) -> pl.Expr:
        """Build interpolation expression using shared utility."""
        return PolarsInterpolationUtils.build_interpolation_expr(df=self._df, col_name=col_name, by=by, method=method, order=order, **kwargs)

    def upsample(self, time_column: str, every: str, by: Optional[List[str]] = None) -> pl.DataFrame | pl.LazyFrame:
        """
        Upsamples the DataFrame to a higher frequency by creating a regular time grid.
        
        Args:
            time_column: The datetime column to use for upsampling
            every: The frequency for the new time grid (e.g., '1m', '30s')
            by: Optional list of columns to group by
            
        Returns:
            DataFrame with regular time grid, suitable for chaining
            
        Example:
            df.epl.upsample("timestamp", "1m", by=["device_id"])
        """
        if by is None:
            by = []
            
        if not by:
            # No grouping - simple time grid for entire DataFrame
            min_time = (cast(pl.LazyFrame, self._df).select(pl.min(time_column)).collect() if self.is_lazy else cast(pl.DataFrame, self._df).select(pl.min(time_column))).item()
            max_time = (cast(pl.LazyFrame, self._df).select(pl.max(time_column)).collect() if self.is_lazy else cast(pl.DataFrame, self._df).select(pl.max(time_column))).item()

            time_grid = pl.DataFrame({
                time_column: pl.datetime_range(min_time, max_time, every, eager=True)
            })
        else:
            # Grouped upsampling
            time_bounds = self._df.group_by(by).agg(
                pl.min(time_column).alias("min_time"), 
                pl.max(time_column).alias("max_time")
            )
            
            time_grid = time_bounds.with_columns(
                pl.struct(["min_time", "max_time"]).map_elements(
                    lambda row: pl.datetime_range(row["min_time"], row["max_time"], every, eager=True),
                    return_dtype=pl.List(pl.Datetime)
                ).alias(time_column)
            ).drop("min_time", "max_time").explode(time_column)
        
        # Join with original data
        join_cols = [time_column] + by
        return time_grid.join(self._df, on=join_cols, how="left")  # type: ignore

    def interpolate(self, 
                        columns: Optional[Union[List[str], str]] = None, 
                        by: Optional[str] = None, 
                        method: Union[str, Dict[str, str]] = 'linear',
                        group_by: Optional[List[str]] = None, 
                        suffix: str = "_interp",
                        order: Optional[Union[int, Dict[str, int]]] = None,
                        limit: Optional[int] = None,
                        limit_area: Optional[Literal['inside', 'outside']] = None,
                        limit_direction: Optional[Literal['forward', 'backward', 'both']] = None,
                        inplace: bool = True,
                        exclude_cols: Optional[List[str]] = None,
                        **kwargs) -> pl.DataFrame | pl.LazyFrame:
        """
        Interpolates multiple columns at once with powerful auto-detection and flexible options.
        
        Args:
            columns: List of numeric columns to interpolate. If None, auto-detects all numeric columns.
            by: The column to use as x-coordinate for interpolation. If None, attempts to find datetime column.
            method: Interpolation method. Can be:
                   - str: Single method for all columns (e.g., 'linear')
                   - Dict[str, str]: Per-column methods (e.g., {'temp': 'linear', 'pressure': 'cubic'})
            group_by: Optional list of columns to group by for grouped interpolation
            suffix: Suffix to add to interpolated column names (ignored if inplace=True)
            order: Order for polynomial/spline methods. Can be:
                   - int: Single order for all columns
                   - Dict[str, int]: Per-column orders (e.g., {'temp': 2, 'pressure': 3})
            limit: Maximum number of consecutive NaN values to interpolate
            limit_area: Whether to limit interpolation to 'inside' or 'outside' existing values
            limit_direction: Direction for limiting ('forward', 'backward', 'both')
            inplace: If True, replaces original columns instead of creating new ones with suffix
            exclude_cols: List of columns to exclude from auto-detection
            **kwargs: Additional keyword arguments passed to the interpolation method
            
        Returns:
            DataFrame with interpolated columns added or replaced
            
        Examples:
            # Auto-detect all numeric columns and datetime index
            df.epl.interpolate_cols(group_by=["device_id"])
            
            # Specific columns with custom method
            df.epl.interpolate_cols(
                columns=["temperature", "pressure"], 
                by="timestamp", 
                method="cubic",
                group_by=["device_id"]
            )
            
            # Replace original columns (inplace)
            df.epl.interpolate_cols(
                columns=["hr", "bp"], 
                by="timestamp", 
                method="linear",
                group_by=["patient_id"],
                inplace=True
            )
            
            # Advanced scipy interpolation
            df.epl.interpolate_cols(
                columns=["signal"], 
                by="time", 
                method="pchip",
                group_by=["sensor_id"],
                bc_type="natural"  # scipy kwarg
            )
        """
        
        logger.debug(f"🔧 DataFrame interpolate starting", metadata={
            'columns': columns, 'by': by, 'method': method, 'group_by': group_by,
            'suffix': suffix, 'order': order, 'inplace': inplace, 'dataframe_shape': self.shape
        })
        
        # --- Step 0: Normalize columns parameter ---
        if isinstance(columns, str):
            columns = [columns]
        
        # --- Step 1: Auto-detect the index column if not provided (for methods that need it) ---
        methods_needing_by = self._get_methods_needing_by_parameter(method)
        
        if methods_needing_by and by is None:
            logger.trace("🔬 Auto-detecting index column...")
            # Look for datetime columns first
            datetime_cols = [
                col for col, dtype in self.schema.items()
                if dtype in [pl.Datetime, pl.Date]
            ]
            logger.trace(f"🔬 Found datetime columns: {datetime_cols}")
            
            if len(datetime_cols) == 1:
                by = datetime_cols[0]
                logger.debug(f"✅ Auto-detected index column: {by}")
            else:
                logger.error(f"❌ Cannot auto-detect index column: found {len(datetime_cols)} datetime columns")
                raise ValueError("Could not auto-detect index column. Please specify 'by' parameter.")
        elif by is not None:
            logger.trace(f"🔬 Using specified index column: {by}")
        else:
            logger.trace(f"🔬 No index column needed for method(s): {method}")
        
        # --- Step 2: Auto-detect columns to interpolate if not provided ---
        if columns is None:
            logger.trace("🔬 Auto-detecting columns to interpolate...")
            # Auto-detect numeric columns, excluding index and groupby columns
            exclude_cols_set = set([by] + (group_by or []) + (exclude_cols or []))
            logger.trace(f"🔬 Excluding columns: {exclude_cols_set}")
            
            numeric_types = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64]
            columns = [
                col for col, dtype in self.schema.items()
                if col not in exclude_cols_set and any(dtype == numeric_type for numeric_type in numeric_types)
            ]
            
            logger.debug(f"✅ Auto-detected numeric columns: {columns}")
            
            if not columns:
                logger.error("❌ No numeric columns found for auto-detection")
                raise ValueError("No numeric columns found for interpolation. Please specify columns explicitly.")
        else:
            logger.trace(f"🔬 Using specified columns: {columns}")
        
        # --- Step 3: Build interpolation expressions ---
        logger.debug(f"📝 Building interpolation expressions for {len(columns)} columns")
        interp_exprs = []
        for col in columns:
            logger.trace(f"🔬 Processing column: {col}")
            
            # Get per-column method and order if specified
            if isinstance(method, dict):
                col_method = method.get(col, 'linear')  # Default to linear if not specified
                logger.trace(f"🔬 Per-column method for {col}: {col_method}")
            else:
                col_method = method
                logger.trace(f"🔬 Using global method for {col}: {col_method}")
                
            if isinstance(order, dict):
                col_order = order.get(col, None)  # Default to None if not specified
                logger.trace(f"🔬 Per-column order for {col}: {col_order}")
            else:
                col_order = order
                logger.trace(f"🔬 Using global order for {col}: {col_order}")
            
            # Create the interpolation expression with per-column parameters
            logger.trace(f"🔬 Creating interpolation expression for {col}: method={col_method}, order={col_order}")
            expr = PolarsInterpolationUtils.build_interpolation_expr(
                df=self._df, col_name=col, by=by, method=col_method, order=col_order, **kwargs
            )
            
            # Apply grouping if specified
            if group_by:
                logger.trace(f"🔬 Applying grouping by {group_by} for column {col}")
                expr = expr.over(group_by)
            
            # Determine the alias (output column name)
            alias = col if inplace else f"{col}{suffix}"
            logger.trace(f"🔬 Column {col}: {'inplace replacement' if inplace else f'creating new column {alias}'}")
            
            interp_exprs.append(expr.alias(alias))
        
        # --- Step 4: Apply the interpolation ---
        logger.debug(f"⚡ Applying {len(interp_exprs)} interpolation expressions")
        
        # DEBUG: Check data types before interpolation
        logger.debug(f"🔬 DataFrame dtypes before interpolation: {self._df.dtypes}")
        logger.debug(f"🔬 DataFrame schema before interpolation: {self._df.schema}")
        
        # Check if any columns being interpolated have invalid types
        for col in columns:
            col_dtype = self.schema[col]
            logger.debug(f"🔬 Column {col} dtype: {col_dtype}")
            if col_dtype not in [pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.UInt64, pl.UInt32]:
                logger.error(f"❌ Column {col} has invalid dtype for interpolation: {col_dtype}")
        
        # Check if the 'by' column has valid type  
        if by:
            by_dtype = self.schema[by]
            logger.debug(f"🔬 By column {by} dtype: {by_dtype}")
            valid_by_types = [pl.Date, pl.Datetime, pl.Int64, pl.Int32, pl.UInt64, pl.UInt32, pl.Float32, pl.Float64]
            if by_dtype not in valid_by_types:
                logger.error(f"❌ By column {by} has invalid dtype for interpolation: {by_dtype}")
        
        result = self._df.with_columns(interp_exprs)
        
        
        # --- Step 5: Apply limit constraints at DataFrame level ---
        # Only apply DataFrame-level limits for methods that don't handle them at expression level
        needs_dataframe_limits = self._needs_dataframe_level_limits(method, limit, limit_area, limit_direction)
        
        if needs_dataframe_limits:
            # Determine which limits need DataFrame-level processing
            df_limit = limit if not self._method_handles_limit_at_expression_level(method) else None
            df_limit_area = limit_area if not self._method_handles_limit_area_at_expression_level(method) else None
            df_limit_direction = limit_direction  # Always needs DataFrame-level processing
            
            logger.debug(f"🔧 Applying DataFrame-level limit constraints: limit={df_limit}, limit_area={df_limit_area}, limit_direction={df_limit_direction}")
            result = self._apply_interpolation_limits(
                df=result, 
                original_df=self._df,
                columns=columns,
                limit=df_limit,
                limit_area=df_limit_area, 
                limit_direction=df_limit_direction,
                inplace=inplace,
                suffix=suffix,
                group_by=group_by
            )
        
        logger.debug(f"✅ DataFrame interpolation completed: {self.shape} → {UniversalPolarsDataFrameExtension(result).shape}")
        
        return result

    def _method_handles_limit_at_expression_level(self, method: Union[str, List[str], Dict[str, str]]) -> bool:
        """Check if method can handle limit parameter at expression level."""
        if isinstance(method, dict):
            # If any method in dict can't handle it, we need DataFrame-level processing
            return all(self._method_handles_limit_at_expression_level(m) for m in method.values())
        elif isinstance(method, list):
            return all(self._method_handles_limit_at_expression_level(m) for m in method)
        else:
            # Only ffill and bfill can handle limit at expression level
            return method in ('ffill', 'bfill')
    
    def _method_handles_limit_area_at_expression_level(self, method: Union[str, List[str], Dict[str, str]]) -> bool:
        """Check if method can handle limit_area parameter at expression level."""
        if isinstance(method, dict):
            return all(self._method_handles_limit_area_at_expression_level(m) for m in method.values())
        elif isinstance(method, list):
            return all(self._method_handles_limit_area_at_expression_level(m) for m in method)
        else:
            # Only ffill and bfill can handle limit_area at expression level
            return method in ('ffill', 'bfill')
    
    def _needs_dataframe_level_limits(self, method: Union[str, List[str], Dict[str, str]], 
                                     limit: Optional[int], limit_area: Optional[str], 
                                     limit_direction: Optional[str]) -> bool:
        """Determine if any limit constraints need DataFrame-level processing."""
        if limit_direction is not None:
            return True  # limit_direction always needs DataFrame-level processing
        
        if limit is not None and not self._method_handles_limit_at_expression_level(method):
            return True
            
        if limit_area is not None and not self._method_handles_limit_area_at_expression_level(method):
            return True
            
        return False

    def _get_methods_needing_by_parameter(self, method: Union[str, List[str], Dict[str, str]]) -> bool:
        """Determine if any methods in the specification need a 'by' parameter."""
        methods_not_needing_by = {'ffill', 'bfill', 'fillna'}
        
        if isinstance(method, dict):
            return any(m not in methods_not_needing_by for m in method.values())
        elif isinstance(method, list):
            return any(m not in methods_not_needing_by for m in method)
        else:
            return method not in methods_not_needing_by

    def _apply_interpolation_limits(self, 
                                   df: pl.DataFrame | pl.LazyFrame, 
                                   original_df: pl.DataFrame | pl.LazyFrame,
                                   columns: List[str],
                                   limit: Optional[int] = None,
                                   limit_area: Optional[Literal['inside', 'outside']] = None, 
                                   limit_direction: Optional[Literal['forward', 'backward', 'both']] = None,
                                   inplace: bool = False,
                                   suffix: str = "_interp",
                                   group_by: Optional[List[str]] = None) -> pl.DataFrame:
        """
        Apply limit constraints to interpolated results at DataFrame level.
        
        This method implements the limit logic using actual DataFrame operations
        rather than expressions, allowing for complex consecutive null counting.
        """
        result = cast(pl.LazyFrame, df).collect() if hasattr(df, 'collect') else cast(pl.DataFrame, df)  # Ensure we have a DataFrame to work with
        original_df = cast(pl.LazyFrame, original_df).collect() if hasattr(original_df, 'collect') else cast(pl.DataFrame, original_df)

        for col in columns:
            target_col = col if inplace else f"{col}{suffix}"
            original_col = col
            
            # Get the original and interpolated series
            original_series = original_df[original_col] 
            interpolated_series = result[target_col]
            
            # Create mask for originally null values
            original_null_mask = original_series.is_null()
            if original_series.dtype.is_float():
                original_null_mask = original_null_mask | original_series.is_nan()
            
            # Apply limit constraints
            constrained_series = self._apply_series_limits(
                original_series=original_series,
                interpolated_series=interpolated_series, 
                original_null_mask=original_null_mask,
                limit=limit,
                limit_area=limit_area,
                limit_direction=limit_direction
            )
            
            # Update the result DataFrame
            result = result.with_columns(constrained_series.alias(target_col))
        
        return result
    
    def _apply_series_limits(self,
                           original_series: pl.Series,
                           interpolated_series: pl.Series,
                           original_null_mask: pl.Series,
                           limit: Optional[int] = None,
                           limit_area: Optional[Literal['inside', 'outside']] = None,
                           limit_direction: Optional[Literal['forward', 'backward', 'both']] = None) -> pl.Series:
        """Apply limit constraints to a single series."""
        result_series = interpolated_series
        
        # Apply consecutive limit with direction
        if limit is not None:
            # Simple approach: identify consecutive null runs and limit them
            result_values = interpolated_series.to_list()
            original_values = original_series.to_list()
            null_mask_values = original_null_mask.to_list()
            direction = limit_direction or 'forward'  # Default to 'forward' if not specified (matches pandas)
            
            
            i = 0
            while i < len(null_mask_values):
                if null_mask_values[i]:  # Found start of null run
                    run_start = i
                    # Find end of consecutive null run
                    while i < len(null_mask_values) and null_mask_values[i]:
                        i += 1
                    run_end = i
                    run_length = run_end - run_start
                    
                    # If run exceeds limit, revert excess values based on direction
                    if run_length > limit:
                        if direction == 'forward':
                            # Keep first 'limit' values, revert the rest
                            for j in range(run_start + limit, run_end):
                                result_values[j] = original_values[j]
                        elif direction == 'backward':
                            # Keep last 'limit' values, revert the rest  
                            for j in range(run_start, run_end - limit):
                                result_values[j] = original_values[j]
                        else:  # direction == 'both'
                            # Apply limit from both ends (pandas behavior)
                            # Keep first 'limit' values AND last 'limit' values
                            if run_length > 2 * limit:
                                # Revert middle values that exceed both limits
                                for j in range(run_start + limit, run_end - limit):
                                    result_values[j] = original_values[j]
                            # If run_length <= 2 * limit, keep all values (no reversion needed)
                else:
                    i += 1
            
            result_series = pl.Series(result_values)
        
        # Apply limit_area constraints (inside/outside existing values) 
        if limit_area is not None:
            # Convert to working with lists for simplicity
            result_values = result_series.to_list()
            original_values = original_series.to_list()
            null_mask_values = original_null_mask.to_list()
            
            # Find first and last valid (non-null) indices
            first_valid_idx = None
            last_valid_idx = None
            for i, is_null in enumerate(null_mask_values):
                if not is_null:
                    if first_valid_idx is None:
                        first_valid_idx = i
                    last_valid_idx = i
            
            if first_valid_idx is not None and last_valid_idx is not None:
                for i in range(len(result_values)):
                    if null_mask_values[i]:  # Originally null
                        if limit_area == 'inside':
                            # Only allow interpolation between first and last valid
                            if i < first_valid_idx or i > last_valid_idx:
                                result_values[i] = original_values[i]
                        elif limit_area == 'outside':
                            # Only allow interpolation outside first and last valid
                            if first_valid_idx <= i <= last_valid_idx:
                                result_values[i] = original_values[i]
                
                result_series = pl.Series(result_values)
        
        return result_series

    def rolling(
        self,
        index_column: str,
        period: str,
        group_by: Optional[List[str]] = None,
        columns: Optional[List[str]] = None,
        default_agg: str = "mean",
        suffix: str = "_rolling",
        closed: Literal['left', 'right', 'both', 'none'] = 'none',
        offset: Optional[str] = None,
        inplace: bool = False,
        **aggs: Tuple[str, Union[str, pl.Expr, Callable]],
    ) -> pl.DataFrame | pl.LazyFrame:
        """
        Performs rolling window aggregation on a DataFrame with flexible column handling.

        This method acts as a wrapper around Polars' `rolling` function. It applies
        the rolling window over the `index_column`. If `group_by` is provided, the
        rolling operation is performed independently for each group.

        Args:
            index_column: The name of the datetime/temporal or integer column to roll over.
            period: The length of the rolling window (e.g., '1d', '2h', '15m').
            group_by: An optional list of column names to group by before the rolling operation.
            columns: List of columns to apply default aggregation to. If None and no aggs provided,
                     applies to all numeric columns except index_column and group_by columns.
            default_agg: Default aggregation function to apply to columns when no specific aggs provided.
            suffix: Suffix to add to aggregated column names when using columns parameter.
            closed: Sets which side of the interval is closed. One of {'left', 'right', 'both', 'none'}.
            offset: An optional offset to shift the window boundaries (e.g., '-1d').
            inplace: If True, replace original columns. If False, create new columns with suffix.
            **aggs: Keyword arguments where the key is the desired alias for the new
                    column and the value is a tuple of (source_column, aggregation_function).
                    The aggregation_function can be a string (e.g., 'sum', 'mean'),
                    a Polars expression (e.g., pl.col('value').quantile(0.75)),
                    or a callable that takes a column name and returns a Polars expression.

        Returns:
            A new Polars DataFrame with the rolling aggregated data.

        Examples:
            # Using explicit aggregations
            df.epl.rolling(
                index_column='timestamp', 
                period='1h',
                group_by=['device_id'],
                temp_avg=('temperature', 'mean'),
                pressure_max=('pressure', 'max')
            )
            
            # Using default aggregation on specific columns
            df.epl.rolling(
                index_column='timestamp',
                period='30m', 
                group_by=['device_id'],
                columns=['temperature', 'pressure'],
                default_agg='mean',
                suffix='_smooth'
            )
            
            # Auto-detect numeric columns (backwards compatible with rolling_smooth)
            df.epl.rolling(
                index_column='timestamp',
                period='30m',
                group_by=['device_id']
            )
        """
        
        # Sort the dataframe once, as rolling operations require sorted data.
        sort_cols = [index_column] + (group_by or [])
        sorted_df = self._df.sort(sort_cols)
        
        # --- Step 1: Determine what columns to aggregate ---
        if aggs and columns:
            raise ValueError("Cannot specify both 'columns' and explicit '**aggs'. Choose one approach.")
        
        agg_expressions = []
        
        if aggs:
            # Explicit aggregations provided - supports any column type including categorical/string
            for alias, (source_column, agg_func) in aggs.items():
                base_expr = pl.col(source_column)

                if isinstance(agg_func, str):
                    # Simple string aggregation functions (mean, max, min, etc.)
                    if hasattr(base_expr, agg_func):
                        final_expr = getattr(base_expr, agg_func)()
                    else:
                        raise AttributeError(f"The aggregation function '{agg_func}' is not a valid Polars expression method.")
                elif isinstance(agg_func, pl.Expr):
                    # Direct Polars expression - supports any operation including categorical/string
                    final_expr = agg_func
                elif callable(agg_func):
                    # Callable that returns a Polars expression - full flexibility for custom operations
                    final_expr = agg_func(source_column)
                else:
                    raise TypeError(f"Aggregation function for '{alias}' must be a string, Polars expression, or callable, not {type(agg_func)}.")

                agg_expressions.append(final_expr.alias(alias))
                
        else:
            # Use columns parameter or auto-detect numeric columns
            if columns is None:
                # Auto-detect numeric columns for default aggregations only
                # When using custom aggs, any column type can be specified explicitly
                exclude_cols = [index_column] + (group_by or [])
                numeric_types = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64]
                columns = [
                    col for col, dtype in zip(sorted_df.columns, sorted_df.dtypes)
                    if col not in exclude_cols and any(dtype == numeric_type for numeric_type in numeric_types)
                ]
                
                if not columns:
                    raise ValueError("No numeric columns found for default aggregation. Please specify columns explicitly or use **aggs for custom aggregations on non-numeric columns.")
            
            # Apply default aggregation to specified columns
            used_aliases = set()  # Track used aliases to avoid duplicates
            
            for col in columns:
                if hasattr(pl.col(col), default_agg):
                    final_expr = getattr(pl.col(col), default_agg)()
                    # Create alias based on inplace parameter
                    alias = col if inplace else f"{col}{suffix}"
                    
                    # Check for duplicates
                    if alias in used_aliases:
                        # Add counter to make unique
                        counter = 2
                        while f"{alias}_{counter}" in used_aliases:
                            counter += 1
                        alias = f"{alias}_{counter}"
                    
                    used_aliases.add(alias)
                    agg_expressions.append(final_expr.alias(alias))
                else:
                    raise AttributeError(f"The aggregation function '{default_agg}' is not a valid Polars expression method.")

        # --- Step 2: Perform the rolling aggregation ---
        rolling_result = sorted_df.rolling(
            index_column=index_column,
            period=period,
            group_by=group_by,
            closed=closed,
            offset=offset,
        ).agg(agg_expressions)

        rolling_result = cast(pl.LazyFrame, rolling_result).collect() if hasattr(rolling_result, 'collect') else cast(pl.DataFrame, rolling_result)
        
        # Fix Polars bug: rolling aggregations produce inf instead of null for all-null windows
        for col in rolling_result.columns:
            if rolling_result[col].dtype in [pl.Float64, pl.Float32]:
                inf_count = rolling_result.select(pl.col(col).is_infinite().sum()).item()
                if inf_count > 0:
                    rolling_result = rolling_result.with_columns(
                        pl.when(pl.col(col).is_infinite())
                        .then(None)
                        .otherwise(pl.col(col))
                        .alias(col)
                    )

        # --- Step 3: Decide what to return based on inplace ---
        if not inplace:
            # Join the aggregated results back to the sorted original dataframe.
            join_keys = [index_column] + (group_by or [])
            return sorted_df.join(rolling_result, on=join_keys, how="left")  # type: ignore
        else:
            # Return rolling results but preserve metadata columns
            # Find metadata columns in the original dataframe
            metadata_cols = [col for col in sorted_df.columns if col.endswith('_meta_count')]
            if metadata_cols:
                # Join metadata columns back to rolling results
                join_keys = [index_column] + (group_by or [])
                metadata_df = sorted_df.select(join_keys + metadata_cols)
                return rolling_result.join(metadata_df, on=join_keys, how="left") # type: ignore
            else:
                return rolling_result


    def resample(self,
                 time_column: str,
                 every: str,
                 group_by: Optional[List[str]] = None,
                 columns: Optional[List[str]] = None,
                 default_agg: str = "mean",
                 suffix: str = "_resampled",
                 period: Optional[str] = None,
                 offset: Optional[str] = None,
                 include_boundaries: bool = True,
                 closed: Literal['left', 'right', 'both', 'none'] = 'left',
                 label: Literal['left', 'right', 'datapoint'] = 'left',
                 start_by: Literal['window', 'datapoint', 'monday'] = 'window',
                 **aggs: Union[pl.Expr, Callable]) -> pl.DataFrame | pl.LazyFrame:
        """
        Downsamples time-series data by a given time interval with flexible column handling.
        
        This method acts as a wrapper around Polars' `group_by_dynamic` function. It applies
        time-based grouping and aggregation over the `time_column`. If `group_by` is provided,
        the operation is performed independently for each group.

        Args:
            time_column: The column to use as the time index for resampling.
            every: The interval of the windows (e.g., '1h', '30m', '1d').
            group_by: Optional list of column names to group by before resampling.
            columns: List of columns to apply default aggregation to. If None and no aggs provided,
                     applies to all numeric columns except time_column and group_by columns.
            default_agg: Default aggregation function to apply to columns when no specific aggs provided.
            suffix: Suffix to add to aggregated column names when using columns parameter.
            period: The duration of the windows (e.g., '2h' window every '1h'). Defaults to `every`.
            offset: An offset to shift the window boundaries (e.g., '-1h').
            include_boundaries: Whether to include window start and end times in the output.
            closed: Which side of the interval is closed. One of {'left', 'right', 'both', 'none'}.
            label: Which boundary to use as the label ('left', 'right', 'datapoint').
            start_by: How to determine the start of the first window ('window', 'datapoint', 'monday').
            **aggs: Keyword arguments where the key is the desired alias and value is a Polars expression
                    or a callable that returns a Polars expression. Supports any column type including
                    categorical/string data when using custom expressions or callables.

        Returns:
            A new Polars DataFrame with the resampled and aggregated data.

        Examples:
            # Using explicit aggregations
            df.epl.resample(
                time_column='timestamp',
                every='1h',
                group_by=['device_id'],
                temperature_mean=pl.col('temperature').mean(),
                pressure_max=pl.col('pressure').max()
            )
            
            # Using default aggregation on specific columns
            df.epl.resample(
                time_column='timestamp',
                every='30m',
                group_by=['device_id'],
                columns=['temperature', 'pressure'],
                default_agg='mean',
                suffix='_avg'
            )
            
            # Auto-detect numeric columns for resampling
            df.epl.resample(
                time_column='timestamp',
                every='1h',
                group_by=['device_id']
            )
        """
        
        # --- Step 1: Determine what columns to aggregate ---
        if aggs and columns:
            raise ValueError("Cannot specify both 'columns' and explicit '**aggs'. Choose one approach.")
        
        agg_expressions = []
        
        if aggs:
            # Explicit aggregations provided - supports any column type including categorical/string
            for col_name, agg_spec in aggs.items():
                if isinstance(agg_spec, list):
                    # Handle list of aggregation function names
                    for agg_func in agg_spec:
                        if isinstance(agg_func, str):
                            # Convert string to Polars expression
                            expr = getattr(pl.col(col_name), agg_func)()
                            alias_name = f"{col_name}_{agg_func}"
                            agg_expressions.append(expr.alias(alias_name))
                        else:
                            # Assume it's already a Polars expression
                            agg_expressions.append(agg_func)
                elif isinstance(agg_spec, str):
                    # Handle single aggregation function name
                    expr = getattr(pl.col(col_name), agg_spec)()
                    alias_name = f"{col_name}_{agg_spec}"
                    agg_expressions.append(expr.alias(alias_name))
                elif callable(agg_spec):
                    # Callable that returns a Polars expression - full flexibility for custom operations
                    agg_expressions.append(agg_spec().alias(col_name))
                else:
                    # Assume it's a Polars expression
                    agg_expressions.append(agg_spec.alias(col_name))
        else:
            # Use columns parameter or auto-detect numeric columns
            if columns is None:
                # Auto-detect numeric columns for default aggregations only
                # When using custom aggs, any column type can be specified explicitly
                exclude_cols = [time_column] + (group_by or [])
                numeric_types = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64]
                columns = [
                    col for col, dtype in self.schema.items()
                    if col not in exclude_cols and any(dtype == numeric_type for numeric_type in numeric_types)
                ]
                
                if not columns:
                    raise ValueError("No numeric columns found for default aggregation. Please specify columns explicitly or use **aggs for custom aggregations on non-numeric columns.")
            
            # Apply default aggregation to specified columns
            for col in columns:
                if hasattr(pl.col(col), default_agg):
                    final_expr = getattr(pl.col(col), default_agg)()
                    alias = f"{col}{suffix}"
                    agg_expressions.append(final_expr.alias(alias))
                else:
                    raise AttributeError(f"The aggregation function '{default_agg}' is not a valid Polars expression method.")

        # --- Step 2: Perform the resampling ---
        # The period defaults to the 'every' interval if not specified
        dynamic_period = period if period is not None else every
        
        # Check for metadata columns and include them in aggregation
        metadata_cols = [col for col in self.columns if '_meta_count' in col]
        for meta_col in metadata_cols:
            # Sum the metadata counts during resampling
            agg_expressions.append(pl.col(meta_col).sum().alias(meta_col))

        return self._df.group_by_dynamic(
            time_column,
            every=every,
            period=dynamic_period,
            offset=offset,
            include_boundaries=include_boundaries,
            closed=closed,
            group_by=group_by,
            start_by=start_by,
            label=label
        ).agg(agg_expressions)

    def ffill(self, columns: List[str], limit: Optional[int] = None, limit_area: Optional[Literal['inside', 'outside']] = None, 
              group_by: Optional[List[str]] = None, suffix: str = "_filled", inplace: bool = True) -> pl.DataFrame | pl.LazyFrame:
        """Forward fills nulls in one or more columns with optional group awareness and suffix."""
        if group_by:
            # Create expressions with group awareness
            fill_exprs = [self._build_ffill_expr(c, limit=limit, limit_area=limit_area).over(group_by).alias(c if inplace else f"{c}{suffix}") for c in columns]
        else:
            fill_exprs = [self._build_ffill_expr(c, limit=limit, limit_area=limit_area).alias(c if inplace else f"{c}{suffix}") for c in columns]
        return self._df.with_columns(fill_exprs)

    def bfill(self, columns: List[str], limit: Optional[int] = None, limit_area: Optional[Literal['inside', 'outside']] = None,
              group_by: Optional[List[str]] = None, suffix: str = "_filled", inplace: bool = True) -> pl.DataFrame | pl.LazyFrame:
        """Backward fills nulls in one or more columns with optional group awareness and suffix."""
        if group_by:
            # Create expressions with group awareness
            fill_exprs = [self._build_bfill_expr(c, limit=limit, limit_area=limit_area).over(group_by).alias(c if inplace else f"{c}{suffix}") for c in columns]
        else:
            fill_exprs = [self._build_bfill_expr(c, limit=limit, limit_area=limit_area).alias(c if inplace else f"{c}{suffix}") for c in columns]
        return self._df.with_columns(fill_exprs)

    def fillna(self,
               value: Any = None,
               strategy: Optional[Literal['forward', 'backward', 'min', 'max', 'mean', 'zero', 'one']] = None,
               limit: Optional[int] = None,
               matches_supertype: bool = True,
               columns: Optional[List[str]] = None,
               group_by: Optional[List[str]] = None,
               suffix: str = "_filled", inplace: bool = True) -> pl.DataFrame | pl.LazyFrame:
        """Fills null values in one or more columns with optional group awareness and suffix."""
        if columns is None:
            columns = [col for col in self.columns if group_by is None or col not in group_by]
            
        if value is not None:
            if group_by:
                fill_exprs = [pl.col(c).fill_null(value).over(group_by).alias(c if inplace else f"{c}{suffix}") for c in columns]
            else:
                fill_exprs = [pl.col(c).fill_null(value).alias(c if inplace else f"{c}{suffix}") for c in columns]
        elif strategy is not None:
            fill_exprs = []
            for c in columns:
                if strategy == 'forward':
                    expr = self._build_ffill_expr(c, limit=limit)
                elif strategy == 'backward':
                    expr = self._build_bfill_expr(c, limit=limit)
                elif strategy == 'mean':
                    expr = pl.col(c).fill_null(pl.col(c).mean())
                elif strategy == 'min':
                    expr = pl.col(c).fill_null(pl.col(c).min())
                elif strategy == 'max':
                    expr = pl.col(c).fill_null(pl.col(c).max())
                elif strategy == 'zero':
                    expr = pl.col(c).fill_null(0)
                elif strategy == 'one':
                    expr = pl.col(c).fill_null(1)
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")
                    
                # Apply group and suffix logic
                if group_by:
                    expr = expr.over(group_by)
                expr = expr.alias(c if inplace else f"{c}{suffix}")
                    
                fill_exprs.append(expr)
        else:
            raise ValueError("Either 'value' or 'strategy' must be provided")
            
        return self._df.with_columns(fill_exprs)



    def process_time_series_v2(self,
                              time_column: str,
                              operations: List[str],
                              group_by: Optional[List[str]] = None,
                              
                              # Global column control
                              target_columns: Optional[List[str]] = None,
                              exclude_columns: Optional[List[str]] = None,

                              ### Operation-specific parameters (can be single values or lists for repeated operations)
                              
                              # Upsample/Resample shared parameters
                              every: Optional[Union[str, List[str]]] = None,  # frequency for upsample/resample
                              
                              # Resample parameters  
                              resample_default_agg: Union[str, List[str]] = 'mean',
                              resample_suffix: Union[str, List[str]] = '_resampled',
                              resample_period: Optional[Union[str, List[str]]] = None,
                              resample_offset: Optional[Union[str, List[str]]] = None,
                              resample_include_boundaries: Union[bool, List[bool]] = True,
                              resample_closed: Union[Literal['left', 'right', 'both', 'none'], List[Literal['left', 'right', 'both', 'none']]] = 'left',
                              resample_label: Union[Literal['left', 'right', 'datapoint'], List[Literal['left', 'right', 'datapoint']]] = 'left',
                              resample_start_by: Union[Literal['window', 'datapoint', 'monday'], List[Literal['window', 'datapoint', 'monday']]] = 'window',
                              resample_aggs: Optional[Union[Dict[str, pl.Expr], List[Dict[str, pl.Expr]]]] = None,
                              
                              # Interpolate parameters
                              interpolate_method: Union[str, List[str], Dict[str, str]] = 'linear',
                              interpolate_suffix: Union[str, List[str]] = '_interp', 
                              interpolate_order: Optional[Union[int, List[int], Dict[str, int]]] = None,
                              interpolate_exclude_cols: Optional[Union[List[str], List[List[str]]]] = None,
                              interpolate_kwargs: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
                              
                              # Fill parameters (ffill, bfill, fillna)
                              fill_method: Union[str, List[str]] = 'ffill',  # 'ffill', 'bfill', 'fillna'
                              fill_suffix: Union[str, List[str]] = '_filled',
                              fill_limit: Optional[Union[int, List[int]]] = None,
                              fill_limit_area: Optional[Union[Literal['inside', 'outside'], List[Literal['inside', 'outside']]]] = None,
                              fill_value: Optional[Union[Any, List[Any]]] = None,
                              fill_strategy: Optional[Union[Literal['forward', 'backward', 'min', 'max', 'mean', 'zero', 'one'], List[Literal['forward', 'backward', 'min', 'max', 'mean', 'zero', 'one']]]] = None,
                              
                              # Rolling parameters
                              rolling_period: Optional[Union[str, List[str]]] = None,
                              rolling_default_agg: Union[str, List[str]] = 'mean', 
                              rolling_suffix: Union[str, List[str]] = '_rolling',
                              rolling_closed: Union[Literal['left', 'right', 'both', 'none'], List[Literal['left', 'right', 'both', 'none']]] = 'none',
                              rolling_offset: Optional[Union[str, List[str]]] = None,
                              rolling_aggs: Optional[Union[Dict[str, Union[str, pl.Expr]], List[Dict[str, Union[str, pl.Expr]]]]] = None,

                              # Output control
                              simple_column_names: bool = True, # TODO: change this later
                              inplace: bool = True,  # Whether to replace original columns or create new ones
                              
                              # Metadata tracking
                              track_metadata: bool = True,
                              metadata_suffix: str = '_meta',
                              ) -> pl.DataFrame | pl.LazyFrame:
        """
        Robust time series processing pipeline with per-column control and operation validation.
        
        Args:
            time_column: The datetime column for time-based operations
            operations: List of operations to perform. Valid: ['upsample', 'resample', 'interpolate', 'ffill', 'bfill', 'fillna', 'ffill->bfill', 'rolling']
                       Must be unique OR repeated operations must have matching list parameters
            group_by: Optional grouping columns for grouped operations
            target_columns: Specific columns to process (auto-detects numeric if None)
            exclude_columns: Columns to exclude from auto-detection
            column_configs: Per-column operation parameters. Format:
                          {'column_name': {'operation_name': {'param': value}}}
            
            # Global parameters (can be single values or lists for repeated operations)
            every: Time frequency for upsample/resample operations
            resample_default_agg: Aggregation method for downsampling. Can be:
                        - str: Single aggregation for all columns (e.g., 'mean')
                        - List[str]: Different aggregations for repeated resample operations
                        - Dict[str, str/List/Expr]: Per-column aggregations where:
                          * str: Single aggregation for that column
                          * List[str]: Multiple aggregations for that column (creates multiple output columns)
                          * pl.Expr: Custom expression for that column
                          * List[pl.Expr]: Multiple custom expressions for that column
            resample_suffix: Suffix for resampled columns
            
            interpolate_method: Interpolation method. Can be:
                        - str: Single method for all columns (e.g., 'linear')
                        - List[str]: Different methods for repeated interpolate operations
                        - Dict[str, str]: Per-column methods (e.g., {'temp': 'linear', 'pressure': 'cubic'})
            interpolate_order: Order for polynomial methods. Can be:
                        - int: Single order for all columns
                        - List[int]: Different orders for repeated operations
                        - Dict[str, int]: Per-column orders (e.g., {'temp': 2, 'pressure': 3})
            interpolate_suffix: Suffix for interpolated columns
            interpolate_kwargs: Additional scipy parameters
            
            fill_method: Fill method ('ffill', 'bfill', 'fillna', 'ffill->bfill')
                        'ffill->bfill' runs forward fill then backward fill sequentially with same parameters
            fill_value: Value for fillna
            fill_limit: Max consecutive fills
            fill_suffix: Suffix for filled columns
            
            rolling_period: Rolling window size
            rolling_default_agg: Aggregation method
            rolling_suffix: Suffix for rolling columns
            rolling_offset: Offset for rolling windows
            
            inplace: Whether to replace original columns instead of creating new ones. Note: Automatically set to True 
                     for downsampling operations (time index changes make original retention impossible)
            simple_column_names: When False (default), concatenates all operation suffixes (e.g., HR_mean_interp_rolling_filled).
                               When True and inplace is True, uses column names from the most recent branch point.
                               For example: HR -> [HR_min, HR_max] -> [HR_min_filled, HR_max_filled] becomes [HR_min, HR_max].
                               If no branch point exists, uses the original column name.
            
            track_metadata: Whether to create metadata count columns (>0 = original data, 0 = imputed)
            metadata_suffix: Suffix for metadata columns
            
            yaml_save_path: Optional path to save the configuration as YAML for reproducibility.
                           The saved file will include all parameters and metadata about the operation.
            
        Returns:
            Processed DataFrame with column name tracking and optional metadata columns
        """
        # Validate operations
        valid_operations = {'upsample', 'resample', 'interpolate', 'ffill', 'bfill', 'fillna', 'ffill->bfill', 'rolling'}
        invalid_ops = set(operations) - valid_operations
        if invalid_ops:
            raise ValueError(f"Invalid operations: {invalid_ops}. Valid: {valid_operations}")
        
        # Validate repeated operations have matching parameter lists
        op_counts = Counter(operations)
        repeated_ops = [op for op, count in op_counts.items() if count > 1]
        
        if repeated_ops:
            for op in repeated_ops:
                count = op_counts[op]
                if op == 'resample' and every is not None:
                    if not isinstance(every, list) or len(every) != count:
                        raise ValueError(f"Operation '{op}' appears {count} times but every is not a list of length {count}")
                elif op == 'interpolate':
                    if not isinstance(interpolate_method, list) or len(interpolate_method) != count:
                        raise ValueError(f"Operation '{op}' appears {count} times but interpolate_method is not a list of length {count}")
                elif op in ['ffill', 'bfill', 'fillna', 'ffill->bfill']:
                    if not isinstance(fill_method, list) or len(fill_method) != count:
                        raise ValueError(f"Operation '{op}' appears {count} times but fill_method is not a list of length {count}")
                elif op == 'rolling':
                    if not isinstance(rolling_period, list) or len(rolling_period) != count:
                        raise ValueError(f"Operation '{op}' appears {count} times but rolling_period is not a list of length {count}")
        
        # Auto-detect target columns if not specified
        if target_columns is None:
            # Exclude metadata columns from auto-detection
            exclude_cols = set([time_column] + (group_by or []) + (exclude_columns or []))
            exclude_cols.update([col for col in self.columns if metadata_suffix in col])  # Exclude existing metadata columns
            
            numeric_types = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64]
            target_columns = [
                col for col, dtype in self.schema.items()
                if col not in exclude_cols and any(dtype == numeric_type for numeric_type in numeric_types)
            ]
            
        if not target_columns:
            raise ValueError("No target columns found. Please specify target_columns explicitly.")
        
        # Initialize enhanced column tracking
        # Structure: {source_column: {operation_order: {before_columns, after_columns, operation, operation_instance, parameters}}}
        enhanced_column_tracking = {col: {} for col in target_columns}
        
        # Initialize simple column history tracking (kept for backward compatibility)
        column_history = {col: {} for col in target_columns}  # original -> {iteration: {new_name: source_name}}
        current_columns = {col: [col] for col in target_columns}  # current mapping: original -> [current_names]
        result_df = self._df
        
        # Initialize metadata tracking if enabled
        if track_metadata:
            metadata_columns = {}  # original_col -> count_col mapping
            metadata_exprs = []
            
            for col in target_columns:
                # Create count column: >0 = original data points, 0 = imputed
                count_col_name = f"{col}{metadata_suffix}_count"  
                metadata_columns[col] = count_col_name
                # Create dtype-aware expression for metadata tracking
                col_dtype = (self._df.collect_schema() if hasattr(self._df, 'collect') else self._df.schema)[col]
                if col_dtype.is_float():
                    not_null_expr = (~pl.col(col).is_null()) & (~pl.col(col).is_nan())
                else:
                    not_null_expr = ~pl.col(col).is_null()
                metadata_exprs.append(
                    pl.when(not_null_expr).then(1).otherwise(0).alias(count_col_name)
                )
            
            # Add initial metadata columns
            result_df = result_df.with_columns(metadata_exprs)
        else:
            metadata_columns = {}
        
        # Track operation execution for repeated operations
        op_execution_counts = Counter()
        operation_counter = 0  # Track total operations executed
        
        logger.debug(f"🚀 Starting time series processing pipeline", metadata={
            'operations': operations, 'target_columns': target_columns, 'group_by': group_by,
            'dataframe_shape': UniversalPolarsDataFrameExtension(result_df).shape, 'track_metadata': track_metadata
        })
        
        # Execute operations in order using unified approach
        for operation in operations:
            operation_counter += 1
            op_execution_counts[operation] += 1
            execution_index = op_execution_counts[operation] - 1
            
            logger.debug(f"🔧 Executing operation {operation_counter}/{len(operations)}: {operation} (instance #{op_execution_counts[operation]})")
            logger.trace(f"🔬 Pre-operation dataframe shape: {UniversalPolarsDataFrameExtension(result_df).shape}")
            
            # Get current parameters for this execution
            def get_param(param, default=None):
                if isinstance(param, list):
                    return param[execution_index] if execution_index < len(param) else default
                return param if param is not None else default
            
            # Get current columns to operate on from our simple tracking
            if operation in ['ffill', 'bfill', 'ffill->bfill']:
                # For fill operations, only process the LATEST transformed columns (ignore originals)
                # Use the enhanced tracking system to get current columns properly
                current_column_names = []
                if enhanced_column_tracking:
                    logger.debug(f"🔬 Enhanced tracking available with {len(enhanced_column_tracking)} source columns")
                    for orig_col in current_columns.keys():
                        latest_cols = get_current_columns_from_tracking(enhanced_column_tracking, orig_col)
                        logger.debug(f"🔬 For {orig_col}, tracking returned: {latest_cols}")
                        current_column_names.extend(latest_cols)
                    logger.debug(f"🔬 All latest columns from tracking: {current_column_names}")
                else:
                    # Fallback to simple logic if tracking not available
                    logger.debug(f"🔬 No enhanced tracking available, using fallback")
                    for col_list in current_columns.values():
                        current_column_names.extend(col_list)
                logger.debug(f"🔬 Fill operation using columns: {current_column_names}")
            else:
                # For other operations, use all available columns
                current_column_names = []
                for col_list in current_columns.values():
                    current_column_names.extend(col_list)
            
            # Debug logging
            logger.debug(f"🔬 Current column mapping for operation {operation}: {current_columns}")
            logger.debug(f"🔬 Current column names to process: {current_column_names}")
            
            # Build operation-specific parameters using prefixed parameter names
            operation_kwargs = {}
            operation_aggs = None  # Initialize for all operations
            
            if operation == 'upsample':
                operation_kwargs = {
                    'every': get_param(every),
                    'by': group_by,
                }
                operation_aggs = None
            elif operation == 'resample':
                # Include period in suffix for clarity
                period = get_param(every)
                base_suffix = get_param(resample_suffix, '_resampled')
                suffix_with_period = f"{base_suffix}_{period}" if period else base_suffix
                
                # Special handling for resample_default_agg when it's a list of aggregations
                # We want to use ALL aggregations in the list for a single operation, not select one
                raw_default_agg = resample_default_agg
                operation_aggs = get_param(resample_aggs)
                
                if isinstance(raw_default_agg, list) and not operation_aggs:
                    # Convert list of aggregations to explicit agg expressions for each column
                    operation_aggs = {}
                    for col in current_column_names:
                        # Each column gets all the aggregation functions as a list
                        operation_aggs[col] = raw_default_agg
                    
                    operation_kwargs = {
                        'every': period,
                        'suffix': suffix_with_period,
                        'period': get_param(resample_period),
                        'offset': get_param(resample_offset),
                        'include_boundaries': get_param(resample_include_boundaries),
                        'closed': get_param(resample_closed),
                        'label': get_param(resample_label),
                        'start_by': get_param(resample_start_by),
                        'group_by': group_by,
                    }
                else:
                    # Single aggregation or explicit aggs provided
                    operation_kwargs = {
                        'every': period,
                        'default_agg': get_param(resample_default_agg),
                        'suffix': suffix_with_period,
                        'period': get_param(resample_period),
                        'offset': get_param(resample_offset),
                        'include_boundaries': get_param(resample_include_boundaries),
                        'closed': get_param(resample_closed),
                        'label': get_param(resample_label),
                        'start_by': get_param(resample_start_by),
                        'group_by': group_by,
                    }
                    
            elif operation == 'interpolate':
                # Process existing columns with per-column method support
                # Use inplace=True when not keeping originals
                operation_kwargs = {
                    'method': get_param(interpolate_method),  # Now supports dict for per-column methods
                    'suffix': get_param(interpolate_suffix),
                    'order': get_param(interpolate_order),   # Now supports dict for per-column orders
                    'inplace': inplace,
                    'exclude_cols': get_param(interpolate_exclude_cols),
                    'group_by': group_by,
                    'by': time_column,  # Polars interpolation needs time_column as 'by' parameter
                }
     
                operation_aggs = get_param(interpolate_kwargs)
                    
            elif operation in ['ffill', 'bfill', 'ffill->bfill']:
                operation_kwargs = {
                    'limit': get_param(fill_limit),
                    'limit_area': get_param(fill_limit_area),
                    'suffix': get_param(fill_suffix, '_filled'),
                    'inplace': inplace,
                    'group_by': group_by,
                }
                operation_aggs = None
            elif operation == 'fillna':
                operation_kwargs = {
                    'value': get_param(fill_value),
                    'strategy': get_param(fill_strategy),
                    'limit': get_param(fill_limit),
                    'matches_supertype': True,
                    'suffix': get_param(fill_suffix, '_filled'),
                    'inplace': inplace,
                    'group_by': group_by,
                }
                operation_aggs = None
            elif operation == 'rolling':
                operation_kwargs = {
                    'period': get_param(rolling_period),
                    'default_agg': get_param(rolling_default_agg),
                    'suffix': get_param(rolling_suffix, '_rolling'),
                    'closed': get_param(rolling_closed),
                    'offset': get_param(rolling_offset),
                    'inplace': inplace,
                    'group_by': group_by,
                }
                # Collect aggs for separate passing
                operation_aggs = get_param(rolling_aggs)
            
            # Remove None values to avoid passing unnecessary parameters
            operation_kwargs = {k: v for k, v in operation_kwargs.items() if v is not None}
            
                
            # Execute the operation directly with already-filtered parameters
            try:
                # Add columns parameter for operations that need it
                if operation not in ['upsample'] and not operation_aggs:
                    operation_kwargs['columns'] = current_column_names
                
                # Add method-specific standard parameters
                if operation in ['rolling']:
                    operation_kwargs['index_column'] = time_column
                elif operation not in ['ffill', 'bfill', 'fillna', 'ffill->bfill']:
                    operation_kwargs['time_column'] = time_column
                
                # Remove None values to avoid passing unnecessary parameters
                filtered_kwargs = {k: v for k, v in operation_kwargs.items() if v is not None}
                logger.trace(f"🔬 Operation parameters: {filtered_kwargs}")
                
                # Add aggs if present (for resample/rolling methods)
                if operation_aggs:
                    filtered_kwargs.update(operation_aggs)
                    logger.trace(f"🔬 Added aggregations: {operation_aggs}")
                
                prev_shape = UniversalPolarsDataFrameExtension(result_df).shape
                
                # Handle composite operations and get the method
                if operation == 'ffill->bfill':
                    # Sequential operations: ffill then bfill
                    logger.trace("🔬 Executing sequential ffill->bfill operations")
                    method = getattr(PolarsDataFrameInterpolationExtension(result_df), 'ffill')
                    result_df = method(**filtered_kwargs)
                    logger.trace(f"🔬 After ffill: {prev_shape} → {result_df.shape}")

                    method = getattr(PolarsDataFrameInterpolationExtension(result_df), 'bfill')
                    result_df = method(**filtered_kwargs)
                    logger.trace(f"🔬 After bfill: {result_df.shape}")
                else:
                    # Single operation
                    logger.trace(f"🔬 Executing single operation: {operation}")
                    method = getattr(PolarsDataFrameInterpolationExtension(result_df), operation)
                    result_df = method(**filtered_kwargs)
                    logger.debug(f"⚡ Operation {operation} completed: {prev_shape} → {result_df.shape}")
                    logger.debug(f"🔬 Columns after {operation}: {result_df.columns}")
                    
                    
                        
            except Exception as e:
                logger.error(f"❌ Failed to execute {operation} operation: {str(e)}")
                raise RuntimeError(f"Failed to execute {operation} operation: {str(e)}") from e
            
            # Update column history with new column names after operation
            exclude_columns = set([time_column] + (group_by or []) + 
                                [col for col in result_df.columns if col.endswith('_meta_count')]) # type: ignore
            new_data_columns = [col for col in result_df.columns if col not in exclude_columns]
            
            # Create mapping from new columns back to their source columns
            iteration_mapping = {}  # new_column -> source_column
            
            # For operations with aggs or default aggs (multi-column output per input)
            # Note: resample and rolling use default_agg when no explicit aggs are provided
            if operation in ['resample', 'rolling'] and (operation_aggs or 
                                                        (operation == 'resample' and operation_kwargs.get('default_agg')) or
                                                        (operation == 'rolling' and operation_kwargs.get('default_agg'))):
                for orig_col in target_columns:
                    # Find all new columns that came from this original column
                    new_cols_from_orig = [col for col in new_data_columns 
                                         if col.startswith(orig_col + '_')]
                    logger.debug(f"🔬 For original column {orig_col}, found new columns: {new_cols_from_orig}")
                    # Map each new column to the source column it came from
                    for new_col in new_cols_from_orig:
                        # For multi-agg operations, map to the original column name
                        # All aggregated columns (e.g., HR_mean, HR_std) derive from the original (HR)
                        iteration_mapping[new_col] = orig_col
            else:
                # For standard operations (single column output per input)
                # Get suffix from operation_kwargs if not inplace
                if operation in ['interpolate', 'ffill', 'bfill', 'fillna', 'ffill->bfill', 'rolling']:
                    # For inplace operations, no suffix is used
                    if operation_kwargs.get('inplace', False):
                        current_suffix = None
                    else:
                        current_suffix = operation_kwargs.get('suffix', f'_{operation}')
                elif operation == 'resample':
                    # For resample, include the period in the suffix
                    base_suffix = operation_kwargs.get('suffix', '_resampled')
                    period = operation_kwargs.get('every', '')
                    current_suffix = f"{base_suffix}_{period}" if period else base_suffix
                else:
                    current_suffix = f'_{operation}'
                
                # Check if this is an in-place operation that needs renaming
                in_place_operations = ['interpolate', 'ffill', 'bfill', 'fillna', 'ffill->bfill']
                needs_rename = operation in in_place_operations and current_suffix and inplace
                
                rename_mapping = {}
                for orig_col in target_columns:
                    for source_col in current_columns[orig_col]:
                        if current_suffix:
                            # Operation should have suffix
                            new_col = f"{source_col}{current_suffix}"
                            if new_col in new_data_columns:
                                # Operation created new column with suffix
                                iteration_mapping[new_col] = source_col
                                # If not inplace, also map the original to itself
                                if not inplace:
                                    iteration_mapping[source_col] = source_col
                            elif needs_rename:
                                # In-place operation: need to rename column
                                rename_mapping[source_col] = new_col
                                iteration_mapping[new_col] = source_col
                            else:
                                # Operation processed in-place without rename
                                iteration_mapping[source_col] = source_col
                        else:
                            # No suffix - map to self
                            iteration_mapping[source_col] = source_col
                
                # Apply the rename if needed
                if rename_mapping:
                    result_df = result_df.rename(rename_mapping)
                    # Update new_data_columns to reflect the rename
                    new_data_columns = [rename_mapping.get(col, col) if col in rename_mapping else col 
                                       for col in new_data_columns]
            
            # Update column history and current columns
            for orig_col in target_columns:
                column_history[orig_col][operation_counter] = {}
                
            # Fill the history for this iteration
            for new_col, source_col in iteration_mapping.items():
                # Find which original column this new_col belongs to
                for orig_col in target_columns:
                    if (source_col in current_columns[orig_col] or 
                        source_col == orig_col or
                        any(source_col in column_history[orig_col][i].keys() 
                            for i in column_history[orig_col].keys())):
                        column_history[orig_col][operation_counter][new_col] = source_col
                        break
            
            # Update current_columns mapping with the actual column names after any renames
            for orig_col in target_columns:
                iteration_data = column_history[orig_col][operation_counter]
                if iteration_data:
                    # Prioritize newly created columns (with suffixes) over retained originals
                    # This ensures downstream operations process the transformed columns, not originals
                    new_cols = list(iteration_data.keys())
                    
                    # Get previous columns to identify which are newly created
                    prev_cols = current_columns[orig_col] if operation_counter > 1 else [orig_col]
                    
                    # Separate newly created vs retained columns
                    retained_cols = [col for col in new_cols if col in prev_cols]
                    created_cols = [col for col in new_cols if col not in prev_cols]
                    
                    # Prioritize created columns for downstream processing
                    if created_cols:
                        current_columns[orig_col] = created_cols
                        logger.debug(f"🔬 Updated current_columns[{orig_col}] = {created_cols} (prioritizing created columns)")
                    else:
                        current_columns[orig_col] = new_cols
                        logger.debug(f"🔬 Updated current_columns[{orig_col}] = {new_cols}")
            
            # Update enhanced column tracking with proper provenance
            for orig_col in target_columns:
                # Build the transformations mapping for this step
                transformations = {}
                iteration_data = column_history[orig_col].get(operation_counter, {})
                
                if iteration_data:
                    # Group by source column to show branching
                    for new_col, source_col in iteration_data.items():
                        if source_col not in transformations:
                            transformations[source_col] = []
                        transformations[source_col].append(new_col)
                else:
                    # No transformation for this original column at this step
                    # Use columns from previous step or original
                    if operation_counter == 1:
                        transformations[orig_col] = [orig_col]
                    else:
                        prev_step = operation_counter - 1
                        if prev_step in enhanced_column_tracking[orig_col]:
                            # Get all outputs from previous step
                            prev_transformations = enhanced_column_tracking[orig_col][prev_step].get("transformations", {})
                            for outputs in prev_transformations.values():
                                for col in outputs:
                                    transformations[col] = [col]
                        else:
                            # Fallback: use current columns
                            for col in current_columns[orig_col]:
                                transformations[col] = [col]
                
                # Capture the operation parameters used
                operation_params = {}
                if operation_kwargs:
                    # Filter out None values and internal parameters
                    filtered_params = {k: v for k, v in operation_kwargs.items() 
                                     if v is not None and not k.startswith('_')}
                    operation_params.update(filtered_params)
                
                # Record the enhanced tracking entry with proper provenance
                enhanced_column_tracking[orig_col][operation_counter] = {
                    "operation": operation,
                    "operation_instance": op_execution_counts[operation],
                    "parameters": operation_params,
                    "transformations": transformations  # KEY: before_col -> [after_cols] mapping
                }
                
                # Debug logging
                logger.debug(f"🔬 Enhanced tracking for {orig_col} step {operation_counter}:")
                logger.debug(f"   Operation: {operation} #{op_execution_counts[operation]}")
                for input_col, output_cols in transformations.items():
                    if len(output_cols) > 1:
                        logger.debug(f"   {input_col} → [BRANCHES INTO {len(output_cols)}]: {output_cols}")
                    else:
                        logger.debug(f"   {input_col} → {output_cols[0]}")
            
            # Note: Metadata counts should only be updated by resample/upsample operations
            # which handle counting source values in windows internally.
            # Interpolation/filling operations should not modify metadata.

        # Calculate final columns from enhanced tracking
        enhanced_tracking_summary = {}
        for col, steps in enhanced_column_tracking.items():
            if steps:
                final_step = max(steps.keys())
                final_transformations = steps[final_step].get("transformations", {})
                final_columns = []
                for outputs in final_transformations.values():
                    final_columns.extend(outputs)
                enhanced_tracking_summary[col] = {
                    'total_steps': len(steps),
                    'final_columns': final_columns
                }
            else:
                enhanced_tracking_summary[col] = {
                    'total_steps': 0,
                    'final_columns': [col]
                }
        
        # Apply simple_column_names if requested
        if simple_column_names and inplace:
            # Build rename mapping to use names from the first branch point
            rename_map = {}
            
            for orig_col in enhanced_column_tracking:
                steps = enhanced_column_tracking[orig_col]
                if not steps:
                    continue
                    
                # Find the FIRST branch point (where 1 column became multiple)
                # This gives the simplest column names from the earliest branching
                first_branch_step = None
                
                for step_num in sorted(steps.keys()):
                    transformations = steps[step_num].get("transformations", {})
                    
                    # Check if this step has branching (1 input -> multiple outputs)
                    for input_col, output_cols in transformations.items():
                        if len(output_cols) > 1:
                            # This is a branch point - use the FIRST one for simplest names
                            if first_branch_step is None:
                                first_branch_step = step_num
                                break  # Use the first branch point, not the most recent
                
                # Get the final columns for this original column
                final_step = max(steps.keys())
                final_transformations = steps[final_step].get("transformations", {})
                final_columns = []
                for outputs in final_transformations.values():
                    final_columns.extend(outputs)
                
                # Apply renaming based on branch point
                if first_branch_step is not None:
                    # Use pattern matching to map final columns to branch columns
                    # Get the branch point transformations
                    branch_transformations = steps[first_branch_step].get("transformations", {})
                    
                    for input_col, branch_cols in branch_transformations.items():
                        if len(branch_cols) > 1:  # This is the branching we want
                            # For each final column, find which branch column it corresponds to
                            # by checking if the branch column name is a prefix of the final column name
                            for final_col in final_columns:
                                for branch_col in branch_cols:
                                    # Check if this branch column name is contained in the final column name
                                    # This handles cases like: SPO2_mean -> SPO2_mean_interp_rolling_ffill_bfill
                                    if final_col.startswith(branch_col):
                                        rename_map[final_col] = branch_col
                                        break  # Found the match, move to next final column
                else:
                    # No branch point - use original column name
                    for final_col in final_columns:
                        if final_col != orig_col:
                            rename_map[final_col] = orig_col
            
            # Apply the renaming
            if rename_map:
                result_df = result_df.rename(rename_map)
                
                # Update the enhanced_tracking_summary with new names
                for orig_col, summary in enhanced_tracking_summary.items():
                    summary['final_columns'] = [rename_map.get(col, col) for col in summary['final_columns']]
        
        logger.debug(f"🎉 Time series processing pipeline completed", metadata={
            'operations_executed': len(operations), 
            'final_shape': UniversalPolarsDataFrameExtension(result_df).shape,
            'final_columns': list(result_df.columns),
            'enhanced_tracking_summary': enhanced_tracking_summary
        })
        
        # Return both the result DataFrame and the enhanced tracking
        # Note: Enhanced tracking should be handled by the caller, not stored as class variable
        return result_df
    
    

    def aggregate_connected_segments(
        self,
        *,
        start_col: str,
        end_col: str,
        by: Optional[Union[str, Iterable[str]]] = None,
        tolerance: TimeDeltaLike = None, # type: ignore
        agg_fn: Optional[Union[
            Callable[[pl.DataFrame], Union[pl.Series, dict, pl.DataFrame]],  # DataFrame function
            dict[str, pl.Expr],  # Expression dict
            Callable[[], dict[str, pl.Expr]]  # Expression generator
        ]] = None,
        compute_union_duration: bool = True,
        return_labels: bool = False,
        ) -> pl.DataFrame | pl.LazyFrame | Tuple[pl.DataFrame, pl.DataFrame]:

        return ag_segs(
                        frame=self._df,
                        start_col=start_col,
                        end_col=end_col,
                        by=by,
                        tolerance=tolerance,
                        agg_fn=agg_fn,
                        compute_union_duration=compute_union_duration,
                        return_labels=return_labels)


# Enhanced Column Tracking Helper Functions
def get_enhanced_column_tracking(df):
    """
    Extract enhanced column tracking from a processed DataFrame.
    
    Args:
        df: DataFrame returned from process_time_series_v2
        
    Returns:
        dict: Enhanced column tracking dictionary or None if not available
    """
    return getattr(df, '_enhanced_column_tracking', None)

def get_current_columns_from_tracking(tracking_dict, source_column):
    """
    Get current active columns for a source column from enhanced tracking.
    Returns only the LATEST/NEWEST columns created, not preserved intermediate ones.
    
    Args:
        tracking_dict: Enhanced column tracking dictionary
        source_column: Original source column name
        
    Returns:
        list: Only the latest/newest active column names
    """
    if not tracking_dict or source_column not in tracking_dict:
        return [source_column]
    
    steps = tracking_dict[source_column]
    if not steps:
        return [source_column]
    
    final_step = max(steps.keys())
    final_transformations = steps[final_step].get("transformations", {})
    
    # For rolling operations with inplace=false, we get both old and new columns
    # We need to identify and return only the newly created ones
    all_outputs = []
    for outputs in final_transformations.values():
        all_outputs.extend(outputs)
    
    if not all_outputs:
        return [source_column]
    
    # If we have transformations from the previous step, identify what's truly new
    if final_step > 1:
        prev_step = final_step - 1
        prev_transformations = steps[prev_step].get("transformations", {})
        prev_outputs = []
        for outputs in prev_transformations.values():
            prev_outputs.extend(outputs)
        
        # Return only columns that are NEW in this step (not in previous step)
        new_columns = [col for col in all_outputs if col not in prev_outputs]
        
        if new_columns:
            return new_columns
        else:
            # If no new columns were created, return all outputs
            return all_outputs
    
    # For first step, return all outputs
    return all_outputs

def get_column_lineage_from_tracking(tracking_dict, source_column):
    """
    Get complete transformation lineage for a source column.
    
    Args:
        tracking_dict: Enhanced column tracking dictionary
        source_column: Original source column name
        
    Returns:
        list: List of transformation steps with details
    """
    if not tracking_dict or source_column not in tracking_dict:
        return []
    
    lineage = []
    steps = tracking_dict[source_column]
    
    for step_num in sorted(steps.keys()):
        step_info = steps[step_num]
        transformations = step_info.get("transformations", {})
        
        # Convert transformations to input/output format
        input_columns = list(transformations.keys())
        output_columns = []
        for outputs in transformations.values():
            output_columns.extend(outputs)
        
        lineage.append({
            "step": step_num,
            "operation": step_info["operation"],
            "operation_instance": step_info["operation_instance"],
            "input_columns": input_columns,
            "output_columns": output_columns,
            "transformations": transformations,
            "parameters": step_info.get("parameters", {})
        })
    
    return lineage

def get_all_final_columns_from_tracking(tracking_dict):
    """
    Get all final column names after all transformations.
    
    Args:
        tracking_dict: Enhanced column tracking dictionary
        
    Returns:
        list: All final column names
    """
    if not tracking_dict:
        return []
    
    final_columns = []
    for source_col in tracking_dict:
        final_columns.extend(get_current_columns_from_tracking(tracking_dict, source_col))
    
    return final_columns

def print_enhanced_tracking_summary(df):
    """
    Print a readable summary of the enhanced column tracking.
    
    Args:
        df: DataFrame returned from process_time_series_v2
    """
    tracking = get_enhanced_column_tracking(df)
    if not tracking:
        print("No enhanced column tracking found in DataFrame")
        return
    
    print("=== Enhanced Column Tracking Summary (V2 - Provenance) ===\n")
    
    for source_col, steps in tracking.items():
        print(f"🌳 {source_col}:")
        if not steps:
            print("   No transformations applied")
            continue
            
        for step_num, step_info in steps.items():
            op_name = step_info['operation']
            op_instance = step_info['operation_instance']
            transformations = step_info.get('transformations', {})
            
            print(f"   📍 Step {step_num}: {op_name} (instance #{op_instance})")
            
            # Show transformations with proper provenance
            for input_col, output_cols in transformations.items():
                if len(output_cols) == 1 and output_cols[0] == input_col:
                    print(f"      {input_col} → (no change)")
                elif len(output_cols) == 1:
                    print(f"      {input_col} → {output_cols[0]}")
                else:
                    print(f"      {input_col} → [BRANCHES INTO {len(output_cols)}]")
                    for output_col in output_cols:
                        print(f"         ├─→ {output_col}")
            
            # Show key parameters
            params = step_info.get('parameters', {})
            key_params = []
            for param in ['every', 'agg', 'method', 'period', 'default_agg']:
                if param in params and params[param] is not None:
                    key_params.append(f"{param}={params[param]}")
            
            if key_params:
                print(f"      Parameters: {', '.join(key_params)}")
        
        # Show final result
        final_columns = get_current_columns_from_tracking(tracking, source_col)
        print(f"   📍 Final columns: {final_columns}\n")

def get_column_transformation_tree(tracking_dict, source_column):
    """
    Get a tree representation of how a source column branches through transformations.
    
    Args:
        tracking_dict: Enhanced column tracking dictionary
        source_column: Original source column name
        
    Returns:
        dict: Tree structure showing branching transformations
    """
    if not tracking_dict or source_column not in tracking_dict:
        return {}
    
    steps = tracking_dict[source_column]
    if not steps:
        return {}
    
    # Build transformation tree
    tree = {"source": source_column, "transformations": []}
    
    for step_num in sorted(steps.keys()):
        step_info = steps[step_num]
        mapping = step_info.get('column_mapping', {})
        
        transformation = {
            "step": step_num,
            "operation": step_info['operation'],
            "operation_instance": step_info['operation_instance'],
            "branches": []
        }
        
        for input_col, output_cols in mapping.items():
            transformation["branches"].append({
                "input": input_col,
                "outputs": output_cols,
                "parameters": step_info.get('parameters', {})
            })
        
        tree["transformations"].append(transformation)
    
    return tree

def trace_column_origin(tracking_dict, final_column_name):
    """
    Trace a final column name back to its original source and transformation path.
    
    Args:
        tracking_dict: Enhanced column tracking dictionary
        final_column_name: The final column name to trace back
        
    Returns:
        dict: Origin information and transformation path
    """
    # Find which source column this final column came from
    for source_col, steps in tracking_dict.items():
        for step_num, step_info in steps.items():
            if final_column_name in step_info.get('after_columns', []):
                # Found it - trace back through the steps
                path = []
                current_col = final_column_name
                
                # Work backwards through steps
                for reverse_step in sorted(steps.keys(), reverse=True):
                    step_data = steps[reverse_step]
                    mapping = step_data.get('column_mapping', {})
                    
                    # Find which input column led to current_col
                    for input_col, output_cols in mapping.items():
                        if current_col in output_cols:
                            path.insert(0, {
                                "step": reverse_step,
                                "operation": step_data['operation'],
                                "input": input_col,
                                "output": current_col,
                                "parameters": step_data.get('parameters', {})
                            })
                            current_col = input_col
                            break
                
                return {
                    "source_column": source_col,
                    "final_column": final_column_name,
                    "transformation_path": path
                }
    
    return {"error": f"Column {final_column_name} not found in tracking"}

def get_branching_summary(tracking_dict):
    """
    Get a summary of where branching occurs in the transformations.
    
    Args:
        tracking_dict: Enhanced column tracking dictionary
        
    Returns:
        dict: Summary of branching operations
    """
    branching_summary = {}
    
    for source_col, steps in tracking_dict.items():
        branches = []
        
        for step_num, step_info in steps.items():
            mapping = step_info.get('column_mapping', {})
            
            # Check if this step creates branches (1 input -> multiple outputs)
            for input_col, output_cols in mapping.items():
                if len(output_cols) > 1:
                    branches.append({
                        "step": step_num,
                        "operation": step_info['operation'],
                        "input": input_col,
                        "outputs": output_cols,
                        "branch_factor": len(output_cols)
                    })
        
        if branches:
            branching_summary[source_col] = branches
    
    return branching_summary


