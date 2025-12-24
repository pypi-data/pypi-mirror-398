import polars as pl
from typing import List, Tuple, cast, Type
from CoreUtilities.core_types import CoreDataType

pl_df = pl.DataFrame | pl.LazyFrame

class UniversalPolarsDataFrameExtension:
    """
    DataFrame-level API for universal Polars enhancements. This class is subclassed by other extensions.
    """
    def __init__(self, df: pl_df):
        self._df: pl_df = df
        self._schema, self._length, self._columns, self._width, self._shape = None, None, None, None, None

    @property
    def schema(self) -> dict:
        if self._schema is None:
            self._schema = cast(pl.LazyFrame, self._df).collect_schema() if self.is_lazy else self._df.schema
        return self._schema
    
    @property
    def length(self) -> int:
        if self._length is None:
            self._length = cast(int, cast(pl.LazyFrame, self._df.select(pl.count())).collect().item() if self.is_lazy else cast(pl.DataFrame, self._df).height)
        return self._length

    @property
    def width(self) -> int:
        if self._width is None:
            self._width = len(self.schema)
        return self._width

    @property
    def height(self) -> int:
        """Get the height (number of rows) of the DataFrame."""
        return self.length
    
    @property
    def columns(self) -> List[str]:
        if self._columns is None:
            self._columns = list(self.schema.keys())
        return self._columns

    @property
    def shape(self) -> Tuple[int, int]:
        """Get the shape of the DataFrame as (rows, columns)."""
        if self._shape is None:
            self._shape = (self.length, self.width)
        return self._shape
    
    @property
    def is_lazy(self) -> bool:
        """Check if the underlying DataFrame is a LazyFrame."""
        return hasattr(self._df, 'collect')
    

    def isnull(self) -> pl_df:
        """
        Detect missing values (null and NaN for float columns).

        For float columns, checks both is_null() and is_nan() since Polars
        treats them differently.

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            Boolean DataFrame indicating null/NaN values.
        """
        null_checks = []
        for col, col_dtype in self.schema.items():
            
            if CoreDataType.FLOAT.get_core_type(cast(Type, col_dtype)) == CoreDataType.FLOAT:
                # For float columns, check both null and NaN
                null_check = (pl.col(col).is_null() | pl.col(col).is_nan()).alias(col)
            else:
                # For other types, only check null
                null_check = pl.col(col).is_null().alias(col)
            
            null_checks.append(null_check)
        
        return self._df.select(null_checks)
    
    def isna(self) -> pl_df:
        """
        Detect missing values (alias for isnull).

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            Boolean DataFrame indicating missing values.
        """
        return self.isnull()

    def notnull(self) -> pl_df:
        """
        Detect non-missing values (opposite of isnull).

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            Boolean DataFrame indicating non-missing values.
        """
        not_null_checks = []
        for col, col_dtype in self.schema.items():
            
            if CoreDataType.FLOAT.get_core_type(cast(Type, col_dtype)) == CoreDataType.FLOAT:
                # For float columns, check both null and NaN
                not_null_check = (pl.col(col).is_not_null() & pl.col(col).is_not_nan()).alias(col)
            else:
                # For other types, only check null
                not_null_check = pl.col(col).is_not_null().alias(col)
            
            not_null_checks.append(not_null_check)
        
        return self._df.select(not_null_checks)
    
    def notna(self) -> pl_df:
        """
        Detect non-missing values (alias for notnull).

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            Boolean DataFrame indicating non-missing values.
        """
        return self.notnull()

    def set_columns(self, new_columns: List[str]) -> pl_df:
        """
        Set new column names for the DataFrame and return a new DataFrame.

        Since Polars DataFrames are immutable, this method returns a new DataFrame
        with the renamed columns rather than modifying in-place.

        Parameters
        ----------
        new_columns : list of str
            A list of new column names. Must have the same length as the current
            number of columns.

        Returns
        -------
        pl.DataFrame or pl.LazyFrame
            New DataFrame with renamed columns.

        Raises
        ------
        ValueError
            If the number of new column names doesn't match the number of existing columns.
        TypeError
            If new_columns is not a list of strings.
        """
        if not isinstance(new_columns, (list, tuple)):
            raise TypeError("new_columns must be a list or tuple")
        
        new_columns = list(new_columns)  # Convert to list for consistency
        
        if len(new_columns) != len(self.columns):
            raise ValueError(
                f"Number of new column names ({len(new_columns)}) must match "
                f"number of existing columns ({len(self.columns)})"
            )
        
        # Validate that all column names are strings
        for i, col_name in enumerate(new_columns):
            if not isinstance(col_name, str):
                raise TypeError(f"Column name at index {i} must be a string, got {type(col_name)}")
        
        # Create mapping from old names to new names
        column_mapping = dict(zip(self.columns, new_columns))
        
        # Return the renamed DataFrame
        return self._df.rename(column_mapping)