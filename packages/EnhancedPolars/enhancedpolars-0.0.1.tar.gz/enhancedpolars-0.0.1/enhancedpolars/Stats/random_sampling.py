"""
Polars Random Sampling Utilities

This module provides utilities for generating random samples compatible with Polars,
including normal, uniform, choice, and truncated normal distributions.
"""

import polars as pl
import numpy as np
from typing import Optional, List

try:
    from scipy.stats import truncnorm
    SCIPY_AVAILABLE = True
except ImportError:
    truncnorm = None
    SCIPY_AVAILABLE = False


def get_samples_from_truncated_gaussian_interval(
    mean: float | int,
    std: float | int,
    lower_z_score: float | int,
    upper_z_score: float | int,
    n_samples: int = 1,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Generate random samples from a truncated normal distribution.

    This function samples from a normal distribution with specified mean and standard deviation,
    truncated at the given z-score boundaries.

    Parameters
    ----------
    mean : float or int
        The mean of the underlying normal distribution.
    std : float or int
        The standard deviation of the underlying normal distribution.
    lower_z_score : float or int
        The lower boundary as a z-score (number of standard deviations from the mean).
    upper_z_score : float or int
        The upper boundary as a z-score (number of standard deviations from the mean).
    n_samples : int, optional
        The number of samples to generate, by default 1.
    random_state : int, optional
        Random seed for reproducible results, by default None.

    Returns
    -------
    np.ndarray
        Array of random samples from the truncated normal distribution.

    Raises
    ------
    AssertionError
        If scipy.stats is not available.

    Examples
    --------
    >>> # Generate 5 samples from a normal distribution with mean=10, std=2,
    >>> # truncated between -1 and 1 standard deviations
    >>> samples = get_samples_from_truncated_gaussian_interval(10, 2, -1, 1, 5, 42)
    >>> print(samples)
    [8.2 9.5 10.8 11.2 9.1]

    Notes
    -----
    The truncation boundaries are specified in terms of z-scores, which are the number
    of standard deviations from the mean. For example, a z-score of -1 corresponds to
    one standard deviation below the mean.
    """
    assert SCIPY_AVAILABLE, "get_samples_from_truncated_gaussian_interval requires scipy.stats to be installed"
    return truncnorm(
        lower_z_score,
        ((upper_z_score + 0.00001) if lower_z_score == upper_z_score else upper_z_score),
        loc=mean,
        scale=std
    ).rvs(n_samples, random_state=random_state)  # type: ignore


def get_random_normal_exp(
    n_ext: pl.Expr | int,
    mu: float,
    sigma: float,
    rng: np.random.Generator
) -> pl.Series:
    """
    Create a Polars Series that contains random samples from a normal distribution.

    Parameters
    ----------
    n_ext : pl.Expr | int
        Number of samples to generate.
    mu : float
        Mean of the normal distribution.
    sigma : float
        Standard deviation of the normal distribution.
    rng : np.random.Generator
        Random number generator for reproducible results.

    Returns
    -------
    pl.Series
        Polars Series that contains random samples.

    Examples
    --------
    >>> # Example usage in a Polars DataFrame
    >>> import polars as pl
    >>> df = pl.DataFrame({"x": [1, 2, 3, 7, 8, 9]})
    >>> rng = np.random.default_rng(12345)
    >>> random_series = get_random_normal_exp(6, mu=0, sigma=1, rng=rng)
    >>> df.with_columns(pl.when(pl.col("x") > 6).then(random_series).otherwise(pl.col("x")).alias("result"))

    Notes
    -----
    This function generates a full-length replacement vector like the test_2.py pattern.
    """

    # Generate full-length replacement vector for the entire dataframe (like test_2.py example)
    if isinstance(n_ext, int):
        n_rows = n_ext
    else:
        raise ValueError("n_ext must be an integer for dataframe length")

    # Generate random samples using the specified distribution
    random_samples = rng.normal(mu, sigma, n_rows)

    # Return as Polars series
    return pl.Series(values=random_samples, dtype=pl.Float64)


def get_random_uniform_exp(
    n_ext: pl.Expr | int,
    low: float,
    high: float,
    rng: np.random.Generator
) -> pl.Series:
    """
    Create a Polars Series that contains random samples from a uniform distribution.

    Parameters
    ----------
    n_ext : pl.Expr | int
        Number of samples to generate.
    low : float
        Lower bound of the uniform distribution.
    high : float
        Upper bound of the uniform distribution.
    rng : np.random.Generator
        Random number generator for reproducible results.

    Returns
    -------
    pl.Series
        Polars Series that contains random samples.

    Examples
    --------
    >>> # Example usage in a Polars DataFrame
    >>> import polars as pl
    >>> df = pl.DataFrame({"x": [1, 2, 3, 7, 8, 9]})
    >>> rng = np.random.default_rng(12345)
    >>> random_series = get_random_uniform_exp(6, low=0, high=1, rng=rng)
    >>> df.with_columns(pl.when(pl.col("x") > 6).then(random_series).otherwise(pl.col("x")).alias("result"))

    Notes
    -----
    This function generates a full-length replacement vector like the test_2.py pattern.
    """

    # Generate full-length replacement vector for the entire dataframe (like test_2.py example)
    if isinstance(n_ext, int):
        n_rows = n_ext
    else:
        raise ValueError("n_ext must be an integer for dataframe length")

    # Generate random samples using the specified distribution
    random_samples = rng.uniform(low, high, n_rows)

    # Return as Polars series
    return pl.Series(values=random_samples, dtype=pl.Float64)


def get_random_choice_exp(
    n_ext: pl.Expr | int,
    options: list,
    rng: np.random.Generator,
    return_dtype: pl.DataType,
    p: Optional[List[float]] = None
) -> pl.Series:
    """
    Create a Polars Series that generates random samples from a choice distribution.

    Parameters
    ----------
    n_ext : pl.Expr | int
        Number of samples to generate.
    options : list
        List of options to choose from.
    rng : np.random.Generator
        Random number generator for reproducible results.
    return_dtype : pl.DataType
        The Polars data type for the returned series.
    p : Optional[List[float]]
        Probabilities associated with each option. If None, uniform probabilities are used.

    Returns
    -------
    pl.Series
        Polars Series that generates random samples.

    Examples
    --------
    >>> # Example usage in a Polars DataFrame
    >>> import polars as pl
    >>> df = pl.DataFrame({"x": [1, 2, 3, 7, 8, 9]})
    >>> rng = np.random.default_rng(12345)
    >>> threshold = 6
    >>> cond = pl.col("x") > threshold
    >>> n_ext = pl.len().filter(cond)
    >>> random_expr = get_random_choice_exp(6, options=[0, 1], rng=rng, return_dtype=pl.Int64)
    >>> df.with_columns(random_expr.alias("random_samples"))

    Notes
    -----
    This function uses NumPy's random number generation capabilities to create a Polars Series.
    The generated series will produce random samples from the specified choice distribution.
    """

    # Generate full-length replacement vector for the entire dataframe (like test_2.py example)
    # n_ext should be the dataframe length for when/then operations
    if isinstance(n_ext, int):
        n_rows = n_ext
    else:
        raise ValueError("n_ext must be an integer for dataframe length")

    # Generate random choices using the specified distribution
    random_choices = rng.choice(options, size=n_rows, p=p, replace=True)

    # Return as Polars series with correct dtype
    return pl.Series(values=random_choices, dtype=return_dtype)


def get_random_truncated_normal_exp(
    n_ext: pl.Expr | int,
    mu: float,
    sigma: float,
    lower_z: float,
    upper_z: float,
    random_seed: int
) -> pl.Series:
    """
    Create a Polars Series that contains random samples from a truncated normal distribution.

    Parameters
    ----------
    n_ext : pl.Expr | int
        Number of samples to generate.
    mu : float
        Mean of the normal distribution.
    sigma : float
        Standard deviation of the normal distribution.
    lower_z : float
        Lower bound in terms of z-scores.
    upper_z : float
        Upper bound in terms of z-scores.
    random_seed : int
        Random seed for reproducible results.

    Returns
    -------
    pl.Series
        Polars Series that contains random truncated normal samples.

    Examples
    --------
    >>> # Example usage in a Polars DataFrame
    >>> import polars as pl
    >>> df = pl.DataFrame({"x": [1, 2, 3, 7, 8, 9]})
    >>> random_series = get_random_truncated_normal_exp(6, mu=0, sigma=1, lower_z=-1, upper_z=1, random_seed=42)
    >>> df.with_columns(pl.when(pl.col("x") > 6).then(random_series).otherwise(pl.col("x")).alias("result"))
    """
    # Generate full-length replacement vector for the entire dataframe (like test_2.py example)
    if isinstance(n_ext, int):
        n_rows = n_ext
    else:
        raise ValueError("n_ext must be an integer for dataframe length")

    # Generate random samples using the specified distribution
    random_samples = get_samples_from_truncated_gaussian_interval(
        mean=mu,
        std=sigma,
        lower_z_score=lower_z,
        upper_z_score=upper_z,
        n_samples=n_rows,
        random_state=random_seed
    )

    # Return as Polars series
    return pl.Series(values=random_samples, dtype=pl.Float64)
