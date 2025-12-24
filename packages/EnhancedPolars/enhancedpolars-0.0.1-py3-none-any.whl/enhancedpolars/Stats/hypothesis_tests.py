"""
Polars Hypothesis Testing Module

This module provides comprehensive statistical hypothesis testing functionality as a
namespace extension for Polars DataFrames and LazyFrames. It supports both wide and
long format data, with flexible group comparison specifications.

Features:
- Chi-square tests for categorical data
- Fisher's exact test for 2x2 contingency tables
- T-tests (independent, paired, one-sample)
- ANOVA (F-test, Kruskal-Wallis)
- Normality tests (Shapiro-Wilk, Anderson-Darling, D'Agostino-Pearson, Kolmogorov-Smirnov)
- Post-hoc tests (Tukey HSD)
- Auto-test functionality to automatically select appropriate tests
- Manuscript table generation for publication-ready output

The module efficiently handles LazyFrames by only collecting the specific columns
needed for each test, preserving the benefits of lazy evaluation.
"""

import polars as pl
import numpy as np
from typing import Optional, List, Dict, Any, Union, Tuple, Literal, TYPE_CHECKING, cast
from dataclasses import dataclass, field
import warnings
from ..base import UniversalPolarsDataFrameExtension

if TYPE_CHECKING:
    from scipy.stats import (
        chi2_contingency, fisher_exact, kruskal, f_oneway, 
        tukey_hsd, shapiro, normaltest, anderson, kstest, 
        ttest_ind, ttest_rel, ttest_1samp
    )
    from scipy import stats

try:
    from scipy.stats import (
        chi2_contingency, fisher_exact, kruskal, f_oneway, 
        tukey_hsd, shapiro, normaltest, anderson, kstest, 
        ttest_ind, ttest_rel, ttest_1samp
    )
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy not available. Statistical tests will not work.")


@dataclass
class TestResult:
    """Container for statistical test results."""
    test_name: str
    statistic: float
    p_value: float
    degrees_of_freedom: Optional[int] = None
    comparison: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)
    p_value_corrected: Optional[float] = None
    correction_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            "test": self.test_name,
            "statistic": self.statistic,
            "p_value": self.p_value
        }
        if self.degrees_of_freedom is not None:
            result["df"] = self.degrees_of_freedom
        if self.comparison:
            result["comparison"] = self.comparison
        if self.p_value_corrected is not None:
            result["p_value_corrected"] = self.p_value_corrected
        if self.correction_method:
            result["correction_method"] = self.correction_method
        result.update(self.additional_info)
        return result
    
    def __repr__(self) -> str:
        parts = [f"{self.test_name}:"]
        if self.comparison:
            parts.append(f"comparison={self.comparison}")
        parts.append(f"statistic={self.statistic:.4f}")
        parts.append(f"p={self.p_value:.4f}")
        if self.p_value_corrected is not None:
            parts.append(f"p_corr={self.p_value_corrected:.4f}")
        if self.degrees_of_freedom is not None:
            parts.append(f"df={self.degrees_of_freedom}")
        return " ".join(parts)



class PolarsStatsTests(UniversalPolarsDataFrameExtension):
    """
    Statistical hypothesis testing namespace for Polars DataFrames and LazyFrames.
    
    This namespace provides various statistical tests for both wide and long format data.
    For group comparisons, you can specify comparisons as tuples of (reference, comparison).
    
    LazyFrame Optimization:
    - Only collects the specific columns needed for each test
    - Applies filtering before collection to minimize data transfer
    - Preserves lazy evaluation benefits wherever possible
    """
    
    def __init__(self, df: pl.DataFrame | pl.LazyFrame):
        super().__init__(df)
        
        if not SCIPY_AVAILABLE:
            raise ImportError("scipy is required for statistical tests. Install with: pip install scipy")
    
    def _apply_multiple_comparison_correction(
        self,
        results: List[TestResult],
        method: Optional[str] = None,
        alpha: float = 0.05
    ) -> List[TestResult]:
        """
        Apply multiple comparison correction to a list of test results.
        
        Parameters:
        -----------
        results : List[TestResult]
            Test results to correct
        method : str, optional
            Correction method. Options:
            - 'bonferroni': Bonferroni correction
            - 'holm': Holm-Bonferroni correction  
            - 'sidak': Sidak correction
            - 'holm-sidak': Holm-Sidak correction
            - 'simes-hochberg': Simes-Hochberg correction
            - 'hommel': Hommel correction
            - 'fdr_bh': Benjamini-Hochberg FDR correction
            - 'fdr_by': Benjamini-Yekutieli FDR correction
            - 'fdr_tsbh': Two-stage Benjamini-Hochberg FDR correction
            - 'fdr_tsbky': Two-stage Benjamini-Krieger-Yekutieli FDR correction
        alpha : float, default=0.05
            Family-wise error rate or false discovery rate
            
        Returns:
        --------
        List[TestResult]
            Results with corrected p-values
        """
        if method is None or len(results) <= 1:
            return results
        
        # Extract p-values
        p_values = np.array([result.p_value for result in results])
        
        # Apply correction
        try:
            # Try using statsmodels if available (more comprehensive)
            from statsmodels.stats.multitest import multipletests
            reject, p_corrected, _, _ = multipletests(
                p_values, alpha=alpha, method=method
            )
        except ImportError:
            # Fall back to scipy
            if hasattr(stats, 'false_discovery_control') and method.startswith('fdr_'):
                # Use scipy's new FDR function if available
                if method == 'fdr_bh':
                    reject, p_corrected = stats.false_discovery_control(p_values, method='bh')
                else:
                    # For other FDR methods, implement basic Benjamini-Hochberg
                    sorted_indices = np.argsort(p_values)
                    sorted_p = p_values[sorted_indices]
                    m = len(p_values)
                    reject = np.zeros(m, dtype=bool)
                    p_corrected = np.zeros(m)
                    
                    for i in range(m-1, -1, -1):
                        p_corrected[sorted_indices[i]] = min(1.0, sorted_p[i] * m / (i + 1))
                        if i < m - 1:
                            p_corrected[sorted_indices[i]] = min(
                                float(p_corrected[sorted_indices[i]]), 
                                float(p_corrected[sorted_indices[i+1]])
                            )
                        reject[sorted_indices[i]] = p_corrected[sorted_indices[i]] <= alpha
            else:
                # Implement basic Bonferroni correction
                if method == 'bonferroni':
                    p_corrected = np.minimum(p_values * len(p_values), 1.0)
                    reject = p_corrected <= alpha
                else:
                    raise ValueError(f"Method '{method}' not available. Install statsmodels for more options.")
        
        # Update results with corrected p-values
        corrected_results = []
        for i, result in enumerate(results):
            corrected_result = TestResult(
                test_name=result.test_name,
                statistic=result.statistic,
                p_value=result.p_value,
                degrees_of_freedom=result.degrees_of_freedom,
                comparison=result.comparison,
                additional_info=result.additional_info.copy(),
                p_value_corrected=float(p_corrected[i]),
                correction_method=method
            )
            corrected_result.additional_info['significant_corrected'] = bool(reject[i])
            corrected_results.append(corrected_result)
        
        return corrected_results
    
    def _collect_columns(self, columns: List[str]) -> pl.DataFrame:
        """
        Efficiently collect only specified columns from a LazyFrame.
        
        Parameters:
        -----------
        columns : List[str]
            Columns to collect
            
        Returns:
        --------
        pl.DataFrame
            DataFrame with only the specified columns
        """
        if self.is_lazy:
            # Select only needed columns before collecting
            return self._df.select(columns).collect()  # type: ignore
        else:
            return self._df.select(columns)  # type: ignore
    
    def _collect_filtered(
        self, 
        columns: List[str],
        filter_expr: Optional[pl.Expr] = None
    ) -> pl.DataFrame:
        """
        Collect specific columns with optional filtering.
        
        Parameters:
        -----------
        columns : List[str]
            Columns to collect
        filter_expr : pl.Expr, optional
            Filter expression to apply before collecting
            
        Returns:
        --------
        pl.DataFrame
            Filtered DataFrame with specified columns
        """
        if self.is_lazy:
            lazy_df = self._df.select(columns)
            if filter_expr is not None:
                lazy_df = lazy_df.filter(filter_expr)
            return lazy_df.collect()  # type: ignore
        else:
            df = self._df.select(columns)
            if filter_expr is not None:
                df = df.filter(filter_expr)
            return cast(pl.DataFrame, df)
    
    def _parse_comparisons(
        self, 
        comparisons: List[Tuple[str, Union[str, List[str]]]]
    ) -> List[Tuple[str, str]]:
        """
        Parse comparison specifications into individual pairs.
        
        Parameters:
        -----------
        comparisons : List[Tuple[str, Union[str, List[str]]]]
            List of (reference, comparison) tuples
            
        Returns:
        --------
        List[Tuple[str, str]]
            Flattened list of individual comparison pairs
        """
        pairs = []
        for ref, comps in comparisons:
            if isinstance(comps, str):
                pairs.append((ref, comps))
            else:
                for comp in comps:
                    pairs.append((ref, comp))
        return pairs
    
    def _get_group_data_long(
        self, 
        value_col: str,
        group_col: str,
        groups: List[str]
    ) -> List[np.ndarray]:
        """
        Extract data for specified groups from long format.
        Only collects the necessary columns and rows.
        """
        # Build filter expression for all groups at once
        filter_expr = pl.col(group_col).is_in(groups)
        
        # Collect only needed columns with filtering
        df = self._collect_filtered([value_col, group_col], filter_expr)
        
        # Extract arrays for each group
        return [
            df.filter(pl.col(group_col) == group)[value_col].drop_nulls().to_numpy()
            for group in groups
        ]
    
    def _get_group_data_wide(
        self,
        columns: List[str]
    ) -> List[np.ndarray]:
        """
        Extract data for specified columns from wide format.
        Only collects the necessary columns.
        """
        df = self._collect_columns(columns)
        return [df[col].drop_nulls().to_numpy() for col in columns]

    def chi2_test(
        self,
        comparisons: List[Tuple[str, Union[str, List[str]]]],
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        correction: bool = True,
        lambda_: Optional[float] = None,
        multiple_comparisons: Optional[str] = None,
        alpha: float = 0.05
    ) -> List[TestResult]:
        """
        Perform chi-square tests of independence for categorical data.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        comparisons : List[Tuple[str, Union[str, List[str]]]]
            List of (reference, comparison) tuples. Each comparison can be:
            - A single group name (str)
            - A list of group names (List[str])
            In wide format, these are column names. In long format, these are group values.
            
        value_col : str, optional
            For long format: column containing the categorical values to test
            
        group_col : str, optional
            For long format: column containing group identifiers
            
        correction : bool, default=True
            Apply Yates' continuity correction for 2x2 tables
            
        lambda_ : float, optional
            Power parameter for Cressie-Read divergence statistic.
            None (default) uses Pearson's chi-squared.
            
        multiple_comparisons : str, optional
            Method for multiple comparison correction. Options include:
            'bonferroni', 'holm', 'sidak', 'holm-sidak', 'simes-hochberg', 
            'hommel', 'fdr_bh', 'fdr_by', 'fdr_tsbh', 'fdr_tsbky'
            
        alpha : float, default=0.05
            Family-wise error rate or false discovery rate for corrections
            
        Returns:
        --------
        List[TestResult]
            Test results for each comparison, with corrected p-values if requested
            
        Examples:
        ---------
        >>> # Wide format - each column is a group
        >>> df = pl.DataFrame({
        ...     "control": ["A", "B", "A", "C", "B"],
        ...     "treatment1": ["A", "A", "B", "B", "C"],
        ...     "treatment2": ["B", "B", "A", "C", "A"]
        ... })
        >>> results = df.stats_tests.chi2_test([
        ...     ("control", ["treatment1", "treatment2"])
        ... ])
        
        >>> # Long format - groups in a column
        >>> df_long = pl.DataFrame({
        ...     "group": ["control"]*5 + ["treatment1"]*5 + ["treatment2"]*5,
        ...     "category": ["A","B","A","C","B"] + ["A","A","B","B","C"] + ["B","B","A","C","A"]
        ... })
        >>> results = df_long.stats_tests.chi2_test(
        ...     [("control", "treatment1")],
        ...     value_col="category",
        ...     group_col="group"
        ... )
        """
        results = []
        pairs = self._parse_comparisons(comparisons)
        
        if value_col and group_col:
            # Long format - collect only needed groups
            all_groups = list(set([p[0] for p in pairs] + [p[1] for p in pairs]))
            filter_expr = pl.col(group_col).is_in(all_groups)
            df = self._collect_filtered([value_col, group_col], filter_expr)
            
            for ref, comp in pairs:
                ref_data = df.filter(pl.col(group_col) == ref)[value_col].to_list()
                comp_data = df.filter(pl.col(group_col) == comp)[value_col].to_list()
                
                # Create contingency table
                all_categories = sorted(set(ref_data + comp_data))
                ref_counts = [ref_data.count(cat) for cat in all_categories]
                comp_counts = [comp_data.count(cat) for cat in all_categories]
                contingency = np.array([ref_counts, comp_counts])
                
                # Perform chi-square test
                chi2_result = chi2_contingency(
                    contingency, 
                    correction=correction,
                    lambda_=lambda_
                )
                chi2_stat, p_val, dof, expected = chi2_result
                
                results.append(TestResult(
                    test_name="chi2",
                    statistic=float(chi2_stat), # type: ignore
                    p_value=float(p_val), # type: ignore
                    degrees_of_freedom=int(dof), # type: ignore
                    comparison=f"{ref} vs {comp}",
                    additional_info={"expected_frequencies": expected.tolist()} # type: ignore
                ))
        else:
            # Wide format - collect only needed columns
            all_cols = list(set([p[0] for p in pairs] + [p[1] for p in pairs]))
            df = self._collect_columns(all_cols)
            
            for ref, comp in pairs:
                ref_data = df[ref].drop_nulls().to_list()
                comp_data = df[comp].drop_nulls().to_list()
                
                # Create contingency table
                all_categories = sorted(set(ref_data + comp_data))
                ref_counts = [ref_data.count(cat) for cat in all_categories]
                comp_counts = [comp_data.count(cat) for cat in all_categories]
                contingency = np.array([ref_counts, comp_counts])
                
                # Perform chi-square test
                chi2_result = chi2_contingency(
                    contingency,
                    correction=correction,
                    lambda_=lambda_
                )
                chi2_stat, p_val, dof, expected = chi2_result
                
                results.append(TestResult(
                    test_name="chi2",
                    statistic=float(chi2_stat), # type: ignore
                    p_value=float(p_val), # type: ignore
                    degrees_of_freedom=int(dof), # type: ignore
                    comparison=f"{ref} vs {comp}",
                    additional_info={"expected_frequencies": expected.tolist()} # type: ignore
                ))
        
        # Apply multiple comparison correction if requested
        if multiple_comparisons:
            results = self._apply_multiple_comparison_correction(
                results, multiple_comparisons, alpha
            )
        
        return results
    
    def fisher_exact(
        self,
        comparisons: List[Tuple[str, Union[str, List[str]]]],
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        alternative: Literal["two-sided", "greater", "less"] = "two-sided",
        multiple_comparisons: Optional[Literal["fdr_bh", "fdr_by", "bonferroni", "holm", "holm-sidak", "simes-hochberg"]] = None,
        alpha: float = 0.05
    ) -> List[TestResult]:
        """
        Perform Fisher's exact test for 2x2 contingency tables.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        comparisons : List[Tuple[str, Union[str, List[str]]]]
            List of (reference, comparison) tuples for 2x2 tables
            
        value_col : str, optional
            For long format: column containing the binary categorical values
            
        group_col : str, optional
            For long format: column containing group identifiers
            
        alternative : {"two-sided", "greater", "less"}
            Alternative hypothesis
            
        Returns:
        --------
        List[TestResult]
            Test results for each comparison
        """
        results = []
        pairs = self._parse_comparisons(comparisons)
        
        if value_col and group_col:
            # Long format - collect only needed groups
            all_groups = list(set([p[0] for p in pairs] + [p[1] for p in pairs]))
            filter_expr = pl.col(group_col).is_in(all_groups)
            df = self._collect_filtered([value_col, group_col], filter_expr)
            
            for ref, comp in pairs:
                ref_data = df.filter(pl.col(group_col) == ref)[value_col].to_list()
                comp_data = df.filter(pl.col(group_col) == comp)[value_col].to_list()
                
                # Check for binary data
                unique_vals = sorted(set(ref_data + comp_data))
                if len(unique_vals) != 2:
                    raise ValueError(f"Fisher's exact test requires exactly 2 categories, found {len(unique_vals)}")
                
                # Create 2x2 table
                ref_counts = [ref_data.count(val) for val in unique_vals]
                comp_counts = [comp_data.count(val) for val in unique_vals]
                contingency = np.array([ref_counts, comp_counts])
                
                # Perform test
                fisher_result = fisher_exact(contingency, alternative=alternative)
                odds_ratio, p_val = fisher_result
                
                results.append(TestResult(
                    test_name="fisher_exact",
                    statistic=float(odds_ratio), # type: ignore
                    p_value=float(p_val), # type: ignore
                    comparison=f"{ref} vs {comp}",
                    additional_info={
                        "alternative": alternative,
                        "odds_ratio": float(odds_ratio) # type: ignore
                    }
                ))
        else:
            # Wide format - collect only needed columns
            all_cols = list(set([p[0] for p in pairs] + [p[1] for p in pairs]))
            df = self._collect_columns(all_cols)
            
            for ref, comp in pairs:
                ref_data = df[ref].drop_nulls().to_list()
                comp_data = df[comp].drop_nulls().to_list()
                
                # Check for binary data
                unique_vals = sorted(set(ref_data + comp_data))
                if len(unique_vals) != 2:
                    raise ValueError(f"Fisher's exact test requires exactly 2 categories, found {len(unique_vals)}")
                
                # Create 2x2 table
                ref_counts = [ref_data.count(val) for val in unique_vals]
                comp_counts = [comp_data.count(val) for val in unique_vals]
                contingency = np.array([ref_counts, comp_counts])
                
                # Perform test
                fisher_result = fisher_exact(contingency, alternative=alternative)
                odds_ratio, p_val = fisher_result
                
                results.append(TestResult(
                    test_name="fisher_exact",
                    statistic=float(odds_ratio), # type: ignore
                    p_value=float(p_val), # type: ignore
                    comparison=f"{ref} vs {comp}",
                    additional_info={
                        "alternative": alternative,
                        "odds_ratio": float(odds_ratio) # type: ignore
                    }
                ))
        
        # Apply multiple comparison correction if requested
        if multiple_comparisons:
            results = self._apply_multiple_comparison_correction(
                results, multiple_comparisons, alpha
            )
        
        return results
    
    def t_test(
        self,
        comparisons: List[Tuple[str, Union[str, List[str]]]],
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        test_type: Literal["independent", "paired", "one-sample"] = "independent",
        equal_var: bool = True,
        alternative: Literal["two-sided", "greater", "less"] = "two-sided",
        popmean: float = 0.0,
        multiple_comparisons: Optional[Literal["fdr_bh", "fdr_by", "bonferroni", "holm", "holm-sidak", "simes-hochberg"]] = None,
        alpha: float = 0.05
    ) -> List[TestResult]:
        """
        Perform t-tests for comparing means.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        comparisons : List[Tuple[str, Union[str, List[str]]]]
            List of (reference, comparison) tuples.
            For one-sample test, use column names directly.
            
        value_col : str, optional
            For long format: column containing the numeric values
            
        group_col : str, optional
            For long format: column containing group identifiers
            
        test_type : {"independent", "paired", "one-sample"}
            Type of t-test to perform
            
        equal_var : bool, default=True
            For independent t-test: assume equal variances (Student's t-test)
            If False, use Welch's t-test
            
        alternative : {"two-sided", "greater", "less"}
            Alternative hypothesis
            
        popmean : float, default=0.0
            For one-sample test: population mean to test against
            
        Returns:
        --------
        List[TestResult]
            Test results for each comparison
            
        Examples:
        ---------
        >>> # Independent samples t-test (wide format)
        >>> df = pl.DataFrame({
        ...     "group_a": [1.2, 2.3, 1.8, 2.1, 1.9],
        ...     "group_b": [2.1, 3.2, 2.8, 3.0, 2.5]
        ... })
        >>> results = df.stats_tests.t_test([("group_a", "group_b")])
        
        >>> # Paired t-test
        >>> results = df.stats_tests.t_test(
        ...     [("group_a", "group_b")],
        ...     test_type="paired"
        ... )
        """
        results = []
        
        if test_type == "one-sample":
            # One-sample t-test against population mean
            if value_col and group_col:
                # Long format
                groups_to_test = [ref for ref, _ in comparisons]
                filter_expr = pl.col(group_col).is_in(groups_to_test)
                df = self._collect_filtered([value_col, group_col], filter_expr)
                
                for ref, _ in comparisons:
                    data = df.filter(pl.col(group_col) == ref)[value_col].drop_nulls().to_numpy()
                    ttest_result = ttest_1samp(data, popmean, alternative=alternative)
                    t_stat, p_value = ttest_result
                    
                    results.append(TestResult(
                        test_name="t_test_1samp",
                        statistic=float(t_stat), # type: ignore
                        p_value=float(p_value), # type: ignore
                        degrees_of_freedom=len(data) - 1,
                        comparison=f"{ref} vs μ={popmean}",
                        additional_info={
                            "alternative": alternative,
                            "sample_mean": float(np.mean(data)),
                            "population_mean": popmean
                        }
                    ))
            else:
                # Wide format
                cols_to_test = [ref for ref, _ in comparisons]
                df = self._collect_columns(cols_to_test)
                
                for ref, _ in comparisons:
                    data = df[ref].drop_nulls().to_numpy()
                    ttest_result = ttest_1samp(data, popmean, alternative=alternative)
                    t_stat, p_value = ttest_result
                    
                    results.append(TestResult(
                        test_name="t_test_1samp",
                        statistic=float(t_stat), # type: ignore
                        p_value=float(p_value), # type: ignore
                        degrees_of_freedom=len(data) - 1,
                        comparison=f"{ref} vs μ={popmean}",
                        additional_info={
                            "alternative": alternative,
                            "sample_mean": float(np.mean(data)),
                            "population_mean": popmean
                        }
                    ))
        else:
            pairs = self._parse_comparisons(comparisons)
            
            if value_col and group_col:
                # Long format - collect only needed groups
                all_groups = list(set([p[0] for p in pairs] + [p[1] for p in pairs]))
                filter_expr = pl.col(group_col).is_in(all_groups)
                df = self._collect_filtered([value_col, group_col], filter_expr)
                
                for ref, comp in pairs:
                    ref_data = df.filter(pl.col(group_col) == ref)[value_col].drop_nulls().to_numpy()
                    comp_data = df.filter(pl.col(group_col) == comp)[value_col].drop_nulls().to_numpy()
                    
                    if test_type == "independent":
                        ttest_result = ttest_ind(
                            ref_data, comp_data,
                            equal_var=equal_var,
                            alternative=alternative
                        )
                        t_stat, p_value = ttest_result
                        test_name = "t_test_ind" if equal_var else "welch_t_test"
                        dof = len(ref_data) + len(comp_data) - 2 if equal_var else None
                    elif test_type == "paired":
                        if len(ref_data) != len(comp_data):
                            raise ValueError("Paired t-test requires equal sample sizes")
                        ttest_result = ttest_rel(ref_data, comp_data, alternative=alternative)
                        t_stat, p_value = ttest_result
                        test_name = "t_test_paired"
                        dof = len(ref_data) - 1
                    
                    results.append(TestResult(
                        test_name=test_name,
                        statistic=float(t_stat), # type: ignore
                        p_value=float(p_value), # type: ignore
                        degrees_of_freedom=dof,
                        comparison=f"{ref} vs {comp}",
                        additional_info={
                            "alternative": alternative,
                            "mean_diff": float(np.mean(ref_data) - np.mean(comp_data))
                        }
                    ))
            else:
                # Wide format - collect only needed columns
                all_cols = list(set([p[0] for p in pairs] + [p[1] for p in pairs]))
                df = self._collect_columns(all_cols)
                
                for ref, comp in pairs:
                    ref_data = df[ref].drop_nulls().to_numpy()
                    comp_data = df[comp].drop_nulls().to_numpy()
                    
                    if test_type == "independent":
                        ttest_result = ttest_ind(
                            ref_data, comp_data,
                            equal_var=equal_var,
                            alternative=alternative
                        )
                        t_stat, p_value = ttest_result
                        test_name = "t_test_ind" if equal_var else "welch_t_test"
                        dof = len(ref_data) + len(comp_data) - 2 if equal_var else None
                    elif test_type == "paired":
                        if len(ref_data) != len(comp_data):
                            raise ValueError("Paired t-test requires equal sample sizes")
                        ttest_result = ttest_rel(ref_data, comp_data, alternative=alternative)
                        t_stat, p_value = ttest_result
                        test_name = "t_test_paired"
                        dof = len(ref_data) - 1
                    
                    results.append(TestResult(
                        test_name=test_name,
                        statistic=float(t_stat), # type: ignore
                        p_value=float(p_value), # type: ignore
                        degrees_of_freedom=dof,
                        comparison=f"{ref} vs {comp}",
                        additional_info={
                            "alternative": alternative,
                            "mean_diff": float(np.mean(ref_data) - np.mean(comp_data))
                        }
                    ))
        
        # Apply multiple comparison correction if requested
        if multiple_comparisons:
            results = self._apply_multiple_comparison_correction(
                results, multiple_comparisons, alpha
            )
        
        return results
    
    def anova(
        self,
        groups: Union[List[str], Tuple[str, List[str]]],
        value_col: Optional[str] = None,
        group_col: Optional[str] = None
    ) -> TestResult:
        """
        Perform one-way ANOVA (F-test) for comparing multiple group means.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        groups : List[str] or Tuple[str, List[str]]
            Either a list of all groups to compare, or a tuple of
            (reference, comparisons) where all groups will be tested together
            
        value_col : str, optional
            For long format: column containing the numeric values
            
        group_col : str, optional  
            For long format: column containing group identifiers
            
        Returns:
        --------
        TestResult
            ANOVA test result
            
        Examples:
        ---------
        >>> # Wide format
        >>> df = pl.DataFrame({
        ...     "group_a": [1.2, 2.3, 1.8, 2.1],
        ...     "group_b": [2.1, 3.2, 2.8, 3.0],
        ...     "group_c": [1.5, 2.0, 1.7, 1.9]
        ... })
        >>> result = df.stats_tests.anova(["group_a", "group_b", "group_c"])
        """
        # Normalize groups input
        if isinstance(groups, tuple):
            ref, comps = groups
            all_groups = [ref] + (comps if isinstance(comps, list) else [comps])
        else:
            all_groups = groups
        
        # Extract data
        if value_col and group_col:
            # Long format
            group_data = self._get_group_data_long(value_col, group_col, all_groups)
        else:
            # Wide format
            group_data = self._get_group_data_wide(all_groups)
        
        # Perform ANOVA
        anova_result = f_oneway(*group_data)
        f_stat, p_value = anova_result
        
        # Calculate degrees of freedom
        k = len(group_data)  # number of groups
        n = sum(len(g) for g in group_data)  # total observations
        df_between = k - 1
        df_within = n - k
        
        return TestResult(
            test_name="anova",
            statistic=float(f_stat),
            p_value=float(p_value),
            degrees_of_freedom=df_between,
            comparison=" vs ".join(all_groups),
            additional_info={
                "df_within": df_within,
                "df_between": df_between,
                "group_means": {g: float(np.mean(d)) for g, d in zip(all_groups, group_data)}
            }
        )
    
    def kruskal_wallis(
        self,
        groups: Union[List[str], Tuple[str, List[str]]],
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        nan_policy: Literal["propagate", "omit", "raise"] = "omit"
    ) -> TestResult:
        """
        Perform Kruskal-Wallis H test (non-parametric ANOVA).
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        groups : List[str] or Tuple[str, List[str]]
            Groups to compare
            
        value_col : str, optional
            For long format: column containing the numeric values
            
        group_col : str, optional
            For long format: column containing group identifiers
            
        nan_policy : {"propagate", "omit", "raise"}
            How to handle NaN values
            
        Returns:
        --------
        TestResult
            Kruskal-Wallis test result
        """
        # Normalize groups input
        if isinstance(groups, tuple):
            ref, comps = groups
            all_groups = [ref] + (comps if isinstance(comps, list) else [comps])
        else:
            all_groups = groups
        
        # Extract data
        if value_col and group_col:
            group_data = self._get_group_data_long(value_col, group_col, all_groups)
        else:
            group_data = self._get_group_data_wide(all_groups)
        
        # Perform test
        kruskal_result = kruskal(*group_data, nan_policy=nan_policy)
        h_stat, p_value = kruskal_result
        
        return TestResult(
            test_name="kruskal_wallis",
            statistic=float(h_stat),
            p_value=float(p_value),
            degrees_of_freedom=len(all_groups) - 1,
            comparison=" vs ".join(all_groups),
            additional_info={
                "group_medians": {g: float(np.median(d)) for g, d in zip(all_groups, group_data)}
            }
        )
    
    def tukey_hsd(
        self,
        groups: Union[List[str], Tuple[str, List[str]]],
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        confidence_level: float = 0.95,
        multiple_comparisons: Optional[Literal["fdr_bh", "fdr_by", "bonferroni", "holm", "holm-sidak", "simes-hochberg"]] = None,
        alpha: float = 0.05
    ) -> List[TestResult]:
        """
        Perform Tukey's HSD (Honestly Significant Difference) post-hoc test.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        groups : List[str] or Tuple[str, List[str]]
            Groups to compare pairwise
            
        value_col : str, optional
            For long format: column containing the numeric values
            
        group_col : str, optional
            For long format: column containing group identifiers
            
        confidence_level : float, default=0.95
            Confidence level for intervals
            
        Returns:
        --------
        List[TestResult]
            Pairwise comparison results
        """
        # Normalize groups input
        if isinstance(groups, tuple):
            ref, comps = groups
            all_groups = [ref] + (comps if isinstance(comps, list) else [comps])
        else:
            all_groups = groups
        
        # Extract data for Tukey HSD
        if value_col and group_col:
            # Long format - collect only needed groups
            filter_expr = pl.col(group_col).is_in(all_groups)
            df = self._collect_filtered([value_col, group_col], filter_expr)
            values = df[value_col].to_numpy()
            labels = df[group_col].to_numpy()
        else:
            # Wide format - collect only needed columns
            df = self._collect_columns(all_groups)
            values = []
            labels = []
            for group in all_groups:
                group_data = df[group].drop_nulls().to_numpy()
                values.extend(group_data)
                labels.extend([group] * len(group_data))
            values = np.array(values)
            labels = np.array(labels)
        
        # Perform Tukey HSD
        tukey_result = tukey_hsd(*[values[labels == g] for g in all_groups])
        
        # Extract pairwise results
        test_results = []
        confidence_intervals = tukey_result.confidence_interval(confidence_level)  # type: ignore
        
        for i in range(len(all_groups)):
            for j in range(i + 1, len(all_groups)):
                test_results.append(TestResult(
                    test_name="tukey_hsd",
                    statistic=float(tukey_result.statistic[i, j]),  # type: ignore
                    p_value=float(tukey_result.pvalue[i, j]),  # type: ignore
                    comparison=f"{all_groups[i]} vs {all_groups[j]}",
                    additional_info={
                        "confidence_interval": [
                            float(confidence_intervals.low[i, j]),  # type: ignore
                            float(confidence_intervals.high[i, j])  # type: ignore
                        ],
                        "confidence_level": confidence_level
                    }
                ))
        
        # Apply multiple comparison correction if requested
        if multiple_comparisons:
            test_results = self._apply_multiple_comparison_correction(
                test_results, multiple_comparisons, alpha
            )
        
        return test_results
    
    def shapiro_wilk(
        self,
        columns: Optional[List[str]] = None,
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        groups: Optional[List[str]] = None
    ) -> List[TestResult]:
        """
        Perform Shapiro-Wilk test for normality.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        columns : List[str], optional
            For wide format: columns to test
            
        value_col : str, optional
            For long format: column containing values to test
            
        group_col : str, optional
            For long format: column for grouping
            
        groups : List[str], optional
            For long format: specific groups to test
            
        Returns:
        --------
        List[TestResult]
            Normality test results
        """
        results = []
        
        if columns:
            # Wide format - collect only needed columns
            df = self._collect_columns(columns)
            for col in columns:
                data = df[col].drop_nulls().to_numpy()
                if len(data) < 3:
                    continue
                
                shapiro_result = shapiro(data)
                stat, p_value = shapiro_result
                results.append(TestResult(
                    test_name="shapiro_wilk",
                    statistic=float(stat),
                    p_value=float(p_value),
                    comparison=col,
                    additional_info={
                        "n_samples": len(data),
                        "interpretation": "normal" if p_value > 0.05 else "not normal"
                    }
                ))
        elif value_col and group_col and groups:
            # Long format with groups - collect only needed groups
            filter_expr = pl.col(group_col).is_in(groups)
            df = self._collect_filtered([value_col, group_col], filter_expr)
            
            for group in groups:
                data = df.filter(pl.col(group_col) == group)[value_col].drop_nulls().to_numpy()
                if len(data) < 3:
                    continue
                    
                shapiro_result = shapiro(data)
                stat, p_value = shapiro_result
                results.append(TestResult(
                    test_name="shapiro_wilk",
                    statistic=float(stat),
                    p_value=float(p_value),
                    comparison=f"{group_col}={group}",
                    additional_info={
                        "n_samples": len(data),
                        "interpretation": "normal" if p_value > 0.05 else "not normal"
                    }
                ))
        elif value_col:
            # Long format, entire column - collect only that column
            df = self._collect_columns([value_col])
            data = df[value_col].drop_nulls().to_numpy()
            stat, p_value = shapiro(data)
            results.append(TestResult(
                test_name="shapiro_wilk",
                statistic=float(stat),
                p_value=float(p_value),
                comparison=value_col,
                additional_info={
                    "n_samples": len(data),
                    "interpretation": "normal" if p_value > 0.05 else "not normal"
                }
            ))
        
        return results
    
    def anderson_darling(
        self,
        columns: Optional[List[str]] = None,
        value_col: Optional[str] = None,
        dist: Literal["norm", "expon", "logistic", "gumbel", "gumbel_l", "gumbel_r"] = "norm"
    ) -> List[TestResult]:
        """
        Perform Anderson-Darling test for distribution fit.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        columns : List[str], optional
            Columns to test (wide format)
            
        value_col : str, optional
            Column to test (long format)
            
        dist : str
            Distribution to test against
            
        Returns:
        --------
        List[TestResult]
            Test results
        """
        results = []
        
        cols_to_test = columns if columns else ([value_col] if value_col else [])
        
        if cols_to_test:
            # Collect only needed columns
            df = self._collect_columns(cols_to_test)
            
            for col in cols_to_test:
                data = df[col].drop_nulls().to_numpy()
                anderson_result = anderson(data, dist=dist)
                
                # Find significance level
                sig_level = None
                critical_vals = anderson_result.critical_values  # type: ignore
                sig_levels = anderson_result.significance_level  # type: ignore
                test_stat = anderson_result.statistic  # type: ignore
                
                for i, crit_val in enumerate(critical_vals):
                    if test_stat < crit_val:
                        sig_level = sig_levels[i]
                        break
                
                results.append(TestResult(
                    test_name="anderson_darling",
                    statistic=float(test_stat),
                    p_value=sig_level / 100 if sig_level else 0.001,  # Convert to p-value scale
                    comparison=col,
                    additional_info={
                        "distribution": dist,
                        "critical_values": critical_vals.tolist(),
                        "significance_levels": sig_levels.tolist()
                    }
                ))
        
        return results
    
    def dagostino_pearson(
        self,
        columns: Optional[List[str]] = None,
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        groups: Optional[List[str]] = None
    ) -> List[TestResult]:
        """
        Perform D'Agostino and Pearson's normality test.
        
        Tests for normality using skewness and kurtosis statistics.
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        columns : List[str], optional
            Columns to test (wide format)
            
        value_col : str, optional
            Column to test (long format)
            
        group_col : str, optional
            Column containing group identifiers (long format)
            
        groups : List[str], optional
            Specific groups to test (long format)
            
        Returns:
        --------
        List[TestResult]
            Test results with interpretation
        """
        
        results = []
        
        if value_col and group_col:
            # Long format - collect only needed columns and filter groups
            if groups:
                filter_expr = pl.col(group_col).is_in(groups)
                df = self._collect_filtered([value_col, group_col], filter_expr)
            else:
                df = self._collect_columns([value_col, group_col])
            
            test_groups = groups or df[group_col].unique().sort().to_list()
            for group in test_groups:
                group_data = df.filter(pl.col(group_col) == group)[value_col].drop_nulls().to_numpy()
                
                if len(group_data) < 8:
                    results.append(TestResult(
                        test_name="dagostino_pearson",
                        statistic=np.nan,
                        p_value=np.nan,
                        comparison=f"{value_col} in {group}",
                        additional_info={
                            "error": "Insufficient data (need at least 8 samples)",
                            "interpretation": "Cannot test normality with < 8 samples"
                        }
                    ))
                    continue
                
                stat, p_value = normaltest(group_data)
                
                interpretation = "Normal" if p_value > 0.05 else "Not normal"
                
                results.append(TestResult(
                    test_name="dagostino_pearson",
                    statistic=float(stat),
                    p_value=float(p_value),
                    comparison=f"{value_col} in {group}",
                    additional_info={
                        "interpretation": interpretation,
                        "n_samples": len(group_data)
                    }
                ))
        else:
            # Wide format - collect only needed columns
            cols_to_test = columns if columns else [col for col in self.columns if col != group_col]
            df = self._collect_columns(cols_to_test)
            
            for col in cols_to_test:
                data = df[col].drop_nulls().to_numpy()
                
                if len(data) < 8:
                    results.append(TestResult(
                        test_name="dagostino_pearson",
                        statistic=np.nan,
                        p_value=np.nan,
                        comparison=col,
                        additional_info={
                            "error": "Insufficient data (need at least 8 samples)",
                            "interpretation": "Cannot test normality with < 8 samples"
                        }
                    ))
                    continue
                
                stat, p_value = normaltest(data)
                
                interpretation = "Normal" if p_value > 0.05 else "Not normal"
                
                results.append(TestResult(
                    test_name="dagostino_pearson",
                    statistic=float(stat),
                    p_value=float(p_value),
                    comparison=col,
                    additional_info={
                        "interpretation": interpretation,
                        "n_samples": len(data)
                    }
                ))
        
        return results
    
    def kolmogorov_smirnov(
        self,
        columns: Optional[List[str]] = None,
        value_col: Optional[str] = None,
        group_col: Optional[str] = None,
        groups: Optional[List[str]] = None,
        cdf: str = "norm",
        args: Tuple = ()
    ) -> List[TestResult]:
        """
        Perform Kolmogorov-Smirnov test for goodness of fit.
        
        For LazyFrames, only the necessary columns are collected.
        
        Parameters:
        -----------
        columns : List[str], optional
            Columns to test (wide format)
            
        value_col : str, optional
            Column to test (long format)
            
        group_col : str, optional
            Column containing group identifiers (long format)
            
        groups : List[str], optional
            Specific groups to test (long format)
            
        cdf : str or callable
            Distribution to test against (default: "norm" for normal)
            
        args : tuple
            Parameters for the distribution
            
        Returns:
        --------
        List[TestResult]
            Test results with interpretation
        """
        
        results = []
        
        if value_col and group_col:
            # Long format - collect only needed columns and filter groups
            if groups:
                filter_expr = pl.col(group_col).is_in(groups)
                df = self._collect_filtered([value_col, group_col], filter_expr)
            else:
                df = self._collect_columns([value_col, group_col])
            
            test_groups = groups or df[group_col].unique().sort().to_list()
            for group in test_groups:
                group_data = df.filter(pl.col(group_col) == group)[value_col].drop_nulls().to_numpy()
                
                if len(group_data) < 5:
                    results.append(TestResult(
                        test_name="kolmogorov_smirnov",
                        statistic=np.nan,
                        p_value=np.nan,
                        comparison=f"{value_col} in {group}",
                        additional_info={
                            "error": "Insufficient data (need at least 5 samples)",
                            "interpretation": "Cannot test distribution fit with < 5 samples",
                            "distribution": cdf
                        }
                    ))
                    continue
                
                stat, p_value = kstest(group_data, cdf, args=args)
                
                interpretation = f"Fits {cdf} distribution" if p_value > 0.05 else f"Does not fit {cdf} distribution"
                
                results.append(TestResult(
                    test_name="kolmogorov_smirnov",
                    statistic=float(stat),
                    p_value=float(p_value),
                    comparison=f"{value_col} in {group}",
                    additional_info={
                        "interpretation": interpretation,
                        "distribution": cdf,
                        "n_samples": len(group_data)
                    }
                ))
        else:
            # Wide format - collect only needed columns
            cols_to_test = columns if columns else [col for col in self.columns if col != group_col]
            df = self._collect_columns(cols_to_test)
            
            for col in cols_to_test:
                data = df[col].drop_nulls().to_numpy()
                
                if len(data) < 5:
                    results.append(TestResult(
                        test_name="kolmogorov_smirnov",
                        statistic=np.nan,
                        p_value=np.nan,
                        comparison=col,
                        additional_info={
                            "error": "Insufficient data (need at least 5 samples)",
                            "interpretation": "Cannot test distribution fit with < 5 samples",
                            "distribution": cdf
                        }
                    ))
                    continue
                
                stat, p_value = kstest(data, cdf, args=args)
                
                interpretation = f"Fits {cdf} distribution" if p_value > 0.05 else f"Does not fit {cdf} distribution"
                
                results.append(TestResult(
                    test_name="kolmogorov_smirnov",
                    statistic=float(stat),
                    p_value=float(p_value),
                    comparison=col,
                    additional_info={
                        "interpretation": interpretation,
                        "distribution": cdf,
                        "n_samples": len(data)
                    }
                ))
        
        return results
    
    def auto_test(
        self,
        groups: Optional[Union[List[str], Tuple[str, List[str]]]] = None,
        value_col: Optional[Union[str, List[str]]] = None,
        group_col: Optional[str] = None,
        alpha: float = 0.05,
        force_parametric: bool = False,
        return_recommendation_only: bool = False,
        standardization_dicts: Optional[Dict[str, Dict[str, str]]] = None,
        base_groups: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], List[TestResult]]:
        """
        Automatically determine and optionally execute the best statistical test.
        
        This method analyzes the data characteristics and recommends the most appropriate
        statistical test based on:
        - Data type (numeric/categorical)
        - Number of groups
        - Sample sizes
        - Normality assumptions
        - Equal variance assumptions
        
        Parameters:
        -----------
        groups : List[str] or Tuple[str, List[str]], optional
            Groups to analyze. If None, analyzes all numeric columns
            
        value_col : str or List[str], optional
            For long format: column(s) containing values to analyze.
            If a list is provided, each column will be analyzed separately.
            
        group_col : str, optional  
            For long format: column containing group identifiers
            
        alpha : float, default=0.05
            Significance level for tests and recommendations
            
        force_parametric : bool, default=False
            Force parametric tests even if assumptions aren't fully met
            
        return_recommendation_only : bool, default=False
            If True, only return recommendation without running the test
            
        standardization_dicts : Dict[str, Dict[str, str]], optional
            Dictionary mapping column names to standardization dictionaries.
            Each standardization dict maps original values to standardized values.
            Example: {'Sex': {'M': 'Male', 'F': 'Female', 'male': 'Male', 'female': 'Female'}}
            
        base_groups : Dict[str, str], optional
            Dictionary mapping column names to base group values for comparison.
            For categorical tests, this specifies which category to use as reference.
            Example: {'Sex': 'Male', 'Treatment': 'Control'}
            
        Returns:
        --------
        Dict[str, Any] or List[TestResult]
            If return_recommendation_only=True: recommendation dictionary
            If return_recommendation_only=False: actual test results
        """
        
        # Determine analysis format and get group information
        if group_col:
            # Long format analysis - group_col specified means we want to compare groups
            if not value_col:
                # Auto-analyze all columns except the group column
                schema = self.schema
                analyzable_columns = [col for col in schema.keys() if col != group_col]
                
                if not analyzable_columns:
                    raise ValueError(f"No columns found to analyze (excluding group column '{group_col}')")
                
                # Analyze each column separately
                all_results = []
                for col in analyzable_columns:
                    try:
                        col_result = self.auto_test(
                            groups=groups,
                            value_col=col,
                            group_col=group_col,
                            alpha=alpha,
                            force_parametric=force_parametric,
                            return_recommendation_only=return_recommendation_only,
                            standardization_dicts=standardization_dicts,
                            base_groups=base_groups
                        )
                        
                        if return_recommendation_only:
                            # Add column information to recommendation
                            col_result['analyzed_column'] = col
                            all_results.append(col_result)
                        else:
                            # Add column information to test results
                            for result in col_result:
                                if hasattr(result, 'additional_info') and result.additional_info:
                                    result.additional_info['analyzed_column'] = col
                                else:
                                    result.additional_info = {'analyzed_column': col}
                            all_results.extend(col_result)
                    except Exception as e:
                        # Create error result for this column
                        error_result = TestResult(
                            test_name="auto_test_error",
                            statistic=np.nan,
                            p_value=np.nan,
                            comparison=f"auto_test_failed_for_{col}",
                            additional_info={
                                "error": str(e),
                                "analyzed_column": col
                            }
                        )
                        all_results.append(error_result)
                
                return all_results
            
            elif isinstance(value_col, list):
                # Multiple value columns specified - analyze each one separately with the group_col
                all_results = []
                for col in value_col:
                    try:
                        col_result = self.auto_test(
                            groups=groups,
                            value_col=col,
                            group_col=group_col,
                            alpha=alpha,
                            force_parametric=force_parametric,
                            return_recommendation_only=return_recommendation_only,
                            standardization_dicts=standardization_dicts,
                            base_groups=base_groups
                        )
                        
                        # Check if we got results or an empty list
                        if not col_result:
                            # Empty result - create an error entry
                            error_result = TestResult(
                                test_name="auto_test_error",
                                statistic=np.nan,
                                p_value=np.nan,
                                comparison=f"auto_test_no_results_for_{col}",
                                additional_info={
                                    "error": "No results returned - likely unsupported data type or test failure",
                                    "analyzed_column": col
                                }
                            )
                            all_results.append(error_result)
                            continue
                        
                        if return_recommendation_only:
                            # Add column information to recommendation
                            col_result['analyzed_column'] = col
                            all_results.append(col_result)
                        else:
                            # Add column information to test results
                            for result in col_result:
                                if hasattr(result, 'additional_info') and result.additional_info:
                                    result.additional_info['analyzed_column'] = col
                                else:
                                    result.additional_info = {'analyzed_column': col}
                            all_results.extend(col_result)
                    except Exception as e:
                        # Create error result for this column
                        error_result = TestResult(
                            test_name="auto_test_error",
                            statistic=np.nan,
                            p_value=np.nan,
                            comparison=f"auto_test_failed_for_{col}",
                            additional_info={
                                "error": str(e),
                                "analyzed_column": col
                            }
                        )
                        all_results.append(error_result)
                
                return all_results
            
            df = self._collect_columns([value_col, group_col])
            groups_to_analyze = groups or df[group_col].unique().sort().to_list()
            n_groups = len(groups_to_analyze)
            
            # Extract group data
            group_data = []
            sample_sizes = []
            is_numeric = True
            
            for group in groups_to_analyze:
                group_values = df.filter(pl.col(group_col) == group)[value_col].drop_nulls()
                group_data.append(group_values)
                sample_sizes.append(len(group_values))
                
                # Check if data is numeric
                if not group_values.dtype.is_numeric():
                    is_numeric = False
        else:
            # Wide format analysis
            if isinstance(groups, tuple):
                # Extract reference and comparison groups
                ref_group, comp_groups = groups
                if isinstance(comp_groups, str):
                    groups_to_analyze = [ref_group, comp_groups]
                else:
                    groups_to_analyze = [ref_group] + comp_groups
            elif isinstance(groups, list):
                groups_to_analyze = groups
            else:
                # Analyze all numeric columns

                schema = self.schema
                groups_to_analyze = [col for col, dtype in schema.items() if dtype.is_numeric()]
 
            
            n_groups = len(groups_to_analyze)
            df = self._collect_columns(groups_to_analyze)
            
            # Extract group data  
            group_data = []
            sample_sizes = []
            is_numeric = True
            
            for group in groups_to_analyze:
                group_values = df[group].drop_nulls()
                group_data.append(group_values)
                sample_sizes.append(len(group_values))
                
                # Check if data is numeric
                if not group_values.dtype.is_numeric():
                    is_numeric = False
        
        # Basic validation
        if min(sample_sizes) < 3:
            raise ValueError(f"Insufficient sample size. Minimum group size: {min(sample_sizes)}. Need at least 3.")
        
        # Determine comparison type
        if n_groups == 1:
            comparison_type = "one_sample"
        elif n_groups == 2:
            comparison_type = "two_sample" 
        else:
            comparison_type = "multiple_sample"
        
        # Analyze data characteristics and recommend test
        if is_numeric:
            recommendation = self._recommend_numeric_test(
                group_data, comparison_type, sample_sizes, alpha, force_parametric
            )
        else:
            recommendation = self._recommend_categorical_test(
                group_data, comparison_type, sample_sizes
            )
        
        # Add general information to recommendation
        recommendation.update({
            "groups_analyzed": groups_to_analyze,
            "n_groups": n_groups,
            "sample_sizes": sample_sizes,
            "total_observations": sum(sample_sizes),
            "comparison_type": comparison_type,
            "alpha": alpha,
            "format": "long" if (value_col and group_col) else "wide"
        })
        
        # Return recommendation only if requested
        if return_recommendation_only:
            return recommendation
            
        # Execute the recommended test
        return self._execute_recommended_test(
            recommendation, groups, value_col, group_col, 
            standardization_dicts, base_groups
        )
    
    def _recommend_numeric_test(
        self,
        group_data: List,
        comparison_type: str,
        sample_sizes: List[int],
        alpha: float,
        force_parametric: bool
    ) -> Dict[str, Any]:
        """Recommend appropriate test for numeric data."""
        
        # Test normality for each group
        normality_results = []
        for data in group_data:
            data_array = data.to_numpy() if hasattr(data, 'to_numpy') else np.array(data.to_list())
            
            if len(data_array) < 3:
                normality_results.append({"is_normal": False, "test_used": "insufficient_data", "p_value": np.nan})
                continue
                
            try:
                # Use Shapiro-Wilk for small samples, D'Agostino for larger samples
                from scipy.stats import shapiro, normaltest
                if len(data_array) <= 50:
                    stat, p_val = shapiro(data_array)
                    test_used = "shapiro_wilk"
                else:
                    stat, p_val = normaltest(data_array)
                    test_used = "dagostino_pearson"
                
                normality_results.append({
                    "is_normal": p_val > alpha,
                    "test_used": test_used, 
                    "p_value": p_val,
                    "statistic": stat
                })
            except Exception:
                normality_results.append({"is_normal": False, "test_used": "failed", "p_value": np.nan})
        
        # Assess overall normality
        all_normal = all(result["is_normal"] for result in normality_results)
        sufficient_sample_size = min(sample_sizes) >= 30
        
        # Decision logic based on comparison type
        post_hoc = None  # Initialize post_hoc variable
        
        if comparison_type == "one_sample":
            if force_parametric or (all_normal and sufficient_sample_size):
                recommended_test = "t_test"
                test_params = {"test_type": "one-sample"}
                parametric = True
                alternative = "wilcoxon_signed_rank"
            else:
                recommended_test = "wilcoxon_signed_rank"  
                test_params = {}
                parametric = False
                alternative = "t_test"
                
        elif comparison_type == "two_sample":
            if force_parametric or all_normal:
                recommended_test = "t_test"
                test_params = {"test_type": "independent"}
                parametric = True
                alternative = "mann_whitney_u"
            else:
                recommended_test = "mann_whitney_u"
                test_params = {}
                parametric = False
                alternative = "t_test"
                
        else:  # multiple_sample
            if force_parametric or all_normal:
                recommended_test = "anova"
                test_params = {}
                parametric = True
                alternative = "kruskal_wallis"
                post_hoc = "tukey_hsd"
            else:
                recommended_test = "kruskal_wallis"
                test_params = {}
                parametric = False
                alternative = "anova"
                post_hoc = "dunn_test"
        
        # Generate recommendation reason
        if force_parametric:
            reason = f"Parametric test forced by user override. Sample sizes: {sample_sizes}."
        elif all_normal:
            normal_count = sum(1 for r in normality_results if r["is_normal"])
            reason = f"All {normal_count} groups passed normality testing. Sample sizes: {sample_sizes}."
        else:
            non_normal_count = sum(1 for r in normality_results if not r["is_normal"])
            reason = f"Non-parametric test selected: {non_normal_count} of {len(normality_results)} groups failed normality testing."
        
        return {
            "recommended_test": recommended_test,
            "test_parameters": test_params,
            "is_parametric": parametric,
            "alternative_test": alternative,
            "post_hoc_test": post_hoc if comparison_type == "multiple_sample" else None,
            "normality_results": normality_results,
            "assumptions_met": {
                "normality": all_normal,
                "sufficient_sample_size": sufficient_sample_size,
                "independence": True  # Assumed
            },
            "recommendation_reason": reason,
            "data_type": "numeric"
        }
    
    def _recommend_categorical_test(
        self, 
        group_data: List,
        comparison_type: str, 
        sample_sizes: List[int]
    ) -> Dict[str, Any]:
        """Recommend appropriate test for categorical data."""
        
        if comparison_type == "one_sample":
            # Goodness of fit tests
            data = group_data[0].to_list()
            unique_categories = len(set(data))
            min_expected = len(data) / unique_categories
            
            if unique_categories == 2 and len(data) >= 30:
                recommended_test = "binomial_test"
                reason = "Binomial test for two-category data with adequate sample size."
            elif min_expected >= 5:
                recommended_test = "chi2_test"
                reason = f"Chi-square goodness of fit test. Expected frequency per category: {min_expected:.1f}"
            else:
                recommended_test = "chi2_test"
                reason = f"Chi-square test with caution - low expected frequencies ({min_expected:.1f})"
                
        elif comparison_type == "two_sample":
            # Independence/association tests
            recommended_test = "chi2_test"
            reason = "Chi-square test of independence for categorical association."
            
            # Check if Fisher's exact might be better
            if min(sample_sizes) < 20:
                recommended_test = "fisher_exact"
                reason = "Fisher's exact test recommended for small sample sizes."
                
        else:  # multiple_sample  
            recommended_test = "chi2_test"
            reason = "Chi-square test of independence for multiple categorical variables."
        
        return {
            "recommended_test": recommended_test,
            "test_parameters": {},
            "is_parametric": False,  # Categorical tests are generally non-parametric
            "alternative_test": "fisher_exact" if recommended_test == "chi2_test" else "chi2_test",
            "post_hoc_test": None,
            "assumptions_met": {
                "sufficient_sample_size": min(sample_sizes) >= 5,
                "independence": True  # Assumed
            },
            "recommendation_reason": reason,
            "data_type": "categorical"
        }
    
    def _execute_recommended_test(
        self,
        recommendation: Dict[str, Any],
        groups: Optional[Union[List[str], Tuple[str, List[str]]]],
        value_col: Optional[Union[str, List[str]]],
        group_col: Optional[str],
        standardization_dicts: Optional[Dict[str, Dict[str, str]]] = None,
        base_groups: Optional[Dict[str, str]] = None
    ) -> List[TestResult]:
        """Execute the recommended test and return results."""
        
        test_name = recommendation["recommended_test"]
        test_params = recommendation.get("test_parameters", {})
        
        def _apply_standardization(df: pl.DataFrame, col: str) -> pl.DataFrame:
            """Apply standardization dictionary to a column if provided."""
            if standardization_dicts and col in standardization_dicts:
                std_dict = standardization_dicts[col]
                # Convert categorical to string first, then apply mapping
                try:
                    df_copy = df.clone()
                    # Convert to string if it's categorical
                    if df_copy[col].dtype == pl.Categorical:
                        df_copy = df_copy.with_columns(pl.col(col).cast(pl.Utf8))
                    
                    # Apply each mapping
                    mapping_expr = pl.col(col)
                    for old_val, new_val in std_dict.items():
                        mapping_expr = mapping_expr.str.replace_all(f"^{old_val}$", new_val)
                    
                    return df_copy.with_columns(mapping_expr.alias(col))
                except Exception as e:
                    print(f"Warning: Standardization failed for column {col}: {e}")
                    return df
            return df
        
        def _get_base_group(col: str) -> Optional[str]:
            """Get the base group for a column if specified."""
            if base_groups and col in base_groups:
                return base_groups[col]
            return None
        
        # Map test names to actual method calls
        try:
            if test_name == "chi2_test":
                # Use groups from recommendation if original groups was None
                groups_to_use = groups or recommendation.get("groups_analyzed")
                
                if not groups_to_use:
                    raise ValueError("Chi-square test requires group specification")
                
                # For multiple groups, create an overall contingency table analysis
                if len(groups_to_use) > 2:
                    # Multi-group overall test
                    filter_expr = pl.col(group_col).is_in(groups_to_use)
                    df = self._collect_filtered([value_col, group_col], filter_expr)
                    
                    # Apply standardization if provided
                    df = _apply_standardization(df, value_col)
                    
                    # Get all unique categories after standardization
                    all_categories = sorted(df[value_col].unique().to_list())
                    
                    # Handle base group ordering if specified
                    base_group = _get_base_group(value_col)
                    if base_group and base_group in all_categories:
                        # Move base group to first position for comparison
                        all_categories = [base_group] + [cat for cat in all_categories if cat != base_group]
                    
                    # Create contingency table: rows = groups, columns = categories
                    contingency_data = []
                    group_breakdowns = {}
                    
                    for group in groups_to_use:
                        group_data = df.filter(pl.col(group_col) == group)[value_col].to_list()
                        group_counts = [group_data.count(cat) for cat in all_categories]
                        contingency_data.append(group_counts)
                        
                        # Calculate percentages for breakdown
                        total = sum(group_counts)
                        group_breakdowns[group] = {
                            'counts': dict(zip(all_categories, group_counts)),
                            'percentages': {cat: (count/total)*100 if total > 0 else 0 
                                          for cat, count in zip(all_categories, group_counts)},
                            'total': total
                        }
                    
                    contingency = np.array(contingency_data)
                    
                    # Perform overall chi-square test
                    from scipy.stats import chi2_contingency, chi2
                    chi2_result = chi2_contingency(contingency, correction=True)
                    chi2_stat, p_val, dof, expected = chi2_result
                    
                    # Calculate statistics for each individual category (level)
                    category_stats = {}
                    for i, category in enumerate(all_categories):
                        # Extract counts for this category across all groups
                        category_counts = contingency[:, i]
                        category_totals = [group_breakdowns[group]['total'] for group in groups_to_use]
                        
                        # Create 2x2 contingency for this category vs all others
                        category_vs_others = []
                        for j, group in enumerate(groups_to_use):
                            this_category_count = category_counts[j]
                            other_categories_count = category_totals[j] - this_category_count
                            category_vs_others.append([this_category_count, other_categories_count])
                        
                        category_contingency = np.array(category_vs_others)
                        
                        # Perform chi-square test for this category
                        try:
                            cat_chi2_result = chi2_contingency(category_contingency)
                            cat_chi2_stat, cat_p_val, cat_dof, cat_expected = cat_chi2_result
                            
                            # Calculate effect size (Cramér's V)
                            n = np.sum(category_contingency)
                            cramers_v = np.sqrt(cat_chi2_stat / (n * (min(category_contingency.shape) - 1)))
                            
                            category_stats[category] = {
                                'chi2_statistic': float(cat_chi2_stat),
                                'p_value': float(cat_p_val),
                                'degrees_of_freedom': int(cat_dof),
                                'cramers_v': float(cramers_v),
                                'significant': cat_p_val < 0.05,
                                'counts_by_group': {group: int(count) for group, count in zip(groups_to_use, category_counts)},
                                'percentages_by_group': {group: (count/total)*100 if total > 0 else 0 
                                                       for group, count, total in zip(groups_to_use, category_counts, category_totals)}
                            }
                        except Exception as e:
                            category_stats[category] = {
                                'error': str(e),
                                'counts_by_group': {group: int(count) for group, count in zip(groups_to_use, category_counts)},
                                'percentages_by_group': {group: (count/total)*100 if total > 0 else 0 
                                                       for group, count, total in zip(groups_to_use, category_counts, category_totals)}
                            }
                    
                    return [TestResult(
                        test_name="chi2",
                        statistic=float(chi2_stat),
                        p_value=float(p_val),
                        degrees_of_freedom=int(dof),
                        comparison=" vs ".join(groups_to_use),
                        additional_info={
                            "contingency_table": {
                                "groups": groups_to_use,
                                "categories": all_categories,
                                "observed": contingency.tolist(),
                                "expected": expected.tolist()
                            },
                            "group_breakdowns": group_breakdowns,
                            "overall_categories": all_categories,
                            "category_statistics": category_stats,
                            "significant_categories": [cat for cat, stats in category_stats.items() 
                                                     if stats.get('significant', False)],
                            "base_group": _get_base_group(value_col),
                            "standardization_applied": standardization_dicts and value_col in standardization_dicts
                        }
                    )]
                else:
                    # For 2 groups, apply standardization and use standard pairwise chi-square
                    if standardization_dicts and value_col in standardization_dicts:
                        # Pre-process data with standardization before calling chi2_test
                        filter_expr = pl.col(group_col).is_in(groups_to_use)
                        df = self._collect_filtered([value_col, group_col], filter_expr)
                        df = _apply_standardization(df, value_col)
                        
                        # Update the dataframe in self for the chi2_test call
                        # This is a temporary workaround - ideally chi2_test should accept a dataframe parameter
                        original_df = self._df
                        self._df = df
                        try:
                            comparisons = [(groups_to_use[0], groups_to_use[1])]
                            result = self.chi2_test(comparisons, value_col=value_col, group_col=group_col)
                            
                            # Add base group information if specified
                            base_group = _get_base_group(value_col)
                            if base_group and result and len(result) > 0:
                                if result[0].additional_info is None:
                                    result[0].additional_info = {}
                                result[0].additional_info['base_group'] = base_group
                                result[0].additional_info['standardization_applied'] = True
                            
                            return result
                        finally:
                            # Restore original dataframe
                            self._df = original_df
                    else:
                        # No standardization needed
                        comparisons = [(groups_to_use[0], groups_to_use[1])]
                        result = self.chi2_test(comparisons, value_col=value_col, group_col=group_col)
                        
                        # Add base group information if specified
                        base_group = _get_base_group(value_col)
                        if base_group and result and len(result) > 0:
                            if result[0].additional_info is None:
                                result[0].additional_info = {}
                            result[0].additional_info['base_group'] = base_group
                        
                        return result
                
            elif test_name == "fisher_exact":
                if isinstance(groups, tuple):
                    comparisons = [groups]
                else:
                    comparisons = [(groups[0], groups[1])] if groups and len(groups) >= 2 else []
                    
                return self.fisher_exact(comparisons, value_col=value_col, group_col=group_col)  # type: ignore
                
            elif test_name == "t_test":
                if isinstance(groups, tuple):
                    comparisons = [groups]
                elif groups and len(groups) >= 2:
                    # Create pairwise comparisons
                    comparisons = [(groups[0], groups[1])]
                else:
                    comparisons = [(groups[0], None)] if groups else []
                    
                return self.t_test(comparisons, value_col=value_col, group_col=group_col, **test_params)  # type: ignore
                
            elif test_name == "anova":
                # Use groups from recommendation if original groups was None
                groups_to_use = groups or recommendation.get("groups_analyzed")
                if groups_to_use:
                    return [self.anova(groups_to_use, value_col=value_col, group_col=group_col)]
                else:
                    raise ValueError("ANOVA requires group specification")
                    
            elif test_name == "kruskal_wallis":
                # Use groups from recommendation if original groups was None
                groups_to_use = groups or recommendation.get("groups_analyzed")
                if groups_to_use:
                    return [self.kruskal_wallis(groups_to_use, value_col=value_col, group_col=group_col)]
                else:
                    raise ValueError("Kruskal-Wallis requires group specification")
                    
            else:
                raise NotImplementedError(f"Test '{test_name}' not yet implemented in auto_test execution")
                
        except Exception as e:
            # Return error as a TestResult
            return [TestResult(
                test_name="auto_test_error",
                statistic=np.nan,
                p_value=np.nan,
                comparison="auto_test_failed", 
                additional_info={
                    "error": str(e),
                    "recommended_test": test_name,
                    "recommendation": recommendation
                }
            )]

    def manuscript_table(
        self,
        results: Optional[List[TestResult]] = None,
        group_column: Optional[str] = None,
        variable_columns: Optional[List[str]] = None,
        # Auto-test parameters (when source_data is provided)
        alpha: float = 0.05,
        force_parametric: bool = False,
        standardization_dicts: Optional[Dict[str, Dict[str, str]]] = None,
        base_groups: Optional[Dict[str, str]] = None,
        # Formatting parameters
        format: Literal["dataframe", "latex", "markdown", "html"] = "dataframe",
        p_value_precision: int = 4,
        statistic_precision: int = 3,
        significance_symbols: Optional[Dict[float, str]] = None,
        test_symbols: Optional[Dict[str, str]] = None,
        statistic_symbols: Optional[List[str]] = None,
        include_effect_size: bool = True,
        include_confidence_intervals: bool = True,
        custom_column_names: Optional[Dict[str, str]] = None,
        table_caption: str = "",
        table_label: str = "",
        scientific_notation_threshold: float = 0.001,
        show_test_name: bool = True,
        show_degrees_of_freedom: bool = True,
        show_test_statistic: bool = True,
        show_p_value: bool = True,
        group_by_test: bool = False,
        sort_by_p_value: bool = False,
        separate_group_columns: bool = False,
        include_group_values: bool = False,
        show_category_tests: bool = False,
        use_table_sections: bool = False,
        significance_in_p_value: bool = False,
        superscript_tests: bool = True,
        include_footer: bool = True,
        return_dict: bool = False
    ) -> Union[pl.DataFrame, str, Dict[str, Any]]:
        """
        Generate manuscript-quality statistical tables with professional formatting.
        
        This method creates publication-ready tables with proper significance annotation,
        formatted statistics, and support for multiple output formats including LaTeX,
        Markdown, HTML, and DataFrame formats.
        
        NEW: As a DataFrame extension method, automatically uses the DataFrame as source
        data and can generate statistics internally with configurable symbols.
        
        Parameters:
        -----------
        results : List[TestResult], optional
            Statistical test results to format. If None, the DataFrame and group_column
            will be used to generate statistics automatically.
            
        group_column : str, optional  
            Column name containing group/cohort information for comparison.
            Required when results is None.
            
        variable_columns : List[str], optional
            List of variable column names to analyze. If None, will analyze all
            columns except the group_column.
            
        # Auto-test Parameters (used when source_data is provided):
        alpha : float, default=0.05
            Significance level for statistical tests and recommendations
            
        force_parametric : bool, default=False
            Force parametric tests even if assumptions aren't fully met
            
        standardization_dicts : Dict[str, Dict[str, str]], optional
            Dictionary mapping column names to standardization dictionaries.
            Each standardization dict maps original values to standardized values.
            Example: {'Sex': {'M': 'Male', 'F': 'Female'}, 'Ethnicity': {'Hispanic or Latino': 'Hispanic'}}
            
        base_groups : Dict[str, str], optional
            Dictionary mapping column names to base group values for comparisons.
            Example: {'treatment': 'control', 'group': 'baseline'}
            
        # Formatting Parameters:
        format : str, default="dataframe"
            Output format: "dataframe", "latex", "markdown", "html"
            
        p_value_precision : int, default=4
            Number of decimal places for p-values
            
        statistic_precision : int, default=3
            Number of decimal places for test statistics
            
        significance_symbols : Dict[float, str], optional
            Custom significance symbols mapping p-value thresholds to symbols.
            Default: {0.001: "***", 0.01: "**", 0.05: "*", 1.0: ""}
            
        test_symbols : Dict[str, str], optional
            Custom test type symbols mapping test names to symbols.
            Default: {"chi2": "ᵃ", "kruskal_wallis": "ᵇ", "anova": "ᶜ", "t_test_ind": "ᵈ", "fisher_exact": "ᵉ"}
            Uses letters to distinguish from statistic symbols (numbers) and significance symbols (*, **, ***)
            
        statistic_symbols : List[str], optional
            Custom symbols for statistics (residuals, etc.) in order of usage.
            Default: ["¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]
            Uses numbers to distinguish from test symbols (letters) and significance symbols (*, **, ***)
            
        include_effect_size : bool, default=True
            Whether to include effect size measures when available
            
        include_confidence_intervals : bool, default=True
            Whether to include confidence intervals when available
            
        custom_column_names : Dict[str, str], optional
            Custom column names mapping, e.g., {"test_name": "Test", "p_value": "P-value"}
            
        table_caption : str, default=""
            Table caption for LaTeX/HTML formats
            
        table_label : str, default=""
            Table label for LaTeX cross-referencing
            
        scientific_notation_threshold : float, default=0.001
            P-values below this threshold will be shown in scientific notation
            
        show_test_name : bool, default=True
            Whether to include test name column
            
        show_degrees_of_freedom : bool, default=True
            Whether to include degrees of freedom when available
            
        show_test_statistic : bool, default=True
            Whether to include test statistic column (e.g., Chi-square, t-statistic)
            
        show_p_value : bool, default=True
            Whether to include p-value column
            
        group_by_test : bool, default=False
            Whether to group results by test type
            
        sort_by_p_value : bool, default=False
            Whether to sort results by p-value
            
        separate_group_columns : bool, default=False
            Whether to split comparisons into separate base and comparison group columns
            for better readability in scientific manuscripts
            
        include_group_values : bool, default=False
            Whether to include actual group values (means) in the table.
            Only works when separate_group_columns=True and values are available
            
        show_category_tests : bool, default=False
            Whether to show statistical tests for individual category levels.
            When False, category levels show descriptive statistics only (standard for demographics).
            When True, shows post-hoc tests or standardized residuals if available.
            
        use_table_sections : bool, default=False
            Whether to use proper table sectioning with dividers between variable groups.
            When True, adds horizontal rules and better spacing for LaTeX/Markdown formats.
            
        significance_in_p_value : bool, default=False
            Whether to combine significance symbols with p-values in the same cell
            (scientific manuscript style). When True, p-values appear as "0.023*"
            instead of separate significance columns
            
        superscript_tests : bool, default=True
            Whether to show test types as superscripts in p-value column.
            When True, p-values show as "0.3819²" (consistent superscripts on ALL p-values).
            When False, p-values are clean numbers and test types appear in dedicated "Test" column.
            
        include_footer : bool, default=True
            Whether to include a footer/legend explaining significance symbols and
            statistical methods. Only applies to LaTeX, Markdown, and HTML formats.
            
        return_dict : bool, default=False
            When True, returns a dictionary containing both the formatted table and
            source statistics for post-hoc analyses:
            {
                'formatted_table': <table_output>,
                'source_statistics': <dict_of_raw_stats>,
                'metadata': <formatting_params>
            }
            
        Returns:
        --------
        Union[pl.DataFrame, str, Dict[str, Any]]
            - When return_dict=False: Formatted table as DataFrame or string (for LaTeX/Markdown/HTML)  
            - When return_dict=True: Dictionary with formatted table, source statistics, and metadata
            
        Examples:
        ---------
        >>> # NEW: DataFrame extension method (recommended!)
        >>> table_dict = demographics_df.stats_tests.manuscript_table(
        ...     group_column='cohort',
        ...     variable_columns=['Sex', 'Age', 'Ethnicity'],
        ...     standardization_dicts={
        ...         'Sex': {'M': 'Male', 'F': 'Female', 'male': 'Male', 'female': 'Female'},
        ...         'Ethnicity': {'Hispanic or Latino': 'Hispanic', 'Not Hispanic or Latino': 'Non-Hispanic'}
        ...     },
        ...     format="markdown",
        ...     return_dict=True
        ... )
        >>> 
        >>> # Access formatted table
        >>> display(Markdown(table_dict['formatted_table']))
        >>> 
        >>> # Access source statistics for additional analyses
        >>> raw_stats = table_dict['source_statistics']
        
        >>> # Legacy: Pre-computed results still work
        >>> results = df.stats_tests.t_test([("A", "B"), ("A", "C")])
        >>> table = df.stats_tests.manuscript_table(results=results)
        >>> residuals = raw_stats['Sex']['category_residuals']
        
        >>> # LaTeX table for publication with custom base groups
        >>> latex_table = PolarsStatsTests.manuscript_table(
        ...     source_data=df,
        ...     group_column='treatment_group',
        ...     base_groups={'treatment_group': 'control'},
        ...     format="latex",
        ...     table_caption="Statistical comparisons between treatment groups",
        ...     superscript_tests=False  # Clean p-values + dedicated Test column
        ... )
        """
        
        # Set default significance symbols
        if significance_symbols is None:
            significance_symbols = {0.001: "***", 0.01: "**", 0.05: "*", 1.0: ""}
        
        # Set default test symbols (letters for test types)
        if test_symbols is None:
            test_symbols = {
                "chi2": "ᵃ",
                "kruskal_wallis": "ᵇ", 
                "anova": "ᶜ",
                "f_oneway": "ᶜ",  # Same as anova
                "t_test_ind": "ᵈ",
                "welch_t_test": "ᵈ",  # Same as t_test
                "fisher_exact": "ᵉ",
                "tukey_hsd": "ᶠ"
            }
            
        # Set default statistic symbols (numbers for statistics like residuals)
        if statistic_symbols is None:
            statistic_symbols = ["¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹", "¹⁰"]
        
        # 🔥 NEW: Handle direct source data input 
        source_statistics = {}
        if results is None:
            if group_column is None:
                raise ValueError("group_column must be provided when results is None")
            
            # Determine variables to analyze
            if variable_columns is None:
                # Analyze all columns except the group column
                variable_columns = [col for col in self.columns if col != group_column]
            
            # Generate statistics using auto_test with all parameters on self
            results = self.auto_test(
                value_col=variable_columns,
                    group_col=group_column,
                    alpha=alpha,
                    force_parametric=force_parametric,
                    standardization_dicts=standardization_dicts,
                    base_groups=base_groups
                )
                
            # Store source statistics for return_dict
            for i, result in enumerate(results):
                var_name = variable_columns[i] if i < len(variable_columns) else f"Variable_{i}"
                
                # 🔥 CRITICAL: Ensure analyzed_column is set for variable name display
                if not result.additional_info:
                    result.additional_info = {}
                result.additional_info['analyzed_column'] = var_name
                result.additional_info['source_data'] = self._df  # Set immediately for continuous vars
                result.additional_info['group_column'] = group_column  # Set immediately for continuous vars
                
                source_statistics[var_name] = {
                    'test_result': result,
                    'test_name': result.test_name,
                    'statistic': result.statistic,
                    'p_value': result.p_value,
                    'degrees_of_freedom': result.degrees_of_freedom,
                        'source_data': self._df,
                        'group_column': group_column,
                        'variable_column': var_name,
                        'additional_info': result.additional_info or {}
                    }
                
            # Enrich all results with source data (eliminates manual injection!)
            for result in results:
                if not (result.additional_info and 'category_statistics' in result.additional_info):
                    if not result.additional_info:
                        result.additional_info = {}
                    result.additional_info['source_data'] = self._df
                    result.additional_info['group_column'] = group_column
                    # 🔥 CRITICAL: Ensure analyzed_column is set for all results  
                    if 'analyzed_column' not in result.additional_info:
                        # Find the corresponding variable name
                        for i, res in enumerate(results):
                            if res == result:
                                result.additional_info['analyzed_column'] = variable_columns[i] if i < len(variable_columns) else f"Variable_{i}"
                                break        # Validate inputs
        if results is None:
            raise ValueError("Either 'results' or dataframe extension with 'group_column' must be provided")
        
        # Default column names
        default_column_names = {
            "test_name": "Test",
            "variable_name": "Variable",  # New column for categorical analysis
            "comparison": "Comparison",
            "base_group": "Base Group",
            "comparison_group": "Comparison Group", 
            "base_value": "Base Value",
            "comparison_value": "Comparison Value",
            "statistic": "Statistic",
            "p_value": "P-value",
            "p_value_corrected": "Corrected P-value",
            "degrees_of_freedom": "df",
            "effect_size": "Effect Size",
            "confidence_interval": "95% CI",
            "significance": "Sig."
        }
        
        if custom_column_names:
            default_column_names.update(custom_column_names)
            
        # Sort results if requested
        if sort_by_p_value:
            results = sorted(results, key=lambda x: x.p_value if not np.isnan(x.p_value) else float('inf'))
        
        # Group results by test type if requested
        if group_by_test:
            results = PolarsStatsTests._group_results_by_test(results)
        
        # Convert results to structured data
        table_data = []
        for result in results:
            # 🔥 NEW: For categorical tests, create multiple rows - one overall + one per category
            if (result.additional_info and 'category_statistics' in result.additional_info and 
                include_group_values and separate_group_columns):
                
                # First row: Overall test (BOLD)
                overall_row = PolarsStatsTests._create_overall_test_row(
                    result, show_test_name, show_degrees_of_freedom, 
                    p_value_precision, statistic_precision, scientific_notation_threshold,
                    significance_symbols, significance_in_p_value, format, superscript_tests
                )
                table_data.append(overall_row)
                
                # Additional rows: One per category level
                category_rows = PolarsStatsTests._create_category_level_rows(
                    result, p_value_precision, scientific_notation_threshold,
                    significance_symbols, significance_in_p_value, format, show_category_tests, statistic_precision, 
                    show_degrees_of_freedom, superscript_tests
                )
                if category_rows:  # Safely extend only if not None or empty
                    table_data.extend(category_rows)
                
            else:
                # 🔥 NEW: Handle continuous variables in unified format with cohort columns
                if separate_group_columns and include_group_values:
                    # Create unified continuous variable row with cohort columns using generate_smart_stats
                    row = PolarsStatsTests._create_continuous_variable_row_with_smart_stats(
                        result, show_test_name, show_degrees_of_freedom, 
                        p_value_precision, statistic_precision, scientific_notation_threshold,
                        significance_symbols, significance_in_p_value, format, superscript_tests
                    )
                else:
                    # Standard single-row format for non-categorical tests (legacy)
                    row = {}
                    
                    # Basic columns
                    if show_test_name:
                        row["test_name"] = PolarsStatsTests._format_test_name(result.test_name)
                    
                    # Handle comparison formatting based on separate_group_columns option
                    if separate_group_columns and result.comparison:
                        # Try to parse comparison into base and comparison groups
                        base_group, comp_group = PolarsStatsTests._parse_comparison(result.comparison)
                        row["base_group"] = base_group
                        row["comparison_group"] = comp_group
                        
                        # Legacy: Include base/comparison values for backward compatibility
                        base_val, comp_val = PolarsStatsTests._extract_group_values_static(result, base_group, comp_group)
                        if base_val is not None:
                            row["base_value"] = base_val
                        if comp_val is not None:
                            row["comparison_value"] = comp_val
                    else:
                        row["comparison"] = result.comparison or "N/A"
                    
                    row["statistic"] = PolarsStatsTests._format_statistic(result.statistic, statistic_precision)
                
                # P-value formatting with significance
                p_val_formatted, sig_symbol = PolarsStatsTests._format_p_value(
                    result.p_value, p_value_precision, scientific_notation_threshold, significance_symbols
                )
                
                # Combine significance with p-value if requested (scientific manuscript style)
                if significance_in_p_value:
                    sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                    row["p_value"] = f"{p_val_formatted}{sig_formatted}"
                else:
                    row["p_value"] = p_val_formatted
                    row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                
                # Corrected p-value if available
                if hasattr(result, 'p_value_corrected') and result.p_value_corrected is not None:
                    p_corr_formatted, sig_corr_symbol = PolarsStatsTests._format_p_value(
                        result.p_value_corrected, p_value_precision, scientific_notation_threshold, significance_symbols
                    )
                    if significance_in_p_value:
                        sig_corr_formatted = PolarsStatsTests._format_significance_superscript(sig_corr_symbol, format)
                        row["p_value_corrected"] = f"{p_corr_formatted}{sig_corr_formatted}"
                    else:
                        row["p_value_corrected"] = p_corr_formatted
                        row["corrected_significance"] = PolarsStatsTests._format_significance_superscript(sig_corr_symbol, format)
                
                # Degrees of freedom
                if show_degrees_of_freedom and result.degrees_of_freedom is not None:
                    row["degrees_of_freedom"] = str(result.degrees_of_freedom)
                
                # Effect size and confidence intervals from additional_info
                if include_effect_size and result.additional_info:
                    effect_size = PolarsStatsTests._extract_effect_size(result)
                    if effect_size:
                        row["effect_size"] = effect_size
                        
                if include_confidence_intervals and result.additional_info:
                    ci = PolarsStatsTests._extract_confidence_interval(result)
                    if ci:
                        row["confidence_interval"] = ci
                
                table_data.append(row)
        
        # Create DataFrame
        df_table = pl.DataFrame(table_data)
        
        # Rename columns
        column_mapping = {}
        for old_name in df_table.columns:
            if old_name in default_column_names:
                column_mapping[old_name] = default_column_names[old_name]
            elif old_name.startswith("cohort_"):
                # Rename cohort columns to standardized "Type Cohort" format
                clean_name = old_name.replace("cohort_", "").replace("_", " ").title()
                
                # Standardize to "Type Cohort" format
                if not clean_name.endswith(" Cohort"):
                    clean_name = f"{clean_name} Cohort"
                
                # Handle special cases to avoid conflicts
                if clean_name in ["Test Cohort"]:
                    # This is fine - "Test Cohort" won't conflict with "Test" column
                    pass
                
                column_mapping[old_name] = clean_name
            elif old_name == "all_cohort_values":
                # Special column for overall statistics across all cohorts
                column_mapping[old_name] = "All"

        if column_mapping:
            df_table = df_table.rename(column_mapping)
        
        # 🔥 CRITICAL FIX: Ensure Variable column comes FIRST
        columns = df_table.columns
        variable_col = None
        
        # Find the variable column (could be "Variable" or custom name)
        for col in columns:
            if col in ["Variable", default_column_names.get("variable_name", "Variable")] or "Variable" in col:
                variable_col = col
                break
        
        if variable_col and variable_col != columns[0]:
            # Reorder columns to put Variable first
            other_cols = [c for c in columns if c != variable_col]
            new_order = [variable_col] + other_cols
            df_table = df_table.select(new_order)
        
        # 🔥 Generate formatted output based on format
        if format == "dataframe":
            formatted_output = df_table
        elif format == "latex":
            footer = PolarsStatsTests._generate_footer(results, significance_symbols, format) if include_footer else ""
            formatted_output = PolarsStatsTests._to_latex_table(df_table, table_caption, table_label, footer)
        elif format == "markdown":
            footer = PolarsStatsTests._generate_footer(results, significance_symbols, format) if include_footer else ""
            formatted_output = PolarsStatsTests._to_markdown_table(df_table, footer)
        elif format == "html":
            footer = PolarsStatsTests._generate_footer(results, significance_symbols, format) if include_footer else ""
            formatted_output = PolarsStatsTests._to_html_table(df_table, table_caption, footer)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # 🔥 NEW: Return dictionary with formatted table + source statistics
        if return_dict:
            # Extract detailed source statistics from results for post-hoc analysis
            if not source_statistics:  # If not populated from direct data input
                for result in results:
                    var_name = result.additional_info.get('analyzed_column', 'Unknown') if result.additional_info else 'Unknown'
                    source_statistics[var_name] = {
                        'test_result': result,
                        'test_name': result.test_name,
                        'statistic': result.statistic,
                        'p_value': result.p_value,
                        'degrees_of_freedom': result.degrees_of_freedom,
                        'additional_info': result.additional_info or {}
                    }
                    
                    # Add category-level statistics if available
                    if result.additional_info and 'category_statistics' in result.additional_info:
                        source_statistics[var_name]['category_statistics'] = result.additional_info['category_statistics']
            
            return {
                'formatted_table': formatted_output,
                'source_statistics': source_statistics,
                'metadata': {
                    'format': format,
                    'table_caption': table_caption,
                    'table_label': table_label,
                    'formatting_params': {
                        'p_value_precision': p_value_precision,
                        'statistic_precision': statistic_precision,
                        'significance_symbols': significance_symbols,
                        'superscript_tests': superscript_tests,
                        'show_category_tests': show_category_tests,
                        'separate_group_columns': separate_group_columns,
                        'include_group_values': include_group_values
                    }
                }
            }
        
        # Legacy return: just the formatted output
        return formatted_output
    
    @staticmethod
    def _group_results_by_test(results: List[TestResult]) -> List[TestResult]:
        """Group results by test type, preserving order within groups."""
        from collections import defaultdict
        
        # Group results by test name
        grouped = defaultdict(list)
        for result in results:
            grouped[result.test_name].append(result)
        
        # Flatten back to list, maintaining group structure
        grouped_results = []
        for test_name in sorted(grouped.keys()):
            grouped_results.extend(grouped[test_name])
            
        return grouped_results
    
    @staticmethod
    def _format_test_name(test_name: str) -> str:
        """Format test name for publication."""
        name_mapping = {
            "chi2": "χ² test",
            "fisher_exact": "Fisher's exact test",
            "t_test_ind": "Independent t-test",
            "t_test_paired": "Paired t-test", 
            "t_test_1samp": "One-sample t-test",
            "welch_t_test": "Welch's t-test",
            "anova": "One-way ANOVA",
            "kruskal_wallis": "Kruskal-Wallis H test",
            "tukey_hsd": "Tukey's HSD",
            "shapiro_wilk": "Shapiro-Wilk test",
            "anderson_darling": "Anderson-Darling test",
            "dagostino_pearson": "D'Agostino-Pearson test",
            "kolmogorov_smirnov": "Kolmogorov-Smirnov test"
        }
        return name_mapping.get(test_name, test_name.replace('_', ' ').title())
    
    @staticmethod
    def _format_statistic(statistic: float, precision: int) -> str:
        """Format test statistic with appropriate precision."""
        if np.isnan(statistic):
            return "N/A"
        return f"{statistic:.{precision}f}"
    
    @staticmethod
    def _format_p_value(
        p_value: float, 
        precision: int, 
        sci_threshold: float,
        significance_symbols: Dict[float, str]
    ) -> tuple[str, str]:
        """Format p-value and determine significance symbol."""
        if np.isnan(p_value):
            return "N/A", ""
        
        # Determine significance symbol
        sig_symbol = ""
        for threshold in sorted(significance_symbols.keys()):
            if p_value <= threshold:
                sig_symbol = significance_symbols[threshold]
                break
        
        # Format p-value
        if p_value < sci_threshold:
            formatted = f"{p_value:.2e}"
        elif p_value < 0.001:
            formatted = "< 0.001"
        else:
            formatted = f"{p_value:.{precision}f}"
            
        return formatted, sig_symbol
    
    @staticmethod
    def _extract_effect_size(result: TestResult) -> Optional[str]:
        """Extract effect size from additional_info."""
        info = result.additional_info
        if not info:
            return None
            
        # Look for common effect size measures
        if "cohens_d" in info:
            return f"d = {info['cohens_d']:.3f}"
        elif "eta_squared" in info:
            return f"η² = {info['eta_squared']:.3f}"
        elif "odds_ratio" in info:
            return f"OR = {info['odds_ratio']:.3f}"
        elif "effect_size" in info:
            return f"{info['effect_size']:.3f}"
        elif "mean_diff" in info:
            return f"Δ = {info['mean_diff']:.3f}"
            
        return None
    
    @staticmethod
    def _extract_confidence_interval(result: TestResult) -> Optional[str]:
        """Extract confidence interval from additional_info."""
        info = result.additional_info
        if not info:
            return None
            
        if "confidence_interval" in info:
            ci = info["confidence_interval"]
            if isinstance(ci, (list, tuple)) and len(ci) == 2:
                return f"[{ci[0]:.3f}, {ci[1]:.3f}]"
            
        return None
    
    @staticmethod
    def _to_latex_table(df: pl.DataFrame, caption: str, label: str, footer: str = "") -> str:
        """Convert DataFrame to LaTeX table."""
        # Start table
        n_cols = len(df.columns)
        col_spec = "l" + "c" * (n_cols - 1)  # Left align first column, center others
        
        latex = f"""\\begin{{table}}[htbp]
\\centering"""
        
        if caption:
            latex += f"\n\\caption{{{caption}}}"
            
        if label:
            latex += f"\n\\label{{{label}}}"
            
        latex += f"""
\\begin{{tabular}}{{{col_spec}}}
\\toprule
"""
        
        # Header
        headers = [col.replace('_', '\\_') for col in df.columns]
        latex += " & ".join(headers) + " \\\\\n"
        latex += "\\midrule\n"
        
        # Data rows
        for row in df.iter_rows():
            formatted_row = []
            for val in row:
                if val is None:
                    formatted_row.append("--")
                else:
                    # Escape special LaTeX characters
                    val_str = str(val).replace('_', '\\_').replace('%', '\\%').replace('<', '$<$')
                    formatted_row.append(val_str)
            latex += " & ".join(formatted_row) + " \\\\\n"
        
        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        
        # Add footer if provided
        if footer:
            # Format footer for LaTeX - each line as a note
            footer_lines = footer.split('\n')
            for i, line in enumerate(footer_lines, 1):
                latex += f"\\begin{{tablenotes}}[para]\n"
                latex += f"\\small {line}\n" 
                latex += f"\\end{{tablenotes}}\n"
        
        latex += "\\end{table}"
        
        return latex
    
    @staticmethod
    def _to_markdown_table(df: pl.DataFrame, footer: str = "") -> str:
        """Convert DataFrame to Markdown table."""
        # Get column names and data
        columns = df.columns
        rows = df.iter_rows()
        
        # Header
        md = "| " + " | ".join(columns) + " |\n"
        md += "|" + "|".join([" --- "] * len(columns)) + "|\n"
        
        # Data rows
        for row in rows:
            formatted_row = []
            for val in row:
                if val is None:
                    formatted_row.append("--")
                else:
                    formatted_row.append(str(val))
            md += "| " + " | ".join(formatted_row) + " |\n"
        
        # Add footer if provided
        if footer:
            md += "\n" + footer
            
        return md
    
    @staticmethod
    def _to_html_table(df: pl.DataFrame, caption: str, footer: str = "") -> str:
        """Convert DataFrame to HTML table."""
        html = '<table class="statistical-results">\n'
        
        if caption:
            html += f'  <caption>{caption}</caption>\n'
        
        # Header
        html += '  <thead>\n    <tr>\n'
        for col in df.columns:
            html += f'      <th>{col}</th>\n'
        html += '    </tr>\n  </thead>\n'
        
        # Body
        html += '  <tbody>\n'
        for row in df.iter_rows():
            html += '    <tr>\n'
            for val in row:
                if val is None:
                    html += '      <td>--</td>\n'
                else:
                    html += f'      <td>{val}</td>\n'
            html += '    </tr>\n'
        html += '  </tbody>\n'
        html += '</table>'
        
        # Add footer if provided
        if footer:
            html += '\n<div class="table-footer">\n'
            footer_lines = footer.split('\n')
            for line in footer_lines:
                html += f'<p class="table-note">{line}</p>\n'
            html += '</div>'
        
        return html

    @staticmethod
    def _parse_comparison(comparison: str) -> tuple[str, str]:
        """Parse comparison string into base and comparison groups."""
        # Handle different comparison formats
        if " vs " in comparison:
            parts = comparison.split(" vs ", 1)
            return parts[0].strip(), parts[1].strip()
        elif " v " in comparison:
            parts = comparison.split(" v ", 1)
            return parts[0].strip(), parts[1].strip()
        elif "=" in comparison and "μ" in comparison:
            # One-sample tests like "group_a vs μ=100"
            parts = comparison.split(" vs ", 1)
            return parts[0].strip(), parts[1].strip()
        else:
            # Fallback - return the whole string as base, empty as comparison
            return comparison, ""
    
    @staticmethod
    def _extract_group_values_static(result: TestResult, base_group: str, comp_group: str) -> tuple[str | None, str | None]:
        """Extract group descriptive statistics from result additional_info only (static version)."""
        base_val = None
        comp_val = None
        
        if result.additional_info:
            # Look for pre-computed descriptive statistics
            if "group_descriptives" in result.additional_info:
                desc = result.additional_info["group_descriptives"]
                if isinstance(desc, dict):
                    base_val = desc.get(base_group)
                    comp_val = desc.get(comp_group)
                    return base_val, comp_val
            
            # Look for group means and stds (for parametric tests)
            if "group_means" in result.additional_info and "group_stds" in result.additional_info:
                means = result.additional_info["group_means"]
                stds = result.additional_info["group_stds"]
                if isinstance(means, dict) and isinstance(stds, dict):
                    base_mean = means.get(base_group)
                    comp_mean = means.get(comp_group)
                    base_std = stds.get(base_group)
                    comp_std = stds.get(comp_group)
                    
                    if base_mean is not None and base_std is not None:
                        base_val = f"{base_mean:.2f} ({base_std:.2f})"
                    if comp_mean is not None and comp_std is not None:
                        comp_val = f"{comp_mean:.2f} ({comp_std:.2f})"
                    return base_val, comp_val
                    
            # Look for group medians (for non-parametric tests)
            if "group_medians" in result.additional_info:
                medians = result.additional_info["group_medians"]
                if isinstance(medians, dict):
                    base_median = medians.get(base_group)
                    comp_median = medians.get(comp_group)
                    
                    if base_median is not None:
                        base_val = f"{base_median:.2f}"
                    if comp_median is not None:
                        comp_val = f"{comp_median:.2f}"
                    return base_val, comp_val
            
            # 🔥 NEW: Look for categorical data in category_statistics (for chi-square tests)
            if "category_statistics" in result.additional_info:
                category_stats = result.additional_info["category_statistics"]
                if isinstance(category_stats, dict):
                    # For categorical tests, show the category distribution across groups
                    all_categories = list(category_stats.keys())
                    
                    # Create summary for base_group
                    base_parts = []
                    comp_parts = []
                    
                    for category in all_categories:
                        cat_data = category_stats[category]
                        if 'counts_by_group' in cat_data and 'percentages_by_group' in cat_data:
                            counts = cat_data['counts_by_group']
                            percentages = cat_data['percentages_by_group']
                            
                            if base_group in counts:
                                count = counts[base_group]
                                pct = percentages[base_group]
                                base_parts.append(f"{category}: {count} ({pct:.1f}%)")
                            
                            if comp_group in counts:
                                count = counts[comp_group]
                                pct = percentages[comp_group]
                                comp_parts.append(f"{category}: {count} ({pct:.1f}%)")
                    
                    if base_parts:
                        base_val = "; ".join(base_parts)
                    if comp_parts:
                        comp_val = "; ".join(comp_parts)
                    
                    return base_val, comp_val
        
        # For static version, we can't compute from DataFrame, so return None values
        return base_val, comp_val

    @staticmethod
    def _extract_cohort_values_for_manuscript(result: TestResult) -> dict:
        """Extract cohort values formatted for manuscript table columns."""
        cohort_values = {}
        
        if not result.additional_info:
            return cohort_values
            
        # Handle categorical data from category_statistics
        if "category_statistics" in result.additional_info:
            category_stats = result.additional_info["category_statistics"]
            if isinstance(category_stats, dict):
                # Get all cohorts by looking at the first category
                first_category = next(iter(category_stats.values()))
                if 'counts_by_group' in first_category:
                    all_cohorts = list(first_category['counts_by_group'].keys())
                    
                    # For each cohort, create a summary of all categories
                    for cohort in all_cohorts:
                        cohort_parts = []
                        for category, cat_data in category_stats.items():
                            if 'counts_by_group' in cat_data and 'percentages_by_group' in cat_data:
                                count = cat_data['counts_by_group'].get(cohort, 0)
                                pct = cat_data['percentages_by_group'].get(cohort, 0)
                                cohort_parts.append(f"{category}: {count} ({pct:.1f}%)")
                        
                        if cohort_parts:
                            cohort_values[cohort] = "; ".join(cohort_parts)
                            
        # Handle numeric data from group_means/medians
        elif "group_means" in result.additional_info:
            means = result.additional_info["group_means"]
            stds = result.additional_info.get("group_stds", {})
            
            for cohort, mean_val in means.items():
                if cohort in stds:
                    std_val = stds[cohort]
                    cohort_values[cohort] = f"{mean_val:.2f} ± {std_val:.2f}"
                else:
                    cohort_values[cohort] = f"{mean_val:.2f}"
                    
        elif "group_medians" in result.additional_info:
            medians = result.additional_info["group_medians"]
            
            for cohort, median_val in medians.items():
                cohort_values[cohort] = f"{median_val:.2f}"
        
        return cohort_values

    @staticmethod
    def _create_overall_test_row(result: TestResult, show_test_name: bool, show_degrees_of_freedom: bool,
                                p_value_precision: int, statistic_precision: int, scientific_notation_threshold: float,
                                significance_symbols: dict, significance_in_p_value: bool, format: str, 
                                superscript_tests: bool = True) -> dict:
        """Create the overall test row (bold header) for categorical analysis."""
        row = {}
        
        # Get analyzed column name - this is CRITICAL for proper variable display
        analyzed_col = result.additional_info.get('analyzed_column', 'Variable') if result.additional_info else 'Variable'
        
        # 🔥 ALWAYS set the variable name as the FIRST item in the row
        row["variable_name"] = f"**{analyzed_col}**"
        
        # 🔥 Get test superscript for p-value column (always, not just when show_test_name)
        test_superscript = ""
        if result.test_name == "chi2":
            test_superscript = "²"  # Chi-square superscript
        elif result.test_name == "kruskal_wallis":
            test_superscript = "ᵏʷ"  # Kruskal-Wallis superscript
        elif result.test_name == "anova":
            test_superscript = "ᶠ"   # ANOVA F-test superscript
        elif result.test_name.startswith("t_test"):
            test_superscript = "ᵗ"   # t-test superscript
            
        # Add "All" column for overall test (show total sample size if available)
        if result.additional_info and 'category_statistics' in result.additional_info:
            category_stats = result.additional_info['category_statistics']
            # Calculate total sample size across all categories and cohorts
            total_n = 0
            for cat_data in category_stats.values():
                if 'counts_by_group' in cat_data:
                    total_n += sum(cat_data['counts_by_group'].values())
            
            if total_n > 0:
                row["all_cohort_values"] = f"N = {total_n}"
            else:
                row["all_cohort_values"] = "—"
        else:
            row["all_cohort_values"] = "—"  # Different column name to avoid conflicts
            
        # 🔥 FIX 1: Add cohort columns with N for each group (not empty strings)
        if result.additional_info and 'category_statistics' in result.additional_info:
            category_stats = result.additional_info['category_statistics']
            first_category = next(iter(category_stats.values()))
            if 'counts_by_group' in first_category:
                all_cohorts = list(first_category['counts_by_group'].keys())
                
                # Calculate N for each cohort across all categories
                cohort_totals = {}
                for cat_data in category_stats.values():
                    if 'counts_by_group' in cat_data:
                        for cohort, count in cat_data['counts_by_group'].items():
                            cohort_totals[cohort] = cohort_totals.get(cohort, 0) + count
                
                # Add cohort columns with N values
                for cohort in all_cohorts:
                    clean_cohort_name = cohort.replace("Wearable_Ward_Monitoring_", "")
                    safe_column_name = f"cohort_{clean_cohort_name.replace('_', '_')}"
                    
                    # Show N for each cohort in the overall row
                    cohort_n = cohort_totals.get(cohort, 0)
                    row[safe_column_name] = f"N = {cohort_n}"
            
        # Overall test statistics
        row["statistic"] = PolarsStatsTests._format_statistic(result.statistic, statistic_precision)
        
        # P-value formatting with significance
        p_val_formatted, sig_symbol = PolarsStatsTests._format_p_value(
            result.p_value, p_value_precision, scientific_notation_threshold, significance_symbols
        )
        
        if superscript_tests:
            # Option 1: Consistent superscripts on ALL p-values
            if significance_in_p_value:
                sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                row["p_value"] = f"{p_val_formatted}{sig_formatted}{test_superscript}"
            else:
                row["p_value"] = f"{p_val_formatted}{test_superscript}"
                row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
        else:
            # Option 2: Clean p-values + dedicated Test column
            if significance_in_p_value:
                sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                row["p_value"] = f"{p_val_formatted}{sig_formatted}"
            else:
                row["p_value"] = p_val_formatted
                row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
            
            # Add dedicated Test column
            test_name_map = {
                "chi2": "Chi-square",
                "kruskal_wallis": "Kruskal-Wallis", 
                "anova": "ANOVA",
                "t_test": "t-test",
                "t_test_independent": "t-test",
                "t_test_paired": "Paired t-test"
            }
            row["test_type"] = test_name_map.get(result.test_name, result.test_name.replace("_", " ").title())
        
        # Degrees of freedom
        if show_degrees_of_freedom and result.degrees_of_freedom is not None:
            row["degrees_of_freedom"] = str(result.degrees_of_freedom)
            
        return row

    @staticmethod
    def _create_category_level_rows(result: TestResult, p_value_precision: int, scientific_notation_threshold: float,
                                   significance_symbols: dict, significance_in_p_value: bool, format: str, 
                                   show_category_tests: bool = False, statistic_precision: int = 3, 
                                   show_degrees_of_freedom: bool = True, superscript_tests: bool = True) -> list:
        """Create individual rows for each category level with cohort values."""
        rows = []
        
        if not result.additional_info or 'category_statistics' not in result.additional_info:
            return rows
            
        category_stats = result.additional_info['category_statistics']
        
        # Get base group for reference
        base_group = result.additional_info.get('base_group')
        
        # Get all cohorts from the first category
        first_category = next(iter(category_stats.values()))
        if 'counts_by_group' not in first_category:
            return rows
            
        all_cohorts = list(first_category['counts_by_group'].keys())
        
        # Create a row for each category level
        for category, cat_stats in category_stats.items():
            if 'error' in cat_stats:
                continue
                
            row = {}
            
            # 🔥 Category name with proper 5-space indentation for visual hierarchy
            row["variable_name"] = f"     {category}"
            
            # Add "All" column with overall statistics across all cohorts
            total_count = sum(cat_stats['counts_by_group'].values())
            
            # Calculate CORRECT overall percentage - this category as % of total sample
            grand_total = 0
            for all_cat_stats in category_stats.values():
                if 'counts_by_group' in all_cat_stats:
                    grand_total += sum(all_cat_stats['counts_by_group'].values())
            
            if grand_total > 0:
                overall_pct = (total_count / grand_total) * 100
                row["all_cohort_values"] = f"{total_count} ({overall_pct:.1f}%)"
            else:
                row["all_cohort_values"] = f"{total_count} (—%)"
            
            # 🔥 FIX 1: Add individual cohort columns with N and values (n, %)
            for cohort in all_cohorts:
                count = cat_stats['counts_by_group'].get(cohort, 0)
                
                # Calculate cohort total to get correct percentage within cohort
                cohort_total = 0
                for all_cat_stats in category_stats.values():
                    if 'counts_by_group' in all_cat_stats:
                        cohort_total += all_cat_stats['counts_by_group'].get(cohort, 0)
                
                if cohort_total > 0:
                    pct = (count / cohort_total) * 100
                else:
                    pct = 0
                
                # Clean cohort name for column (will be renamed to "Type Cohort" format later)
                clean_cohort_name = cohort.replace("Wearable_Ward_Monitoring_", "")
                safe_column_name = f"cohort_{clean_cohort_name.replace('_', '_')}"
                
                # 🔥 FIX: Format as "n (percentage%)" with cohort N displayed
                row[safe_column_name] = f"{count} ({pct:.1f}%)"
                
                # Mark reference group
                if base_group and category == base_group:
                    row[safe_column_name] += " (ref)"
            
            # 🔥 FIX: Individual category levels should show proper statistical analysis
            # Control whether to show tests for individual categories
            if show_category_tests:
                # Show individual statistical tests if requested and available
                if 'standardized_residual' in cat_stats:
                    # Show standardized residual if available (indicates contribution to chi-square)
                    residual = cat_stats['standardized_residual']
                    
                    # Format based on output format - use clean superscript
                    if format == 'html':
                        row["statistic"] = f"{residual:.3f}¹" if residual is not None else "—"
                    else:
                        row["statistic"] = f"{residual:.3f}¹" if residual is not None else "—"
                    
                    # 🔥 FIX 3: Show ACTUAL p-values, not "n.s."
                    # Calculate p-value from standardized residual (two-tailed test)
                    if residual is not None:
                        import scipy.stats as stats
                        p_value_residual = 2 * (1 - stats.norm.cdf(abs(residual)))  # Two-tailed p-value
                        
                        p_val_formatted, sig_symbol = PolarsStatsTests._format_p_value(
                            p_value_residual, p_value_precision, scientific_notation_threshold, significance_symbols
                        )
                        
                        if superscript_tests:
                            # Option 1: Consistent superscripts - residual tests get ¹
                            residual_superscript = "¹"
                            
                            if significance_in_p_value:
                                sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                                row["p_value"] = f"{p_val_formatted}{sig_formatted}{residual_superscript}"
                            else:
                                row["p_value"] = f"{p_val_formatted}{residual_superscript}"
                                row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                        else:
                            # Option 2: Clean p-values + dedicated Test column
                            if significance_in_p_value:
                                sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                                row["p_value"] = f"{p_val_formatted}{sig_formatted}"
                            else:
                                row["p_value"] = p_val_formatted
                                row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                            
                            # Add dedicated Test column for residuals
                            row["test_type"] = "Residual"
                    else:
                        row["p_value"] = "—"
                        row["significance"] = ""
                    
                    # Add degrees of freedom (for residuals, df = 1 per cell comparison)
                    row["degrees_of_freedom"] = "1"
                        
                elif 'p_value' in cat_stats and cat_stats['p_value'] != result.p_value:
                    # Only show p-value if it's different from overall (i.e., a proper post-hoc test)
                    p_val_formatted, sig_symbol = PolarsStatsTests._format_p_value(
                        cat_stats['p_value'], p_value_precision, scientific_notation_threshold, significance_symbols
                    )
                    
                    if superscript_tests:
                        # Option 1: Consistent superscripts - post-hoc tests get ¹
                        posthoc_superscript = "¹"  # Use residual superscript for category-level tests
                        
                        if significance_in_p_value:
                            sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                            row["p_value"] = f"{p_val_formatted}{sig_formatted}{posthoc_superscript}"
                        else:
                            row["p_value"] = f"{p_val_formatted}{posthoc_superscript}"
                            row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                    else:
                        # Option 2: Clean p-values + dedicated Test column
                        if significance_in_p_value:
                            sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                            row["p_value"] = f"{p_val_formatted}{sig_formatted}"
                        else:
                            row["p_value"] = p_val_formatted
                            row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                        
                        # Add dedicated Test column for post-hoc tests
                        row["test_type"] = "Post-hoc"
                    
                    # Show the post-hoc test statistic if available
                    if 'statistic' in cat_stats:
                        row["statistic"] = PolarsStatsTests._format_statistic(cat_stats['statistic'], statistic_precision)
                    else:
                        # 🔥 FIX: If no pre-computed statistic, calculate standardized residual
                        # This handles cases where categories have p-values but no statistic
                        if 'counts_by_group' in cat_stats and result.additional_info:
                            try:
                                observed_counts = cat_stats['counts_by_group']
                                category_stats_all = result.additional_info['category_statistics']
                                
                                # Get cohort totals
                                cohort_totals = {}
                                for cat_data in category_stats_all.values():
                                    if 'counts_by_group' in cat_data:
                                        for cohort, count in cat_data['counts_by_group'].items():
                                            cohort_totals[cohort] = cohort_totals.get(cohort, 0) + count
                                
                                category_total = sum(observed_counts.values())
                                grand_total = sum(cohort_totals.values())
                                
                                # Calculate residual
                                max_abs_residual = 0
                                for cohort, observed in observed_counts.items():
                                    if cohort in cohort_totals and grand_total > 0:
                                        expected = (cohort_totals[cohort] * category_total) / grand_total
                                        if expected > 0:
                                            residual = (observed - expected) / (expected * (1 - category_total/grand_total) * (1 - cohort_totals[cohort]/grand_total)) ** 0.5
                                            max_abs_residual = max(max_abs_residual, abs(residual))
                                
                                if max_abs_residual > 0:
                                    if format == 'html':
                                        row["statistic"] = f"{max_abs_residual:.3f}¹"
                                    else:
                                        row["statistic"] = f"{max_abs_residual:.3f}¹"
                                else:
                                    row["statistic"] = "0.000¹"
                            except Exception:
                                row["statistic"] = "—"
                        else:
                            row["statistic"] = "—"
                    
                    # Add degrees of freedom if available
                    if 'degrees_of_freedom' in cat_stats:
                        row["degrees_of_freedom"] = str(cat_stats['degrees_of_freedom'])
                    else:
                        # If calculating residual, use df=1
                        if 'statistic' not in cat_stats and 'counts_by_group' in cat_stats:
                            row["degrees_of_freedom"] = "1"
                        else:
                            row["degrees_of_freedom"] = "—"
                else:
                    # 🔥 FIX 2: ENSURE ALL CATEGORIES GET STATISTICS - Compute standardized residuals for all categories
                    # This shows which categories contribute most to the overall chi-square
                    if 'counts_by_group' in cat_stats and result.additional_info:
                        try:
                            # Calculate standardized residual for this category
                            observed_counts = cat_stats['counts_by_group']
                            category_stats_all = result.additional_info['category_statistics']
                            
                            # Get total counts for each cohort across all categories
                            cohort_totals = {}
                            for cat_data in category_stats_all.values():
                                if 'counts_by_group' in cat_data:
                                    for cohort, count in cat_data['counts_by_group'].items():
                                        cohort_totals[cohort] = cohort_totals.get(cohort, 0) + count
                            
                            # Calculate category total across all cohorts
                            category_total = sum(observed_counts.values())
                            grand_total = sum(cohort_totals.values())
                            
                            # Calculate standardized residuals for all cohorts in this category
                            max_abs_residual = 0
                            residuals = []
                            
                            for cohort, observed in observed_counts.items():
                                if cohort in cohort_totals and grand_total > 0:
                                    expected = (cohort_totals[cohort] * category_total) / grand_total
                                    if expected > 0:
                                        # Proper standardized residual formula
                                        residual = (observed - expected) / (expected * (1 - category_total/grand_total) * (1 - cohort_totals[cohort]/grand_total)) ** 0.5
                                        residuals.append(residual)
                                        max_abs_residual = max(max_abs_residual, abs(residual))
                            
                            if max_abs_residual > 0:
                                # Show the maximum absolute residual as the test statistic
                                if format == 'html':
                                    row["statistic"] = f"{max_abs_residual:.3f}¹"
                                else:
                                    row["statistic"] = f"{max_abs_residual:.3f}¹"
                                
                                # Degrees of freedom for residual analysis (1 per comparison)
                                row["degrees_of_freedom"] = "1"
                                
                                # 🔥 FIX 3: Calculate and show ACTUAL p-value from standardized residual
                                import scipy.stats as stats
                                p_value_residual = 2 * (1 - stats.norm.cdf(max_abs_residual))  # Two-tailed p-value
                                
                                p_val_formatted, sig_symbol = PolarsStatsTests._format_p_value(
                                    p_value_residual, p_value_precision, scientific_notation_threshold, significance_symbols
                                )
                                
                                if superscript_tests:
                                    # Option 1: Consistent superscripts - manual residual gets ¹
                                    manual_residual_superscript = "¹"
                                    
                                    if significance_in_p_value:
                                        sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                                        row["p_value"] = f"{p_val_formatted}{sig_formatted}{manual_residual_superscript}"
                                    else:
                                        row["p_value"] = f"{p_val_formatted}{manual_residual_superscript}"
                                        row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                                else:
                                    # Option 2: Clean p-values + dedicated Test column
                                    if significance_in_p_value:
                                        sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                                        row["p_value"] = f"{p_val_formatted}{sig_formatted}"
                                    else:
                                        row["p_value"] = p_val_formatted
                                        row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
                                    
                                    # Add dedicated Test column for manual residuals
                                    row["test_type"] = "Residual"
                            else:
                                row["statistic"] = "0.000"
                                row["p_value"] = "1.0000"  # Perfect agreement, p = 1
                                row["degrees_of_freedom"] = "1"
                                row["significance"] = ""
                                
                        except Exception as e:
                            # Fallback if residual calculation fails - still show something
                            row["statistic"] = "—"
                            row["p_value"] = "—"
                            row["degrees_of_freedom"] = "—"
                            row["significance"] = ""
                            
                            # Add empty test_type column for consistency when superscript_tests=False
                            if not superscript_tests:
                                row["test_type"] = "—"
                    else:
                        # No data for residual calculation
                        row["statistic"] = ""
                        row["p_value"] = ""
                        row["degrees_of_freedom"] = ""
                        row["significance"] = ""
                        
                        # Add empty test_type column for consistency when superscript_tests=False
                        if not superscript_tests:
                            row["test_type"] = ""
            else:
                # 📊 DESCRIPTIVE ONLY: Standard demographics table format
                # Category levels show descriptive statistics only, no individual tests
                row["statistic"] = ""
                row["p_value"] = ""
                row["degrees_of_freedom"] = ""
                row["significance"] = ""
                
                # Add empty test_type column for consistency when superscript_tests=False
                if not superscript_tests:
                    row["test_type"] = ""
            
            rows.append(row)
            
        return rows
            
    @staticmethod
    def _create_continuous_variable_row_with_smart_stats(result: TestResult, show_test_name: bool, show_degrees_of_freedom: bool,
                                                        p_value_precision: int, statistic_precision: int, scientific_notation_threshold: float,
                                                        significance_symbols: dict, significance_in_p_value: bool, format: str, superscript_tests: bool = True) -> dict:
        """Create a unified row for continuous variables with cohort columns using generate_smart_stats."""
        try:
            from .stats import generate_smart_stats
        except ImportError:
            # Fallback if import fails
            return PolarsStatsTests._create_basic_continuous_row(
                result, show_test_name, show_degrees_of_freedom,
                p_value_precision, statistic_precision, scientific_notation_threshold,
                significance_symbols, significance_in_p_value, format
            )
        
        row = {}
        
        # Variable name should ALWAYS be set regardless of show_test_name
        analyzed_col = result.additional_info.get('analyzed_column', 'Variable') if result.additional_info else 'Variable'
        
        if show_test_name:
            # Add test-specific symbols when show_test_name=True
            test_symbol = ""
            if result.test_name == "kruskal_wallis":
                test_symbol = " (Kruskal-Wallis)"  # Clean readable format
            elif result.test_name == "anova":
                test_symbol = " (ANOVA)"   # Clean readable format
            elif result.test_name.startswith("t_test"):
                test_symbol = " (t-test)"   # Clean readable format
            
            row["variable_name"] = f"**{analyzed_col}**{test_symbol}"
        else:
            # Clean variable name without test info
            row["variable_name"] = f"**{analyzed_col}**"
            
        # Get the original dataframe and column info from result
        if result.additional_info and 'source_data' in result.additional_info:
            source_df = result.additional_info['source_data']
            analyzed_col = result.additional_info.get('analyzed_column')
            group_col = result.additional_info.get('group_column', 'cohort')
            
            if source_df is not None and analyzed_col and analyzed_col in source_df.columns:
                try:
                    # Use generate_smart_stats to get proper descriptive statistics
                    stats_result = generate_smart_stats(
                        source_df,
                        group_by=group_col,
                        columns=[analyzed_col],
                        return_type='dictionary',
                        stack_results=False
                    )
                    
                    # Extract statistics for each cohort
                    all_stats = {}
                    for group_key, group_data in stats_result.items():
                        if analyzed_col in group_data:
                            col_stats = group_data[analyzed_col]
                            
                            # Determine if data is normal (has mean/std) or non-normal (use median/IQR)
                            if 'mean' in col_stats and 'std' in col_stats:
                                # Normal distribution: mean (std)
                                if col_stats['mean'] is not None and col_stats['std'] is not None:
                                    stat_str = f"{col_stats['mean']:.1f} ({col_stats['std']:.1f})"
                                else:
                                    stat_str = "—"
                            elif 'median' in col_stats and 'q25' in col_stats and 'q75' in col_stats:
                                # Non-normal distribution: median (IQR)
                                if (col_stats['median'] is not None and 
                                    col_stats['q25'] is not None and 
                                    col_stats['q75'] is not None):
                                    iqr = f"{col_stats['q25']:.1f}-{col_stats['q75']:.1f}"
                                    stat_str = f"{col_stats['median']:.1f} ({iqr})"
                                else:
                                    stat_str = "—"
                            else:
                                stat_str = "—"
                            
                            all_stats[group_key] = stat_str
                    
                    # Calculate overall statistics across all groups
                    overall_stats = generate_smart_stats(
                        source_df,
                        columns=[analyzed_col],
                        return_type='dictionary',
                        stack_results=False
                    )
                    
                    if analyzed_col in overall_stats:
                        col_overall = overall_stats[analyzed_col]
                        if 'mean' in col_overall and 'std' in col_overall and col_overall['mean'] is not None:
                            row["all_cohort_values"] = f"{col_overall['mean']:.1f} ({col_overall['std']:.1f})"
                        elif 'median' in col_overall and 'q25' in col_overall and 'q75' in col_overall:
                            if (col_overall['median'] is not None and 
                                col_overall['q25'] is not None and 
                                col_overall['q75'] is not None):
                                iqr = f"{col_overall['q25']:.1f}-{col_overall['q75']:.1f}"
                                row["all_cohort_values"] = f"{col_overall['median']:.1f} ({iqr})"
                            else:
                                row["all_cohort_values"] = "—"
                        else:
                            row["all_cohort_values"] = "—"
                    else:
                        row["all_cohort_values"] = "—"
                    
                    # Add individual cohort columns
                    for group_key, stat_str in all_stats.items():
                        # Clean cohort name for column (consistent with categorical format)
                        clean_cohort_name = str(group_key).replace("Wearable_Ward_Monitoring_", "")
                        safe_column_name = f"cohort_{clean_cohort_name.replace('_', '_')}"
                        row[safe_column_name] = stat_str
                        
                except Exception as e:
                    # Fallback if generate_smart_stats fails
                    row["all_cohort_values"] = "—"
                    print(f"Warning: Could not generate smart stats for {analyzed_col}: {e}")
            else:
                row["all_cohort_values"] = "—"
        else:
            row["all_cohort_values"] = "—"
        
        # Test statistics
        row["statistic"] = PolarsStatsTests._format_statistic(result.statistic, statistic_precision)
        
        # P-value formatting with significance AND test superscripts
        p_val_formatted, sig_symbol = PolarsStatsTests._format_p_value(
            result.p_value, p_value_precision, scientific_notation_threshold, significance_symbols
        )
        
        # 🔥 Add test type superscripts for continuous variables when superscript_tests=True
        test_superscript = ""
        if superscript_tests:
            if result.test_name == "kruskal_wallis":
                test_superscript = "ᵏʷ"  # Kruskal-Wallis superscript
            elif result.test_name == "anova":
                test_superscript = "ᶠ"   # ANOVA F-test superscript
            elif result.test_name.startswith("t_test"):
                test_superscript = "ᵗ"   # t-test superscript
        
        if significance_in_p_value:
            sig_formatted = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
            row["p_value"] = f"{p_val_formatted}{test_superscript}{sig_formatted}"
        else:
            row["p_value"] = f"{p_val_formatted}{test_superscript}"
            row["significance"] = PolarsStatsTests._format_significance_superscript(sig_symbol, format)
        
        # Degrees of freedom
        if show_degrees_of_freedom and result.degrees_of_freedom is not None:
            row["degrees_of_freedom"] = str(result.degrees_of_freedom)
        else:
            row["degrees_of_freedom"] = ""
            
        return row

    def _extract_group_values(self, result: TestResult, base_group: str, comp_group: str) -> tuple[str | None, str | None]:
        """Extract group descriptive statistics from result or dataframe."""
        base_val = None
        comp_val = None
        
        if result.additional_info:
            # Look for pre-computed descriptive statistics
            if "group_descriptives" in result.additional_info:
                desc = result.additional_info["group_descriptives"]
                if isinstance(desc, dict):
                    base_val = desc.get(base_group)
                    comp_val = desc.get(comp_group)
                    return base_val, comp_val
            
            # Look for group means and stds (for parametric tests)
            if "group_means" in result.additional_info and "group_stds" in result.additional_info:
                means = result.additional_info["group_means"]
                stds = result.additional_info["group_stds"]
                if isinstance(means, dict) and isinstance(stds, dict):
                    base_mean = means.get(base_group)
                    comp_mean = means.get(comp_group)
                    base_std = stds.get(base_group)
                    comp_std = stds.get(comp_group)
                    
                    if base_mean is not None and base_std is not None:
                        base_val = f"{base_mean:.2f} ({base_std:.2f})"
                    if comp_mean is not None and comp_std is not None:
                        comp_val = f"{comp_mean:.2f} ({comp_std:.2f})"
                    return base_val, comp_val
        
        # If we don't have pre-computed values, try to compute from the dataframe
        # This is a fallback that requires access to the original data
        try:
            base_val = self._compute_group_descriptive(base_group)
            comp_val = self._compute_group_descriptive(comp_group)
        except:
            # If computation fails, return None values
            pass
                
        return base_val, comp_val
    
    def _compute_group_descriptive(self, group_name: str) -> str | None:
        """Compute descriptive statistics for a group from the dataframe."""
        try:
            # Check if group_name corresponds to a column in our dataframe
            if group_name in self.columns:
                col_data = self._df.select(pl.col(group_name)).drop_nulls()
                if len(col_data) == 0: # type: ignore
                    return None
                
                # Get the data as a series
                series = col_data.get_column(group_name) # type: ignore
                
                # Test for normality using Shapiro-Wilk (for small samples) or basic checks
                is_normal = self._is_approximately_normal(series)
                
                if is_normal:
                    # For normal data: mean (std)
                    mean_val = float(series.mean()) # type: ignore
                    std_val = float(series.std()) # type: ignore
                    return f"{mean_val:.2f} ({std_val:.2f})"
                else:
                    # For non-normal data: median (Q25, Q75)
                    median_val = float(series.median()) # type: ignore
                    q25 = float(series.quantile(0.25)) # type: ignore
                    q75 = float(series.quantile(0.75)) # type: ignore
                    return f"{median_val:.2f} ({q25:.2f}, {q75:.2f})"
            else:
                return None
        except Exception:
            return None
    
    def _is_approximately_normal(self, series: pl.Series) -> bool:
        """Quick normality assessment for descriptive statistics choice."""
        try:
            import scipy.stats as stats
            data = series.to_numpy()
            
            # For small samples (n < 50), use Shapiro-Wilk
            if len(data) < 50:
                _, p_value = stats.shapiro(data)
                return p_value > 0.05
            else:
                # For larger samples, use D'Agostino and Pearson's test
                _, p_value = stats.normaltest(data)
                return p_value > 0.05
        except:
            # If statistical tests fail, use simple heuristics
            try:
                # Check skewness and kurtosis
                skew = float(series.skew()) # type: ignore
                # Consider roughly normal if |skewness| < 1
                return abs(skew) < 1.0
            except:
                # Ultimate fallback - assume normal
                return True

    @staticmethod
    def _generate_footer(results: List[TestResult], significance_symbols: Dict[float, str], format: str) -> str:
        """Generate footer/legend explaining significance symbols and statistical methods."""
        footer_lines = []
        
        # Get unique test types
        test_types = set()
        has_corrected_p = False
        
        for result in results:
            test_types.add(result.test_name)
            if hasattr(result, 'p_value_corrected') and result.p_value_corrected is not None:
                has_corrected_p = True
        
        # Significance symbols explanation
        sig_text = ""
        if significance_symbols:
            # Sort by threshold (descending)
            sorted_symbols = sorted([(threshold, symbol) for threshold, symbol in significance_symbols.items() 
                                   if symbol.strip()], reverse=True)
            
            if sorted_symbols:
                if format == "latex":
                    sig_text = "Significance levels: "
                    sig_parts = []
                    for threshold, symbol in sorted_symbols:
                        if threshold < 1.0:  # Skip the empty symbol threshold
                            sig_parts.append(f"$^{{{symbol}}}$ p < {threshold}")
                    sig_text += ", ".join(sig_parts) + "."
                elif format == "markdown":
                    sig_text = "**Significance levels:** "
                    sig_parts = []
                    for threshold, symbol in sorted_symbols:
                        if threshold < 1.0:
                            sig_parts.append(f"{symbol} p < {threshold}")
                    sig_text += ", ".join(sig_parts) + "."
                elif format == "html":
                    sig_text = "<strong>Significance levels:</strong> "
                    sig_parts = []
                    for threshold, symbol in sorted_symbols:
                        if threshold < 1.0:
                            sig_parts.append(f"<sup>{symbol}</sup> p < {threshold}")
                    sig_text += ", ".join(sig_parts) + "."
                
                if sig_text:
                    footer_lines.append(sig_text)
        
        # Multiple comparisons correction note
        if has_corrected_p:
            footer_lines.append("Corrected p-values account for multiple comparisons using FDR (Benjamini-Hochberg) method.")
        
        # Statistical methods explanation
        method_descriptions = {
            "t_test_ind": "Independent samples t-test",
            "welch_t_test": "Welch's t-test (unequal variances)",
            "t_test_paired": "Paired t-test", 
            "t_test_1samp": "One-sample t-test",
            "anova": "One-way ANOVA",
            "kruskal_wallis": "Kruskal-Wallis H test",
            "chi2": "Chi-square test of independence",
            "fisher_exact": "Fisher's exact test",
            "tukey_hsd": "Tukey's HSD post-hoc test"
        }
        
        # Filter out None values and get method descriptions
        used_methods = [method_descriptions.get(test_type, test_type) for test_type in sorted(test_types) if test_type]
        if used_methods:
            methods_text = f"Statistical methods: {', '.join(used_methods)}." # type: ignore
            footer_lines.append(methods_text)
        
        # Test symbols explanation  
        footer_lines.append("Test symbols: ² Chi-square, ᵏʷ Kruskal-Wallis, ᶠ ANOVA, ᵗ t-test, ¹ standardized residual.")
        
        # Data presentation note
        footer_lines.append("Values presented as mean (standard deviation) for normally distributed data.")
        
        # Join all footer lines
        if format == "latex":
            return "\n".join(footer_lines)
        elif format == "markdown":
            return "\n\n" + "\n\n".join(footer_lines)
        else:  # HTML
            return "\n".join(footer_lines)

    @staticmethod
    def _format_significance_superscript(sig_symbol: str, format: str) -> str:
        """Format significance symbols as superscript based on output format."""
        if not sig_symbol or sig_symbol.strip() == "":
            return ""
            
        if format == "latex":
            return f"$^{{{sig_symbol}}}$"
        elif format == "html":
            return f"<sup>{sig_symbol}</sup>"
        elif format == "markdown":
            return f"^{sig_symbol}^"
        else:
            # For dataframe/csv, use Unicode superscript characters
            return self._convert_to_unicode_superscript(sig_symbol)
    
    def _convert_to_unicode_superscript(self, text: str) -> str:
        """Convert text to Unicode superscript characters."""
        # Unicode superscript mapping
        superscript_map = {
            '*': '⁺',  # Using ⁺ as asterisk superscript substitute
            '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
            '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
            '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
            'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ',
            'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ',
            'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ',
            'p': 'ᵖ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ',
            'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ'
        }
        
        # For significance symbols, use proper asterisk-like superscripts
        if text == "*":
            return "＊"  # Full-width asterisk (more visible)
        elif text == "**":
            return "＊＊"
        elif text == "***":
            return "＊＊＊"
        else:
            # For other text, convert character by character
            result = ""
            for char in text:
                result += superscript_map.get(char, char)
            return result

    def summary_table(self, results: List[TestResult]) -> pl.DataFrame:
        """
        Convert test results to a basic summary DataFrame.
        
        For manuscript-quality tables, use manuscript_table() instead.
        
        Parameters:
        -----------
        results : List[TestResult]
            Test results to summarize
            
        Returns:
        --------
        pl.DataFrame
            Basic summary table of results
        """
        data = []
        for result in results:
            row = result.to_dict()
            data.append(row)
        
        return pl.DataFrame(data)

    def compare_descriptive_stats(
        self,
        stats_df: pl.DataFrame,
        group_col: str = "group",
        base_group: Optional[str] = None,
        include_tests: bool = True,
        test_type: Literal["auto", "parametric", "non_parametric"] = "auto",
        significance_level: float = 0.05,
        multiple_comparisons: Optional[str] = "fdr_bh",
        format: Literal["dataframe", "latex", "markdown", "html"] = "dataframe",
        **manuscript_table_kwargs
    ) -> Union[pl.DataFrame, str]:
        """
        Compare descriptive statistics between groups with automatic statistical testing.
        
        Takes output from stats.py descriptive statistics and creates manuscript-ready
        comparison tables with statistical tests between groups.
        
        Parameters:
        -----------
        stats_df : pl.DataFrame
            DataFrame containing descriptive statistics from stats.py output
            
        group_col : str, default="group"
            Column name that identifies the groups to compare
            
        base_group : str, optional
            Reference group for comparisons. If None, uses first group alphabetically
            
        include_tests : bool, default=True
            Whether to perform statistical tests between groups
            
        test_type : str, default="auto"
            Type of statistical test: "auto", "parametric", "non_parametric"
            
        significance_level : float, default=0.05
            Alpha level for statistical significance
            
        multiple_comparisons : str, optional, default="fdr_bh"
            Multiple comparison correction method
            
        format : str, default="dataframe"
            Output format: "dataframe", "latex", "markdown", "html"
            
        **manuscript_table_kwargs
            Additional arguments passed to manuscript_table method
            
        Returns:
        --------
        Union[pl.DataFrame, str]
            Formatted comparison table
            
        Examples:
        ---------
        >>> # Basic usage with stats.py output
        >>> stats_output = df.stats.descriptive_stats(group_by="treatment")
        >>> comparison = df.stats_tests.compare_descriptive_stats(
        ...     stats_output, 
        ...     group_col="treatment",
        ...     base_group="control"
        ... )
        
        >>> # Generate LaTeX table for publication
        >>> latex_comparison = df.stats_tests.compare_descriptive_stats(
        ...     stats_output,
        ...     format="latex",
        ...     separate_group_columns=True,
        ...     include_group_values=True,
        ...     significance_in_p_value=True
        ... )
        """
        
        # Validate inputs
        if group_col not in stats_df.columns:
            raise ValueError(f"Group column '{group_col}' not found in stats_df")
        
        # Get unique groups
        groups = sorted(stats_df[group_col].unique().to_list())
        if len(groups) < 2:
            raise ValueError("Need at least 2 groups for comparison")
        
        # Set base group if not specified
        if base_group is None:
            base_group = groups[0]
        elif base_group not in groups:
            raise ValueError(f"Base group '{base_group}' not found in data")
        
        # Get non-group columns (these are the statistics)
        stat_columns = [col for col in stats_df.columns if col != group_col]
        
        # Create transposed comparison table
        comparison_data = []
        
        for stat_col in stat_columns:
            # Get values for each group
            group_values = {}
            for group in groups:
                filtered = stats_df.filter(pl.col(group_col) == group)
                if len(filtered) > 0:
                    value = filtered[stat_col].item(0)
                    group_values[group] = value
                else:
                    group_values[group] = None
            
            # Create row for this statistic
            row = {
                "Statistic": stat_col,
                "Base_Group": base_group,
                "Base_Value": group_values.get(base_group)
            }
            
            # Add comparison groups and their values
            for group in groups:
                if group != base_group:
                    row[f"{group}_Value"] = group_values.get(group)
                    
                    # Calculate difference/ratio if both values are numeric
                    base_val = group_values.get(base_group)
                    comp_val = group_values.get(group)
                    
                    if base_val is not None and comp_val is not None:
                        try:
                            base_float = float(base_val)
                            comp_float = float(comp_val)
                            diff = comp_float - base_float
                            ratio = comp_float / base_float if base_float != 0 else None
                            row[f"{group}_Difference"] = diff
                            row[f"{group}_Ratio"] = ratio
                        except (ValueError, TypeError):
                            # Non-numeric values
                            row[f"{group}_Difference"] = None
                            row[f"{group}_Ratio"] = None
                    else:
                        row[f"{group}_Difference"] = None
                        row[f"{group}_Ratio"] = None
            
            comparison_data.append(row)
        
        # Create comparison DataFrame
        comparison_df = pl.DataFrame(comparison_data)
        
        # If statistical tests are requested and we have access to raw data
        if include_tests and hasattr(self, '_df'):
            try:
                test_results = self._perform_group_comparisons(
                    groups, base_group, test_type, multiple_comparisons # type: ignore
                )
                
                # Merge test results with comparison data
                comparison_df = self._merge_test_results_with_descriptives(
                    comparison_df, test_results, groups, base_group # type: ignore
                )
            except Exception as e:
                # If tests fail, continue without them
                print(f"Warning: Statistical tests failed: {e}")
        
        # Format output
        if format == "dataframe":
            return comparison_df
        else:
            # Use manuscript_table formatting
            return self._format_descriptive_comparison(
                comparison_df, format, **manuscript_table_kwargs
            )
    
    def _perform_group_comparisons(
        self, 
        groups: List[str], 
        base_group: str, 
        test_type: str, 
        multiple_comparisons: Optional[str]
    ) -> List:
        """Perform statistical tests between groups."""
        test_pairs = []
        
        # Create all pairwise comparisons with base group
        for group in groups:
            if group != base_group:
                test_pairs.append((base_group, group))
        
        # Perform statistical tests based on test_type
        if test_type == "parametric":
            results = self.t_test(test_pairs, multiple_comparisons=multiple_comparisons) # type: ignore
        elif test_type == "non_parametric":
            # Use Welch's t-test as a more robust alternative
            results = self.t_test(test_pairs, equal_var=False, multiple_comparisons=multiple_comparisons) # type: ignore
        else:  # auto
            # Use t-test as default (could be enhanced with normality testing)
            results = self.t_test(test_pairs, multiple_comparisons=multiple_comparisons) # type: ignore
        
        return results
    
    def _merge_test_results_with_descriptives(
        self, 
        comparison_df: pl.DataFrame, 
        test_results: List, 
        groups: List[str], 
        base_group: str
    ) -> pl.DataFrame:
        """Merge statistical test results with descriptive comparison data."""
        
        # Create a mapping of comparisons to test results
        test_map = {}
        for result in test_results:
            if hasattr(result, 'comparison') and result.comparison:
                test_map[result.comparison] = result
        
        # Add test result data to each row
        enhanced_data = []
        for row in comparison_df.iter_rows(named=True):
            enhanced_row = dict(row)
            
            for group in groups:
                if group != base_group:
                    # Try different comparison formats
                    comparison_keys = [
                        f"{base_group} vs {group}",
                        f"{group} vs {base_group}",
                        f"{base_group}_vs_{group}"
                    ]
                    
                    test_result = None
                    for key in comparison_keys:
                        if key in test_map:
                            test_result = test_map[key]
                            break
                    
                    if test_result:
                        enhanced_row[f"{group}_Test_Statistic"] = round(test_result.statistic, 4) if test_result.statistic is not None else None
                        enhanced_row[f"{group}_P_Value"] = round(test_result.p_value, 6) if test_result.p_value is not None else None
                        
                        # Determine significance
                        if test_result.p_value is not None:
                            if test_result.p_value < 0.001:
                                sig = "***"
                            elif test_result.p_value < 0.01:
                                sig = "**"
                            elif test_result.p_value < 0.05:
                                sig = "*"
                            else:
                                sig = ""
                            enhanced_row[f"{group}_Significance"] = sig
                        else:
                            enhanced_row[f"{group}_Significance"] = ""
                    else:
                        enhanced_row[f"{group}_Test_Statistic"] = None
                        enhanced_row[f"{group}_P_Value"] = None
                        enhanced_row[f"{group}_Significance"] = ""
            
            enhanced_data.append(enhanced_row)
        
        return pl.DataFrame(enhanced_data)
    
    def _format_descriptive_comparison(
        self, 
        comparison_df: pl.DataFrame, 
        format: str, 
        **kwargs
    ) -> str:
        """Format descriptive comparison table using manuscript table formatting."""
        
        if format == "latex":
            footer = "Group comparisons with statistical testing. Base group used as reference for all comparisons."
            return self._to_latex_table(comparison_df, 
                                      kwargs.get("table_caption", "Descriptive Statistics Group Comparisons"),
                                      kwargs.get("table_label", "tab:group_comparison"),
                                      footer)
        elif format == "markdown":
            footer = "\n\n**Group comparisons with statistical testing.** Base group used as reference for all comparisons."
            return self._to_markdown_table(comparison_df, footer)
        elif format == "html":
            footer = "Group comparisons with statistical testing. Base group used as reference for all comparisons."
            return self._to_html_table(comparison_df, 
                                     kwargs.get("table_caption", "Descriptive Statistics Group Comparisons"),
                                     footer)
        else:
            return str(comparison_df)
    

