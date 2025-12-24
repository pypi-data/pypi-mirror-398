"""
Comprehensive test suite for Stats module (descriptive_stats.py, hypothesis_tests.py, random_sampling.py).

Tests cover:
- StatsConfig configuration
- Descriptive statistics generation
- Smart stats with type-aware analysis
- Random sampling functions
- Hypothesis testing methods
"""

import sys
from pathlib import Path
import pytest
import polars as pl
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhancedpolars.Stats.descriptive_stats import (
    StatsConfig,
    generate_comprehensive_stats,
    quick_stats,
    full_stats,
    get_column_appropriate_stats,
    generate_smart_stats,
    generate_autocorrelation_stats,
    generate_correlation_stats,
    generate_window_stats,
    safe_combine_expressions,
)
from enhancedpolars.Stats.random_sampling import (
    get_random_normal_exp,
    get_random_uniform_exp,
    get_random_choice_exp,
    get_random_truncated_normal_exp,
    SCIPY_AVAILABLE as SCIPY_AVAILABLE_SAMPLING,
)

# Conditionally import scipy-dependent function
if SCIPY_AVAILABLE_SAMPLING:
    from enhancedpolars.Stats.random_sampling import get_samples_from_truncated_gaussian_interval

# Check for scipy availability for hypothesis tests
try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ============================================================================
# StatsConfig Tests
# ============================================================================

class TestStatsConfig:
    """Tests for StatsConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = StatsConfig()

        assert config.include_length is True
        assert config.include_count is True
        assert config.include_mean is True
        assert config.include_std is True
        assert config.include_min is True
        assert config.include_max is True
        assert config.include_median is True
        assert config.include_mad is True
        assert config.include_n_unique is True
        # Default quantiles
        assert 0.25 in config.quantiles
        assert 0.50 in config.quantiles
        assert 0.75 in config.quantiles

    def test_custom_quantiles(self):
        """Test custom quantile configuration."""
        config = StatsConfig(quantiles=[0.1, 0.5, 0.9])

        assert config.quantiles == [0.1, 0.5, 0.9]

    def test_disabled_stats(self):
        """Test disabling specific statistics."""
        config = StatsConfig(
            include_mean=False,
            include_std=False,
            include_variance=False
        )

        assert config.include_mean is False
        assert config.include_std is False
        assert config.include_variance is False

    def test_advanced_stats_config(self):
        """Test advanced statistics configuration."""
        config = StatsConfig(
            include_variance=True,
            include_skewness=True,
            include_kurtosis=True,
            include_sum=True,
            include_range=True,
            include_iqr=True
        )

        assert config.include_variance is True
        assert config.include_skewness is True
        assert config.include_kurtosis is True
        assert config.include_sum is True
        assert config.include_range is True
        assert config.include_iqr is True

    def test_null_handling_config(self):
        """Test null handling configuration."""
        config = StatsConfig(
            include_null_count=True,
            include_null_percentage=True
        )

        assert config.include_null_count is True
        assert config.include_null_percentage is True

    def test_prefix_suffix_config(self):
        """Test prefix and suffix configuration."""
        config = StatsConfig(prefix="stat_", suffix="_metric")

        assert config.prefix == "stat_"
        assert config.suffix == "_metric"

    def test_autocorrelation_config(self):
        """Test autocorrelation configuration."""
        config = StatsConfig(
            include_autocorrelation=True,
            autocorr_lags=[1, 2, 5, 10]
        )

        assert config.include_autocorrelation is True
        assert config.autocorr_lags == [1, 2, 5, 10]


# ============================================================================
# Descriptive Stats Tests
# ============================================================================

class TestGenerateComprehensiveStats:
    """Tests for generate_comprehensive_stats function."""

    @pytest.fixture
    def numeric_df(self):
        """Create sample DataFrame with numeric data."""
        return pl.DataFrame({
            "int_col": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "float_col": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.0],
        })

    def test_basic_stats_single_column(self, numeric_df):
        """Test basic statistics generation for single column."""
        exprs = generate_comprehensive_stats("int_col")

        assert len(exprs) > 0
        assert all(isinstance(e, pl.Expr) for e in exprs)

        # Apply expressions in a select
        result = numeric_df.select(exprs)
        assert result.shape[0] == 1

    def test_basic_stats_multiple_columns(self, numeric_df):
        """Test statistics generation for multiple columns."""
        exprs = generate_comprehensive_stats(["int_col", "float_col"])

        assert len(exprs) > 0

        result = numeric_df.select(exprs)
        assert result.shape[0] == 1
        # Should have stats for both columns
        assert any("int_col" in c for c in result.columns)
        assert any("float_col" in c for c in result.columns)

    def test_stats_with_config(self, numeric_df):
        """Test statistics with custom configuration."""
        config = StatsConfig(
            quantiles=[0.25, 0.75],
            include_mean=True,
            include_std=False
        )
        exprs = generate_comprehensive_stats("int_col", config)

        result = numeric_df.select(exprs)

        # Should have mean but not std
        col_names = result.columns
        assert any("mean" in c for c in col_names)
        assert not any("std" in c for c in col_names)

    def test_stats_with_nulls(self):
        """Test statistics with null values."""
        df = pl.DataFrame({
            "value": [1.0, None, 3.0, None, 5.0]
        })
        config = StatsConfig(include_null_count=True, include_null_percentage=True)
        exprs = generate_comprehensive_stats("value", config)

        result = df.select(exprs)

        # Should have null count
        null_cols = [c for c in result.columns if "null" in c.lower()]
        assert len(null_cols) > 0

    def test_stats_with_prefix_suffix(self, numeric_df):
        """Test statistics with custom prefix and suffix."""
        config = StatsConfig(prefix="pre_", suffix="_suf")
        exprs = generate_comprehensive_stats("int_col", config)

        result = numeric_df.select(exprs)

        # All columns should have prefix and suffix
        for col in result.columns:
            assert col.startswith("pre_")
            assert col.endswith("_suf")

    def test_stats_with_custom_expressions(self, numeric_df):
        """Test statistics with custom expressions."""
        custom_exprs = {
            "int_col_squared_mean": pl.col("int_col").pow(2).mean(),
        }
        exprs = generate_comprehensive_stats("int_col", custom_expressions=custom_exprs)

        result = numeric_df.select(exprs)

        assert "int_col_squared_mean" in result.columns

    def test_stats_in_groupby(self, numeric_df):
        """Test statistics expressions in group_by context."""
        df = pl.DataFrame({
            "group": ["A", "A", "B", "B", "A"],
            "value": [1, 2, 3, 4, 5]
        })

        exprs = generate_comprehensive_stats("value")
        result = df.group_by("group").agg(exprs)

        assert result.shape[0] == 2  # Two groups


class TestQuickStats:
    """Tests for quick_stats function."""

    def test_quick_stats_basic(self):
        """Test quick statistics."""
        df = pl.DataFrame({
            "value": [1, 2, 3, 4, 5]
        })

        exprs = quick_stats("value")
        result = df.select(exprs)

        assert result.shape[0] == 1
        # Quick stats should have basic stats
        col_names = result.columns
        assert any("mean" in c for c in col_names)

    def test_quick_stats_multiple_columns(self):
        """Test quick statistics for multiple columns."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6]
        })

        exprs = quick_stats(["a", "b"])
        result = df.select(exprs)

        assert any("a_" in c for c in result.columns)
        assert any("b_" in c for c in result.columns)


class TestFullStats:
    """Tests for full_stats function."""

    def test_full_stats_basic(self):
        """Test full statistics."""
        df = pl.DataFrame({
            "value": [1.0, 2.0, 3.0, 4.0, 5.0]
        })

        exprs = full_stats("value")
        result = df.select(exprs)

        # Full stats should have more columns than quick stats
        assert result.shape[0] == 1
        # Should include advanced stats
        col_names = result.columns
        assert any("skewness" in c for c in col_names) or any("variance" in c for c in col_names)


class TestGetColumnAppropriateStats:
    """Tests for get_column_appropriate_stats function."""

    def test_numeric_column_stats(self):
        """Test appropriate stats for numeric column."""
        df = pl.DataFrame({"value": [1, 2, 3]})

        result = get_column_appropriate_stats(df, ["value"])

        assert isinstance(result, dict)
        assert "value" in result
        assert isinstance(result["value"], list)
        assert all(isinstance(e, pl.Expr) for e in result["value"])

    def test_string_column_stats(self):
        """Test appropriate stats for string column."""
        df = pl.DataFrame({"value": ["a", "b", "c"]})

        result = get_column_appropriate_stats(df, ["value"])

        assert isinstance(result, dict)
        assert "value" in result

    def test_datetime_column_stats(self):
        """Test appropriate stats for datetime column."""
        df = pl.DataFrame({
            "value": pl.Series([
                "2024-01-01", "2024-01-02", "2024-01-03"
            ]).str.to_datetime()
        })

        result = get_column_appropriate_stats(df, ["value"])

        assert isinstance(result, dict)
        assert "value" in result

    def test_boolean_column_stats(self):
        """Test appropriate stats for boolean column."""
        df = pl.DataFrame({"value": [True, False, True, True]})

        result = get_column_appropriate_stats(df)

        assert isinstance(result, dict)
        assert "value" in result

    def test_all_columns_default(self):
        """Test getting stats for all columns when columns=None."""
        df = pl.DataFrame({
            "num": [1, 2, 3],
            "str": ["a", "b", "c"]
        })

        result = get_column_appropriate_stats(df)

        assert "num" in result
        assert "str" in result

    def test_with_prefix(self):
        """Test with custom prefix."""
        df = pl.DataFrame({"value": [1, 2, 3]})

        result = get_column_appropriate_stats(df, prefix="test_")

        # Expressions should use prefix
        assert "value" in result


class TestGenerateSmartStats:
    """Tests for generate_smart_stats function."""

    def test_smart_stats_basic(self):
        """Test smart statistics on mixed DataFrame."""
        df = pl.DataFrame({
            "numeric": [1, 2, 3, 4, 5],
            "string": ["a", "b", "c", "d", "e"],
        })

        result = generate_smart_stats(df)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] > 0

    def test_smart_stats_with_groupby(self):
        """Test smart statistics with grouping."""
        df = pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1, 2, 3, 4],
        })

        result = generate_smart_stats(df, group_by="group")

        assert isinstance(result, pl.DataFrame)

    def test_smart_stats_specific_columns(self):
        """Test smart statistics for specific columns."""
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "c": ["x", "y", "z"]
        })

        result = generate_smart_stats(df, columns=["a", "b"])

        assert isinstance(result, pl.DataFrame)

    def test_smart_stats_return_type_dict(self):
        """Test smart statistics returning dictionary."""
        df = pl.DataFrame({
            "value": [1, 2, 3, 4, 5]
        })

        result = generate_smart_stats(df, return_type="dictionary")

        assert isinstance(result, dict)

    def test_smart_stats_no_stack(self):
        """Test smart statistics without stacking results."""
        df = pl.DataFrame({
            "value": [1, 2, 3]
        })

        result = generate_smart_stats(df, stack_results=False)

        assert isinstance(result, pl.DataFrame)

    def test_smart_stats_lazyframe(self):
        """Test smart statistics with LazyFrame."""
        lf = pl.DataFrame({
            "value": [1, 2, 3, 4, 5]
        }).lazy()

        result = generate_smart_stats(lf)

        assert isinstance(result, pl.DataFrame)


class TestGenerateAutocorrelationStats:
    """Tests for generate_autocorrelation_stats function."""

    def test_autocorr_basic(self):
        """Test basic autocorrelation statistics."""
        exprs = generate_autocorrelation_stats("value", lags=[1, 2, 3])

        assert len(exprs) == 3
        assert all(isinstance(e, pl.Expr) for e in exprs)

    def test_autocorr_with_prefix(self):
        """Test autocorrelation with custom prefix."""
        exprs = generate_autocorrelation_stats("value", lags=[1], prefix="ac_")

        assert len(exprs) == 1

    def test_autocorr_lag_zero(self):
        """Test autocorrelation at lag 0."""
        exprs = generate_autocorrelation_stats("value", lags=[0, 1])

        # Lag 0 should be included (always 1.0)
        assert len(exprs) == 2


class TestGenerateCorrelationStats:
    """Tests for generate_correlation_stats function."""

    def test_correlation_basic(self):
        """Test basic correlation statistics."""
        exprs = generate_correlation_stats(["a", "b", "c"])

        # Should have 3 pairs: (a,b), (a,c), (b,c)
        assert len(exprs) == 3

    def test_correlation_two_columns(self):
        """Test correlation for two columns."""
        exprs = generate_correlation_stats(["x", "y"])

        assert len(exprs) == 1

    def test_correlation_with_prefix(self):
        """Test correlation with custom prefix."""
        exprs = generate_correlation_stats(["a", "b"], prefix="corr_")

        assert len(exprs) == 1


class TestGenerateWindowStats:
    """Tests for generate_window_stats function."""

    def test_window_stats_basic(self):
        """Test basic rolling window statistics."""
        exprs = generate_window_stats("value", window_size=3)

        assert len(exprs) > 0
        assert all(isinstance(e, pl.Expr) for e in exprs)

    def test_window_stats_with_config(self):
        """Test rolling window with custom config."""
        config = StatsConfig(
            include_mean=True,
            include_std=True,
            include_median=False,
            quantiles=[]
        )
        exprs = generate_window_stats("value", window_size=5, config=config)

        assert len(exprs) > 0

    def test_window_stats_applied(self):
        """Test applying window stats to DataFrame."""
        df = pl.DataFrame({
            "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        })

        exprs = generate_window_stats("value", window_size=3)
        result = df.with_columns(exprs)

        assert result.shape[0] == 10


class TestSafeCombineExpressions:
    """Tests for safe_combine_expressions function."""

    def test_combine_basic(self):
        """Test basic expression combination."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        expr_groups = [
            [pl.col("a").mean().alias("a_mean")],
            [pl.col("b").sum().alias("b_sum")]
        ]

        result = safe_combine_expressions(df, expr_groups)

        assert "a_mean" in result.columns
        assert "b_sum" in result.columns

    def test_combine_with_lazyframe(self):
        """Test expression combination with LazyFrame."""
        lf = pl.DataFrame({"a": [1, 2, 3]}).lazy()

        expr_groups = [[pl.col("a").mean().alias("a_mean")]]

        result = safe_combine_expressions(lf, expr_groups)

        # Should return LazyFrame
        assert isinstance(result, pl.LazyFrame)


# ============================================================================
# Random Sampling Tests
# ============================================================================

@pytest.mark.skipif(not SCIPY_AVAILABLE_SAMPLING, reason="scipy not installed")
class TestTruncatedGaussianSampling:
    """Tests for truncated Gaussian sampling."""

    def test_basic_sampling(self):
        """Test basic truncated Gaussian sampling."""
        samples = get_samples_from_truncated_gaussian_interval(
            mean=0.0,
            std=1.0,
            lower_z_score=-2.0,
            upper_z_score=2.0,
            n_samples=100,
            random_state=42
        )

        assert len(samples) == 100
        # All samples should be within z-score bounds * std + mean
        lower = -2.0 * 1.0 + 0.0
        upper = 2.0 * 1.0 + 0.0
        assert all(lower <= s <= upper for s in samples)

    def test_sampling_with_different_mean(self):
        """Test sampling with different mean."""
        samples = get_samples_from_truncated_gaussian_interval(
            mean=5.0,
            std=1.0,
            lower_z_score=-1.0,
            upper_z_score=1.0,
            n_samples=100,
            random_state=42
        )

        # Bounds are z_low * std + mean to z_high * std + mean
        lower = -1.0 * 1.0 + 5.0  # 4.0
        upper = 1.0 * 1.0 + 5.0   # 6.0

        assert all(lower <= s <= upper for s in samples)


class TestRandomNormalExp:
    """Tests for random normal expression generation."""

    def test_basic_normal(self):
        """Test basic normal distribution sampling."""
        rng = np.random.default_rng(42)
        series = get_random_normal_exp(
            n_ext=100,
            mu=0.0,
            sigma=1.0,
            rng=rng
        )

        assert isinstance(series, pl.Series)
        assert len(series) == 100
        assert series.dtype == pl.Float64

    def test_normal_mean_std(self):
        """Test that samples have approximately correct mean and std."""
        rng = np.random.default_rng(42)
        series = get_random_normal_exp(
            n_ext=10000,
            mu=5.0,
            sigma=2.0,
            rng=rng
        )

        # With large sample, mean and std should be close
        assert abs(series.mean() - 5.0) < 0.5
        assert abs(series.std() - 2.0) < 0.5

    def test_normal_reproducibility(self):
        """Test reproducibility with same random generator state."""
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)

        series1 = get_random_normal_exp(10, 0.0, 1.0, rng1)
        series2 = get_random_normal_exp(10, 0.0, 1.0, rng2)

        assert series1.to_list() == series2.to_list()


class TestRandomUniformExp:
    """Tests for random uniform expression generation."""

    def test_basic_uniform(self):
        """Test basic uniform distribution sampling."""
        rng = np.random.default_rng(42)
        series = get_random_uniform_exp(
            n_ext=100,
            low=0.0,
            high=1.0,
            rng=rng
        )

        assert isinstance(series, pl.Series)
        assert len(series) == 100
        assert series.min() >= 0.0
        assert series.max() <= 1.0

    def test_uniform_bounds(self):
        """Test uniform distribution bounds."""
        rng = np.random.default_rng(42)
        series = get_random_uniform_exp(
            n_ext=1000,
            low=10.0,
            high=20.0,
            rng=rng
        )

        assert series.min() >= 10.0
        assert series.max() <= 20.0


class TestRandomChoiceExp:
    """Tests for random choice expression generation."""

    def test_basic_choice(self):
        """Test basic random choice."""
        rng = np.random.default_rng(42)
        series = get_random_choice_exp(
            n_ext=100,
            options=["A", "B", "C"],
            rng=rng,
            return_dtype=pl.Utf8
        )

        assert isinstance(series, pl.Series)
        assert len(series) == 100
        # All values should be from choices
        unique_vals = set(series.to_list())
        assert unique_vals.issubset({"A", "B", "C"})

    def test_choice_with_probabilities(self):
        """Test random choice with probabilities."""
        rng = np.random.default_rng(42)
        series = get_random_choice_exp(
            n_ext=10000,
            options=["A", "B"],
            rng=rng,
            return_dtype=pl.Utf8,
            p=[0.9, 0.1]
        )

        counts = series.value_counts()
        a_count = counts.filter(pl.col("") == "A")["count"][0]

        # A should be significantly more common
        assert a_count > 8000

    def test_choice_integer_options(self):
        """Test random choice with integer options."""
        rng = np.random.default_rng(42)
        series = get_random_choice_exp(
            n_ext=50,
            options=[1, 2, 3],
            rng=rng,
            return_dtype=pl.Int64
        )

        assert series.dtype == pl.Int64
        assert set(series.to_list()).issubset({1, 2, 3})


@pytest.mark.skipif(not SCIPY_AVAILABLE_SAMPLING, reason="scipy not installed")
class TestRandomTruncatedNormalExp:
    """Tests for truncated normal expression generation."""

    def test_basic_truncated_normal(self):
        """Test basic truncated normal sampling."""
        series = get_random_truncated_normal_exp(
            n_ext=100,
            mu=0.0,
            sigma=1.0,
            lower_z=-2.0,
            upper_z=2.0,
            random_seed=42
        )

        assert isinstance(series, pl.Series)
        assert len(series) == 100
        assert series.dtype == pl.Float64

    def test_truncated_bounds(self):
        """Test truncated normal respects bounds."""
        series = get_random_truncated_normal_exp(
            n_ext=1000,
            mu=5.0,
            sigma=1.0,
            lower_z=-1.0,
            upper_z=1.0,
            random_seed=42
        )

        # Bounds should be respected
        assert series.min() >= 4.0  # mu - 1*sigma
        assert series.max() <= 6.0  # mu + 1*sigma


# ============================================================================
# Hypothesis Tests - TestResult Tests
# ============================================================================

@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_basic_result(self):
        """Test basic TestResult creation."""
        from enhancedpolars.Stats.hypothesis_tests import TestResult

        result = TestResult(
            test_name="t-test",
            statistic=2.5,
            p_value=0.05,
            degrees_of_freedom=10
        )

        assert result.test_name == "t-test"
        assert result.statistic == 2.5
        assert result.p_value == 0.05
        assert result.degrees_of_freedom == 10

    def test_to_dict(self):
        """Test TestResult to_dict conversion."""
        from enhancedpolars.Stats.hypothesis_tests import TestResult

        result = TestResult(
            test_name="t-test",
            statistic=2.5,
            p_value=0.05
        )

        d = result.to_dict()

        assert isinstance(d, dict)
        assert d["test"] == "t-test"
        assert d["statistic"] == 2.5
        assert d["p_value"] == 0.05

    def test_repr(self):
        """Test TestResult string representation."""
        from enhancedpolars.Stats.hypothesis_tests import TestResult

        result = TestResult(
            test_name="t-test",
            statistic=2.5,
            p_value=0.05
        )

        repr_str = repr(result)

        assert "t-test" in repr_str

    def test_result_with_correction(self):
        """Test TestResult with p-value correction."""
        from enhancedpolars.Stats.hypothesis_tests import TestResult

        result = TestResult(
            test_name="t-test",
            statistic=2.5,
            p_value=0.05,
            p_value_corrected=0.10,
            correction_method="bonferroni"
        )

        assert result.p_value_corrected == 0.10
        assert result.correction_method == "bonferroni"

    def test_result_with_additional_info(self):
        """Test TestResult with additional info."""
        from enhancedpolars.Stats.hypothesis_tests import TestResult

        result = TestResult(
            test_name="t-test",
            statistic=2.5,
            p_value=0.05,
            additional_info={"effect_size": 0.8, "n_samples": 100}
        )

        assert result.additional_info["effect_size"] == 0.8
        assert result.additional_info["n_samples"] == 100


# ============================================================================
# PolarsStatsTests Tests
# ============================================================================

@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestPolarsStatsTestsInit:
    """Tests for PolarsStatsTests initialization."""

    def test_init_dataframe(self):
        """Test initialization with DataFrame."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        df = pl.DataFrame({"a": [1, 2, 3]})
        stats = PolarsStatsTests(df)

        assert stats._df is not None

    def test_init_lazyframe(self):
        """Test initialization with LazyFrame."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        lf = pl.DataFrame({"a": [1, 2, 3]}).lazy()
        stats = PolarsStatsTests(lf)

        assert stats._df is not None


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestTTest:
    """Tests for t_test method."""

    @pytest.fixture
    def two_group_df(self):
        """Create DataFrame with two groups for t-test."""
        np.random.seed(42)
        return pl.DataFrame({
            "group": ["A"] * 50 + ["B"] * 50,
            "value": list(np.random.normal(10, 2, 50)) + list(np.random.normal(12, 2, 50))
        })

    def test_independent_t_test_wide_format(self):
        """Test independent samples t-test in wide format."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        df = pl.DataFrame({
            "group_a": list(np.random.normal(10, 2, 50)),
            "group_b": list(np.random.normal(12, 2, 50))
        })
        stats = PolarsStatsTests(df)

        result = stats.t_test(
            comparisons=[("group_a", "group_b")]
        )

        assert isinstance(result, list)
        assert len(result) > 0

    def test_independent_t_test_long_format(self, two_group_df):
        """Test independent samples t-test in long format."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        stats = PolarsStatsTests(two_group_df)

        result = stats.t_test(
            comparisons=[("A", "B")],
            value_col="value",
            group_col="group"
        )

        assert isinstance(result, list)
        assert len(result) > 0

    def test_one_sample_t_test(self):
        """Test one-sample t-test."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        df = pl.DataFrame({
            "value": [10.1, 9.8, 10.2, 9.9, 10.0, 10.3, 9.7]
        })
        stats = PolarsStatsTests(df)

        result = stats.t_test(
            comparisons=[("value", "value")],  # For one-sample, use same column
            test_type="one-sample",
            popmean=10.0
        )

        assert isinstance(result, list)


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestChiSquareTest:
    """Tests for chi2_test method."""

    @pytest.fixture
    def categorical_df(self):
        """Create DataFrame with categorical data."""
        return pl.DataFrame({
            "category1": ["A", "A", "B", "B", "A", "B", "A", "B"] * 10,
            "category2": ["X", "Y", "X", "Y", "Y", "X", "X", "Y"] * 10
        })

    def test_chi2_wide_format(self):
        """Test chi-square test in wide format."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        df = pl.DataFrame({
            "cat_a": ["X", "X", "Y", "Y", "X"] * 10,
            "cat_b": ["X", "Y", "Y", "X", "Y"] * 10
        })
        stats = PolarsStatsTests(df)

        result = stats.chi2_test(
            comparisons=[("cat_a", "cat_b")]
        )

        assert isinstance(result, list)


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestANOVA:
    """Tests for ANOVA method."""

    @pytest.fixture
    def multi_group_df(self):
        """Create DataFrame with multiple groups."""
        np.random.seed(42)
        return pl.DataFrame({
            "group": ["A"] * 30 + ["B"] * 30 + ["C"] * 30,
            "value": (
                list(np.random.normal(10, 2, 30)) +
                list(np.random.normal(12, 2, 30)) +
                list(np.random.normal(11, 2, 30))
            )
        })

    def test_anova_wide_format(self):
        """Test one-way ANOVA in wide format."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        np.random.seed(42)
        df = pl.DataFrame({
            "group_a": list(np.random.normal(10, 2, 30)),
            "group_b": list(np.random.normal(12, 2, 30)),
            "group_c": list(np.random.normal(11, 2, 30))
        })
        stats = PolarsStatsTests(df)

        result = stats.anova(groups=["group_a", "group_b", "group_c"])

        assert result is not None

    def test_anova_long_format(self, multi_group_df):
        """Test one-way ANOVA in long format."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        stats = PolarsStatsTests(multi_group_df)

        result = stats.anova(
            groups=["A", "B", "C"],
            value_col="value",
            group_col="group"
        )

        assert result is not None


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestNormalityTests:
    """Tests for normality testing methods."""

    @pytest.fixture
    def normal_data(self):
        """Create normally distributed data."""
        np.random.seed(42)
        return pl.DataFrame({
            "value": np.random.normal(0, 1, 100).tolist()
        })

    @pytest.fixture
    def non_normal_data(self):
        """Create non-normally distributed data."""
        np.random.seed(42)
        return pl.DataFrame({
            "value": np.random.exponential(1, 100).tolist()
        })

    def test_shapiro_wilk(self, normal_data):
        """Test Shapiro-Wilk normality test."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        stats = PolarsStatsTests(normal_data)

        result = stats.shapiro_wilk(columns=["value"])

        assert isinstance(result, list)
        assert len(result) > 0

    def test_anderson_darling(self, normal_data):
        """Test Anderson-Darling test."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        stats = PolarsStatsTests(normal_data)

        result = stats.anderson_darling(columns=["value"])

        assert isinstance(result, list)


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestKruskalWallis:
    """Tests for Kruskal-Wallis test."""

    def test_kruskal_wallis_wide_format(self):
        """Test Kruskal-Wallis test in wide format."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        np.random.seed(42)
        df = pl.DataFrame({
            "group_a": list(np.random.uniform(1, 5, 20)),
            "group_b": list(np.random.uniform(3, 7, 20)),
            "group_c": list(np.random.uniform(2, 6, 20))
        })
        stats = PolarsStatsTests(df)

        result = stats.kruskal_wallis(groups=["group_a", "group_b", "group_c"])

        assert result is not None

    def test_kruskal_wallis_long_format(self):
        """Test Kruskal-Wallis test in long format."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        np.random.seed(42)
        df = pl.DataFrame({
            "group": ["A"] * 20 + ["B"] * 20 + ["C"] * 20,
            "value": (
                list(np.random.uniform(1, 5, 20)) +
                list(np.random.uniform(3, 7, 20)) +
                list(np.random.uniform(2, 6, 20))
            )
        })
        stats = PolarsStatsTests(df)

        result = stats.kruskal_wallis(
            groups=["A", "B", "C"],
            value_col="value",
            group_col="group"
        )

        assert result is not None


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not installed")
class TestAutoTest:
    """Tests for auto_test method."""

    def test_auto_test_numeric_two_groups(self):
        """Test auto_test with numeric data and two groups."""
        from enhancedpolars.Stats.hypothesis_tests import PolarsStatsTests

        np.random.seed(42)
        df = pl.DataFrame({
            "group": ["A"] * 30 + ["B"] * 30,
            "value": list(np.random.normal(10, 2, 30)) + list(np.random.normal(12, 2, 30))
        })
        stats = PolarsStatsTests(df)

        result = stats.auto_test(
            groups=["A", "B"],
            value_col="value",
            group_col="group"
        )

        # auto_test should return results
        assert result is not None


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dataframe_stats(self):
        """Test statistics on empty DataFrame."""
        df = pl.DataFrame({"value": []}).cast({"value": pl.Float64})

        # Should not raise, but may have null results
        exprs = quick_stats("value")
        result = df.select(exprs)

        assert result.shape[0] == 1

    def test_all_null_column(self):
        """Test statistics on all-null column."""
        df = pl.DataFrame({
            "value": [None, None, None]
        }).cast({"value": pl.Float64})

        config = StatsConfig()
        exprs = generate_comprehensive_stats("value", config)
        result = df.select(exprs)

        # Should handle gracefully
        assert result.shape[0] == 1

    def test_single_value(self):
        """Test statistics on single value."""
        df = pl.DataFrame({"value": [42.0]})

        exprs = quick_stats("value")
        result = df.select(exprs)

        assert result.shape[0] == 1

    def test_large_quantile_list(self):
        """Test with many quantiles."""
        config = StatsConfig(
            quantiles=[i/100 for i in range(1, 100)]  # 99 quantiles
        )
        exprs = generate_comprehensive_stats("value", config)

        assert len(exprs) > 99  # At least 99 quantile expressions

    def test_mixed_types_smart_stats(self):
        """Test smart stats with mixed data types."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True]
        })

        result = generate_smart_stats(df)

        assert isinstance(result, pl.DataFrame)

    def test_random_sampling_invalid_n(self):
        """Test random sampling with invalid n parameter."""
        rng = np.random.default_rng(42)

        # Should raise for non-integer n_ext when using expressions
        with pytest.raises((ValueError, TypeError)):
            get_random_normal_exp(
                n_ext=pl.lit(10),  # Expression instead of int
                mu=0.0,
                sigma=1.0,
                rng=rng
            )
