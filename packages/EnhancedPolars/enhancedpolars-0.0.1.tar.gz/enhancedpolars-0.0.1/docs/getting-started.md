# Getting Started

## Installation

### From PyPI

```bash
pip install EnhancedPolars
```

Or with uv:

```bash
uv add EnhancedPolars
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/EnhancedPolars.git
cd EnhancedPolars

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Dependencies




### Core Dependencies

| Package | Minimum Version | Purpose |
|---------|-----------------|---------|
| Python | 3.13.2+ | Runtime |
| polars | 1.33.0+ | Core DataFrame library |
| numpy | 2.3.0+ | Numerical operations |
| pandas | 2.3.0+ | DataFrame interoperability |
| pyarrow | 21.0.0+ | Arrow format support |
| tqdm | 4.67.0+ | Progress bars |
| python-dateutil | 2.9.0+ | Date parsing |
| SQLUtilities | 0.1.1+ | SQL dialect support |
| CoreUtilities | 0.0.6+ | Type definitions |
| joblib | 1.5.0+ | Model serialization |

### Optional Dependencies

| Package | Minimum Version | Extra | Purpose |
|---------|-----------------|-------|---------|
| scipy | 1.16.0+ | `[sci]` | Statistical functions, interpolation |
| scikit-learn | 1.7.0+ | `[ml]` | ML preprocessing, scalers, encoders |

Install optional dependencies with:

```bash
pip install "EnhancedPolars[all]"  # All optional deps
pip install "EnhancedPolars[sci]"  # Scientific computing only
pip install "EnhancedPolars[ml]"   # ML preprocessing only
```


## Quick Start

### Basic Setup

```python
import polars as pl

# Import the enhanced polars module
from enhancedpolars import epl

# Register the 'epl' namespace on all DataFrames/LazyFrames
from enhancedpolars.register import *
```

### Reading Data

```python
# Read CSV with automatic type optimization
df = epl.read_csv("data.csv", cleanup=True)

# Read with specific cleanup options
df = epl.read_csv(
    "data.csv",
    cleanup=True,
    optimize_types=True,
    clean_column_names=True,
    desired_column_name_case='snake_case'
)

# Read Parquet
df = epl.read_parquet("data.parquet")

# Read Excel
df = epl.read_excel("data.xlsx", sheet_name="Sheet1")
```

### Using the `epl` Namespace

Once you import `from enhancedpolars.register import *`, all DataFrames and LazyFrames gain access to the `epl` namespace:

```python
df = pl.DataFrame({
    "id": [1, 2, 3],
    "value": [10.5, 20.3, 30.1],
    "category": ["A", "B", "A"]
})

# Access properties
print(df.epl.shape)      # (3, 3)
print(df.epl.columns)    # ['id', 'value', 'category']
print(df.epl.length)     # 3

# Pandas-like indexing
row = df.epl.loc[0]                    # First row
subset = df.epl.loc[0:2, ["id", "value"]]  # Slice with columns
value = df.epl.at[1, "value"]          # Single value access
```

### Merging DataFrames

```python
left = pl.DataFrame({"key": [1, 2, 3], "left_val": ["a", "b", "c"]})
right = pl.DataFrame({"key": [2, 3, 4], "right_val": ["x", "y", "z"]})

# Inner join with automatic dtype resolution
result = left.epl.merge(right, on="key", how="inner")

# Left join
result = left.epl.merge(right, on="key", how="left")

# Asof join (for time series)
result = left.epl.merge_asof(right, on="timestamp", by="group")
```

### GroupBy Operations

```python
df = pl.DataFrame({
    "group": ["A", "A", "B", "B"],
    "value": [1, 2, 3, 4]
})

# Pandas-style aggregation
result = df.epl.groupby(["group"]).agg({"value": ["mean", "sum", "max"]})

# Custom function application
def double_values(group_df):
    return group_df.with_columns(pl.col("value") * 2)

result = df.epl.groupby(["group"]).apply(double_values)
```

### ML Preprocessing

```python
# Standardize numeric columns
df_scaled, scaler_meta = df.epl.standardize(columns=["value"])

# One-hot encode categorical columns
df_encoded = df.epl.one_hot_encode(columns=["category"])

# Complete ML-ready transformation
df_ready, metadata = df.epl.make_ml_ready(
    target_col="label",
    exclude_cols=["id"],
    default_numeric_scaler="StandardScaler"
)
```

### SQL Operations

```python
from sqlutilities import DatabaseConnection, SQLDialect

# Create a database connection
conn = DatabaseConnection(
    host="localhost",
    database="mydb",
    username="user",
    password="pass",
    dialect=SQLDialect.POSTGRES
)

# Upload DataFrame to SQL table
df.epl.to_sql(
    connection=conn,
    table_name="my_table",
    if_exists="replace",
    batch_size=10000
)
```

### Interpolation

```python
df = pl.DataFrame({
    "time": [1, 2, 3, 4, 5],
    "value": [1.0, None, None, 4.0, 5.0]
})

# Forward fill
df_filled = df.epl.ffill(columns=["value"])

# Linear interpolation
df_interp = df.epl.interpolate(columns=["value"], method="linear")
```

## LazyFrame Support

Most operations work seamlessly with LazyFrames:

```python
lf = pl.scan_csv("large_data.csv")

# Operations return LazyFrame when input is LazyFrame
result = lf.epl.merge(other_lf, on="key", how="left")

# Collect when ready
df = result.collect()
```

## Next Steps

- See [API Reference](api-reference.md) for complete method documentation
- Check [Examples](examples.md) for more detailed use cases
- Read [Contributing](contributing.md) to contribute to the project
