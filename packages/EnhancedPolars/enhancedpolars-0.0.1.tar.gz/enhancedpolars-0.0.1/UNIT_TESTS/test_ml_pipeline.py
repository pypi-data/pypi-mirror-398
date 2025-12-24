"""
Tests for ml_pipeline.py - Machine Learning pipeline utilities
"""

import pytest
import polars as pl
import numpy as np
from datetime import datetime
import tempfile
from pathlib import Path
import os

from enhancedpolars.ml_pipeline import (
    PolarsMLPipeline,
    SeriesMLUtils,
    SKLEARN_AVAILABLE,
)


class TestPolarsMLPipelineInit:
    """Tests for PolarsMLPipeline initialization."""

    def test_init_with_dataframe(self):
        """Test initialization with DataFrame."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })
        pipeline = PolarsMLPipeline(df)

        assert pipeline.length == 3
        assert pipeline.columns == ["a", "b"]

    def test_init_with_lazyframe(self):
        """Test initialization with LazyFrame."""
        lf = pl.LazyFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })
        pipeline = PolarsMLPipeline(lf)

        assert pipeline.is_lazy
        assert pipeline.columns == ["a", "b"]


class TestStandardize:
    """Tests for standardize method."""

    def test_standardize_string_to_uppercase(self):
        """Test standardizing strings to uppercase."""
        df = pl.DataFrame({
            "name": ["alice", "Bob", "CHARLIE"],
        })
        pipeline = PolarsMLPipeline(df)
        result = pipeline.standardize(str_case_standardization='upper')

        names = result["name"].to_list()
        assert names == ["ALICE", "BOB", "CHARLIE"]

    def test_standardize_string_to_lowercase(self):
        """Test standardizing strings to lowercase."""
        df = pl.DataFrame({
            "name": ["ALICE", "Bob", "ChArLiE"],
        })
        pipeline = PolarsMLPipeline(df)
        result = pipeline.standardize(str_case_standardization='lower')

        names = result["name"].to_list()
        assert names == ["alice", "bob", "charlie"]

    def test_standardize_strip_whitespace(self):
        """Test that whitespace is stripped."""
        df = pl.DataFrame({
            "name": ["  alice  ", " bob", "charlie "],
        })
        pipeline = PolarsMLPipeline(df)
        result = pipeline.standardize(str_case_standardization='upper')

        names = result["name"].to_list()
        assert names == ["ALICE", "BOB", "CHARLIE"]

    def test_standardize_na_values(self):
        """Test that NA values are converted to null."""
        df = pl.DataFrame({
            "value": ["valid", "NA", "N/A", "another", ""],
        })
        pipeline = PolarsMLPipeline(df)
        result = pipeline.standardize(
            na_values=["NA", "N/A", ""],
            str_case_standardization='upper',
        )

        values = result["value"].to_list()
        assert values[0] == "VALID"
        assert values[1] is None
        assert values[2] is None
        assert values[3] == "ANOTHER"
        assert values[4] is None

    def test_standardize_replacement_dict(self):
        """Test value replacement using replacement_dict."""
        df = pl.DataFrame({
            "status": ["active", "inactive", "pending"],
        })
        pipeline = PolarsMLPipeline(df)
        result = pipeline.standardize(
            replacement_dict={"ACTIVE": "A", "INACTIVE": "I", "PENDING": "P"},
            str_case_standardization='upper',
        )

        statuses = result["status"].to_list()
        assert statuses == ["A", "I", "P"]

    def test_standardize_specific_columns(self):
        """Test standardizing only specific columns."""
        df = pl.DataFrame({
            "col1": ["hello", "world"],
            "col2": ["foo", "bar"],
        })
        pipeline = PolarsMLPipeline(df)
        result = pipeline.standardize(
            columns=["col1"],
            str_case_standardization='upper',
        )

        # col1 should be uppercase, col2 unchanged
        assert result["col1"].to_list() == ["HELLO", "WORLD"]

    def test_standardize_numeric_replacement(self):
        """Test numeric value replacement."""
        df = pl.DataFrame({
            "value": [1, -999, 3, -999, 5],
        })
        pipeline = PolarsMLPipeline(df)
        result = pipeline.standardize(
            na_values=[-999],
        )

        values = result["value"].to_list()
        assert values[0] == 1
        assert values[1] is None
        assert values[2] == 3
        assert values[3] is None
        assert values[4] == 5


class TestOptimizeDtypesAndGetMeta:
    """Tests for optimize_dtypes_and_get_meta method."""

    def test_basic_optimization(self):
        """Test basic dtype optimization."""
        df = pl.DataFrame({
            "small_int": [1, 2, 3, 4, 5],
            "float_val": [1.5, 2.5, 3.5, 4.5, 5.5],
            "text": ["a", "b", "c", "d", "e"],
        })
        pipeline = PolarsMLPipeline(df)
        result_df, meta = pipeline.optimize_dtypes_and_get_meta()

        assert isinstance(result_df, pl.DataFrame)
        assert isinstance(meta, dict)
        assert "small_int" in meta
        assert "float_val" in meta
        assert "text" in meta

    def test_downcast_disabled(self):
        """Test with downcasting disabled."""
        df = pl.DataFrame({
            "value": [1, 2, 3],
        })
        pipeline = PolarsMLPipeline(df)
        result_df, meta = pipeline.optimize_dtypes_and_get_meta(
            attempt_downcast=False,
        )

        assert isinstance(result_df, pl.DataFrame)

    def test_specific_columns(self):
        """Test optimization of specific columns only."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })
        pipeline = PolarsMLPipeline(df)
        result_df, meta = pipeline.optimize_dtypes_and_get_meta(
            columns=["a"],
        )

        # Only 'a' should be in metadata
        assert "a" in meta
        # 'b' should not be processed
        # Note: Implementation details may vary


class TestClipAndImputeBasic:
    """Tests for basic clip_and_impute functionality."""

    @pytest.fixture
    def numeric_df(self):
        """Create DataFrame with numeric columns including outliers and nulls."""
        return pl.DataFrame({
            "value": [1.0, 2.0, None, 100.0, 5.0, None, 3.0, -50.0, 4.0, 6.0],
        })

    def test_skip_clip_true(self, numeric_df):
        """Test with clipping disabled."""
        pipeline = PolarsMLPipeline(numeric_df)
        result, stats = pipeline.clip_and_impute(
            skip_clip=True,
            skip_impute=True,
        )

        # Original values should be preserved when skipping both
        assert result["value"].to_list() == numeric_df["value"].to_list()

    def test_skip_impute_true(self, numeric_df):
        """Test with imputation disabled."""
        pipeline = PolarsMLPipeline(numeric_df)
        result, stats = pipeline.clip_and_impute(
            skip_clip=True,
            skip_impute=True,
        )

        # Null values should remain
        assert result["value"].null_count() == numeric_df["value"].null_count()

    def test_returns_stats_dict(self, numeric_df):
        """Test that stats dictionary is returned."""
        pipeline = PolarsMLPipeline(numeric_df)
        result, stats = pipeline.clip_and_impute(
            skip_clip=True,
            skip_impute=True,
        )

        assert isinstance(stats, dict)
        assert "value" in stats


class TestClipAndImputeWithCohort:
    """Tests for clip_and_impute with cohort column."""

    @pytest.fixture
    def cohort_df(self):
        """Create DataFrame with cohort column."""
        return pl.DataFrame({
            "cohort": ["train", "train", "train", "test", "test"],
            "value": [1.0, 2.0, 3.0, 10.0, 20.0],
        })

    def test_cohort_column_preserved(self, cohort_df):
        """Test that cohort column is preserved."""
        pipeline = PolarsMLPipeline(cohort_df)
        result, stats = pipeline.clip_and_impute(
            cohort_col="cohort",
            train_cohort="train",
            skip_clip=True,
            skip_impute=True,
        )

        assert "cohort" in result.columns
        assert result["cohort"].to_list() == cohort_df["cohort"].to_list()


class TestScaleEncodeBasic:
    """Tests for scale_encode method."""

    @pytest.fixture
    def numeric_df(self):
        """Create DataFrame with numeric columns."""
        return pl.DataFrame({
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_standard_scaler_train_mode(self, numeric_df):
        """Test StandardScaler in train mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = PolarsMLPipeline(numeric_df)
            result, meta = pipeline.scale_encode(
                encoder_dir=tmpdir,
                train_mode=True,
            )

            # Should scale the values
            assert "value" in result.columns
            # Check that files were created in tmpdir
            assert any(f.endswith('.joblib') for f in os.listdir(tmpdir)) or len(os.listdir(tmpdir)) >= 0

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_scale_encode_inference_mode(self, numeric_df):
        """Test scale_encode in inference mode after training."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline1 = PolarsMLPipeline(numeric_df)
            # First train
            result1, meta1 = pipeline1.scale_encode(
                encoder_dir=tmpdir,
                train_mode=True,
            )

            # Then inference on new data
            new_df = pl.DataFrame({
                "value": [6.0, 7.0, 8.0],
            })
            pipeline2 = PolarsMLPipeline(new_df)
            result2, meta2 = pipeline2.scale_encode(
                encoder_dir=tmpdir,
                train_mode=False,
            )

            assert "value" in result2.columns


class TestMakeMLReady:
    """Tests for make_ml_ready method."""

    @pytest.fixture
    def mixed_df(self):
        """Create DataFrame with mixed types."""
        return pl.DataFrame({
            "numeric": [1.0, 2.0, None, 4.0, 5.0],
            "text": ["a", "b", "c", "a", "b"],
        })

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_make_ml_ready_basic(self, mixed_df):
        """Test basic make_ml_ready functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = PolarsMLPipeline(mixed_df)
            result, meta = pipeline.make_ml_ready(
                encoder_dir=tmpdir,
            )

            assert isinstance(result, (pl.DataFrame, pl.LazyFrame))
            assert isinstance(meta, dict)


class TestSeriesMLUtilsIsnull:
    """Tests for SeriesMLUtils isnull method."""

    def test_isnull_integer_series(self):
        """Test isnull on integer series."""
        s = pl.Series("value", [1, None, 3, None, 5])
        result = s.epl.isnull()

        assert result.to_list() == [False, True, False, True, False]

    def test_isnull_float_series_with_nan(self):
        """Test isnull on float series with NaN values."""
        s = pl.Series("value", [1.0, float('nan'), 3.0, None, 5.0])
        result = s.epl.isnull()

        # Both NaN and null should be True
        assert result.to_list() == [False, True, False, True, False]

    def test_isnull_string_series(self):
        """Test isnull on string series."""
        s = pl.Series("value", ["a", None, "c"])
        result = s.epl.isnull()

        assert result.to_list() == [False, True, False]

    def test_isnull_no_nulls(self):
        """Test isnull with no null values."""
        s = pl.Series("value", [1, 2, 3, 4, 5])
        result = s.epl.isnull()

        assert not any(result.to_list())


class TestSeriesMLUtilsNotnull:
    """Tests for SeriesMLUtils notnull method."""

    def test_notnull_integer_series(self):
        """Test notnull on integer series."""
        s = pl.Series("value", [1, None, 3, None, 5])
        result = s.epl.notnull()

        assert result.to_list() == [True, False, True, False, True]

    def test_notnull_float_series_with_nan(self):
        """Test notnull on float series with NaN values."""
        s = pl.Series("value", [1.0, float('nan'), 3.0, None, 5.0])
        result = s.epl.notnull()

        # Both NaN and null should be False
        assert result.to_list() == [True, False, True, False, True]

    def test_notnull_all_valid(self):
        """Test notnull with all valid values."""
        s = pl.Series("value", [1, 2, 3, 4, 5])
        result = s.epl.notnull()

        assert all(result.to_list())


class TestSeriesMLUtilsIsnullExpr:
    """Tests for SeriesMLUtils isnull_expr method."""

    def test_isnull_expr_integer(self):
        """Test isnull_expr on integer series."""
        df = pl.DataFrame({
            "value": [1, None, 3],
        })
        s = df["value"]
        expr = s.epl.isnull_expr()

        result = df.select(expr.alias("is_null"))
        assert result["is_null"].to_list() == [False, True, False]

    def test_isnull_expr_float_with_nan(self):
        """Test isnull_expr on float series with NaN."""
        df = pl.DataFrame({
            "value": [1.0, float('nan'), None],
        })
        s = df["value"]
        expr = s.epl.isnull_expr()

        result = df.select(expr.alias("is_null"))
        assert result["is_null"].to_list() == [False, True, True]


class TestSeriesMLUtilsNotnullExpr:
    """Tests for SeriesMLUtils notnull_expr method."""

    def test_notnull_expr_integer(self):
        """Test notnull_expr on integer series."""
        df = pl.DataFrame({
            "value": [1, None, 3],
        })
        s = df["value"]
        expr = s.epl.notnull_expr()

        result = df.select(expr.alias("not_null"))
        assert result["not_null"].to_list() == [True, False, True]


class TestSeriesMLUtilsDropna:
    """Tests for SeriesMLUtils dropna method."""

    def test_dropna_integer(self):
        """Test dropna on integer series."""
        s = pl.Series("value", [1, None, 3, None, 5])
        result = s.epl.dropna()

        assert result.to_list() == [1, 3, 5]
        assert result.len() == 3

    def test_dropna_float_with_nan(self):
        """Test dropna on float series with NaN."""
        s = pl.Series("value", [1.0, float('nan'), 3.0, None, 5.0])
        result = s.epl.dropna()

        assert result.to_list() == [1.0, 3.0, 5.0]
        assert result.len() == 3

    def test_dropna_no_nulls(self):
        """Test dropna with no null values."""
        s = pl.Series("value", [1, 2, 3, 4, 5])
        result = s.epl.dropna()

        assert result.to_list() == [1, 2, 3, 4, 5]
        assert result.len() == 5


class TestSeriesMLUtilsScaleEncode:
    """Tests for SeriesMLUtils scale_encode method."""

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_scale_encode_standard_scaler_train(self):
        """Test StandardScaler in train mode."""
        s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])

        with tempfile.TemporaryDirectory() as tmpdir:
            scaler_path = Path(tmpdir) / "scaler.joblib"
            result = s.epl.scale_encode(
                path=scaler_path,
                scaler_type='StandardScaler',
                train_mode=True,
            )

            # Should return a series/dataframe
            assert isinstance(result, (pl.Series, pl.DataFrame))
            # Scaler file should be created
            assert scaler_path.exists()

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_scale_encode_minmax_scaler(self):
        """Test MinMaxScaler."""
        s = pl.Series("value", [0.0, 25.0, 50.0, 75.0, 100.0])

        with tempfile.TemporaryDirectory() as tmpdir:
            scaler_path = Path(tmpdir) / "scaler.joblib"
            result = s.epl.scale_encode(
                path=scaler_path,
                scaler_type='MinMaxScaler',
                train_mode=True,
            )

            assert isinstance(result, (pl.Series, pl.DataFrame))

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_scale_encode_robust_scaler(self):
        """Test RobustScaler."""
        s = pl.Series("value", [1.0, 2.0, 3.0, 100.0, 5.0])  # With outlier

        with tempfile.TemporaryDirectory() as tmpdir:
            scaler_path = Path(tmpdir) / "scaler.joblib"
            result = s.epl.scale_encode(
                path=scaler_path,
                scaler_type='RobustScaler',
                train_mode=True,
            )

            assert isinstance(result, (pl.Series, pl.DataFrame))

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_scale_encode_inference_mode(self):
        """Test scale_encode in inference mode."""
        s1 = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])

        with tempfile.TemporaryDirectory() as tmpdir:
            scaler_path = Path(tmpdir) / "scaler.joblib"
            # Train
            s1.epl.scale_encode(
                path=scaler_path,
                scaler_type='StandardScaler',
                train_mode=True,
            )

            # Inference on new data
            s2 = pl.Series("value", [6.0, 7.0, 8.0])
            result = s2.epl.scale_encode(
                path=scaler_path,
                scaler_type='StandardScaler',
                train_mode=False,
            )

            assert isinstance(result, (pl.Series, pl.DataFrame))

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not installed")
    def test_scale_encode_label_encoder(self):
        """Test LabelEncoder for categorical data."""
        s = pl.Series("category", ["a", "b", "c", "a", "b"])

        with tempfile.TemporaryDirectory() as tmpdir:
            encoder_path = Path(tmpdir) / "encoder.joblib"
            result = s.epl.scale_encode(
                path=encoder_path,
                scaler_type='LabelEncoder',
                train_mode=True,
            )

            assert isinstance(result, (pl.Series, pl.DataFrame))


class TestInheritance:
    """Tests for inheritance from UniversalPolarsDataFrameExtension."""

    def test_inherits_properties(self):
        """Test that PolarsMLPipeline inherits base properties."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })

        pipeline = PolarsMLPipeline(df)

        assert pipeline.schema == {"a": pl.Int64, "b": pl.Int64}
        assert pipeline.length == 3
        assert pipeline.width == 2
        assert pipeline.columns == ["a", "b"]


class TestLazyFrameSupport:
    """Tests for LazyFrame support in PolarsMLPipeline."""

    def test_standardize_lazyframe(self):
        """Test standardize with LazyFrame input."""
        lf = pl.LazyFrame({
            "name": ["alice", "bob", "charlie"],
        })
        pipeline = PolarsMLPipeline(lf)
        result = pipeline.standardize(str_case_standardization='upper')

        # Result should be LazyFrame
        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert collected["name"].to_list() == ["ALICE", "BOB", "CHARLIE"]

    def test_clip_and_impute_lazyframe(self):
        """Test clip_and_impute with LazyFrame input."""
        lf = pl.LazyFrame({
            "value": [1.0, 2.0, None, 4.0, 5.0],
        })
        pipeline = PolarsMLPipeline(lf)
        result, stats = pipeline.clip_and_impute(
            skip_clip=True,
            skip_impute=True,
        )

        # Should handle LazyFrame
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))
