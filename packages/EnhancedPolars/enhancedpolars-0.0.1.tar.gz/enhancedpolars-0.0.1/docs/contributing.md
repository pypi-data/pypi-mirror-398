# Contributing Guide

Thank you for your interest in contributing to EnhancedPolars! This document provides guidelines for contributing code, documentation, and bug reports.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style Guide](#code-style-guide)
- [Architecture Guidelines](#architecture-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Messages](#commit-messages)

---

## Development Setup

### Prerequisites

- Python 3.13.2 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Git

### Setting Up Your Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/EnhancedPolars.git
cd EnhancedPolars

# Create virtual environment and install dependencies
uv sync

# Install dev dependencies
uv sync --dev

# Verify installation
uv run pytest UNIT_TESTS/ -v
```

### Running Tests

```bash
# Run all tests
uv run pytest UNIT_TESTS/ -v

# Run specific test file
uv run pytest UNIT_TESTS/test_merging.py -v

# Run specific test
uv run pytest UNIT_TESTS/test_merging.py::TestMergeBasic::test_merge_inner -v

# Run with coverage
uv run pytest UNIT_TESTS/ --cov=src --cov-report=html
```

---

## Code Style Guide

### General Principles

1. **Clarity over cleverness** - Write code that is easy to read and understand
2. **Consistency** - Follow existing patterns in the codebase
3. **Minimal changes** - Only modify what's necessary for your feature/fix
4. **No over-engineering** - Avoid premature abstraction and unnecessary complexity

### Python Style

#### Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 120 characters
- Use double quotes for strings (`"string"` not `'string'`)
- Add trailing commas in multi-line collections

#### Imports

Order imports as follows, separated by blank lines:

```python
# Standard library
import os
from typing import Optional, List, Union

# Third-party
import polars as pl
import numpy as np

# Local
from .base import UniversalPolarsDataFrameExtension
from .merging import PolarsMerging
```

#### Type Hints

Always use type hints for function signatures:

```python
def merge(
    self,
    right: Union[pl.DataFrame, pl.LazyFrame],
    on: Optional[str] = None,
    how: Literal["inner", "left", "right", "outer"] = "inner",
) -> Union[pl.DataFrame, pl.LazyFrame]:
    """Merge two DataFrames."""
    ...
```

#### Docstrings

Use NumPy-style docstrings for all public functions and classes:

```python
def merge_asof(
    self,
    right: Union[pl.DataFrame, pl.LazyFrame],
    on: str,
    strategy: Literal["backward", "forward", "nearest"] = "backward",
) -> Union[pl.DataFrame, pl.LazyFrame]:
    """
    Perform an asof join with automatic dtype resolution.

    Parameters
    ----------
    right : DataFrame or LazyFrame
        The right DataFrame to join with.
    on : str
        Column name to join on. Must be sorted.
    strategy : {'backward', 'forward', 'nearest'}, default 'backward'
        Strategy for matching:
        - 'backward': Match with the last row where right <= left
        - 'forward': Match with the first row where right >= left
        - 'nearest': Match with the closest row

    Returns
    -------
    DataFrame or LazyFrame
        Result of the asof join with resolved dtypes.

    Raises
    ------
    ValueError
        If the 'on' column is not present in both DataFrames.

    Examples
    --------
    >>> left = pl.DataFrame({"time": [1, 2, 3], "value": [10, 20, 30]})
    >>> right = pl.DataFrame({"time": [1, 3], "data": ["a", "b"]})
    >>> left.epl.merge_asof(right, on="time")
    """
    ...
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `PolarsMerging`, `UniversalPolarsDataFrameExtension` |
| Functions/Methods | snake_case | `merge_asof`, `read_csv` |
| Variables | snake_case | `left_df`, `column_names` |
| Constants | UPPER_SNAKE_CASE | `MAX_BATCH_SIZE`, `DEFAULT_SUFFIX` |
| Private | Leading underscore | `_internal_method`, `_cached_schema` |
| Type aliases | PascalCase | `DataFrame`, `ColumnName` |

### Error Handling

- Use specific exception types, not bare `Exception`
- Provide helpful error messages with context
- Validate inputs early and fail fast

```python
def set_columns(self, new_columns: List[str]) -> pl.DataFrame:
    if not isinstance(new_columns, (list, tuple)):
        raise TypeError(
            f"new_columns must be a list or tuple, got {type(new_columns).__name__}"
        )

    if len(new_columns) != self.width:
        raise ValueError(
            f"Number of new column names ({len(new_columns)}) must match "
            f"number of columns ({self.width})"
        )

    for i, name in enumerate(new_columns):
        if not isinstance(name, str):
            raise TypeError(
                f"Column name at index {i} must be a string, got {type(name).__name__}"
            )

    ...
```

---

## Architecture Guidelines

### Extension Pattern

All DataFrame extensions should inherit from `UniversalPolarsDataFrameExtension`:

```python
from .base import UniversalPolarsDataFrameExtension

class MyExtension(UniversalPolarsDataFrameExtension):
    """Extension providing my functionality."""

    def my_method(self, arg1: str) -> pl.DataFrame:
        """Do something with the DataFrame."""
        # Access the DataFrame via self._df
        return self._df.with_columns(...)
```

### LazyFrame Support

All operations should work with both DataFrame and LazyFrame:

```python
def my_method(self) -> Union[pl.DataFrame, pl.LazyFrame]:
    # Use self._df directly - it could be either type
    result = self._df.with_columns(...)

    # Return same type as input (automatic with most Polars operations)
    return result
```

When you need to materialize for inspection:

```python
def my_method(self) -> Union[pl.DataFrame, pl.LazyFrame]:
    # Get schema without collecting
    if isinstance(self._df, pl.LazyFrame):
        schema = self._df.collect_schema()
    else:
        schema = self._df.schema

    # If you must collect, remember the input type
    was_lazy = isinstance(self._df, pl.LazyFrame)
    df = self._df.collect() if was_lazy else self._df

    # ... do work ...

    # Return as original type
    return result.lazy() if was_lazy else result
```

### Namespace Registration

To add methods to the `epl` namespace, add your extension class to the `build_namespace` call in `register.py`:

```python
# In register.py
UDNamespace = build_namespace("epl", [
    PolarsDataFrameInterpolationExtension,
    UniversalPolarsDataFrameIndexingExtension,
    PolarsMerging,
    # ... other extensions ...
    MyNewExtension,  # Add your extension here
])
```

### Polars API Compatibility

- Use native Polars methods (not pandas equivalents) internally
- Use `pl.col()` expressions, not `df["column"]` for operations
- Prefer lazy evaluation when possible
- Remember Polars uses snake_case (e.g., `is_not_null()` not `notnull()`)

---

## Testing Requirements

### Test Coverage

- All public methods must have tests
- Aim for >90% code coverage on new code
- Include edge cases (empty DataFrames, null values, etc.)

### Test Structure

```python
import pytest
import polars as pl
from enhancedpolars.my_module import MyExtension


class TestMyExtension:
    """Tests for MyExtension class."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4.0, 5.0, 6.0],
        })

    def test_my_method_basic(self, sample_df):
        """Test basic functionality."""
        ext = MyExtension(sample_df)
        result = ext.my_method()

        assert result.shape == (3, 2)
        assert "a" in result.columns

    def test_my_method_with_lazyframe(self, sample_df):
        """Test with LazyFrame input."""
        lf = sample_df.lazy()
        ext = MyExtension(lf)
        result = ext.my_method()

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected.shape == (3, 2)

    def test_my_method_empty_df(self):
        """Test with empty DataFrame."""
        df = pl.DataFrame({"a": [], "b": []}).cast({"a": pl.Int64, "b": pl.Float64})
        ext = MyExtension(df)
        result = ext.my_method()

        assert result.shape[0] == 0

    def test_my_method_raises_on_invalid_input(self, sample_df):
        """Test error handling."""
        ext = MyExtension(sample_df)

        with pytest.raises(ValueError, match="expected positive"):
            ext.my_method(invalid_arg=-1)
```

### Test Naming

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>` or `Test<Feature>`
- Test methods: `test_<method>_<scenario>`

### Type Narrowing for Pylance

When testing methods that return `DataFrame | LazyFrame`, narrow the type for assertions:

```python
def test_merge_result_shape(self, left_df, right_df):
    """Test merge returns correct shape."""
    ext = PolarsMerging(left_df)
    result = ext.merge(right_df, on="key")

    # Narrow type for Pylance
    if isinstance(result, pl.LazyFrame):
        result = result.collect()

    assert result.shape[0] == 4
```

---

## Pull Request Process

### Before Submitting

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Write tests** for your changes

3. **Run the full test suite**:
   ```bash
   uv run pytest UNIT_TESTS/ -v
   ```

4. **Check for type errors** (if using an IDE with Pylance)

5. **Update documentation** if adding new features

### PR Requirements

- Clear, descriptive title
- Description of what the PR does and why
- Link to any related issues
- All tests passing
- No decrease in code coverage

### PR Template

```markdown
## Summary
Brief description of the changes.

## Changes
- Added X functionality
- Fixed Y bug
- Updated Z documentation

## Testing
Describe how you tested the changes.

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] No breaking changes (or documented if necessary)
```

---

## Commit Messages

Use clear, descriptive commit messages:

### Format

```
<type>: <short description>

<optional longer description>

<optional footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `test` | Adding/updating tests |
| `refactor` | Code refactoring (no functional change) |
| `perf` | Performance improvement |
| `chore` | Build/tooling changes |

### Examples

```
feat: add merge_asof method with automatic sorting

Adds merge_asof to PolarsMerging class that automatically sorts
DataFrames before performing the asof join.

Closes #42
```

```
fix: handle empty DataFrame in interpolation

Previously, interpolate() would raise an error on empty DataFrames.
Now it returns the empty DataFrame unchanged.
```

```
test: add comprehensive tests for groupby apply method
```

---

## Questions?

If you have questions about contributing, please open an issue on GitHub.
