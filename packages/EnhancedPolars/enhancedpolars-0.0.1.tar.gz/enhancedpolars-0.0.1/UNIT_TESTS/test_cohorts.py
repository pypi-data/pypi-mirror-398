"""
Tests for cohorts.py - PolarsCohorts extension
"""

import pytest
import polars as pl
import pandas as pd
from datetime import datetime
from enhancedpolars.cohorts import PolarsCohorts, SKLEARN_AVAILABLE


class TestTrainTestValSplitBasic:
    """Tests for basic train_test_val_split functionality."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for splitting."""
        return pl.DataFrame({
            "id": list(range(100)),
            "feature1": [i * 2 for i in range(100)],
            "feature2": [i % 10 for i in range(100)],
            "label": [i % 2 for i in range(100)],
        })

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_default_split_random(self, sample_df):
        """Test random split with default percentages."""
        ext = PolarsCohorts(sample_df)
        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
            split_type='random',
        )

        assert "cohort" in result.columns
        # Check that all rows have a cohort assigned
        assert result["cohort"].null_count() == 0

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_split_with_project_name(self, sample_df):
        """Test split with project name prefix."""
        ext = PolarsCohorts(sample_df)
        result = ext.train_test_val_split(
            project_name="MyProject",
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
            split_type='random',
        )

        # Cohort names should start with project name
        cohorts = result["cohort"].unique().to_list()
        assert all("MyProject_" in c for c in cohorts)

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_split_percentages_sum_to_one(self, sample_df):
        """Test that split percentages must sum to 1."""
        ext = PolarsCohorts(sample_df)
        with pytest.raises(AssertionError):
            ext.train_test_val_split(
                dev_percent=0.5,
                val_percent=0.2,
                test_percent=0.2,  # Sum = 0.9, not 1
            )


class TestTrainTestValSplitLongitudinal:
    """Tests for longitudinal (time-based) splits."""

    @pytest.fixture
    def time_df(self):
        """Create a DataFrame with time column."""
        return pl.DataFrame({
            "id": list(range(100)),
            "timestamp": [datetime(2023, 1, 1 + (i % 28), i % 24) for i in range(100)],
            "value": [i * 10 for i in range(100)],
        })

    def test_longitudinal_split_basic(self, time_df):
        """Test basic longitudinal split."""
        ext = PolarsCohorts(time_df)
        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
            split_type='longitudinal',
            time_index_col='timestamp',
        )

        assert "cohort" in result.columns
        # All rows should have cohort assigned
        assert result["cohort"].null_count() == 0

    def test_longitudinal_requires_time_col(self, time_df):
        """Test that longitudinal split requires time column."""
        ext = PolarsCohorts(time_df)
        with pytest.raises(AssertionError):
            ext.train_test_val_split(
                dev_percent=0.7,
                val_percent=0.1,
                test_percent=0.2,
                split_type='longitudinal',
                # time_index_col not specified
            )

    def test_longitudinal_with_random_fallback_no_time(self, time_df):
        """Test that longitudinal_with_random_fallback falls back to random without time col."""
        df = time_df.drop("timestamp")
        ext = PolarsCohorts(df)

        if SKLEARN_AVAILABLE:
            result = ext.train_test_val_split(
                dev_percent=0.7,
                val_percent=0.1,
                test_percent=0.2,
                split_type='longitudinal_with_random_fallback',
            )
            assert "cohort" in result.columns
        else:
            pytest.skip("sklearn required for random fallback")


class TestTrainTestValSplitStratification:
    """Tests for stratified splits."""

    @pytest.fixture
    def stratified_df(self):
        """Create a DataFrame with stratification columns."""
        return pl.DataFrame({
            "id": list(range(100)),
            "category": ["A", "B", "C", "D"] * 25,
            "value": [i * 10 for i in range(100)],
        })

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_stratified_random_split(self, stratified_df):
        """Test random split with stratification."""
        ext = PolarsCohorts(stratified_df)
        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
            split_type='random',
            stratification_columns=['category'],
        )

        assert "cohort" in result.columns


class TestTrainTestValSplitEdgeCases:
    """Tests for edge cases in train_test_val_split."""

    def test_single_cohort_dev_only(self):
        """Test when only development cohort is requested."""
        df = pl.DataFrame({
            "id": list(range(10)),
            "value": [i * 10 for i in range(10)],
        })
        ext = PolarsCohorts(df)
        result = ext.train_test_val_split(
            dev_percent=1.0,
            val_percent=0.0,
            test_percent=0.0,
        )

        assert "cohort" in result.columns
        # All should be in Development cohort
        cohorts = result["cohort"].unique().to_list()
        assert len(cohorts) == 1
        assert "Development" in cohorts[0]

    def test_single_cohort_test_only(self):
        """Test when only test cohort is requested."""
        df = pl.DataFrame({
            "id": list(range(10)),
            "value": [i * 10 for i in range(10)],
        })
        ext = PolarsCohorts(df)
        result = ext.train_test_val_split(
            dev_percent=0.0,
            val_percent=0.0,
            test_percent=1.0,
        )

        assert "cohort" in result.columns
        cohorts = result["cohort"].unique().to_list()
        assert len(cohorts) == 1
        assert "Test" in cohorts[0]


    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pl.DataFrame({
            "id": [],
            "value": [],
        }).cast({"id": pl.Int64, "value": pl.Int64})
        ext = PolarsCohorts(df)
        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
        )

        assert "cohort" in result.columns


    def test_single_row_dataframe(self):
        """Test with single-row DataFrame."""
        df = pl.DataFrame({
            "id": [1],
            "value": [10],
        })
        ext = PolarsCohorts(df)
        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
        )

        assert "cohort" in result.columns
        assert result.shape[0] == 1


class TestTrainTestValSplitWithRowId:
    """Tests for row ID handling."""

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_row_id_created_if_missing(self):
        """Test that row_id is created if not present."""
        df = pl.DataFrame({
            "value": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],  # Need more rows for split
        })
        ext = PolarsCohorts(df)

        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,  # Non-zero to avoid sklearn edge case
            test_percent=0.2,
            split_type='random',
        )

        # row_id should not be in final result (dropped)
        assert "row_id" not in result.columns

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_existing_unique_index_col_used(self):
        """Test that existing unique_index_col is used."""
        df = pl.DataFrame({
            "my_id": list(range(20)),  # Need enough rows for split
            "value": [i * 10 for i in range(20)],
        })
        ext = PolarsCohorts(df)

        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,  # Non-zero to avoid sklearn edge case
            test_percent=0.2,
            split_type='random',
            unique_index_col='my_id',
        )

        # my_id should still be in result
        assert "my_id" in result.columns


class TestTrainTestValSplitRandomState:
    """Tests for reproducibility with random state."""

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_reproducible_splits(self):
        """Test that same random_state produces same splits."""
        df = pl.DataFrame({
            "id": list(range(50)),
            "value": [i * 10 for i in range(50)],
        })

        ext1 = PolarsCohorts(df)
        result1 = ext1.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
            split_type='random',
            random_state=42,
        )

        ext2 = PolarsCohorts(df)
        result2 = ext2.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
            split_type='random',
            random_state=42,
        )

        # Same random state should produce same results
        assert result1["cohort"].equals(result2["cohort"])


class TestLazyFrame:
    """Tests for LazyFrame input."""

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_lazyframe_input(self):
        """Test that LazyFrame input works."""
        lf = pl.LazyFrame({
            "id": list(range(20)),
            "value": [i * 10 for i in range(20)],
        })

        ext = PolarsCohorts(lf)
        result = ext.train_test_val_split(
            dev_percent=0.7,
            val_percent=0.1,
            test_percent=0.2,
            split_type='random',
        )

        # Result should be a DataFrame (collected)
        assert isinstance(result, pl.DataFrame)
        assert "cohort" in result.columns


class TestInheritance:
    """Tests for inheritance from UniversalPolarsDataFrameExtension."""

    def test_inherits_properties(self):
        """Test that PolarsCohorts inherits base properties."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

        ext = PolarsCohorts(df)

        assert ext.schema == {"a": pl.Int64, "b": pl.Int64}
        assert ext.length == 3
        assert ext.width == 2
        assert ext.columns == ["a", "b"]
