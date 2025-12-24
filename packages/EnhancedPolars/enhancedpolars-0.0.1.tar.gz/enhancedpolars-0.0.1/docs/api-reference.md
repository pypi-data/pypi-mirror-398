# API Reference

This document provides comprehensive API documentation for all EnhancedPolars modules.

## Table of Contents

- [EnhancedPolars (epl)](#enhancedpolars-epl)
- [Unified Namespace (epl)](#unified-namespace-ud)
- [Indexing](#indexing)
- [Merging](#merging)
- [GroupBy](#groupby)
- [Interpolation](#interpolation)
- [ML Pipeline](#ml-pipeline)
- [Series Extensions](#series-extensions)
- [I/O Operations](#io-operations)
- [SQL Operations](#sql-operations)
- [Statistics](#statistics)
- [Time Integration](#time-integration)
- [Cohorts](#cohorts)

---

## EnhancedPolars (epl)

The `EnhancedPolars` class provides enhanced I/O operations and utility methods. It acts as a drop-in replacement for the `polars` module with additional functionality.

```python
from enhancedpolars import epl
```

### I/O Methods

#### `epl.read_csv()`

Read CSV with optional automatic cleanup and type optimization.

```python
df = epl.read_csv(
    source,                           # File path or file-like object
    cleanup=False,                    # Enable automatic cleanup
    optimize_types=True,              # Optimize column dtypes
    type_inference_confidence=0.6,    # Confidence threshold for type inference
    clean_column_names=True,          # Clean column names
    desired_column_name_case='snake_case',  # 'snake_case', 'camelCase', 'PascalCase', etc.
    **kwargs                          # Additional polars.read_csv arguments
)
```

#### `epl.read_parquet()`

Read Parquet files with optional cleanup.

```python
df = epl.read_parquet(source, cleanup=False, **kwargs)
```

#### `epl.read_excel()`

Read Excel files.

```python
df = epl.read_excel(
    source,
    sheet_name=None,      # Sheet name or index
    cleanup=False,
    **kwargs
)
```

#### `epl.read_json()`

Read JSON files with optional cleanup.

```python
df = epl.read_json(source, cleanup=False, **kwargs)
```

### Utility Methods

#### `epl.cleanup()`

Clean and optimize a DataFrame.

```python
df = epl.cleanup(
    df,
    optimize_types=True,
    type_inference_confidence=0.6,
    attempt_numeric_to_datetime=False,
    clean_column_names=True,
    desired_column_name_case='preserve'
)
```

#### `epl.optimize_dtypes()`

Optimize column data types to reduce memory usage.

```python
df = epl.optimize_dtypes(
    df,
    confidence=0.6,
    attempt_numeric_to_datetime=False
)
```

#### `epl.infer_dtypes()`

Infer optimal data types for columns.

```python
inferred_types = epl.infer_dtypes(df, confidence=0.6)
```

---

## Unified Namespace (epl)

The `epl` namespace provides access to all extension methods on any DataFrame or LazyFrame.

```python
from enhancedpolars.register import *

df = pl.DataFrame({"a": [1, 2, 3]})
df.epl.method_name()  # Access any extension method
```

### Properties

| Property | Description |
|----------|-------------|
| `df.epl.schema` | Column names and types |
| `df.epl.columns` | List of column names |
| `df.epl.length` | Number of rows |
| `df.epl.height` | Alias for length |
| `df.epl.width` | Number of columns |
| `df.epl.shape` | Tuple of (rows, columns) |
| `df.epl.is_lazy` | True if LazyFrame |

### Null Detection

```python
# DataFrame of boolean masks for null/NaN values
null_mask = df.epl.isnull()   # or df.epl.isna()

# DataFrame of boolean masks for non-null values
valid_mask = df.epl.notnull()  # or df.epl.notna()
```

---

## Indexing

Pandas-like indexing accessors for DataFrames.

### loc - Label-based Indexing

```python
# Single row by index
row = df.epl.loc[0]

# Row slice
rows = df.epl.loc[0:5]

# Row and column selection
subset = df.epl.loc[0:5, ["col1", "col2"]]

# Boolean indexing
filtered = df.epl.loc[df["value"] > 10]
```

### iloc - Position-based Indexing

```python
# Single row by position
row = df.epl.iloc[0]

# Row slice by position
rows = df.epl.iloc[0:5]

# Row and column by position
subset = df.epl.iloc[0:5, 0:2]
```

### at - Single Value Access (Label-based)

```python
value = df.epl.at[0, "column_name"]
```

### iat - Single Value Access (Position-based)

```python
value = df.epl.iat[0, 0]  # First row, first column
```

---

## Merging

Enhanced merge operations with automatic dtype conflict resolution.

### merge()

```python
result = df.epl.merge(
    right,                    # DataFrame to merge with
    how='inner',              # 'inner', 'left', 'right', 'outer', 'cross'
    on=None,                  # Column(s) to join on (both sides)
    left_on=None,             # Left join column(s)
    right_on=None,            # Right join column(s)
    suffix='_right',          # Suffix for overlapping columns
    validate=None,            # 'one_to_one', 'one_to_many', 'many_to_one', 'many_to_many'
    nulls_equal=False         # Treat nulls as equal in join
)
```

### merge_asof()

Time-aware merge for time series data. Automatically sorts DataFrames.

```python
result = df.epl.merge_asof(
    right,
    on='timestamp',           # Column to match on (must be sorted)
    by=None,                  # Additional exact-match columns
    strategy='backward',      # 'backward', 'forward', 'nearest'
    tolerance=None,           # Maximum distance for match
    allow_exact_matches=True
)
```

### concat()

Concatenate DataFrames with automatic dtype resolution.

```python
result = df.epl.concat(
    df2, df3,                 # DataFrames to concatenate
    how='vertical',           # 'vertical', 'horizontal', 'diagonal'
    rechunk=False,
    parallel=True
)
```

---

## GroupBy

Enhanced groupby operations with pandas-like syntax.

### groupby()

```python
gb = df.epl.groupby(["group_col"])
```

### agg()

Aggregation with pandas-style dictionary syntax.

```python
# Polars style
result = gb.agg(
    pl.col("value").mean().alias("mean_value"),
    max_value=pl.col("value").max()
)

# Pandas style (dictionary)
result = gb.agg({
    "col1": "mean",
    "col2": "max",
    "col3": ["mean", "max", "sum"]
})
```

### apply()

Apply custom function to each group.

```python
def process_group(group_df):
    return group_df.with_columns(pl.col("value") * 2)

result = gb.apply(process_group)
```

### Fill Methods

```python
# Forward fill within groups
result = df.epl.groupby(["group"]).ffill(columns=["value"])

# Backward fill within groups
result = df.epl.groupby(["group"]).bfill(columns=["value"])

# Fill with specific values
result = df.epl.groupby(["group"]).fillna(columns=["value"], value=0)
```

---

## Interpolation

Methods for filling missing values and interpolation.

### ffill() - Forward Fill

```python
result = df.epl.ffill(
    columns=None,    # Columns to fill (None = all)
    limit=None       # Maximum consecutive fills
)
```

### bfill() - Backward Fill

```python
result = df.epl.bfill(columns=None, limit=None)
```

### interpolate()

```python
result = df.epl.interpolate(
    columns=None,
    method='linear',  # 'linear', 'nearest', 'cubic', 'polynomial'
    order=None        # For polynomial interpolation
)
```

### fillna()

```python
result = df.epl.fillna(
    columns=None,
    value=None,       # Static fill value
    method=None       # 'ffill' or 'bfill'
)
```

### rolling()

Rolling window operations.

```python
result = df.epl.rolling(
    window=3,
    columns=["value"],
    agg="mean",       # 'mean', 'sum', 'min', 'max', 'std', 'var'
    min_periods=1,
    center=False
)
```

---

## ML Pipeline

Machine learning preprocessing utilities.

### standardize()

Standardize numeric columns (z-score normalization).

```python
df_scaled, metadata = df.epl.standardize(
    columns=None,          # Columns to standardize (None = all numeric)
    exclude_columns=None,  # Columns to exclude
    with_mean=True,
    with_std=True
)
```

### clip_and_impute()

Clip outliers and impute missing values.

```python
df_cleaned = df.epl.clip_and_impute(
    columns=None,
    lower_quantile=0.01,
    upper_quantile=0.99,
    impute_strategy='median'  # 'mean', 'median', 'mode', 'constant'
)
```

### make_ml_ready()

Complete ML preprocessing pipeline.

```python
df_ready, metadata = df.epl.make_ml_ready(
    target_col=None,
    exclude_cols=None,
    one_hot_threshold=None,           # Dict of {col: threshold}
    default_one_hot_threshold=10,     # Default unique value threshold
    default_numeric_scaler='StandardScaler'
)
```

### Series ML Extensions (epl)

```python
series = df["column"]

# Null/NaN detection (handles both null and NaN for floats)
mask = series.epl.isnull()
mask = series.epl.notnull()

# Scale/encode with saved scaler
scaled = series.epl.scale_encode(
    path="scaler.joblib",
    scaler_type='StandardScaler',  # or 'MinMaxScaler', 'LabelEncoder', etc.
    train_mode=False
)

# Drop null and NaN values
cleaned = series.epl.dropna()
```

---

## Series Extensions

### epl Namespace (Series)

```python
series = df["column"]

# Null/NaN detection
mask = series.epl.isnull()
mask = series.epl.notnull()

# Expression generation
expr = series.epl.isnull_expr()
expr = series.epl.notnull_expr()
```

---

## I/O Operations

### to_excel()

Write DataFrame to Excel file.

```python
df.epl.to_excel(
    path,
    sheet_name="Sheet1",
    **kwargs
)
```

### to_parquet()

Write DataFrame to Parquet file.

```python
df.epl.to_parquet(path, **kwargs)
```

---

## SQL Operations

### to_sql()

Upload DataFrame to SQL database.

```python
df.epl.to_sql(
    connection,           # DatabaseConnection object
    table_name,
    schema=None,
    if_exists='fail',     # 'fail', 'replace', 'append'
    batch_size=10000,
    method='bulk',        # 'bulk', 'multi', 'single'
    dtype_map=None        # Override column type mappings
)
```

---

## Statistics

Statistical methods available through the `epl` namespace.

### Descriptive Statistics

```python
# Summary statistics
stats = df.epl.describe()

# Correlation matrix
corr = df.epl.corr()

# Covariance matrix
cov = df.epl.cov()
```

### Hypothesis Tests

```python
# T-test
result = df.epl.ttest(col1, col2)

# Chi-square test
result = df.epl.chi2_test(col1, col2)

# ANOVA
result = df.epl.anova(value_col, group_col)
```

---

## Time Integration

Utilities for time series data.

### add_time_boundaries()

Add start/end boundary rows to time series data.

```python
from enhancedpolars.time_integration import add_time_boundaries

result = add_time_boundaries(
    data_structure,
    dt_name="timestamp",
    start=start_datetime,      # or DataFrame with start times
    end=end_datetime,          # or DataFrame with end times
    id_name=None,              # ID column for grouped data
    label_name=None,           # Label column for multi-label expansion
    start_fill_value=None,
    end_fill_value=None,
    trim=True
)
```

### aggregate_connected_segments()

Aggregate overlapping time intervals.

```python
from enhancedpolars.time_integration import aggregate_connected_segments

result = aggregate_connected_segments(
    frame,
    start_col="start",
    end_col="end",
    by=None,                   # Group by columns
    tolerance=None,            # Gap tolerance for connectivity
    agg_fn=None,               # Aggregation function
    compute_union_duration=True
)
```

---

## Cohorts

Cohort analysis utilities.

### create_cohorts()

Create cohort assignments.

```python
df_with_cohorts = df.epl.create_cohorts(
    date_col="signup_date",
    period="month"            # 'day', 'week', 'month', 'quarter', 'year'
)
```

### cohort_analysis()

Perform cohort retention analysis.

```python
result = df.epl.cohort_analysis(
    cohort_col="cohort",
    period_col="activity_date",
    value_col="revenue",
    agg="sum"
)
```

---

## Type Reference

### Supported Scalers (ML Pipeline)

| Scaler | Description |
|--------|-------------|
| `StandardScaler` | Z-score normalization (mean=0, std=1) |
| `MinMaxScaler` | Scale to [0, 1] range |
| `RobustScaler` | Scale using median and IQR (outlier-resistant) |
| `MaxAbsScaler` | Scale by maximum absolute value |
| `QuantileTransformer` | Transform to uniform or normal distribution |
| `PowerTransformer` | Apply power transform (Box-Cox, Yeo-Johnson) |
| `LabelEncoder` | Encode categorical labels as integers |
| `OneHotEncoder` | One-hot encode categorical variables |
| `OrdinalEncoder` | Encode ordinal categories as integers |

### Join Types

| Type | Description |
|------|-------------|
| `inner` | Only matching rows from both DataFrames |
| `left` | All rows from left, matching from right |
| `right` | All rows from right, matching from left |
| `outer` | All rows from both DataFrames |
| `cross` | Cartesian product of both DataFrames |

### Interpolation Methods

| Method | Description |
|--------|-------------|
| `linear` | Linear interpolation between points |
| `nearest` | Use nearest valid value |
| `cubic` | Cubic spline interpolation |
| `polynomial` | Polynomial interpolation (requires `order` parameter) |
