# EnhancedPolars Documentation

Welcome to the EnhancedPolars documentation. This library provides enhanced utilities for [Polars](https://pola.rs/) DataFrames, bringing pandas-like convenience while maintaining Polars' performance advantages.

## Table of Contents

- [Getting Started](getting-started.md) - Installation, setup, and quick start guide
- [API Reference](api-reference.md) - Complete API documentation for all modules
- [Examples](examples.md) - Practical usage examples and tutorials
- [Contributing](contributing.md) - Contributing guidelines and style guide

## Overview

EnhancedPolars extends Polars with:

- **Unified Namespace (`epl`)** - Access all extensions through `df.epl.*`
- **Pandas-like Indexing** - `loc`, `iloc`, `at`, `iat` accessors
- **Enhanced Merging** - Automatic dtype resolution for joins
- **ML Pipeline Tools** - Standardization, encoding, and preprocessing
- **SQL Integration** - Direct DataFrame upload to databases
- **Time Series Utilities** - Boundary handling and cohort analysis
- **Statistical Functions** - Hypothesis tests and descriptive statistics
- **Interpolation** - Forward fill, backward fill, and advanced interpolation

## Quick Example

```python
import polars as pl
from enhancedpolars import epl
from enhancedpolars.register import *  # Register the 'epl' namespace

# Read data with automatic type optimization
df = epl.read_csv("data.csv", cleanup=True)

# Use pandas-like indexing
subset = df.epl.loc[0:10, ["col1", "col2"]]

# Perform operations through the unified namespace
result = df.epl.merge(other_df, on="key", how="left")

# ML preprocessing
scaled_df, metadata = df.epl.make_ml_ready(target_col="label")

# Upload to SQL database
df.epl.to_sql(connection, "table_name")
```

## Architecture

```
enhancedpolars/
├── enhancedpolars/
│   ├── __init__.py          # Package exports
│   ├── register.py          # Namespace registration (epl)
│   ├── epl.py               # EnhancedPolars - enhanced I/O and utilities
│   ├── base.py              # Base extension class
│   ├── indexing.py          # loc/iloc/at/iat accessors
│   ├── merging.py           # Enhanced merge operations
│   ├── groupby.py           # GroupBy extensions
│   ├── io.py                # I/O operations (Excel, Parquet, etc.)
│   ├── interpolation.py     # Interpolation methods
│   ├── ml_pipeline.py       # ML preprocessing utilities
│   ├── series.py            # Series extensions
│   ├── cohorts.py           # Cohort analysis
│   ├── time_integration.py  # Time series utilities
│   ├── to_sql.py            # SQL upload functionality
│   ├── pyarrow_typing.py    # PyArrow type utilities
│   └── Stats/
│       ├── descriptive_stats.py
│       ├── hypothesis_tests.py
│       └── random_sampling.py
└── docs/
    ├── README.md             # This file
    ├── getting-started.md
    ├── api-reference.md
    ├── examples.md
    └── contributing.md
```

## License

MIT License - see [LICENSE](../LICENSE) for details.
