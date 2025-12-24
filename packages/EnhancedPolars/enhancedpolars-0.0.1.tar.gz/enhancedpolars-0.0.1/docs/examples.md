# Examples

This document provides practical examples for common use cases with EnhancedPolars.

## Table of Contents

- [Data Loading and Cleaning](#data-loading-and-cleaning)
- [Data Manipulation](#data-manipulation)
- [Time Series Operations](#time-series-operations)
- [Machine Learning Preprocessing](#machine-learning-preprocessing)
- [Database Integration](#database-integration)
- [Statistical Analysis](#statistical-analysis)

---

## Data Loading and Cleaning

### Load and Clean CSV Data

```python
from enhancedpolars import epl
from enhancedpolars.register import *

# Read CSV with automatic cleanup
df = epl.read_csv(
    "messy_data.csv",
    cleanup=True,
    optimize_types=True,
    clean_column_names=True,
    desired_column_name_case='snake_case'
)

print(df.schema)
# Before cleanup: {'Column Name!': String, ' Value ': String, 'DATE': String}
# After cleanup:  {'column_name': Int64, 'value': Float64, 'date': Date}
```

### Handle Multiple File Formats

```python
# Read various formats with consistent cleanup
csv_df = epl.read_csv("data.csv", cleanup=True)
parquet_df = epl.read_parquet("data.parquet", cleanup=True)
excel_df = epl.read_excel("data.xlsx", sheet_name="Sheet1", cleanup=True)
json_df = epl.read_json("data.json", cleanup=True)
```

### Custom Type Inference

```python
# Control type inference sensitivity
df = epl.read_csv(
    "data.csv",
    cleanup=True,
    type_inference_confidence=0.8,  # Higher = more conservative
    attempt_numeric_to_datetime=True  # Try to parse numeric timestamps
)
```

---

## Data Manipulation

### Pandas-like Indexing

```python
import polars as pl
from enhancedpolars.register import *

df = pl.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
    "score": [85, 92, 78, 95, 88],
    "department": ["Sales", "Engineering", "Sales", "Engineering", "Marketing"]
})

# Row selection
first_row = df.epl.loc[0]
first_three = df.epl.loc[0:3]

# Column selection
names_scores = df.epl.loc[:, ["name", "score"]]

# Combined selection
subset = df.epl.loc[1:4, ["name", "department"]]

# Position-based access
value = df.epl.iat[2, 2]  # Third row, third column
print(f"Charlie's score: {value}")  # 78

# Boolean indexing
high_scorers = df.epl.loc[df["score"] > 90]
```

### Advanced Merging

```python
# Sample DataFrames
customers = pl.DataFrame({
    "customer_id": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "David"],
    "region": ["East", "West", "East", "West"]
})

orders = pl.DataFrame({
    "order_id": [101, 102, 103, 104, 105],
    "customer_id": [1, 2, 1, 3, 5],  # Note: customer 5 doesn't exist
    "amount": [100.0, 250.0, 75.0, 300.0, 50.0]
})

# Left join - keep all customers
result = customers.epl.merge(orders, on="customer_id", how="left")

# Inner join - only matching records
result = customers.epl.merge(orders, on="customer_id", how="inner")

# With validation
result = customers.epl.merge(
    orders,
    on="customer_id",
    how="left",
    validate="one_to_many"  # One customer can have many orders
)
```

### Time Series Asof Join

```python
# Stock prices
prices = pl.DataFrame({
    "timestamp": pl.datetime_range(
        datetime(2024, 1, 1, 9, 0),
        datetime(2024, 1, 1, 16, 0),
        interval="1h",
        eager=True
    ),
    "price": [100.0, 101.5, 102.0, 101.0, 103.5, 104.0, 103.0, 105.0]
})

# Trade executions
trades = pl.DataFrame({
    "trade_time": [
        datetime(2024, 1, 1, 9, 30),
        datetime(2024, 1, 1, 11, 45),
        datetime(2024, 1, 1, 14, 15),
    ],
    "quantity": [100, 50, 200]
})

# Match each trade with the most recent price
result = trades.epl.merge_asof(
    prices,
    left_on="trade_time",
    right_on="timestamp",
    strategy="backward"  # Use price at or before trade time
)

print(result)
# shape: (3, 4)
# ┌─────────────────────┬──────────┬─────────────────────┬───────┐
# │ trade_time          ┆ quantity ┆ timestamp           ┆ price │
# │ ---                 ┆ ---      ┆ ---                 ┆ ---   │
# │ datetime[μs]        ┆ i64      ┆ datetime[μs]        ┆ f64   │
# ╞═════════════════════╪══════════╪═════════════════════╪═══════╡
# │ 2024-01-01 09:30:00 ┆ 100      ┆ 2024-01-01 09:00:00 ┆ 100.0 │
# │ 2024-01-01 11:45:00 ┆ 50       ┆ 2024-01-01 11:00:00 ┆ 102.0 │
# │ 2024-01-01 14:15:00 ┆ 200      ┆ 2024-01-01 14:00:00 ┆ 104.0 │
# └─────────────────────┴──────────┴─────────────────────┴───────┘
```

### GroupBy Operations

```python
df = pl.DataFrame({
    "department": ["Sales", "Sales", "Engineering", "Engineering", "Marketing"],
    "employee": ["Alice", "Bob", "Charlie", "David", "Eve"],
    "salary": [50000, 55000, 75000, 80000, 60000],
    "bonus": [5000, 6000, 10000, 12000, 7000]
})

# Pandas-style dictionary aggregation
summary = df.epl.groupby(["department"]).agg({
    "salary": ["mean", "max", "min"],
    "bonus": "sum"
})

print(summary)
# shape: (3, 5)
# ┌─────────────┬──────────────┬────────────┬────────────┬───────────┐
# │ department  ┆ salary_mean  ┆ salary_max ┆ salary_min ┆ bonus_sum │
# ├─────────────┼──────────────┼────────────┼────────────┼───────────┤
# │ Sales       ┆ 52500.0      ┆ 55000      ┆ 50000      ┆ 11000     │
# │ Engineering ┆ 77500.0      ┆ 80000      ┆ 75000      ┆ 22000     │
# │ Marketing   ┆ 60000.0      ┆ 60000      ┆ 60000      ┆ 7000      │
# └─────────────┴──────────────┴────────────┴────────────┴───────────┘

# Custom function per group
def add_rank(group_df):
    return group_df.with_columns(
        pl.col("salary").rank().alias("salary_rank")
    )

ranked = df.epl.groupby(["department"]).apply(add_rank)
```

---

## Time Series Operations

### Interpolation

```python
# Sensor data with missing readings
df = pl.DataFrame({
    "timestamp": pl.datetime_range(
        datetime(2024, 1, 1),
        datetime(2024, 1, 1, 0, 9),
        interval="1m",
        eager=True
    ),
    "temperature": [20.0, None, None, 23.0, 24.0, None, 26.0, None, None, 29.0]
})

# Forward fill - use last known value
df_ffill = df.epl.ffill(columns=["temperature"])

# Backward fill
df_bfill = df.epl.bfill(columns=["temperature"])

# Linear interpolation
df_interp = df.epl.interpolate(columns=["temperature"], method="linear")

print(df_interp)
# Gaps are filled with linearly interpolated values
```

### Rolling Statistics

```python
df = pl.DataFrame({
    "date": pl.date_range(date(2024, 1, 1), date(2024, 1, 10), eager=True),
    "value": [10, 12, 8, 15, 11, 14, 16, 13, 17, 19]
})

# 3-day rolling average
df_rolling = df.epl.rolling(
    window=3,
    columns=["value"],
    agg="mean",
    min_periods=1
)

print(df_rolling)
```

### Grouped Time Series Fill

```python
# Multiple sensors with gaps
df = pl.DataFrame({
    "sensor": ["A", "A", "A", "B", "B", "B"],
    "time": [1, 2, 3, 1, 2, 3],
    "reading": [10.0, None, 12.0, None, 25.0, None]
})

# Forward fill within each sensor group
df_filled = df.epl.groupby(["sensor"]).ffill(columns=["reading"])
```

---

## Machine Learning Preprocessing

### Complete ML Pipeline

```python
df = pl.DataFrame({
    "age": [25, 30, 35, 40, None, 50],
    "income": [50000, 60000, 75000, 90000, 100000, 120000],
    "category": ["A", "B", "A", "C", "B", "A"],
    "target": [0, 1, 0, 1, 1, 0]
})

# Complete preprocessing
df_ready, metadata = df.epl.make_ml_ready(
    target_col="target",
    exclude_cols=[],
    default_one_hot_threshold=5,      # One-hot encode if <= 5 unique values
    default_numeric_scaler="StandardScaler"
)

print(df_ready.columns)
# ['age', 'income', 'category_A', 'category_B', 'category_C', 'target']

print(metadata)
# Contains scaler info, column mappings, etc.
```

### Series-Level Scaling

```python
# Train a scaler and save it
series = df["income"]
scaled = series.epl.scale_encode(
    path="income_scaler.joblib",
    scaler_type="StandardScaler",
    train_mode=True  # Fit and save the scaler
)

# Apply saved scaler to new data
new_series = new_df["income"]
new_scaled = new_series.epl.scale_encode(
    path="income_scaler.joblib",
    scaler_type="StandardScaler",
    train_mode=False  # Load and transform only
)
```

### Handle Nulls and Outliers

```python
df = pl.DataFrame({
    "value": [1.0, 2.0, None, 100.0, 3.0, None, 4.0, 200.0]  # Has nulls and outliers
})

# Clip outliers and impute nulls
df_clean = df.epl.clip_and_impute(
    columns=["value"],
    lower_quantile=0.05,
    upper_quantile=0.95,
    impute_strategy="median"
)
```

### Categorical Encoding

```python
df = pl.DataFrame({
    "color": ["red", "blue", "green", "red", "blue"],
    "size": ["S", "M", "L", "XL", "M"]
})

# One-hot encode (for low cardinality)
df_encoded = df.epl.one_hot_encode(columns=["color"])

# Label encode (for high cardinality or ordinal)
size_series = df["size"]
size_encoded = size_series.epl.scale_encode(
    path="size_encoder.joblib",
    scaler_type="LabelEncoder",
    train_mode=True
)
```

---

## Database Integration

### Upload to PostgreSQL

```python
from sqlutilities import DatabaseConnection, SQLDialect

# Create connection
conn = DatabaseConnection(
    host="localhost",
    port=5432,
    database="mydb",
    username="user",
    password="password",
    dialect=SQLDialect.POSTGRES
)

# Upload DataFrame
df.epl.to_sql(
    connection=conn,
    table_name="customers",
    schema="public",
    if_exists="replace",  # 'fail', 'replace', 'append'
    batch_size=10000
)
```

### Upload Large DataFrames

```python
# For large DataFrames, use chunked upload
large_df.epl.to_sql(
    connection=conn,
    table_name="big_table",
    if_exists="append",
    batch_size=50000,  # Rows per batch
    method="bulk"      # Use bulk insert for speed
)
```

### Custom Type Mappings

```python
# Override automatic type inference
df.epl.to_sql(
    connection=conn,
    table_name="products",
    dtype_map={
        "description": "TEXT",
        "price": "DECIMAL(10,2)",
        "created_at": "TIMESTAMP WITH TIME ZONE"
    }
)
```

---

## Statistical Analysis

### Descriptive Statistics

```python
df = pl.DataFrame({
    "group": ["A", "A", "B", "B", "B"],
    "value1": [10, 20, 30, 40, 50],
    "value2": [1.5, 2.5, 3.5, 4.5, 5.5]
})

# Summary statistics
stats = df.epl.describe()
print(stats)

# Correlation matrix
corr = df.epl.corr()
print(corr)
```

### Hypothesis Testing

```python
# T-test between groups
from scipy import stats

group_a = df.filter(pl.col("group") == "A")["value1"]
group_b = df.filter(pl.col("group") == "B")["value1"]

t_stat, p_value = stats.ttest_ind(group_a.to_numpy(), group_b.to_numpy())
print(f"T-statistic: {t_stat:.4f}, p-value: {p_value:.4f}")
```

---

## Working with LazyFrames

### Lazy Evaluation Pipeline

```python
# All operations work with LazyFrames
lf = pl.scan_csv("large_file.csv")

# Chain operations lazily
result = (
    lf
    .pipe(lambda x: x.epl.merge(other_lf, on="key", how="left"))
    .filter(pl.col("value") > 0)
    .group_by("category")
    .agg(pl.col("value").mean())
)

# Execute when ready
df = result.collect()
```

### Memory-Efficient Processing

```python
# Process large files without loading entirely into memory
lf = pl.scan_parquet("huge_dataset/*.parquet")

# Apply transformations lazily
processed = lf.epl.fillna(columns=["value"], value=0)

# Stream results to file
processed.sink_parquet("output/processed.parquet")
```

---

## Best Practices

### 1. Use Lazy Evaluation for Large Data

```python
# Good - lazy evaluation
lf = pl.scan_csv("large.csv")
result = lf.filter(...).group_by(...).agg(...).collect()

# Avoid - loads everything into memory
df = pl.read_csv("large.csv")
result = df.filter(...).group_by(...).agg(...)
```

### 2. Chain Operations

```python
# Good - single chain
result = (
    df
    .epl.fillna(columns=["value"], value=0)
    .epl.merge(other_df, on="key")
    .filter(pl.col("value") > 0)
)

# Avoid - multiple intermediate DataFrames
df1 = df.epl.fillna(columns=["value"], value=0)
df2 = df1.epl.merge(other_df, on="key")
result = df2.filter(pl.col("value") > 0)
```

### 3. Use Expressions Over Iteration

```python
# Good - vectorized
df = df.with_columns(pl.col("value") * 2)

# Avoid - row-by-row iteration
for i in range(len(df)):
    df[i, "value"] *= 2
```

### 4. Validate Early

```python
# Check data before expensive operations
assert df.epl.length > 0, "DataFrame is empty"
assert "required_col" in df.epl.columns, "Missing required column"
assert df["id"].is_unique().all(), "IDs must be unique"
```
