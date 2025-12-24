# EnhancedPolars

Enhanced utilities for [Polars](https://pola.rs/) DataFrames, providing pandas-like convenience while maintaining Polars' blazing-fast performance.

## Features

- **Unified Namespace (`epl`)** - Access all extensions through `df.epl.*`
- **Pandas-like Indexing** - `loc`, `iloc`, `at`, `iat` accessors
- **Enhanced Merging** - Automatic dtype resolution and asof joins
- **ML Pipeline Tools** - Standardization, encoding, and preprocessing
- **SQL Integration** - Direct DataFrame upload to databases
- **Time Series Utilities** - Interpolation, boundaries, and cohort analysis
- **Statistical Functions** - Hypothesis tests and descriptive statistics
- **Full LazyFrame Support** - All operations work with lazy evaluation

---

## Installation

```bash
pip install EnhancedPolars
```

Or with uv:

```bash
uv add EnhancedPolars
```

---

## Quick Start

```python
import polars as pl
from enhancedpolars import epl
from enhancedpolars.register import *  # Register the 'epl' namespace

# Read data with automatic type optimization
df = epl.read_csv("data.csv", cleanup=True)

# Pandas-like indexing
subset = df.epl.loc[0:10, ["col1", "col2"]]
value = df.epl.at[0, "col1"]

# Enhanced merging with automatic dtype resolution
result = df.epl.merge(other_df, on="key", how="left")

# Time-aware asof join
trades = trades_df.epl.merge_asof(prices_df, on="timestamp", strategy="backward")

# GroupBy with pandas-style syntax
summary = df.epl.groupby(["category"]).agg({
    "value": ["mean", "sum", "max"],
    "count": "sum"
})

# ML preprocessing
df_ready, metadata = df.epl.make_ml_ready(
    target_col="label",
    default_numeric_scaler="StandardScaler"
)

# SQL upload
df.epl.to_sql(connection, "table_name", if_exists="replace")
```

---

## Documentation

| Document                                   | Description                             |
| ------------------------------------------ | --------------------------------------- |
| [Getting Started](docs/getting-started.md) | Installation and quick start guide      |
| [API Reference](docs/api-reference.md)     | Complete API documentation              |
| [Examples](docs/examples.md)               | Practical usage examples                |
| [Contributing](docs/contributing.md)       | Contributing guidelines and style guide |

---

## Key Modules

### Indexing

```python
df.epl.loc[0]                      # First row
df.epl.loc[0:5, ["a", "b"]]        # Slice with columns
df.epl.iloc[0, 0]                  # Position-based access
df.epl.at[0, "column"]             # Single value access
```

### Merging

```python
df.epl.merge(right, on="key", how="left")
df.epl.merge_asof(right, on="timestamp", by="group")
df.epl.concat(df2, df3, how="vertical")
```

### GroupBy

```python
df.epl.groupby(["col"]).agg({"value": ["mean", "sum"]})
df.epl.groupby(["col"]).apply(custom_function)
df.epl.groupby(["col"]).ffill(columns=["value"])
```

### Interpolation

```python
df.epl.ffill(columns=["value"])
df.epl.bfill(columns=["value"])
df.epl.interpolate(columns=["value"], method="linear")
df.epl.fillna(columns=["value"], value=0)
```

### ML Pipeline

```python
df.epl.standardize(columns=["numeric_col"])
df.epl.clip_and_impute(columns=["value"], impute_strategy="median")
df.epl.make_ml_ready(target_col="label")

# Series-level operations
series.epl.scale_encode(path="scaler.joblib", scaler_type="StandardScaler")
series.epl.isnull()  # Handles both null and NaN
```

### SQL

```python
df.epl.to_sql(connection, "table_name", if_exists="replace", batch_size=10000)
```

---

## Requirements

### Core Dependencies

- **Python** 3.13.2+
- **polars** >= 1.33.0
- **numpy** >= 2.3.0
- **pandas** >= 2.3.0
- **pyarrow** >= 21.0.0
- Plus: tqdm, python-dateutil, joblib

### Optional Dependencies

Install with extras for additional functionality:

```bash
# For scientific computing (interpolation, hypothesis tests)
pip install "EnhancedPolars[sci]"

# For ML preprocessing (scalers, encoders)
pip install "EnhancedPolars[ml]"

# Install all optional dependencies
pip install "EnhancedPolars[all]"
```

- **`[sci]`** - Scientific computing: scipy >= 1.16.0
- **`[ml]`** - Machine learning: scikit-learn >= 1.7.0


---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**@Ruppert20**

---

## AI Authorship Disclaimer

This package was developed with the assistance of LLM-based coding tools (Claude Code by Anthropic). AI tools were used for the following activities:

- **Code authorship** - Implementation of utilities, functions, and classes
- **Test development** - Creation of comprehensive unit tests
- **Documentation** - Generation of NumPy-style docstrings and README content
- **Code review** - Identification of bugs, edge cases, and improvements

Users should evaluate the code for their specific use cases and report any issues through the GitHub issue tracker.

---

## Contributing

See [Contributing Guide](docs/contributing.md) for guidelines on:

- Development setup
- Code style
- Testing requirements
- Pull request process
