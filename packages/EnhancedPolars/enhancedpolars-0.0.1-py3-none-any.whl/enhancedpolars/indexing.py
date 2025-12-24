"""
Polars DataFrame Extension for Pandas-style Indexing (Version 2)

This module provides a polars DataFrame extension that adds pandas-style indexing
methods (.loc, .iloc, .at, .iat) and boolean indexing through the 'ud_idx' namespace.

Since Polars DataFrames are immutable, setter operations return a new DataFrame.
"""

import polars as pl
from typing import Any, Literal, Union, cast, Type, Optional, List, Tuple, Iterator
import numpy as np
from .epl import EnhancedPolars as ep, CoreDataType
import logging
from .base import UniversalPolarsDataFrameExtension

def cast_value_to_column_type(value: Any, dtype: pl.DataType) -> Any:
    """Cast a value to match the column's dtype using polars_typing utilities."""
    # Handle null/None values first
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    # Create a temporary single-value series with the new value
    temp_series = pl.Series([value])
    
    # If the series already has the same dtype as the column, no conversion needed
    if temp_series.dtype == dtype:
        return value
    
    # Try to convert to the target dtype
    try:
        converted = ep.convert_to_polars_dtype(temp_series, dtype)
        return converted[0]
    except (AssertionError, Exception):
        # If conversion fails, just return the original value
        # This can happen with new columns where dtype inference is perfect
        return value
        
   
class UniversalPolarsDataFrameIndexingExtension(UniversalPolarsDataFrameExtension):
    """
    Polars DataFrame extension that provides pandas-style indexing.
    
    Accessible via df.ud_idx.loc, df.ud_idx.iloc, df.ud_idx.at, df.ud_idx.iat
    """
    
    def __init__(self, df: Any):
        super().__init__(df)

        # Create accessor objects
        self.loc = LocAccessor(self._df)
        self.iloc = ILocAccessor(self._df)
        self.at = AtAccessor(self._df)
        self.iat = IatAccessor(self._df)


    def __getitem__(self, key):
        """Enable boolean indexing directly on the namespace."""
        if isinstance(key, (pl.Series, pl.Expr)):
            # Boolean indexing with polars Series/Expr
            return self._df.filter(key)
        elif isinstance(key, (list, np.ndarray)) and len(key) == self.length:
            # Boolean array indexing
            if isinstance(key, np.ndarray):
                key = key.tolist()
            return self._df.filter(pl.Series(key))
        else:
            raise TypeError(f"Invalid indexing type: {type(key)}")
    
    
    @property
    def index(self):
        """
        Get the index of the DataFrame (similar to pandas).
        
        Since Polars doesn't have a built-in index concept like pandas,
        this returns a Polars Series representing the row positions.
        
        Returns:
            pl.Series: A Series containing row indices from 0 to len(df)-1
        """
        return pl.Series("index", range(self.length))
    
    def xs(self, key, axis=0, level=None, drop_level=True):
        """
        Return cross-section from the DataFrame.
        
        This method is similar to pandas .xs() but adapted for Polars DataFrames.
        
        Args:
            key: Label or tuple of labels for the cross-section
            axis: {0 or 'index', 1 or 'columns'}, default 0
                Axis to retrieve cross-section from
            level: Not implemented for Polars (no MultiIndex support)
            drop_level: Not applicable for Polars
        
        Returns:
            pl.DataFrame or pl.Series: Cross-section of the DataFrame
        
        Example:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
            >>> df.ud_idx.xs(1)  # Get row at index 1
            >>> df.ud_idx.xs("B", axis=1)  # Get column "B"
        """
        if level is not None:
            raise NotImplementedError("MultiIndex operations not supported in Polars")
        
        if axis in (0, 'index'):
            # Cross-section by row
            if isinstance(key, (int, np.integer)):
                if key < 0:
                    key = self.length + key
                if key < 0 or key >= self.length:
                    raise IndexError(f"Row index {key} is out of bounds")
                
                # Return a Series-like structure (single row as DataFrame)
                return self._df[key:key+1]
            else:
                raise TypeError(f"Row key must be integer for Polars, got {type(key)}")
        
        elif axis in (1, 'columns'):
            # Cross-section by column
            if isinstance(key, str):
                if key not in self.columns:
                    raise KeyError(f"Column '{key}' not found")
                return self._df.select(key)
            elif isinstance(key, (list, tuple)):
                # Multiple columns
                missing_cols = [col for col in key if col not in self.columns]
                if missing_cols:
                    raise KeyError(f"Columns {missing_cols} not found")
                return self._df.select(key)
            else:
                raise TypeError(f"Column key must be string or list of strings, got {type(key)}")
        
        else:
            raise ValueError(f"axis must be 0 or 1, got {axis}")
    
    def where(self, cond, other: Any = None):
        """
        Replace values where the condition is False.
        
        This method provides pandas-style conditional replacement functionality
        for Polars DataFrames.
        
        Args:
            cond: A boolean expression, Series, or DataFrame of same shape.
                Where True, keep the original value. Where False, replace 
                with 'other'.
            other: Value to use where condition is False. Can be scalar,
                Series, or DataFrame. If None, uses null values.
        
        Returns:
            pl.DataFrame: New DataFrame with conditional replacements applied.
        
        Example:
            >>> df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            >>> df.ud_idx.where(df["A"] > 1, 0)  # Replace values where A <= 1 with 0
        """
        # Handle literal values for polars expressions
        other_expr = pl.lit(other) if other is not None else None
        
        # Handle different condition types
        if isinstance(cond, pl.Expr):
            # Single expression condition
            return self._df.with_columns([
                pl.when(cond).then(pl.col(col)).otherwise(other_expr).alias(col)
                for col in self.columns
            ])
        elif isinstance(cond, pl.Series):
            # Series condition - apply to all columns
            if len(cond) != self.length:
                raise ValueError(f"Condition length {len(cond)} doesn't match DataFrame length {self.length}")
            
            return self._df.with_columns([
                pl.when(cond).then(pl.col(col)).otherwise(other_expr).alias(col)
                for col in self.columns
            ])
        elif isinstance(cond, pl.DataFrame):
            # DataFrame condition - element-wise replacement
            if cond.shape != self._shape:
                raise ValueError(f"Condition shape {cond.shape} doesn't match DataFrame shape {self._shape}")
            
            # For DataFrame conditions, we need to be more careful about column types
            # Convert to series-based conditions for each column
            result_df = self._df
            for col in self.columns:
                if col in cond.columns:
                    # Apply condition for this specific column
                    result_df = result_df.with_columns(
                        pl.when(cond[col]).then(pl.col(col)).otherwise(other_expr).alias(col)
                    )
            
            return result_df
        elif isinstance(cond, (list, tuple)) and len(cond) == self.length:
            # List/tuple of boolean values
            cond_series = pl.Series("cond", cond)
            return self._df.with_columns([
                pl.when(cond_series).then(pl.col(col)).otherwise(other_expr).alias(col)
                for col in self.columns
            ])
        else:
            raise TypeError(f"Unsupported condition type: {type(cond)}")
    
   
    
    def any(self, axis: Union[Literal[0, 1, 'index', 'columns'], None] = None):
        """
        Return whether any element is True over requested axis.
        
        Args:
            axis: {0, 1, 'index', 'columns', None}, default None
                If None, return whether any element is True in entire DataFrame.
                If 0 or 'index', return DataFrame indicating if any True in each column.
                If 1 or 'columns', return DataFrame indicating if any True in each row.
        
        Returns:
            bool or pl.DataFrame: Result of any operation.
        """
        if axis is None:
            # Check if any value is True in entire DataFrame
            any_checks = []
            for col, col_dtype in self.schema.items():
                if col_dtype == pl.Boolean:
                    any_checks.append(pl.col(col).any())
                elif CoreDataType.NUMERIC.is_numeric_type(cast(Type, col_dtype)):
                    # For numeric types, any non-zero value is True
                    any_checks.append((pl.col(col) != 0).any())
                else:
                    # For other types, any non-null value is True
                    any_checks.append(pl.col(col).is_not_null().any())
            
            # Create a small DataFrame with the results and check if any is True
            result_df = self._df.select(any_checks)
            return any((result_df.collect() if isinstance(result_df, pl.LazyFrame) else result_df).row(0))
        
        elif axis in (0, 'index'):
            # Any along index (columns) - return Series-like DataFrame
            any_checks = []
            for col, col_dtype in self.schema.items():
                if col_dtype == pl.Boolean:
                    any_checks.append(pl.col(col).any().alias(col))
                elif CoreDataType.NUMERIC.is_numeric_type(cast(Type, col_dtype)):
                    # For numeric types, any non-zero value is True
                    any_checks.append((pl.col(col) != 0).any().alias(col))
                else:
                    # For other types, any non-null value is True
                    any_checks.append(pl.col(col).is_not_null().any().alias(col))
            
            return self._df.select(any_checks)
        
        elif axis in (1, 'columns'):
            # Any along columns (rows) - return Series of row-wise any using horizontal any
            # Build expressions for each column based on dtype  
            col_exprs = []
            for col, col_dtype in self.schema.items():
                if col_dtype == pl.Boolean:
                    # For boolean columns, use the value as-is (True is True, False is False)
                    col_exprs.append(pl.col(col))
                elif CoreDataType.NUMERIC.is_numeric_type(cast(Type, col_dtype)):
                    # For numeric types, any non-zero value is True
                    col_exprs.append(pl.col(col) != 0)
                else:
                    # For other types, any non-null value is True
                    col_exprs.append(pl.col(col).is_not_null())
            
            # Use Polars' built-in any_horizontal for efficiency
            return self._df.select(
                pl.any_horizontal(*col_exprs).alias("any")
            )
        
        else:
            raise ValueError(f"axis must be 0, 1, 'index', 'columns', or None, got {axis}")
    
    def all(self, axis: Union[Literal[0, 1, 'index', 'columns'], None] = None):
        """
        Return whether all elements are True over requested axis.
        
        Args:
            axis: {0, 1, 'index', 'columns', None}, default None
                If None, return whether all elements are True in entire DataFrame.
                If 0 or 'index', return DataFrame indicating if all True in each column.
                If 1 or 'columns', return DataFrame indicating if all True in each row.
        
        Returns:
            bool or pl.DataFrame: Result of all operation.
        """
        if axis is None:
            # Check if all values are True in entire DataFrame
            all_checks = []
            for col, col_dtype in self.schema.items():
                if col_dtype == pl.Boolean:
                    all_checks.append(pl.col(col).all())
                elif CoreDataType.NUMERIC.is_numeric_type(cast(Type, col_dtype)):
                    # For numeric types, all non-zero values are True
                    all_checks.append((pl.col(col) != 0).all())
                else:
                    # For other types, all non-null values are True
                    all_checks.append(pl.col(col).is_not_null().all())
            
            # Create a small DataFrame with the results and check if all are True
            result_df = self._df.select(all_checks)
            return all((result_df.collect() if isinstance(result_df, pl.LazyFrame) else result_df).row(0))

        elif axis in (0, 'index'):
            # All along index (columns) - return Series-like DataFrame
            all_checks = []
            for col, col_dtype in self.schema.items():
                if col_dtype == pl.Boolean:
                    all_checks.append(pl.col(col).all().alias(col))
                elif CoreDataType.NUMERIC.is_numeric_type(cast(Type, col_dtype)):
                    # For numeric types, all non-zero values are True
                    all_checks.append((pl.col(col) != 0).all().alias(col))
                else:
                    # For other types, all non-null values are True
                    all_checks.append(pl.col(col).is_not_null().all().alias(col))
            
            return self._df.select(all_checks)
        
        elif axis in (1, 'columns'):
            # All along columns (rows) - return Series of row-wise all using horizontal all
            # Build expressions for each column based on dtype
            col_exprs = []
            for col, col_dtype in self.schema.items():
                if col_dtype == pl.Boolean:
                    col_exprs.append(pl.col(col))
                elif CoreDataType.NUMERIC.get_core_type(cast(Type, col_dtype)) in (CoreDataType.INTEGER, CoreDataType.FLOAT):
                    # For numeric types, all non-zero values are True
                    col_exprs.append(pl.col(col) != 0)
                else:
                    # For other types, all non-null values are True
                    col_exprs.append(pl.col(col).is_not_null())
            
            # Use Polars' built-in all_horizontal for efficiency
            return self._df.select(
                pl.all_horizontal(*col_exprs).alias("all")
            )
        
        else:
            raise ValueError(f"axis must be 0, 1, 'index', 'columns', or None, got {axis}")
    
    def reset_index(self, 
                    drop: bool = False,
                    name: Optional[str] = None) -> pl.DataFrame | pl.LazyFrame:
        """
        Reset the index of the DataFrame to a default integer index.
        
        Since Polars DataFrames don't have a traditional index like pandas, this method
        provides a consistent interface by either dropping the existing row numbering
        or adding an explicit index column.
        
        Args:
            drop: If True, just return the DataFrame as-is (Polars doesn't have a persistent index)
                If False, add a new column with sequential integers (0, 1, 2, ...)
            name: Name for the new index column (default: 'index'). Only used when drop=False
            
        Returns:
            pl.DataFrame: DataFrame with reset index
            
        Example:
            >>> df = pl.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
            >>> df.ud_idx.reset_index()  # Adds 'index' column with [0, 1, 2]
            >>> df.ud_idx.reset_index(drop=True)  # Returns original DataFrame
            >>> df.ud_idx.reset_index(name='row_id')  # Adds 'row_id' column
        """
        if drop:
            # In Polars, there's no persistent index to drop, so just return the DataFrame
            return self._df
        else:
            # Add an index column with sequential integers
            index_name = name if name is not None else 'index'
            
            # Create a range index starting from 0
            index_values = list(range(self.length))
            
            # Add the index column at the beginning
            return self._df.with_columns(
                pl.Series(index_name, index_values)
            ).select([index_name] + self.columns)
    
    def dropna(self, 
            how: Literal['any', 'all'] = 'any',
            subset: Optional[Union[str, List[str]]] = None) -> pl.DataFrame | pl.LazyFrame:
        """
        Remove missing values from DataFrame.
        
        Since Polars doesn't have traditional row/column axis operations like pandas,
        this method focuses on row-based null removal with column subsetting support.
        
        Args:
            how: Determine if row is removed when we have missing values
                'any': If any NA/null values are present in the row, drop that row
                'all': If all values in the row are NA/null, drop that row
            subset: Column name(s) to consider for null checking. If None, check all columns
            
        Returns:
            pl.DataFrame: DataFrame with missing values removed
            
        Example:
            >>> df = pl.DataFrame({'A': [1, 2, None], 'B': [4, None, 6]})
            >>> df.ud_idx.dropna()  # Drop rows with any null values
            >>> df.ud_idx.dropna(how='all')  # Drop only rows where all values are null
            >>> df.ud_idx.dropna(subset=['A'])  # Drop rows where column A has null values
        """
        # Determine which columns to check
        if subset is not None:
            if isinstance(subset, str):
                check_columns = [subset]
            else:
                check_columns = subset
        else:
            check_columns = self.columns
        
        # Create null check expressions for each column
        null_checks = []
        for col, col_dtype in self.schema.items():
            if col not in check_columns:
                continue

            if CoreDataType.FLOAT.get_core_type(cast(Type, col_dtype)) == CoreDataType.FLOAT:
                # For float columns, check both null and NaN
                null_checks.append(pl.col(col).is_null() | pl.col(col).is_nan())
            else:
                # For other types, only check null
                null_checks.append(pl.col(col).is_null())
        
        if how == 'any':
            # Drop rows where ANY of the checked columns have null values
            if len(null_checks) == 1:
                filter_condition = ~null_checks[0]
            else:
                # Use horizontal any to check if any column has nulls, then negate
                filter_condition = ~pl.any_horizontal(*null_checks)
        elif how == 'all':
            # Drop rows where ALL of the checked columns have null values
            if len(null_checks) == 1:
                filter_condition = ~null_checks[0]
            else:
                # Use horizontal all to check if all columns have nulls, then negate
                filter_condition = ~pl.all_horizontal(*null_checks)
        else:
            raise ValueError(f"Invalid value for 'how': {how}. Must be 'any' or 'all'")
        
        return self._df.filter(filter_condition)
    
    
    def set_loc(self, row_indexer, col_indexer, value):
        """Set values using label-based indexing and return new DataFrame."""
        return self.loc._set_and_return((row_indexer, col_indexer), value)
    
    def set_iloc(self, row_indexer, col_indexer, value):
        """Set values using position-based indexing and return new DataFrame."""
        return self.iloc._set_and_return((row_indexer, col_indexer), value)
    
    def set_at(self, row_idx, col_label, value):
        """Set a single value using labels and return new DataFrame."""
        return self.at._set_and_return((row_idx, col_label), value)
    
    def set_iat(self, row_pos, col_pos, value):
        """Set a single value using positions and return new DataFrame."""
        return self.iat._set_and_return((row_pos, col_pos), value)
    
    def split(self, 
            n_parts: int = 2,
            frac: Optional[List[float]] = None,
            random_state: Optional[int] = None,
            shuffle: bool = True) -> Union[List[pl.DataFrame], List[pl.LazyFrame]]:
        """
        Split DataFrame into n parts.
        
        This method provides splitting functionality for Polars DataFrames,
        with support for both eager and lazy evaluation.
        
        Args:
            n_parts: Number of parts to split into (default: 2).
            frac: List of fractions for each part. Must sum to 1.0.
                If None, splits evenly.
            random_state: Random seed for reproducible splits when shuffle=True.
            shuffle: Whether to shuffle before splitting (default: True).
        
        Returns:
            List of DataFrames/LazyFrames: List of split parts.
        
        Example:
            >>> df = pl.DataFrame({'A': range(10), 'B': range(10, 20)})
            >>> train, val, test = df.ud_idx.split(n_parts=3, random_state=42)
            >>> parts = df.ud_idx.split(n_parts=3, frac=[0.6, 0.2, 0.2])
        """
        if n_parts < 2:
            raise ValueError("n_parts must be at least 2")

        total_rows = self.length

        # Determine split sizes
        if frac is not None:
            if len(frac) != n_parts:
                raise ValueError(f"frac must have {n_parts} elements")
            if not np.isclose(sum(frac), 1.0, atol=1e-6):
                raise ValueError("frac values must sum to 1.0")
            if any(f < 0 or f > 1 for f in frac):
                raise ValueError("All frac values must be between 0 and 1")
            
            # Calculate split sizes
            split_sizes = [int(total_rows * f) for f in frac]
            # Adjust for rounding errors - add remaining rows to the first split
            remaining = total_rows - sum(split_sizes)
            split_sizes[0] += remaining
        else:
            # Split evenly
            base_size = total_rows // n_parts
            remainder = total_rows % n_parts
            split_sizes = [base_size] * n_parts
            # Distribute remainder across first splits
            for i in range(remainder):
                split_sizes[i] += 1
        
        # Create indices
        if shuffle:
            if random_state is not None:
                np.random.seed(random_state)
            indices = np.random.permutation(total_rows)
        else:
            indices = np.arange(total_rows)
        
        # Split indices
        splits_indices = []
        start_idx = 0
        for size in split_sizes:
            end_idx = start_idx + size
            splits_indices.append(indices[start_idx:end_idx].tolist())
            start_idx = end_idx
        
        # Create splits
        splits = []
        for split_indices in splits_indices:
            split_df = self._df.filter(pl.arange(0, total_rows).is_in(split_indices))
            splits.append(split_df)
        return splits

    
    def sample(self,
            n: Optional[int] = None,
            frac: Optional[float] = None,
            replace: bool = False,
            weights: Optional[List[float] | pl.Series] = None,
            random_state: Optional[int] = None,
            shuffle: bool = False,
            stratify: Optional[str] = None) -> pl.DataFrame | pl.LazyFrame:
        """
        Return a random sample of items from the DataFrame.
        
        Uses native Polars sampling when possible for optimal performance.
        Falls back to custom implementation for advanced features like stratification.
        
        Args:
            n: Number of items to return. Cannot be used with frac.
            frac: Fraction of items to return. Cannot be used with n.
            replace: Allow sampling with replacement (default: False).
            weights: Weights for probability of selection. If None, uniform probability.
            random_state: Random seed for reproducible sampling.
            shuffle: Whether to shuffle before sampling (only used with custom sampling).
            stratify: Column name to stratify sampling by (custom feature).
        
        Returns:
            pl.DataFrame or pl.LazyFrame: Random sample from the DataFrame.
        
        Example:
            >>> df = pl.DataFrame({'A': range(100), 'B': range(100, 200), 'group': ['A', 'B'] * 50})
            >>> sample = df.ud_idx.sample(n=10, random_state=42)
            >>> stratified = df.ud_idx.sample(n=20, stratify='group', random_state=42)
        """
        # Validate parameters
        if (n is None) == (frac is None):
            raise ValueError("Exactly one of `n` or `frac` must be provided.")
        if replace:
            logging.warning("Sampling with replacement is not supported lazily. Collecting")
            self._df = cast(pl.LazyFrame, self._df).collect() if self.is_lazy else self._df
        if weights is not None:
            logging.warning("Sampling with Weighted sampling is not supported lazily. Collecting")
            self._df = cast(pl.LazyFrame, self._df).collect() if self.is_lazy else self._df
        if stratify is not None and stratify not in self.columns:
            raise ValueError(f"`stratify` column '{stratify}' not found.")

        seed = 0 if random_state is None else int(random_state)

        # total rows (tiny aggregation; minimal execution)
        total_rows = self.length
        if total_rows == 0:
            return self._df.limit(0)

        # Determine sample size
        if n is not None:
            sample_size = n
            if not replace and sample_size > total_rows:
                raise ValueError(f"Cannot sample {sample_size} rows from DataFrame with {total_rows} rows without replacement")
            sample_frac = None
        elif frac is not None:
            if not 0.0 <= frac <= 1.0:
                raise ValueError("frac must be between 0.0 and 1.0")
            sample_frac = frac
            sample_size = int(total_rows * frac)
        else:
            # Default to n=1
            sample_size = 1
            sample_frac = None

        if self.is_lazy:
            # helper columns
            IDX = "__lf_idx__"
            RKEY = "__rand_key__"
            RNK  = "__rand_rank__"
            K    = "__group_k__"

            # random key: deterministic hash over (idx) or (stratify, idx)
            base = self._df.with_row_index(IDX)
            if stratify:
                base = base.with_columns(
                    pl.struct([pl.col(stratify), pl.col(IDX)]).hash(seed=seed).alias(RKEY)
                )
            else:
                base = base.with_columns(
                    pl.struct([pl.col(IDX)]).hash(seed=seed).alias(RKEY)
                )

            if stratify is None:
                # Global sample: rank by random key; take top target_n
                sampled = base.with_columns(
                    pl.col(RKEY).rank(method="ordinal").alias(RNK)
                ).filter(pl.col(RNK) <= sample_size)

                # Order
                if shuffle:
                    sampled = sampled.sort(by=RKEY)
                else:
                    sampled = sampled.sort(by=IDX)

                return sampled.drop([IDX, RKEY, RNK])

            # --- stratified sampling ---
            # Get per-group counts (small collect)
            grp = stratify
            counts = (
                cast(pl.LazyFrame, self._df).group_by(grp)
                .agg(n=pl.count())
                .collect()
            )

            # decide per-group k: proportional allocation (largest remainder)
            total = counts["n"].sum()
            if frac is not None:
                counts = counts.with_columns(pl.col("n").mul(frac).round(0).cast(pl.Int64).alias(K))
            else:
                # proportional quota
                exact = counts.with_columns((pl.col("n") * sample_size / total).alias("__exact__"))
                floor_k = exact.with_columns(pl.col("__exact__").floor().cast(pl.Int64).alias(K))
                remainder = (exact.select([grp, "__exact__"])  # keep remainder separately
                            .with_columns((pl.col("__exact__") - pl.col("__exact__").floor()).alias("__rem__"))
                            .select([grp, "__rem__"]))
                base_k = floor_k.select([grp, K]).join(remainder, on=grp)

                allocated = base_k[K].sum()
                leftover = sample_size - int(allocated)

                # assign remaining by largest fractional remainder
                base_k = base_k.sort("__rem__", descending=True)
                if leftover > 0:
                    inc = pl.Series([1]*leftover + [0]*max(len(base_k)-leftover, 0))
                    base_k = base_k.with_columns((pl.col(K) + inc).alias(K))
                counts = base_k.select([grp, K])

            # merge quotas back (lazy)
            quotas = counts.lazy()

            # rank rows randomly *within* each stratum and take top-k per stratum
            ranked = (
                base
                .with_columns(pl.col(RKEY).rank(method="ordinal").over(grp).alias(RNK))
                .join(quotas, on=grp, how="inner") # type: ignore
                .filter(pl.col(RNK) <= pl.col(K))
            )

            # Order
            if shuffle:
                ranked = ranked.sort(by=[grp, RKEY])
            else:
                ranked = ranked.sort(by=[grp, IDX])

            return ranked.drop([IDX, RKEY, RNK, K])
        
        if self.is_lazy and (weights is not None or stratify is not None):
            self._df = cast(pl.LazyFrame, self._df).collect()

        total_rows = self.length

        # Determine sample size
        if n is not None:
            sample_size = n
            if not replace and sample_size > total_rows:
                raise ValueError(f"Cannot sample {sample_size} rows from DataFrame with {total_rows} rows without replacement")
            sample_frac = None
        elif frac is not None:
            if not 0.0 <= frac <= 1.0:
                raise ValueError("frac must be between 0.0 and 1.0")
            sample_frac = frac
            sample_size = int(total_rows * frac)
        else:
            # Default to n=1
            sample_size = 1
            sample_frac = None
        
        # Use native polars sampling when possible (for optimal performance)
        if (weights is None and stratify is None):
            # For lazy evaluation, we need to collect first, then make lazy
            if sample_frac is not None:
                # Use native sample with fraction
                return self._df.sample(fraction=sample_frac, seed=random_state, with_replacement=replace, shuffle=shuffle) # type: ignore
            else:
                # Use native sample with n
                return self._df.sample(n=sample_size, seed=random_state, with_replacement=replace, shuffle=shuffle) # type: ignore

        
        # Fall back to custom implementation for advanced features
        # Set random seed if provided
        if random_state is not None:
            np.random.seed(random_state)
        
        # Handle stratified sampling
        if stratify is not None:
            if stratify not in self.columns:
                raise KeyError(f"Stratify column '{stratify}' not found in DataFrame")
            
            # Get unique groups and their proportions
            group_counts = self._df.group_by(stratify).len().sort(stratify)
            groups = group_counts[stratify].to_list() # type: ignore
            counts = group_counts['len'].to_list() # type: ignore
            total_count = sum(counts)
            
            # Calculate samples per group maintaining proportions
            samples_per_group = []
            for count in counts:
                group_sample = max(1, int(sample_size * count / total_count))
                samples_per_group.append(group_sample)
            
            # Adjust for rounding errors
            total_samples = sum(samples_per_group)
            if total_samples != sample_size:
                diff = sample_size - total_samples
                # Distribute difference to largest groups
                group_sizes = list(zip(samples_per_group, range(len(samples_per_group))))
                group_sizes.sort(key=lambda x: counts[x[1]], reverse=True)
                
                for i in range(abs(diff)):
                    idx = group_sizes[i % len(group_sizes)][1]
                    if diff > 0:
                        samples_per_group[idx] += 1
                    elif samples_per_group[idx] > 1:  # Don't go below 1
                        samples_per_group[idx] -= 1
            
            # Sample from each group
            sampled_dfs = []
            for group, sample_count in zip(groups, samples_per_group):
                group_df = self._df.filter(pl.col(stratify) == group)
                gh = cast(int, cast(pl.LazyFrame, group_df.select(pl.count())).collect().item() if hasattr(group_df, 'collect') else cast(pl.DataFrame, group_df).height)
                if gh > 0:
                    if sample_count <= gh or replace:
                        group_indices = np.random.choice(
                            gh,
                            size=sample_count,
                            replace=replace
                        ).tolist()
                        sampled_dfs.append(group_df[group_indices])
            
            # Combine all sampled groups
            if sampled_dfs:
                result_df = pl.concat(sampled_dfs)
                if shuffle:
                    # Shuffle the final result
                    indices = np.random.permutation(len(result_df)).tolist()
                    result_df = result_df[indices]
                
                return result_df
            else:
                # Return empty DataFrame with same schema
                return self._df.clear()
        
        # Handle weighted or replacement sampling
        if weights is not None:
            # Handle weighted sampling
            if isinstance(weights, pl.Series):
                weights_array = weights.to_numpy()
            else:
                weights_array = np.array(weights)
            
            # Normalize weights
            weights_array = weights_array / weights_array.sum()
            
            # Sample indices with weights
            indices = np.random.choice(
                total_rows,
                size=sample_size,
                replace=replace,
                p=weights_array
            ).tolist()
        else:
            # Uniform sampling
            if replace:
                indices = np.random.choice(total_rows, size=sample_size, replace=True).tolist()
            else:
                indices = np.random.choice(total_rows, size=sample_size, replace=False).tolist()
        
        # Apply shuffle if requested
        if shuffle:
            np.random.shuffle(indices)
        
        # Return sampled DataFrame
        return self._df[indices]
    
    def sort_values(self,
                    by: Union[str, List[str]],
                    ascending: Union[bool, List[bool]] = True,
                    na_position: Literal['first', 'last'] = 'last') -> Union[pl.DataFrame, pl.LazyFrame]:
        """
        Sort DataFrame by one or more columns.
        
        This method provides pandas-style sorting functionality for Polars DataFrames,
        with support for both eager and lazy evaluation.
        
        Args:
            by: Column name(s) to sort by.
            ascending: Sort ascending (True) or descending (False).
                    Can be a list for multiple columns.
            na_position: Where to place null values ('first' or 'last').
            lazy: If True, returns a LazyFrame for deferred execution.
        
        Returns:
            pl.DataFrame or pl.LazyFrame: Sorted DataFrame.
        
        Example:
            >>> df = pl.DataFrame({'A': [3, 1, 2], 'B': ['z', 'x', 'y']})
            >>> sorted_df = df.ud_idx.sort_values('A')
            >>> sorted_df = df.ud_idx.sort_values(['A', 'B'], ascending=[True, False])
            >>> sorted_lazy = df.ud_idx.sort_values('A', lazy=True)
        """
        # Convert single column to list
        if isinstance(by, str):
            by = [by]
        
        # Convert single ascending value to list
        if isinstance(ascending, bool):
            ascending = [ascending] * len(by)
        elif len(ascending) != len(by):
            raise ValueError(f"Length of ascending ({len(ascending)}) must match length of by ({len(by)})")
        
        # Validate columns exist
        missing_cols = [col for col in by if col not in self.columns]
        if missing_cols:
            raise KeyError(f"Columns {missing_cols} not found in DataFrame")
        
        # Polars sort with null handling
        result = self._df.sort(by, descending=[not asc for asc in ascending], nulls_last=na_position == 'last')


        return result
    
    def iterrows(self) -> 'IterRowsAccessor':
        """
        Iterate over DataFrame rows as (index, Series) pairs.
        
        This method provides pandas-style row iteration for Polars DataFrames.
        Note: Iteration is generally less efficient than vectorized operations.
        
        Returns:
            IterRowsAccessor: An iterator that yields (index, row_data) tuples.
        
        Example:
            >>> df = pl.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
            >>> for idx, row in df.ud_idx.iterrows():
            ...     print(f"Row {idx}: A={row['A']}, B={row['B']}")
        """
        return IterRowsAccessor(self._df)



class LocAccessor:
    """Label-based accessor for polars DataFrames (similar to pandas .loc)."""
    
    def __init__(self, df: Union[pl.DataFrame, pl.LazyFrame], namespace=None):
        self._df = df
        self._namespace = namespace
        self.length = cast(pl.LazyFrame, df.select(pl.count())).collect()[0, 0] if isinstance(df, pl.LazyFrame) else len(df)

    def __getitem__(self, key):
        """Get items using label-based indexing."""
        if isinstance(key, tuple):
            row_indexer, col_indexer = key[0], key[1] if len(key) > 1 else slice(None)
            return self._get_with_row_col(row_indexer, col_indexer)
        else:
            return self._get_rows(key)
    
    def __setitem__(self, key, value):
        """Set items using label-based indexing."""
        raise NotImplementedError(
            "Due to Polars DataFrame immutability, direct assignment via .loc[] doesn't persist. "
            "Use one of these alternatives:\n"
            "1. df = df.with_columns(pl.lit(value).alias('column_name'))  # for new columns\n"
            "2. df = df.with_columns(pl.col('existing_col').map_elements(...))  # for existing columns\n"
            "3. Use the _set_and_return method and reassign: df = df.ud_master.loc._set_and_return(key, value)"
        )
    
    def _set_and_return(self, key, value):
        """Set values and return the new DataFrame."""
        if isinstance(key, tuple):
            row_indexer, col_indexer = key[0], key[1] if len(key) > 1 else slice(None)
        else:
            row_indexer, col_indexer = key, slice(None)
        
        df = self._df
        
        # Convert row indexer to list of row indices
        if isinstance(row_indexer, int):
            row_indices = [row_indexer]
        elif isinstance(row_indexer, slice):
            start = row_indexer.start if row_indexer.start is not None else 0
            stop = row_indexer.stop if row_indexer.stop is not None else self.length
            if stop < 0:
                stop = self.length + stop + 1
            row_indices = list(range(start, stop))
        elif isinstance(row_indexer, (list, np.ndarray)):
            if isinstance(row_indexer, np.ndarray):
                row_indexer = row_indexer.tolist()
            if all(isinstance(x, bool) for x in row_indexer):
                row_indices = [i for i, val in enumerate(row_indexer) if val]
            else:
                row_indices = row_indexer
        elif isinstance(row_indexer, pl.Series):
            # Boolean mask
            row_indices = [i for i, val in enumerate(row_indexer.to_list()) if val]
        else:
            raise TypeError(f"Invalid row indexer type: {type(row_indexer)}")
        
        # Convert column indexer to list of column names
        if isinstance(col_indexer, str):
            col_names = [col_indexer]
        elif isinstance(col_indexer, list):
            col_names = col_indexer
        elif isinstance(col_indexer, slice):
            cols = list(df.columns)
            if col_indexer == slice(None):
                col_names = cols
            else:
                start = col_indexer.start
                stop = col_indexer.stop
                if isinstance(start, str):
                    start = cols.index(start)
                if isinstance(stop, str):
                    stop = cols.index(stop) + 1
                col_names = cols[slice(start, stop)]
        else:
            col_names = list(df.columns)
        
        # Update values using proper polars expressions
        for col_name in col_names:
            # Handle new column creation (like pandas .loc)
            if col_name not in df.columns:
                # Create a small Series with the value to infer the correct dtype
                sample_series = pl.Series([value])
                inferred_dtype = sample_series.dtype
                
                # Create new column filled with None using the inferred dtype
                df = df.with_columns([pl.lit(None).cast(inferred_dtype).alias(col_name)])
            
            # Create a boolean mask for the rows to update
            if isinstance(row_indexer, pl.Series) and row_indexer.dtype == pl.Boolean:
                # Direct boolean mask
                mask = row_indexer
            else:
                # Convert row indices to boolean mask
                mask_list = [False] * self.length
                for row_idx in row_indices:
                    if row_idx < 0:
                        row_idx = self.length + row_idx
                    if 0 <= row_idx < self.length:
                        mask_list[row_idx] = True
                mask = pl.Series(mask_list)
            
            # Determine the value to set for this column
            if hasattr(value, '__len__') and not isinstance(value, str):
                if len(col_names) == 1:
                    # Single column, use value directly if it's a list/array
                    new_val = value
                else:
                    # Multiple columns, get the value for this specific column
                    col_idx = col_names.index(col_name)
                    if hasattr(value[0] if value else None, '__len__'):
                        # 2D array - extract column values
                        new_val = [row[col_idx] if col_idx < len(row) else None for row in value]
                    else:
                        # 1D array for multiple columns - use single value
                        new_val = value[col_idx] if col_idx < len(value) else None
            else:
                # Scalar value
                new_val = value
            
            # Use when-then-otherwise to update only the masked rows
            if isinstance(new_val, (list, np.ndarray)):
                # If new_val is array-like, we need to create a series and use it with the mask
                if len(new_val) == len(row_indices):
                    # Expand the values to match the full dataframe length
                    full_values = [None] * self.length
                    for i, row_idx in enumerate(row_indices):
                        if row_idx < 0:
                            row_idx = self.length + row_idx
                        if 0 <= row_idx < self.length:
                            full_values[row_idx] = new_val[i]
                    value_series = pl.Series(full_values)
                    df = df.with_columns(
                        pl.when(mask).then(value_series).otherwise(pl.col(col_name)).alias(col_name)
                    )
                else:
                    # Use first value as scalar
                    scalar_val = new_val[0] if len(new_val) > 0 else None
                    df = df.with_columns(
                        pl.when(mask).then(pl.lit(scalar_val)).otherwise(pl.col(col_name)).alias(col_name)
                    )
            else:
                # Scalar value - use directly
                df = df.with_columns(
                    pl.when(mask).then(pl.lit(new_val)).otherwise(pl.col(col_name)).alias(col_name)
                )
        
        return df
    
    def _get_rows(self, row_indexer):
        """Get rows based on the indexer."""
        if isinstance(row_indexer, int):
            return self._df[row_indexer:row_indexer+1]
        elif isinstance(row_indexer, slice):
            start = row_indexer.start if row_indexer.start is not None else 0
            stop = row_indexer.stop if row_indexer.stop is not None else self.length
            if stop < 0:
                stop = self.length + stop + 1
            return self._df[start:stop]
        elif isinstance(row_indexer, (list, pl.Series)):
            if isinstance(row_indexer, list):
                if all(isinstance(x, bool) for x in row_indexer):
                    return self._df.filter(pl.Series(row_indexer))
                else:
                    return (
                            self._df.with_row_count("__row__")
                            .filter(pl.col("__row__").is_in(row_indexer))
                            .drop("__row__")
                        ).collect() if self.is_lazy else self._df[row_indexer] # type: ignore
            else:
                return self._df.filter(row_indexer)
        elif isinstance(row_indexer, np.ndarray):
            if row_indexer.dtype == bool:
                return self._df.filter(pl.Series(row_indexer.tolist()))
            else:
                return self._df[row_indexer.tolist()]
        else:
            raise TypeError(f"Invalid row indexer type: {type(row_indexer)}")
    
    def _get_with_row_col(self, row_indexer, col_indexer):
        """Get specific rows and columns."""
        # First get the rows
        if isinstance(row_indexer, int):
            rows_df = self._df[row_indexer:row_indexer+1]
        elif isinstance(row_indexer, slice):
            start = row_indexer.start if row_indexer.start is not None else 0
            stop = row_indexer.stop if row_indexer.stop is not None else self.length
            if stop < 0:
                stop = self.length + stop + 1
            rows_df = self._df[start:stop]
        elif isinstance(row_indexer, (list, pl.Series, np.ndarray)):
            rows_df = self._get_rows(row_indexer)
        else:
            rows_df = self._df
        
        # Then get the columns
        if isinstance(col_indexer, str):
            result = rows_df.select(col_indexer)
            result = (result.collect() if isinstance(result, pl.LazyFrame) else result)
            if isinstance(row_indexer, int):
                # Return scalar for single row, single column
                return result.item()
            # For single column selection, return as Series for pandas-like behavior
            return result.to_series()
        elif isinstance(col_indexer, list):
            return rows_df.select(col_indexer).collect() if isinstance(rows_df, pl.LazyFrame) else rows_df.select(col_indexer)
        elif isinstance(col_indexer, slice):
            cols = list(rows_df.columns)
            start = col_indexer.start
            stop = col_indexer.stop
            
            if isinstance(start, str):
                start = cols.index(start)
            if isinstance(stop, str):
                stop = cols.index(stop) + 1
            
            selected_cols = cols[slice(start, stop)]
            return rows_df.select(selected_cols).collect() if isinstance(rows_df, pl.LazyFrame) else rows_df.select(selected_cols)
        elif col_indexer is None or (isinstance(col_indexer, slice) and col_indexer == slice(None)):
            return rows_df.collect() if isinstance(rows_df, pl.LazyFrame) else rows_df
        else:
            raise TypeError(f"Invalid column indexer type: {type(col_indexer)}")


class ILocAccessor(UniversalPolarsDataFrameExtension):
    """Integer position-based accessor for polars DataFrames (similar to pandas .iloc)."""
    
    def __init__(self, df: Union[pl.DataFrame, pl.LazyFrame], namespace=None):
        super().__init__(df)
        self._namespace = namespace
        
    def __getitem__(self, key):
        """Get items using integer position-based indexing."""
        if isinstance(key, tuple):
            row_indexer, col_indexer = key[0], key[1] if len(key) > 1 else slice(None)
            return self._get_with_row_col(row_indexer, col_indexer)
        else:
            return self._get_rows(key)
    
    def __setitem__(self, key, value):
        """Set items using integer position-based indexing."""
        return self._set_and_return(key, value)
    
    def _set_and_return(self, key, value):
        """Set values and return the new DataFrame."""
        if isinstance(key, tuple):
            row_indexer, col_indexer = key[0], key[1] if len(key) > 1 else slice(None)
        else:
            row_indexer, col_indexer = key, slice(None)
        
        df = self._df
        
        # Convert row indexer to list of row indices
        if isinstance(row_indexer, int):
            if row_indexer < 0:
                row_indexer = self.length + row_indexer
            row_indices = [row_indexer]
        elif isinstance(row_indexer, slice):
            start, stop, step = row_indexer.start, row_indexer.stop, row_indexer.step
            if start is None:
                start = 0
            elif start < 0:
                start = self.length + start
            if stop is None:
                stop = self.length
            elif stop < 0:
                stop = self.length + stop
            row_indices = list(range(start, stop, step or 1))
        elif isinstance(row_indexer, (list, np.ndarray)):
            if isinstance(row_indexer, np.ndarray):
                row_indexer = row_indexer.tolist()
            row_indices = [i if i >= 0 else self.length + i for i in row_indexer]
        else:
            raise TypeError(f"Invalid row indexer type: {type(row_indexer)}")
        
        # Convert column positions to column names
        cols = self.columns
        if isinstance(col_indexer, int):
            if col_indexer < 0:
                col_indexer = len(cols) + col_indexer
            col_names = [cols[col_indexer]]
        elif isinstance(col_indexer, slice):
            selected_cols = cols[col_indexer]
            col_names = selected_cols
        elif isinstance(col_indexer, (list, np.ndarray)):
            if isinstance(col_indexer, np.ndarray):
                col_indexer = col_indexer.tolist()
            col_indexer = [i if i >= 0 else len(cols) + i for i in col_indexer]
            col_names = [cols[i] for i in col_indexer]
        else:
            col_names = cols
        
        # Update values
        for col_name in col_names:
            col_data = (df.select(col_name).collect() if isinstance(df, pl.LazyFrame) else df)[col_name].to_list()

            for i, row_idx in enumerate(row_indices):
                # Determine the value to set
                if hasattr(value, '__len__') and not isinstance(value, str):
                    if len(col_names) == 1:
                        # Single column, multiple values
                        if i < len(value):
                            new_val = value[i]
                        else:
                            new_val = value[-1] if value else None
                    else:
                        # Multiple columns
                        col_idx = col_names.index(col_name)
                        if hasattr(value[0] if value else None, '__len__'):
                            # 2D array
                            new_val = value[i][col_idx] if i < len(value) else None
                        else:
                            # 1D array for multiple columns
                            new_val = value[col_idx] if col_idx < len(value) else None
                else:
                    # Scalar value
                    new_val = value
                
                # Cast value to appropriate type
                new_val = cast_value_to_column_type(new_val, self.schema[col_name])
                col_data[row_idx] = new_val
            
            # Update the DataFrame
            df = df.with_columns(pl.Series(col_name, col_data))
        
        return df
    
    def _get_rows(self, row_indexer):
        """Get rows based on integer position."""
        if isinstance(row_indexer, int):
            if row_indexer < 0:
                row_indexer = self.length + row_indexer
            return self._df[row_indexer:row_indexer+1]
        elif isinstance(row_indexer, slice):
            return self._df[row_indexer]
        elif isinstance(row_indexer, (list, np.ndarray)):
            if isinstance(row_indexer, np.ndarray):
                row_indexer = row_indexer.tolist()
            row_indexer = [i if i >= 0 else self.length + i for i in row_indexer]
            return (
                        self._df.with_row_count("__row__")
                        .filter(pl.col("__row__") == row_indexer)
                        .drop("__row__")
                    ).collect() if self.is_lazy else self._df[row_indexer] # type: ignore
        else:
            raise TypeError(f"Invalid row indexer type: {type(row_indexer)}")
    
    def _get_with_row_col(self, row_indexer, col_indexer):
        """Get specific rows and columns by position."""
        # First get the rows
        if isinstance(row_indexer, int):
            if row_indexer < 0:
                row_indexer = self.length + row_indexer
            rows_df = self._df[row_indexer:row_indexer+1]
        elif isinstance(row_indexer, slice):
            rows_df = self._df[row_indexer]
        elif isinstance(row_indexer, (list, np.ndarray)):
            rows_df = self._get_rows(row_indexer)
        else:
            rows_df = self._df
        
        # Then get the columns by position
        cols = list(rows_df.columns)
        
        if isinstance(col_indexer, int):
            if col_indexer < 0:
                col_indexer = len(cols) + col_indexer
            col_name = cols[col_indexer]
            result = rows_df.select(col_name).collect() if isinstance(rows_df, pl.LazyFrame) else rows_df.select(col_name)
            if isinstance(row_indexer, int):
                return result.item()
            return result
        elif isinstance(col_indexer, slice):
            selected_cols = cols[col_indexer]
            return rows_df.select(selected_cols)
        elif isinstance(col_indexer, (list, np.ndarray)):
            if isinstance(col_indexer, np.ndarray):
                col_indexer = col_indexer.tolist()
            col_indexer = [i if i >= 0 else len(cols) + i for i in col_indexer]
            selected_cols = [cols[i] for i in col_indexer]
            return rows_df.select(selected_cols)
        elif col_indexer is None:
            return rows_df
        else:
            raise TypeError(f"Invalid column indexer type: {type(col_indexer)}")


class AtAccessor(UniversalPolarsDataFrameExtension):
    """Label-based scalar accessor for polars DataFrames (similar to pandas .at)."""
    
    def __init__(self, df: Union[pl.DataFrame, pl.LazyFrame], namespace=None):
        super().__init__(df)
        self._namespace = namespace
    
    def __getitem__(self, key):
        """Get a single scalar value by row index and column label."""
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError(".at requires exactly two arguments: row_index and column_label")
        
        row_idx, col_label = key
        
        if not isinstance(row_idx, (int, np.integer)):
            raise TypeError(f".at row indexer must be an integer, got {type(row_idx)}")
        if not isinstance(col_label, str):
            raise TypeError(f".at column indexer must be a string, got {type(col_label)}")
        
        if row_idx < 0:
            row_idx = self.length + row_idx
        
        return self._df[row_idx, col_label] # type: ignore
    
    def __setitem__(self, key, value):
        """Set a single scalar value by row index and column label."""
        return self._set_and_return(key, value)
    
    def _set_and_return(self, key, value):
        """Set value and return new DataFrame."""
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError(".at requires exactly two arguments: row_index and column_label")
        
        row_idx, col_label = key
        
        if not isinstance(row_idx, (int, np.integer)):
            raise TypeError(f".at row indexer must be an integer, got {type(row_idx)}")
        if not isinstance(col_label, str):
            raise TypeError(f".at column indexer must be a string, got {type(col_label)}")
        
        
        if row_idx < 0:
            row_idx = self.length + row_idx

        col_data = (self._df.select(col_label).collect() if self.is_lazy else self._df)[col_label].to_list() # type: ignore
        new_val = cast_value_to_column_type(value, self.schema[col_label])
        col_data[row_idx] = new_val

        return self._df.with_columns(pl.Series(col_label, col_data))


class IatAccessor(UniversalPolarsDataFrameExtension):
    """Integer position-based scalar accessor for polars DataFrames (similar to pandas .iat)."""
    
    def __init__(self, df: Union[pl.DataFrame, pl.LazyFrame], namespace=None):
        super().__init__(df)
        self._namespace = namespace

    def __getitem__(self, key):
        """Get a single scalar value by row and column integer positions."""
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError(".iat requires exactly two arguments: row_position and column_position")
        
        row_pos, col_pos = key
        
        if not isinstance(row_pos, (int, np.integer)):
            raise TypeError(f".iat row position must be an integer, got {type(row_pos)}")
        if not isinstance(col_pos, (int, np.integer)):
            raise TypeError(f".iat column position must be an integer, got {type(col_pos)}")
        
        if row_pos < 0:
            row_pos = self.length + row_pos
        if col_pos < 0:
            col_pos = len(self.columns) + col_pos
        
        col_name = self.columns[col_pos]
        return self._df[row_pos, col_name] # type: ignore
    
    def __setitem__(self, key, value):
        """Set a single scalar value by row and column integer positions."""
        return self._set_and_return(key, value)
    
    def _set_and_return(self, key, value):
        """Set value and return new DataFrame."""
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError(".iat requires exactly two arguments: row_position and column_position")
        
        row_pos, col_pos = key
        
        if not isinstance(row_pos, (int, np.integer)):
            raise TypeError(f".iat row position must be an integer, got {type(row_pos)}")
        if not isinstance(col_pos, (int, np.integer)):
            raise TypeError(f".iat column position must be an integer, got {type(col_pos)}")
        
        if row_pos < 0:
            row_pos = self.length + row_pos
        cols = self.columns
        if col_pos < 0:
            col_pos = len(cols) + col_pos
        
        col_name = cols[col_pos]
        col_data = (self._df.select(col_name).collect() if self.is_lazy else self._df)[col_name].to_list() # type: ignore
        new_val = cast_value_to_column_type(value, self.schema[col_name])
        col_data[row_pos] = new_val
        
        return self._df.with_columns(pl.Series(col_name, col_data))


class IterRowsAccessor(UniversalPolarsDataFrameExtension):
    """Iterator for DataFrame rows that mimics pandas iterrows behavior."""
    
    def __init__(self, df: Union[pl.DataFrame, pl.LazyFrame]):
        super().__init__(df)
        self._index = 0
    
    def __iter__(self) -> Iterator[Tuple[int, dict]]:
        """Return the iterator object."""
        return self
    
    def __next__(self) -> Tuple[int, dict]:
        """
        Get the next row as (index, row_dict) tuple.
        
        Returns:
            Tuple of (index, row_dict) where row_dict contains column:value pairs.
        """
        if self._index >= self.length:
            raise StopIteration
        
        # Get the row as a dictionary
        if self.is_lazy:
            row_data = self._df.slice(self._index, 1).collect().row(0, named=True) # type: ignore
        else:
            row_data = self._df.row(self._index, named=True) # type: ignore

        # Return index and row data
        result = (self._index, row_data)
        self._index += 1
        
        return result