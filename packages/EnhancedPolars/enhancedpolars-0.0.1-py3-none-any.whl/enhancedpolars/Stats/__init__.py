"""
Stats Module - Comprehensive Statistical Analysis for Polars

This module provides a well-organized collection of statistical tools for Polars DataFrames:
- Descriptive statistics with intelligent type detection
- Hypothesis testing (t-tests, ANOVA, chi-square, etc.)
- Random sampling utilities

Modules:
--------
- descriptive_stats: Comprehensive descriptive statistics generation
- hypothesis_tests: Statistical hypothesis testing framework
- random_sampling: Random sampling utilities for data generation
"""

# Import from descriptive_stats
from .descriptive_stats import (
    StatsConfig,
    safe_combine_expressions,
    generate_comprehensive_stats,
    generate_autocorrelation_stats,
    generate_correlation_stats,
    generate_window_stats,
    quick_stats,
    full_stats,
    get_column_appropriate_stats,
    generate_smart_stats,
)

# Import from hypothesis_tests
from .hypothesis_tests import (
    TestResult,
    PolarsStatsTests,
)

# Import from random_sampling
from .random_sampling import (
    get_samples_from_truncated_gaussian_interval,
    get_random_normal_exp,
    get_random_uniform_exp,
    get_random_choice_exp,
    get_random_truncated_normal_exp,
)

__all__ = [
    # Descriptive stats
    "StatsConfig",
    "safe_combine_expressions",
    "generate_comprehensive_stats",
    "generate_autocorrelation_stats",
    "generate_correlation_stats",
    "generate_window_stats",
    "quick_stats",
    "full_stats",
    "get_column_appropriate_stats",
    "generate_smart_stats",
    # Hypothesis tests
    "TestResult",
    "PolarsStatsTests",
    # Random sampling
    "get_samples_from_truncated_gaussian_interval",
    "get_random_normal_exp",
    "get_random_uniform_exp",
    "get_random_choice_exp",
    "get_random_truncated_normal_exp",
]
