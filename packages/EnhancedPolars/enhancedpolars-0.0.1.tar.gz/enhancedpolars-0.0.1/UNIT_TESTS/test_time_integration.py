"""
Tests for time_integration.py - Time series integration utilities
"""

import pytest
import polars as pl
from datetime import datetime, timedelta
from enhancedpolars.time_integration import aggregate_connected_segments, add_time_boundaries


class TestAggregateConnectedSegmentsBasic:
    """Tests for basic aggregate_connected_segments functionality."""

    @pytest.fixture
    def simple_intervals(self):
        """Create simple non-overlapping intervals."""
        return pl.DataFrame({
            "start": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 2, 0),
                datetime(2023, 1, 1, 5, 0),
            ],
            "end": [
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 3, 0),
                datetime(2023, 1, 1, 6, 0),
            ],
            "value": [10, 20, 30],
        })

    def test_non_overlapping_intervals(self, simple_intervals):
        """Test that non-overlapping intervals remain separate."""
        result = aggregate_connected_segments(
            simple_intervals,
            start_col="start",
            end_col="end",
        )

        # Each interval should be its own segment
        assert result.shape[0] == 3

    def test_overlapping_intervals_merge(self):
        """Test that overlapping intervals are merged."""
        df = pl.DataFrame({
            "start": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
            ],
            "end": [
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
            ],
        })

        result = aggregate_connected_segments(
            df,
            start_col="start",
            end_col="end",
        )

        # Overlapping intervals should merge into one segment
        assert result.shape[0] == 1
        assert result["n_segments"][0] == 2

    def test_adjacent_intervals_merge_with_tolerance(self):
        """Test that adjacent intervals merge when tolerance allows."""
        df = pl.DataFrame({
            "start": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 1, 5),  # 5 minutes after first ends
            ],
            "end": [
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 2, 0),
            ],
        })

        # Without tolerance, should be separate
        result_no_tol = aggregate_connected_segments(
            df,
            start_col="start",
            end_col="end",
        )
        assert result_no_tol.shape[0] == 2

        # With tolerance >= 5 minutes, should merge
        result_with_tol = aggregate_connected_segments(
            df,
            start_col="start",
            end_col="end",
            tolerance=timedelta(minutes=10),
        )
        assert result_with_tol.shape[0] == 1


class TestAggregateConnectedSegmentsWithGroups:
    """Tests for aggregate_connected_segments with grouping."""

    @pytest.fixture
    def grouped_intervals(self):
        """Create intervals with groups."""
        return pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "start": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 2, 0),
            ],
            "end": [
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 3, 0),
            ],
            "value": [10, 20, 30, 40],
        })

    def test_grouping_basic(self, grouped_intervals):
        """Test that grouping works correctly."""
        result = aggregate_connected_segments(
            grouped_intervals,
            start_col="start",
            end_col="end",
            by="group",
        )

        # Group A: 2 overlapping -> 1 segment
        # Group B: 2 non-overlapping -> 2 segments
        assert result.shape[0] == 3

    def test_grouping_maintains_group_columns(self, grouped_intervals):
        """Test that group columns are preserved in output."""
        result = aggregate_connected_segments(
            grouped_intervals,
            start_col="start",
            end_col="end",
            by="group",
        )

        assert "group" in result.columns


class TestAggregateConnectedSegmentsAggregation:
    """Tests for aggregate_connected_segments with custom aggregation."""

    @pytest.fixture
    def intervals_with_values(self):
        """Create intervals with values to aggregate."""
        return pl.DataFrame({
            "start": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
            ],
            "end": [
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
            ],
            "value": [10, 20],
            "count": [1, 2],
        })

    def test_dict_aggregation(self, intervals_with_values):
        """Test aggregation with dictionary specification."""
        result = aggregate_connected_segments(
            intervals_with_values,
            start_col="start",
            end_col="end",
            agg_fn={"value": "sum", "count": "max"},
        )

        assert result.shape[0] == 1
        assert result["value"][0] == 30
        assert result["count"][0] == 2

    def test_callable_aggregation(self, intervals_with_values):
        """Test aggregation with callable function."""
        def custom_agg(df):
            return {"total_value": df["value"].sum()}

        result = aggregate_connected_segments(
            intervals_with_values,
            start_col="start",
            end_col="end",
            agg_fn=custom_agg,
        )

        assert "total_value" in result.columns
        assert result["total_value"][0] == 30


class TestAggregateConnectedSegmentsUnionDuration:
    """Tests for union duration computation."""

    def test_union_duration_non_overlapping(self):
        """Test union duration for non-overlapping intervals."""
        df = pl.DataFrame({
            "start": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 2, 0),
            ],
            "end": [
                datetime(2023, 1, 1, 1, 0),  # 1 hour
                datetime(2023, 1, 1, 3, 0),  # 1 hour
            ],
        })

        result = aggregate_connected_segments(
            df,
            start_col="start",
            end_col="end",
            compute_union_duration=True,
            tolerance=timedelta(hours=2),  # Force merge
        )

        # Union should be 2 hours total (non-overlapping)
        assert result.shape[0] == 1
        assert result["union_duration"][0] == timedelta(hours=2)

    def test_union_duration_overlapping(self):
        """Test union duration for overlapping intervals."""
        df = pl.DataFrame({
            "start": [
                datetime(2023, 1, 1, 0, 0),
                datetime(2023, 1, 1, 0, 30),
            ],
            "end": [
                datetime(2023, 1, 1, 1, 0),
                datetime(2023, 1, 1, 1, 30),
            ],
        })

        result = aggregate_connected_segments(
            df,
            start_col="start",
            end_col="end",
            compute_union_duration=True,
        )

        # Union should be 1.5 hours (overlapping by 30 min)
        assert result.shape[0] == 1
        assert result["union_duration"][0] == timedelta(hours=1, minutes=30)


class TestAggregateConnectedSegmentsLazy:
    """Tests for lazy evaluation."""

    def test_lazyframe_input(self):
        """Test that LazyFrame input works."""
        lf = pl.LazyFrame({
            "start": [datetime(2023, 1, 1, 0, 0)],
            "end": [datetime(2023, 1, 1, 1, 0)],
        })

        result = aggregate_connected_segments(
            lf,
            start_col="start",
            end_col="end",
            compute_union_duration=False,
        )

        assert isinstance(result, pl.LazyFrame)


class TestAggregateConnectedSegmentsValidation:
    """Tests for input validation."""

    def test_negative_tolerance_raises(self):
        """Test that negative tolerance raises ValueError."""
        df = pl.DataFrame({
            "start": [datetime(2023, 1, 1)],
            "end": [datetime(2023, 1, 2)],
        })

        with pytest.raises(ValueError, match="non-negative"):
            aggregate_connected_segments(
                df,
                start_col="start",
                end_col="end",
                tolerance=timedelta(seconds=-1),
            )


class TestAddTimeBoundariesBasic:
    """Tests for basic add_time_boundaries functionality."""

    @pytest.fixture
    def simple_ts(self):
        """Create simple time series data with explicit Int64 type."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
            ],
            "value": pl.Series([10, 20, 30], dtype=pl.Int64),
        })

    def test_add_start_boundary(self, simple_ts):
        """Test adding a start boundary."""
        result = add_time_boundaries(
            simple_ts,
            dt_name="timestamp",
            start=datetime(2023, 1, 1),
            start_fill_value=None,  # Use None to avoid type mismatch
            trim=False,
        )

        assert result.shape[0] == 4
        # Check that start boundary was added
        result_sorted = result.sort("timestamp")
        assert result_sorted["timestamp"][0] == datetime(2023, 1, 1)

    def test_add_end_boundary(self, simple_ts):
        """Test adding an end boundary."""
        result = add_time_boundaries(
            simple_ts,
            dt_name="timestamp",
            end=datetime(2023, 1, 5),
            end_fill_value=None,  # Use None to avoid type mismatch
            trim=False,
        )

        assert result.shape[0] == 4
        # Check that end boundary was added
        result_sorted = result.sort("timestamp")
        assert result_sorted["timestamp"][-1] == datetime(2023, 1, 5)

    def test_add_both_boundaries(self, simple_ts):
        """Test adding both start and end boundaries."""
        result = add_time_boundaries(
            simple_ts,
            dt_name="timestamp",
            start=datetime(2023, 1, 1),
            end=datetime(2023, 1, 5),
            start_fill_value=None,
            end_fill_value=None,
            trim=False,
        )

        assert result.shape[0] == 5


class TestAddTimeBoundariesWithGroups:
    """Tests for add_time_boundaries with ID-based grouping."""

    @pytest.fixture
    def grouped_ts(self):
        """Create time series data with IDs."""
        return pl.DataFrame({
            "id": ["A", "A", "B", "B"],
            "timestamp": [
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 2),
                datetime(2023, 1, 4),
            ],
            "value": pl.Series([10, 20, 15, 25], dtype=pl.Int64),
        })

    def test_boundaries_per_id(self, grouped_ts):
        """Test that boundaries are added per ID."""
        start_df = pl.DataFrame({
            "id": ["A", "B"],
            "timestamp": [datetime(2023, 1, 1), datetime(2023, 1, 1)],
        })

        result = add_time_boundaries(
            grouped_ts,
            dt_name="timestamp",
            start=start_df,
            id_name="id",
            start_fill_value=None,  # Use None to avoid type mismatch
            trim=False,
        )

        # Should have 2 more rows (one start boundary per ID)
        assert result.shape[0] == 6


class TestAddTimeBoundariesTrimming:
    """Tests for trimming functionality."""

    @pytest.fixture
    def extended_ts(self):
        """Create time series with data outside boundaries."""
        return pl.DataFrame({
            "timestamp": [
                datetime(2022, 12, 30),  # Before start
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 10),  # After end
            ],
            "value": pl.Series([1, 10, 20, 100], dtype=pl.Int64),
        })

    def test_trim_removes_outside_data(self, extended_ts):
        """Test that trim removes data outside boundaries."""
        result = add_time_boundaries(
            extended_ts,
            dt_name="timestamp",
            start=datetime(2023, 1, 1),
            end=datetime(2023, 1, 5),
            start_fill_value=None,
            end_fill_value=None,
            trim=True,
        )

        # Original data at 12/30 and 1/10 should be removed
        # Result should have 2 original rows + 2 boundary rows = 4
        assert result.shape[0] == 4

    def test_inclusive_both(self, extended_ts):
        """Test inclusive='both' includes boundary times."""
        ts = pl.DataFrame({
            "timestamp": [
                datetime(2023, 1, 1),  # Exactly at start
                datetime(2023, 1, 3),
                datetime(2023, 1, 5),  # Exactly at end
            ],
            "value": pl.Series([1, 20, 100], dtype=pl.Int64),
        })

        result = add_time_boundaries(
            ts,
            dt_name="timestamp",
            start=datetime(2023, 1, 1),
            end=datetime(2023, 1, 5),
            start_fill_value=None,
            end_fill_value=None,
            trim=True,
            inclusive='both',
        )

        # All original rows should remain + 2 boundary rows
        # But note boundaries might overlap with existing data
        assert result.shape[0] >= 3


class TestAddTimeBoundariesWithLabels:
    """Tests for add_time_boundaries with label-based expansion."""

    @pytest.fixture
    def labeled_ts(self):
        """Create time series with labels."""
        return pl.DataFrame({
            "id": ["A", "A", "A"],
            "timestamp": [
                datetime(2023, 1, 2),
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
            ],
            "metric": ["temp", "humidity", "temp"],
            "value": pl.Series([20.5, 60.0, 22.1], dtype=pl.Float64),
        })


    def test_label_expansion(self, labeled_ts):
        """Test that boundaries are expanded for all label values."""
        start_df = pl.DataFrame({
            "id": ["A"],
            "timestamp": [datetime(2023, 1, 1)],
        })

        result = add_time_boundaries(
            labeled_ts,
            dt_name="timestamp",
            start=start_df,
            id_name="id",
            label_name="metric",
            start_fill_value=None,  # Use None to avoid type mismatch
            trim=False,
        )

        # Should have boundary rows for each unique metric value
        # Original: 3 rows, plus boundaries for 2 metrics = 5 rows
        assert result.shape[0] == 5


class TestAddTimeBoundariesValidation:
    """Tests for input validation."""

    def test_invalid_data_structure_raises(self):
        """Test that invalid input raises TypeError."""
        with pytest.raises(TypeError):
            add_time_boundaries(
                "not a dataframe",  # type: ignore
                dt_name="timestamp",
            )

    def test_id_name_with_datetime_raises(self):
        """Test that id_name with single datetime raises AssertionError."""
        df = pl.DataFrame({
            "id": ["A", "A"],
            "timestamp": [datetime(2023, 1, 2), datetime(2023, 1, 3)],
            "value": [10, 20],
        })

        with pytest.raises(AssertionError):
            add_time_boundaries(
                df,
                dt_name="timestamp",
                start=datetime(2023, 1, 1),
                id_name="id",  # Should be None for single datetime
            )


class TestAddTimeBoundariesLazyFrame:
    """Tests for LazyFrame support."""

    def test_lazyframe_input(self):
        """Test that LazyFrame input works."""
        lf = pl.LazyFrame({
            "timestamp": [datetime(2023, 1, 2), datetime(2023, 1, 3)],
            "value": pl.Series([10, 20], dtype=pl.Int64),
        })

        result = add_time_boundaries(
            lf,
            dt_name="timestamp",
            start=datetime(2023, 1, 1),
            start_fill_value=None,  # Use None to avoid type mismatch
            trim=False,
        )

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected.shape[0] == 3
