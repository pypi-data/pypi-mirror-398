import polars as pl
import numpy as np
import os
from .epl import EnhancedPolars, CoreDataType
from .Stats import generate_smart_stats, get_random_choice_exp, get_random_normal_exp, get_random_uniform_exp, get_random_truncated_normal_exp
from typing import Any, cast, List, Optional, Literal, Dict, Tuple, Type
import unicodedata
from CoreUtilities import get_logger
from pathlib import Path
import joblib
from .base import UniversalPolarsDataFrameExtension
from .interpolation import PolarsDataFrameInterpolationExtension

try:
    from sklearn.preprocessing import (
        StandardScaler, 
        MinMaxScaler, 
        RobustScaler, 
        MaxAbsScaler, 
        QuantileTransformer, 
        PowerTransformer,
        LabelEncoder,
        OneHotEncoder,
        OrdinalEncoder
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


logger = get_logger(__name__)

stat_points: List[str] = [
        'mean', 'min', 'max', 'median', 'mad', 'median_absolute_deviation', 'mode',
        'nth_quantile', 'nth_standard_deviation', 'fixed_value'
    ]

_clip_stat_points: List[str] = [
        'min', 'max', 'mad', 'median_absolute_deviation',
        'nth_quantile', 'nth_standard_deviation', 'fixed_value'
    ]

_stat_distribution: List[str] = [
    'normal', 'uniform', 'truncated_normal', 'weighted_uniform', 'fixed_value',
    'median_mad_gaussian',  'median_mad_truncated_gausian'
]



_stat_pointsL = Literal[
    'mean', 'min', 'max', 'median', 'mad', 'median_absolute_deviation', 'mode',
    'nth_quantile', 'nth_standard_deviation', 'fixed_value'
]

_stat_distributionL = Literal[
    'normal', 'uniform', 'truncated_normal', 'weighted_uniform', 'fixed_value',
    'median_mad_gaussian', 'median_mad_truncated_gausian'
]



_clip_stat_pointsL = Literal[
        'min', 'max', 
        'nth_quantile', 'nth_standard_deviation', 'fixed_value'
    ]




class PolarsMLPipeline(UniversalPolarsDataFrameExtension):
    def __init__(self, df: pl.DataFrame | pl.LazyFrame):
        super().__init__(df)

    def standardize(self,
                    metadata_columns: Optional[List[str]] = None,
                    columns: Optional[List[str]] = None,
                    replacement_dict: Optional[Dict[Any, Any]] = None,
                    replacement_regex: Optional[Dict[Any, Any]] = None,
                    str_case_standardization: Literal['lower', 'upper', 'title'] = 'upper',
                    na_values: Optional[Dict[str, list[Any]] | list[Any]] = ["", "NA", "N/A", "n/a", "nan", "NULL", "None",
                                                            "#N/A", "#VALUE!", "?", ".", "MISSING", '??'],
                    case_sensitive_repl: bool = False) -> pl.DataFrame | pl.LazyFrame:

        # get column meta from schema
        meta: Dict[str, Any] =  {name: EnhancedPolars.get_dtype_meta(dtype) for name, dtype in self.schema.items()}
        # Handle whole cell replacements
        column_specific_repl: bool = any([k in meta.keys() for k in replacement_dict]) if isinstance(replacement_dict, dict) else False
        default_repl: Optional[Dict[Any, Any]] = {k: v for k,v in (replacement_dict or {}).items() if (k not in meta.keys()) and isinstance(v, dict)} if column_specific_repl else replacement_dict
        column_specific_na: bool = isinstance(na_values, dict)
        default_na_values: Optional[Dict[str, list[Any]] | list[Any]]= {k: v for k,v in na_values.items() if (k not in meta.keys()) and isinstance(v, list)} if column_specific_na else na_values

        # Handle string/text replacements
        column_specific_regx: bool = any([k in meta.keys() for k in (replacement_regex or [])])
        default_regx: Optional[Dict[Any, Any]] = {k: v for k,v in (replacement_regex or {}).items() if (k not in meta.keys()) and isinstance(v, str)} if column_specific_regx else replacement_regex

        columns = columns or self.columns

        assert all([col in self.columns for col in columns]), f'The following user specified columns were missing from the dataframe: {[col for col in columns if col not in self.columns]}'

        metadata_columns = metadata_columns or []

        exps: List[pl.Expr] = []

        for col, _meta in meta.items():
            if col not in columns:
                continue
            elif col in metadata_columns:
                exps.append(pl.col(col))
                continue
            _col_repl = replacement_dict.get(col, default_repl) if isinstance(replacement_dict, dict) else None
            _col_regex = replacement_regex.get(col, default_regx) if isinstance(replacement_regex, dict) else None
            _col_nav = na_values.get(col, default_na_values) if column_specific_na else default_na_values
            assert isinstance(_col_repl, (dict, type(None))), f'The replacement options must be a dict or None for col {col}, but found type: {type(_col_repl)} values: {_col_repl}'
            
            
            col_exp = pl.col(col)
            if _meta['core_data_type'] == CoreDataType.STRING:
                
                if isinstance(_col_regex, dict):
                    for _pat, _repl in _col_regex.items():
                        col_exp = col_exp.str.replace_all(rf'(?i){_pat}' if not (case_sensitive_repl or _pat.startswith('(?i)')) else _pat, _repl, literal=False)
                        
                col_exp = getattr(col_exp.str.strip_chars().str.normalize(form='NFC').str, f'to_{str_case_standardization}case')()
                        
            
                _str_na: List[str] = [x for x in (_col_nav or []) if isinstance(x, str)]
                
                if len(_str_na) > 0:
                    _str_na = getattr(pl.Series(_str_na).str.strip_chars().str.normalize(form='NFC').str, f'to_{str_case_standardization}case')().to_list()
                    
                    
                _str_repl: Dict[str, Any] = {getattr(unicodedata.normalize("NFC", k.strip()),
                                                        str_case_standardization)(): (getattr(unicodedata.normalize("NFC", v.strip()),
                                                        str_case_standardization)() if isinstance(v, str) else v) for k, v in (_col_repl or {}).items() if isinstance(k, str)}
            
                # have replacements take priority over nulls if there is any conflicts
                if (len(_str_na) > 0) or (len(_str_repl) > 0):
                    col_exp = col_exp.replace({**{x: None for x in _str_na}, **_str_repl})
                    
            elif _meta['core_data_type'] in [CoreDataType.FLOAT, CoreDataType.INTEGER]:
                if _col_regex != default_regx:
                    logger.warning('Skipping Regex based replacement for numeric data')
                
                _numeric_na: List[float | int] = [x for x in (_col_nav or []) if isinstance(x, (float, int))]
                _numeric_repl: Dict[float | int, float | int | None] = {k: v for k, v in (_col_repl or {}).items() if isinstance(k, (float, int)) and isinstance(v, (float, int, type(None)))}
                
                # have replacements take priority over nulls if there is any conflicts
                if (len(_numeric_na) > 0) or (len(_numeric_repl) > 0):
                    col_exp = col_exp.replace({**{x: None for x in _numeric_na}, **_numeric_repl})
                    
            elif _meta['core_data_type'] == CoreDataType.CATEGORICAL:
                orig_cats = (self._df.select(col).collect() if isinstance(self._df, pl.LazyFrame) else self._df)[col].cat.get_categories()
                cats = orig_cats.clone()
                
                if isinstance(_col_regex, dict):
                    for _pat, _repl in _col_regex.items():
                        cats = cats.str.replace_all(rf'(?i){_pat}' if not (case_sensitive_repl or _pat.startswith('(?i)')) else _pat, _repl, literal=False)
                        
                cats = getattr(cats.str.strip_chars().str.normalize(form='NFC').str, f'to_{str_case_standardization}case')()
                        
            
                _str_na: List[str] = [x for x in (_col_nav or []) if isinstance(x, str)]
                
                if len(_str_na) > 0:
                    _str_na = getattr(pl.Series(_str_na).str.strip_chars().str.normalize(form='NFC').str, f'to_{str_case_standardization}case')().to_list()
                    
                    
                _str_repl: Dict[str, Any] = {getattr(unicodedata.normalize("NFC", k.strip()),
                                                        str_case_standardization)(): (getattr(unicodedata.normalize("NFC", v.strip()),
                                                        str_case_standardization)() if isinstance(v, str) else v) for k, v in (_col_repl or {}).items() if isinstance(k, str)}
            
                # have replacements take priority over nulls if there is any conflicts
                if (len(_str_na) > 0) or (len(_str_repl) > 0):
                    cats = cats.replace({**{x: None for x in _str_na}, **_str_repl})
                    
                # Create a mapping from original categories to modified categories
                cat_mapping = dict(zip(orig_cats.to_list(), cats.to_list()))
                col_exp = col_exp.replace(cat_mapping)
                
            # ensure the columns keep their original names
            exps.append(col_exp.alias(col))
            
        return self._df.with_columns(exps)

    def optimize_dtypes_and_get_meta(self,
                                    attempt_downcast: bool = True,
                                    attempt_numeric_to_datetime: bool = False,
                                    confidence: float = 1.0,
                                    n: Optional[int] = None,
                                    sample_strat: Literal['first', 'random'] = 'random',
                                    seed: int = 42,
                                    collect_precision_scale: bool = False,
                                    columns: Optional[List] = None) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        # Example feature engineering steps
        df, df_metadata = EnhancedPolars.infer_dtypes(df=self._df,
                                                        attempt_downcast=attempt_downcast,
                                                        attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                                                        confidence=confidence,
                                                        n=n,
                                                        sample_strat=sample_strat,
                                                        seed=seed,
                                                        collect_precision_scale=collect_precision_scale,
                                                        return_df=True,
                                                        columns=columns)

        return cast(pl.DataFrame, df), cast(Dict[str, Any], df_metadata)
    

    def clip_and_impute(self,
                        cohort_col: Optional[str] = None,
                        train_cohort: Optional[str] = None,
                        id_col: Optional[str] = None,
                        default_quantiles: List[float] = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99],
                        skip_clip: Dict[str, bool] | bool = False,
                        default_skip_clip: bool = False, # used only when a dict is used and a column is omitted from the specification

                        # step 5.1: Handle the lower clip limit
                        lower_clip_limit_type: Optional[Dict[str, _clip_stat_pointsL] | _clip_stat_pointsL] = 'nth_quantile', # this desribes how the lower clip limit is computed, e.g. 'nth_quantile', 'nth_standard_deviation', 'median_absolute_deviation', 'mad', 'fixed_value', 'min', 'max'
                        lower_clip_limit: Optional[Dict[str, float | int] | float | int] = 5, # this augments the lower clip limit, e.g. 5th percentile, 1st standard deviation, etc.


                        # step 5.2: Impute values that fell below the lower clip limit.
                        # step 5.2.1:  Can use the lower_clip_lower and lower_clip_upper to create an asymmetric window to impute values that fell below the lower clip limit.
                        lower_clip_lower_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = 'nth_quantile',
                        lower_clip_lower_value: Optional[Dict[str, int | float] | int | float] = 1,
                        lower_clip_upper_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = 'nth_quantile',
                        lower_clip_upper_value: Optional[Dict[str, int | float] | int | float] = 15,

                        # step 5.2.2: Alternatively, can user the lower_clip_center in order to impute a symetric distribution around a center value.
                        lower_clip_center_value: Optional[Dict[str, Any] | Any] = None,
                        lower_clip_center_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = None,

                        # step 5.2.3: The distribution to use for the lower clip limit imputation.
                        lower_clip_distribution: Optional[Dict[str, _stat_distributionL] | _stat_distributionL] = 'truncated_normal',

                        # step 5.3: Handle the upper clip limit
                        upper_clip_limit_type: Optional[Dict[str, _clip_stat_pointsL] | _clip_stat_pointsL] = 'nth_quantile', # this desribes how the upper clip limit is computed, e.g. 'nth_quantile', 'nth_standard_deviation', 'median_absolute_deviation', 'mad', 'fixed_value', 'min', 'max'
                        upper_clip_limit: Optional[Dict[str, int | float] | int | float] = 99, # this augments the upper clip limit, e.g. 95th percentile, 3rd standard deviation, etc.

                        # step 5.4: Impute values that fell above the upper clip limit.
                        # step 5.4.1:  Can use the upper_clip_lower and upper_clip_upper to create an asymmetric window to impute values that fell above the upper clip limit.
                        upper_clip_lower_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = 'nth_quantile',
                        upper_clip_lower_value: Optional[Dict[str, int | float] | int | float] = 85,
                        upper_clip_upper_value: Optional[Dict[str, int | float] | int | float] = 99,
                        upper_clip_upper_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = 'nth_quantile',

                        # step 5.4.2: Alternatively, can user the upper_clip_center in order to impute a symetric distribution around a center value.
                        upper_clip_center_value: Optional[Dict[str, Any] | Any] = None,
                        upper_clip_center_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = None,

                        # step 5.4.3: The distribution to use for the upper clip limit imputation.
                        upper_clip_distribution: Optional[Dict[str, _stat_distributionL] | _stat_distributionL] = 'truncated_normal',

                        # step 6: Impute missing values
                        skip_impute: Dict[str, bool] | bool = False, # if True, would skip imputation of missing values, with the possible exception of those already imputed by the clipping step above
                        default_skip_impute: bool = False, # used only when a dict is used and a column is omitted from the specification

                        # step 6.1.1:  Can use the null_lower and null_upper to create an asymmetric window to impute null values.
                        null_lower_value: Optional[Dict[str, int | float] | int | float] = 15, # this augments the null lower value, e.g. 15th percentile, 1st standard deviation, etc.
                        null_lower_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = 'nth_quantile', # this desribes how the null lower value is computed, e.g. 'nth_quantile', 'nth_standard_deviation', 'median_absolute_deviation', 'mad', 'fixed_value', 'min', 'max'
                        null_upper_value: Optional[Dict[str, int | float] | int | float] = 85, # this augments the null upper value, e.g. 85th percentile, 3rd standard deviation, etc.
                        null_upper_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = 'nth_quantile', # this desribes how the null upper value is computed, e.g. 'nth_quantile', 'nth_standard_deviation', 'median_absolute_deviation', 'mad', 'fixed_value', 'min', 'max'
                        
                        # step 6.1.2:  Can use the null_center to create a symmetric window to impute null values.
                        null_center_value: Optional[Dict[str, Any] | Any] = None,
                        default_missing_value: Optional[Dict[str, Any] | Any] = None, # used only if the impute method is 'fixed_value'. It is an alias for the null_center_value. If both are provided, null_center_value takes precedence.
                        null_center_type: Optional[Dict[str, _stat_pointsL] | _stat_pointsL] = None,

                        # step 6.1.3: The distribution to use for the null value imputation.
                        null_distribution: Optional[Dict[str, _stat_distributionL] | _stat_distributionL] = 'truncated_normal',

                        # safe defaults to override the distrubtion method or default values based on specific dtypes
                        min_categorical_count: Optional[Dict[str, int] | int]= 10, # the minimum number of samples per level to not be replaced based on the other replacement method
                        default_min_categorical_count: int = 10, # the minimum number of samples per level to not be replaced based on the other replacement method (only used if min_categorical_count is a dict and a olumn is not covered or min_categorical_count is None )
                        default_other_value: Optional[str] = 'other', # used only if other_replacement_method is 'default_other_value'
                        default_other_replacement_method: Literal['default_other_value', 'uniform_dist',  'weighted_uniform_dist'] = 'default_other_value',
                        other_replacement_method: Dict[str, Literal['default_other_value', 'uniform_dist',  'weighted_uniform_dist']] | Literal['default_other_value', 'uniform_dist',  'weighted_uniform_dist'] = 'default_other_value',
                        default_cat_impute_method: _stat_distributionL = 'weighted_uniform', # used only if the dtype is categorical and the impute method is not compatible with discrete data
                        default_bool_impute_method: _stat_distributionL = 'fixed_value', # used only if the dtype is boolean and the impute method is not compatible with discrete data
                        default_bool_missing_value: Dict[str, bool] | bool = False, # used only if the dtype is boolean and the impute method is not compatible with discrete data
                        columns: Optional[List[str]] = None,
                        inference_stat_config_dict: Optional[Dict[str, Any]] = None, # this is used to bypass statistical collection and overwrite all other parameters
                        random_seed: int = 42
                        ) -> Tuple[pl.DataFrame | pl.LazyFrame, Dict[str, Any]]:
        
        columns = columns or self.columns

        assert all([col in self.columns for col in columns]), f'The following user specified columns were missing from the dataframe: {[col for col in columns if col not in self.columns]}'

        if cohort_col is not None:
            assert cohort_col in self.columns, f'The specified cohort column {cohort_col} was not found in the dataframe columns: {self.columns}'

        if train_cohort is not None:
            assert isinstance(cohort_col, str)
            assert (self._df.filter(pl.col(cohort_col) == train_cohort).collect() if isinstance(self._df, pl.LazyFrame) else self._df.filter(pl.col(cohort_col) == train_cohort)).height > 0, f'The specified training cohort value {train_cohort} was not found in the cohort column {cohort_col}'

        _random_seed: int = next(iter(inference_stat_config_dict.values()))['random_seed'] if isinstance(inference_stat_config_dict, dict) else random_seed
        exprs: List[pl.Expr] = []
        master_stats: Dict[str, Dict[str, Any] | pl.DataFrame] = {}
        rng = np.random.default_rng(_random_seed)

        for col, meta in {name: EnhancedPolars.get_dtype_meta(dtype) for name, dtype in self.schema.items() if name in columns}.items():
            # Skip the cohort column itself from clip and impute processing
            if col in [cohort_col, id_col]:
                continue
            _col_skip_clip: bool = inference_stat_config_dict[col]['skip_clip'] if isinstance(inference_stat_config_dict, dict) else skip_clip.get(col, default_skip_clip) if isinstance(skip_clip, dict) else skip_clip
            _col_skip_impute: bool = inference_stat_config_dict[col]['skip_impute'] if isinstance(inference_stat_config_dict, dict) else skip_impute.get(col, default_skip_impute) if isinstance(skip_impute, dict) else skip_impute
            _core_dtype: CoreDataType = inference_stat_config_dict[col]['core_data_type'] if isinstance(inference_stat_config_dict, dict) else meta['core_data_type']
            _min_cat_count: Optional[int] = inference_stat_config_dict[col]['min_categorical_count'] if isinstance(inference_stat_config_dict, dict) else min_categorical_count.get(col, default_min_categorical_count) if isinstance(min_categorical_count, dict) else min_categorical_count
            _other_repl_method: Literal['default_other_value', 'uniform_dist',  'weighted_uniform_dist'] = inference_stat_config_dict[col]['other_replacement_method'] if isinstance(inference_stat_config_dict, dict) else other_replacement_method.get(col, default_other_replacement_method) if isinstance(other_replacement_method, dict) else other_replacement_method
            _other_repl_value: Any = inference_stat_config_dict[col]['other_replacement_value'] if isinstance(inference_stat_config_dict, dict) else default_other_value

            # Determine the imputation method based on data type
            if isinstance(inference_stat_config_dict, dict):
                # Using inference config - trust it was validated during training
                _impute_null_method = inference_stat_config_dict[col]['null_impute_method']
            elif isinstance(null_distribution, dict) and col in null_distribution:
                # User explicitly specified a method for this column - use it or fail
                _impute_null_method = null_distribution[col]
                # Validate compatibility
                if _core_dtype in [CoreDataType.STRING, CoreDataType.CATEGORICAL, CoreDataType.BOOLEAN]:
                    if _impute_null_method not in ['default_other_value', 'uniform_dist', 'weighted_uniform_dist', 'weighted_uniform', 'uniform', 'fixed_value', None]:
                        raise ValueError(f"Column '{col}' with type {_core_dtype} cannot use imputation method '{_impute_null_method}'. "
                                       f"Only 'default_other_value', 'uniform_dist', 'weighted_uniform_dist', 'weighted_uniform', 'uniform', 'fixed_value', or None are supported.")
                elif _core_dtype not in [CoreDataType.INTEGER, CoreDataType.FLOAT]:
                    # Temporal and other non-numeric types
                    if _impute_null_method is not None:
                        raise ValueError(f"Column '{col}' with type {_core_dtype} cannot be imputed. Set to None to skip imputation.")
            else:
                # No explicit instruction for this column - use safe defaults
                if _core_dtype in [CoreDataType.INTEGER, CoreDataType.FLOAT]:
                    # Numeric types can use the global default
                    _impute_null_method = null_distribution
                elif _core_dtype == CoreDataType.BOOLEAN:
                    # Boolean gets its safe default
                    _impute_null_method = default_bool_impute_method
                elif _core_dtype in [CoreDataType.CATEGORICAL, CoreDataType.STRING]:
                    # Categorical/String get their safe default
                    _impute_null_method = default_cat_impute_method
                else:
                    # Temporal and other types - skip imputation by default
                    _impute_null_method = None
            _impute_val = (inference_stat_config_dict[col]['null_impute_value'] if isinstance(inference_stat_config_dict, dict) else
                           default_missing_value.get(col) if isinstance(default_missing_value, dict) else
                           default_missing_value if default_missing_value in [True, False] else default_bool_missing_value)
            
            upper_con_exp = pl.lit(False)
            upper_then_exp = pl.lit(None)
            lower_con_exp = pl.lit(False)
            lower_then_exp = pl.lit(None)
            other_exp = pl.lit(False)
            other_then_exp = pl.lit(None)
            null_con_exp = pl.lit(False)
            null_then_exp = pl.lit(None)


            master_stats[col] = {
                'core_data_type': _core_dtype,
                'skip_clip': _col_skip_clip,
                'random_seed': _random_seed,
                'min_categorical_count': _min_cat_count,
                'other_replacement_method': _other_repl_method,
                'other_replacement_value': _other_repl_value,
                'null_impute_method': _impute_null_method,
                'null_impute_value': _impute_val
            }

            if (_core_dtype in [CoreDataType.INTEGER, CoreDataType.FLOAT]):
                if not isinstance(inference_stat_config_dict, dict):
                    _col_quantiles: List[float] = default_quantiles

                    for _type, _val in {lower_clip_center_type.get(col) if isinstance(lower_clip_center_type, dict) else lower_clip_center_type: lower_clip_center_value.get(col) if isinstance(lower_clip_center_value, dict) else lower_clip_center_value,
                                        upper_clip_center_type.get(col) if isinstance(upper_clip_center_type, dict) else upper_clip_center_type: upper_clip_center_value.get(col) if isinstance(upper_clip_center_value, dict) else upper_clip_center_value,
                                        null_center_type.get(col) if isinstance(null_center_type, dict) else null_center_type: null_center_value.get(col) if isinstance(null_center_value, dict) else null_center_value,
                                        lower_clip_lower_type.get(col) if isinstance(lower_clip_lower_type, dict) else lower_clip_lower_type: lower_clip_lower_value.get(col) if isinstance(lower_clip_lower_value, dict) else lower_clip_lower_value,
                                        lower_clip_upper_type.get(col) if isinstance(lower_clip_upper_type, dict) else lower_clip_upper_type: lower_clip_upper_value.get(col) if isinstance(lower_clip_upper_value, dict) else lower_clip_upper_value,
                                        upper_clip_lower_type.get(col) if isinstance(upper_clip_lower_type, dict) else upper_clip_lower_type: upper_clip_lower_value.get(col) if isinstance(upper_clip_lower_value, dict) else upper_clip_lower_value,
                                        upper_clip_upper_type.get(col) if isinstance(upper_clip_upper_type, dict) else upper_clip_upper_type: upper_clip_upper_value.get(col) if isinstance(upper_clip_upper_value, dict) else upper_clip_upper_value,
                                        upper_clip_limit_type.get(col) if isinstance(upper_clip_limit_type, dict) else upper_clip_limit_type: upper_clip_limit.get(col) if isinstance(upper_clip_limit, dict) else upper_clip_limit,
                                        lower_clip_limit_type.get(col) if isinstance(lower_clip_limit_type, dict) else lower_clip_limit_type: lower_clip_limit.get(col) if isinstance(lower_clip_limit, dict) else lower_clip_limit,
                                        null_lower_type.get(col) if isinstance(null_lower_type, dict) else null_lower_type: null_lower_value.get(col) if isinstance(null_lower_value, dict) else null_lower_value,
                                        null_upper_type.get(col) if isinstance(null_upper_type, dict) else null_upper_type: null_upper_value.get(col) if isinstance(null_upper_value, dict) else null_upper_value,
                                        }.items():
                        if (_type in ['nth_quantile', 'nth_standard_deviation']) and (isinstance(_val, (int, float)) and (_val not in _col_quantiles)):
                            _col_quantiles.append(float(_val))

                    _col_quantiles = sorted(list(set(_col_quantiles)))

                else:
                    _col_quantiles: List[float] = inference_stat_config_dict[col]['numeric_quantiles']

                master_stats[col]['numeric_quantiles'] = _col_quantiles
            else:
                # Non numeric columns have no quantiles in polars
                _col_quantiles = []

            stats_dict: Dict[str, Any] = cast(Dict[str, Any], generate_smart_stats(df=self._df,
                                        group_by=cohort_col,
                                        columns=[cohort_col, col] if cohort_col is not None else [col],
                                        prefix="",
                                        numeric_config=None,
                                        datetime_config=None,
                                        string_config=None,
                                        categorical_config=None,
                                        boolean_config=None,
                                        other_config=None,
                                        numeric_quantiles=_col_quantiles,
                                        return_type='dictionary',
                                        stack_results=True))

            if isinstance(inference_stat_config_dict, dict):
                stat_dict = inference_stat_config_dict[col]['stat_dict']
                master_stats[col]['stat_dict'] = stat_dict
                master_stats[col]['pre_clip_imputation_stats'] = stats_dict
            else:
                # When stack_results=True with no grouping, stats_dict structure is {column_name: {stat_name: value}}
                # When stack_results=True with grouping, stats_dict structure is {group_value: {column_name: {stat_name: value}}}
                if cohort_col is not None:
                    stat_dict = stats_dict[cast(str, train_cohort)][col]
                else:
                    stat_dict = stats_dict[col]
                master_stats[col]['stat_dict'] = stat_dict
                master_stats[col]['pre_clip_imputation_stats'] = stats_dict


            if not _col_skip_clip and (_core_dtype in [CoreDataType.INTEGER, CoreDataType.FLOAT, CoreDataType.STRING, CoreDataType.CATEGORICAL]):
                if (_core_dtype in [CoreDataType.INTEGER, CoreDataType.FLOAT]):
                    if isinstance(inference_stat_config_dict, dict):
                        _col_lower_clip_limit_type: Optional[_clip_stat_pointsL] = inference_stat_config_dict[col]['lower_clip_limit_type']
                        _col_lower_clip_limit: Optional[float | int] = inference_stat_config_dict[col]['lower_clip_limit']
                        _col_upper_clip_limit_type: Optional[_clip_stat_pointsL] = inference_stat_config_dict[col]['upper_clip_limit_type']
                        _col_upper_clip_limit: Optional[float | int] = inference_stat_config_dict[col]['upper_clip_limit']
                        _col_lower_clip_center_type: Optional[_clip_stat_pointsL] = inference_stat_config_dict[col]['lower_clip_center_type']
                        _col_lower_clip_center: Optional[float | int] = inference_stat_config_dict[col]['lower_clip_center']
                        _col_upper_clip_center_type: Optional[_clip_stat_pointsL] = inference_stat_config_dict[col]['upper_clip_center_type']
                        _col_upper_clip_center: Optional[float | int] = inference_stat_config_dict[col]['upper_clip_center']
                        _col_lower_clip_distribution: Optional[_stat_distributionL] = inference_stat_config_dict[col]['lower_clip_distribution']
                        _col_upper_clip_distribution: Optional[_stat_distributionL] = inference_stat_config_dict[col]['upper_clip_distribution']
                        _col_lower_clip_limit_abs: Optional[float | int] = inference_stat_config_dict[col]['lower_clip_limit_abs']
                        _col_upper_clip_limit_abs: Optional[float | int] = inference_stat_config_dict[col]['upper_clip_limit_abs']
                        _col_lower_clip_center_abs: Optional[float | int] = inference_stat_config_dict[col]['lower_clip_center_abs']
                        _col_upper_clip_center_abs: Optional[float | int] = inference_stat_config_dict[col]['upper_clip_center_abs']
                    else:
                        _col_lower_clip_limit_type: Optional[_clip_stat_pointsL] = lower_clip_limit_type.get(col) if isinstance(lower_clip_limit_type, dict) else lower_clip_limit_type
                        _col_lower_clip_limit: Optional[float | int] = lower_clip_limit.get(col) if isinstance(lower_clip_limit, dict) else lower_clip_limit
                        _col_upper_clip_limit_type: Optional[_clip_stat_pointsL] = upper_clip_limit_type.get(col) if isinstance(upper_clip_limit_type, dict) else upper_clip_limit_type
                        _col_upper_clip_limit: Optional[float | int] = upper_clip_limit.get(col) if isinstance(upper_clip_limit, dict) else upper_clip_limit
                        _col_lower_clip_center_type: Optional[_clip_stat_pointsL] = lower_clip_center_type.get(col) if isinstance(lower_clip_center_type, dict) else lower_clip_center_type # type: ignore
                        _col_lower_clip_center: Optional[float | int] = lower_clip_center_value.get(col) if isinstance(lower_clip_center_value, dict) else lower_clip_center_value
                        _col_upper_clip_center_type: Optional[_clip_stat_pointsL] = upper_clip_center_type.get(col) if isinstance(upper_clip_center_type, dict) else upper_clip_center_type # type: ignore
                        _col_upper_clip_center: Optional[float | int] = upper_clip_center_value.get(col) if isinstance(upper_clip_center_value, dict) else upper_clip_center_value
                        _col_lower_clip_distribution: Optional[_stat_distributionL] = lower_clip_distribution.get(col) if isinstance(lower_clip_distribution, dict) else lower_clip_distribution
                        _col_upper_clip_distribution: Optional[_stat_distributionL] = upper_clip_distribution.get(col) if isinstance(upper_clip_distribution, dict) else upper_clip_distribution

                        _col_lower_clip_limit_abs: Optional[float | int] = (stat_dict.get(f'q{round(100 * _col_lower_clip_limit)}') if (isinstance(_col_lower_clip_limit, (float, int)) and _col_lower_clip_limit_type in ['nth_quantile']) else
                                                                             _col_lower_clip_limit if _col_lower_clip_limit_type in ['fixed_value'] else
                                                                            (stat_dict.get('mean') - (_col_lower_clip_limit * stat_dict['std'])) if (isinstance(_col_lower_clip_limit, (float, int)) and _col_lower_clip_limit_type in ['nth_standard_deviation']) else
                                                                            stat_dict.get(_col_lower_clip_limit_type) if _col_lower_clip_limit_type in ['min', 'max'] else None)

                        _col_upper_clip_limit_abs: Optional[float | int] = (stat_dict.get(f'q{round(100 * _col_upper_clip_limit)}') if (isinstance(_col_upper_clip_limit, (float, int)) and _col_upper_clip_limit_type in ['nth_quantile']) else
                                                                             _col_upper_clip_limit if _col_upper_clip_limit_type in ['fixed_value'] else
                                                                            (stat_dict.get('mean') + (_col_upper_clip_limit * stat_dict['std'])) if (isinstance(_col_upper_clip_limit, (float, int)) and _col_upper_clip_limit_type in ['nth_standard_deviation']) else
                                                                            stat_dict.get(_col_upper_clip_limit_type) if _col_upper_clip_limit_type in ['min', 'max'] else None)
                        _col_lower_clip_center_abs: Optional[float | int] = (stat_dict.get(_col_lower_clip_center_type.replace('median_absolute_deviation', 'mad')) if (isinstance(_col_lower_clip_center, str) and _col_lower_clip_center_type in ['mean', 'min', 'max', 'median', 'mad', 'median_absolute_deviation', 'mode']) else
                                                                             (stat_dict.get('mean') - (_col_lower_clip_center * stat_dict['std'])) if (isinstance(_col_lower_clip_center, (float, int)) and _col_lower_clip_center_type in ['nth_standard_deviation']) else
                                                                             stat_dict.get(f'q{round(100 * _col_lower_clip_center)}') if (isinstance(_col_lower_clip_center, (float, int)) and _col_lower_clip_center_type in ['nth_quantile']) else None)
                        _col_upper_clip_center_abs: Optional[float | int] = (stat_dict.get(f'q{round(100 * _col_upper_clip_center)}') if (isinstance(_col_upper_clip_center, (float, int)) and _col_upper_clip_center_type in ['nth_quantile']) else
                                                                             _col_upper_clip_center if _col_upper_clip_center_type in ['fixed_value'] else
                                                                            (stat_dict.get('mean') + (_col_upper_clip_center * stat_dict['std'])) if (isinstance(_col_upper_clip_center, (float, int)) and _col_upper_clip_center_type in ['nth_standard_deviation']) else
                                                                            stat_dict.get(_col_upper_clip_center_type) if _col_upper_clip_center_type in ['min', 'max'] else None)


                    master_stats[col]['lower_clip_limit'] = _col_lower_clip_limit
                    master_stats[col]['upper_clip_limit'] = _col_upper_clip_limit
                    master_stats[col]['lower_clip_distribution'] = _col_lower_clip_distribution
                    master_stats[col]['upper_clip_distribution'] = _col_upper_clip_distribution
                    master_stats[col]['lower_clip_center_type'] = _col_lower_clip_center_type
                    master_stats[col]['upper_clip_center_type'] = _col_upper_clip_center_type
                    master_stats[col]['lower_clip_center_value'] = _col_lower_clip_center
                    master_stats[col]['upper_clip_center_value'] = _col_upper_clip_center
                    master_stats[col]['lower_clip_limit_type'] = _col_lower_clip_limit_type
                    master_stats[col]['upper_clip_limit_type'] = _col_upper_clip_limit_type
                    master_stats[col]['lower_clip_limit_abs'] = _col_lower_clip_limit_abs
                    master_stats[col]['upper_clip_limit_abs'] = _col_upper_clip_limit_abs
                    master_stats[col]['lower_clip_center_abs'] = _col_lower_clip_center_abs
                    master_stats[col]['upper_clip_center_abs'] = _col_upper_clip_center_abs

                    if isinstance(_col_lower_clip_limit_abs, (int, float)):
                        lower_con_exp: pl.Expr = pl.col(col) < _col_lower_clip_limit_abs
                        
                        if _col_lower_clip_distribution in ['normal', 'median_mad_gaussian', 'truncated_normal', 'median_mad_truncated_gaussian']:
                           
                            _sigma = stat_dict.get('mad') if _col_lower_clip_distribution in ['median_mad_gaussian', 'median_mad_truncated_gaussian'] else stat_dict.get('std')
                            assert isinstance(_sigma, (float, int))

                            if _col_lower_clip_distribution in ['normal', 'median_mad_gaussian']:
                                assert isinstance(_col_lower_clip_center_abs, (float, int))
                                n_samples: int = (self._df.select(lower_con_exp.sum()).collect() if isinstance(self._df, pl.LazyFrame) else self._df.select(lower_con_exp.sum())).item()
                                if n_samples > 0:
                                    lower_then_exp = get_random_normal_exp(n_ext=self.length, mu=_col_lower_clip_center_abs, sigma=_sigma, rng=rng)
                                else:
                                    lower_then_exp = pl.lit(_col_lower_clip_center_abs)
                            else:
                                n_samples: int = (self._df.select(lower_con_exp.sum()).collect() if isinstance(self._df, pl.LazyFrame) else self._df.select(lower_con_exp.sum())).item()
                                assert isinstance(_col_lower_clip_center_abs, (float, int))
                                if n_samples > 0:
                                    lower_then_exp = get_random_truncated_normal_exp(n_ext=self.length, mu=_col_lower_clip_center_abs, sigma=_sigma, lower_z=-1, upper_z=1, random_seed=_random_seed)
                                else:
                                    lower_then_exp = pl.lit(0)
                        elif _col_lower_clip_distribution in ['fixed_value']:
                            assert isinstance(_col_lower_clip_center, (float, int))
                            lower_then_exp = pl.lit(_col_lower_clip_center)
                        else:
                            raise ValueError(f'Unsupported distribution type: {_col_lower_clip_distribution} for imputing low values for col {col}')

                    if isinstance(_col_upper_clip_limit_abs, (int, float)):
                        upper_con_exp: pl.Expr = pl.col(col) > _col_upper_clip_limit_abs

                        if _col_upper_clip_distribution in ['normal', 'median_mad_gaussian', 'truncated_normal', 'median_mad_truncated_gaussian']:
                           
                            _sigma = stat_dict.get('mad') if _col_upper_clip_distribution in ['median_mad_gaussian', 'median_mad_truncated_gaussian'] else stat_dict.get('std')
                            assert isinstance(_sigma, (float, int))

                            if _col_upper_clip_distribution in ['normal', 'median_mad_gaussian']:
                                assert isinstance(_col_upper_clip_center_abs, (float, int))
                                n_samples: int = (self._df.select(upper_con_exp.sum()).collect() if isinstance(self._df, pl.LazyFrame) else self._df.select(upper_con_exp.sum())).item()
                                if n_samples > 0:
                                    upper_then_exp = get_random_normal_exp(n_ext=self.length, mu=_col_upper_clip_center_abs, sigma=_sigma, rng=rng)
                                else:
                                    upper_then_exp = pl.lit(_col_upper_clip_center_abs)
                            else:
                                n_samples: int = (self._df.select(upper_con_exp.sum()).collect() if isinstance(self._df, pl.LazyFrame) else self._df.select(upper_con_exp.sum())).item()
                                assert isinstance(_col_upper_clip_center_abs, (float, int))
                                if n_samples > 0:
                                    upper_then_exp = get_random_truncated_normal_exp(n_ext=self.length, mu=_col_upper_clip_center_abs, sigma=_sigma, lower_z=-1, upper_z=1, random_seed=_random_seed)
                                else:
                                    upper_then_exp = pl.lit(0)
                        elif _col_upper_clip_distribution in ['fixed_value']:
                            assert isinstance(_col_upper_clip_center, (float, int))
                            upper_then_exp = pl.lit(_col_upper_clip_center)
                        else:
                            raise ValueError(f'Unsupported distribution type: {_col_upper_clip_distribution} for imputing low values for col {col}')

            else:
                if _core_dtype in [CoreDataType.CATEGORICAL, CoreDataType.STRING] and isinstance(_min_cat_count, int):
                    _value_counts = stat_dict['value_counts']

                    if not isinstance(inference_stat_config_dict, dict):
                        _value_counts = {k: v for k, v in _value_counts.items() if v >= _min_cat_count}
                        stat_dict['value_counts'] = _value_counts
                        master_stats[col]['stat_dict']['value_counts'] = stat_dict['value_counts']


                    other_exp: pl.Expr = pl.col(col).is_not_null() & ~pl.col(col).is_in(list(_value_counts.keys()))
                    other_n_ext = pl.len().filter(other_exp)

                    if _other_repl_method == 'default_other_value':
                        other_then_exp = pl.lit(_other_repl_value).cast(self.schema[col]) if _core_dtype in [CoreDataType.CATEGORICAL, CoreDataType.STRING] else pl.lit(_other_repl_value)
                    elif _other_repl_method in ['uniform_dist',  'weighted_uniform_dist']:
                        _total_cnts: int = sum(_value_counts.values())
                        if _total_cnts == 0:
                            if _other_repl_value is not None:
                                other_then_exp = pl.lit(_other_repl_value).cast(self.schema[col]) if _core_dtype in [CoreDataType.CATEGORICAL, CoreDataType.STRING] else pl.lit(_other_repl_value)
                            else:
                                other_then_exp = pl.lit(None).cast(self.schema[col]) if _core_dtype in [CoreDataType.CATEGORICAL, CoreDataType.STRING] else pl.lit(None)
                        else:
                            n_samples: int = (self._df.select(other_n_ext).collect() if isinstance(self._df, pl.LazyFrame) else self._df.select(other_n_ext)).item()
                            if n_samples > 0:
                                # Generate random values for all rows, not just the ones that need replacement
                                other_then_exp = get_random_choice_exp(n_ext=self.length, options=list(_value_counts.keys()), rng=rng, return_dtype=self.schema[col], p=[v / _total_cnts for v in _value_counts.values()] if _other_repl_method == 'weighted_uniform_dist' else None)
                            else:
                                other_then_exp = pl.lit(None).cast(self.schema[col]) if _core_dtype in [CoreDataType.CATEGORICAL, CoreDataType.STRING] else pl.lit(None)


            # Skip imputation if explicitly disabled, or if the method is None (for temporal/other types)
            if not _col_skip_impute and _impute_null_method is not None:
                if _core_dtype in [CoreDataType.FLOAT, CoreDataType.INTEGER]:
                    null_con_exp: pl.Expr = pl.col(col).is_null() | pl.col(col).is_nan()
                else:
                    null_con_exp: pl.Expr = pl.col(col).is_null()        

                if isinstance(inference_stat_config_dict, dict):
                    _null_lower_value: Optional[int | float] = inference_stat_config_dict[col]['null_lower_value']
                    _null_lower_value_type: Optional[_stat_pointsL] = inference_stat_config_dict[col]['null_lower_type']
                    _null_upper_value: Optional[int | float] = inference_stat_config_dict[col]['null_upper_value']
                    _null_upper_value_type: Optional[_stat_pointsL] = inference_stat_config_dict[col]['null_upper_type']
                    _null_center_value: Optional[int | float] = inference_stat_config_dict[col]['null_center_value']
                    _null_center_type: Optional[_stat_pointsL] = inference_stat_config_dict[col]['null_center_type']
                    _default_missing_value: Optional[Any] = inference_stat_config_dict[col]['default_missing_value']
                    _null_distribution: Optional[_stat_distributionL] = inference_stat_config_dict[col]['null_distribution']


                    _null_lower_value_abs: Optional[int | float] = inference_stat_config_dict[col]['null_lower_value_abs']
                    _null_upper_value_abs: Optional[int | float] = inference_stat_config_dict[col]['null_upper_value_abs']
                    _null_center_value_abs: Optional[int | float] = inference_stat_config_dict[col]['null_center_value_abs']

                else:
                    _null_lower_value: Optional[int | float] = null_lower_value.get(col) if isinstance(null_lower_value, dict) else null_lower_value
                    _null_lower_value_type: Optional[_stat_pointsL] = null_lower_type.get(col) if isinstance(null_lower_type, dict) else null_lower_type
                    _null_upper_value: Optional[int | float] = null_upper_value.get(col) if isinstance(null_upper_value, dict) else null_upper_value
                    _null_upper_value_type: Optional[_stat_pointsL] = null_upper_type.get(col) if isinstance(null_upper_type, dict) else null_upper_type
                    _null_center_value: Optional[int | float] = null_center_value.get(col) if isinstance(null_center_value, dict) else null_center_value
                    _null_center_type: Optional[_stat_pointsL] = null_center_type.get(col) if isinstance(null_center_type, dict) else null_center_type
                    _default_missing_value: Optional[Any] = default_missing_value.get(col) if isinstance(default_missing_value, dict) else default_missing_value
                    _null_distribution: Optional[_stat_distributionL] = null_distribution.get(col) if isinstance(null_distribution, dict) else null_distribution

                    _null_lower_value_abs: Optional[int | float] = (stat_dict.get(f'q{round(100 * _null_lower_value)}') if (isinstance(_null_lower_value, (float, int)) and _null_lower_value_type in ['nth_quantile']) else
                                                                    _null_lower_value if _null_lower_value_type in ['fixed_value'] else
                                                                    (stat_dict.get('mean') - (_null_lower_value * stat_dict['std'])) if (isinstance(_null_lower_value, (float, int)) and _null_lower_value_type in ['nth_standard_deviation']) else
                                                                    stat_dict.get(_null_lower_value_type) if _null_lower_value_type in ['min', 'max', 'mode', 'mean', 'mad'] else None)
                    
                    _null_upper_value_abs: Optional[int | float] = (stat_dict.get(f'q{round(100 * _null_upper_value)}') if (isinstance(_null_upper_value, (float, int)) and _null_upper_value_type in ['nth_quantile']) else
                                                                    _null_upper_value if _null_upper_value_type in ['fixed_value'] else
                                                                    (stat_dict.get('mean') + (_null_upper_value * stat_dict['std'])) if (isinstance(_null_upper_value, (float, int)) and _null_upper_value_type in ['nth_standard_deviation']) else
                                                                    stat_dict.get(_null_upper_value_type) if _null_upper_value_type in ['min', 'max', 'mode', 'mean', 'mad'] else None)

                    _null_center_value_abs: Optional[int | float] = (stat_dict.get(f'q{round(100 * _null_center_value)}') if (isinstance(_null_center_value, (float, int)) and (_null_center_type or _impute_null_method) in ['nth_quantile']) else
                                                                    _null_center_value if (_null_center_type or _impute_null_method) in ['fixed_value'] else # type: ignore
                                                                    stat_dict.get('mean' if (_null_center_type or _impute_null_method) in ['normal', 'truncated_normal'] else # type: ignore
                                                                                  'median' if (_null_center_type or _impute_null_method) in ['median_mad_gaussian',  'median_mad_truncated_gausian'] else # type: ignore
                                                                                   (_null_center_type or _impute_null_method)) if (_null_center_type or _impute_null_method) in ['mode', 'mean', 'mad', 'median', 'normal', 'truncated_normal', # type: ignore
                                                                                                                                                                                 'median_mad_gaussian',  'median_mad_truncated_gausian'] else None)


                master_stats[col]['null_lower_value_abs'] = _null_lower_value_abs
                master_stats[col]['null_upper_value_abs'] = _null_upper_value_abs
                master_stats[col]['null_center_value_abs'] = _null_center_value_abs
                master_stats[col]['null_lower_value'] = _null_lower_value
                master_stats[col]['null_upper_value'] = _null_upper_value
                master_stats[col]['null_center_value'] = _null_center_value
                master_stats[col]['null_lower_type'] = _null_lower_value_type
                master_stats[col]['null_upper_type'] = _null_upper_value_type
                master_stats[col]['null_center_type'] = _null_center_type
                master_stats[col]['default_missing_value'] = _default_missing_value
                master_stats[col]['null_distribution'] = _null_distribution

                if _impute_null_method in ['fixed_value']:
                    # Validation for categorical/string types during training
                    if _core_dtype in [CoreDataType.BOOLEAN, CoreDataType.CATEGORICAL, CoreDataType.STRING]:
                        _value_counts = stat_dict.get('value_counts', {})
                        if _value_counts:  # Allow for a bypass during training for a label such as UNKNOWN
                            assert _impute_val in _value_counts, f'The candidate missing value: {_impute_val} was missing from the train values of {_value_counts}'
                    # Validation for numeric types
                    elif _core_dtype in [CoreDataType.INTEGER, CoreDataType.FLOAT]:
                        assert isinstance(_impute_val, (int, float)), f'The candidate missing value: {_impute_val} is not a valid {_core_dtype} type'
                        assert (_impute_val >= stat_dict['min']) and (_impute_val <= stat_dict['max']), f'The candidate default missing value was outside the range of the training data [{stat_dict['min']}, {stat_dict['max']}]'
                    
                    # Ensure type compatibility with the column
                    if _core_dtype in [CoreDataType.CATEGORICAL, CoreDataType.STRING]:
                        null_then_exp = pl.lit(_impute_val).cast(self.schema[col])
                    else:
                        null_then_exp = pl.lit(_impute_val)
                elif _impute_null_method in ['uniform_dist',  'weighted_uniform']:
                    # These methods should only be assigned to compatible types due to upfront validation
                    n_samples: int = (self._df.select(null_con_exp.sum()).collect() if isinstance(self._df, pl.LazyFrame) else self._df.select(null_con_exp.sum())).item()
                    if n_samples > 0:
                        if _core_dtype in [CoreDataType.BOOLEAN, CoreDataType.CATEGORICAL, CoreDataType.STRING]:
                            _value_counts = stat_dict['value_counts']
                            _total_cnts: int = sum(_value_counts.values())
                            if _total_cnts == 0:
                                logger.error('There were no valid training examples for imputation.')
                                null_then_exp = pl.lit(None)
                            else:
                                null_then_exp = get_random_choice_exp(n_ext=self.length, options=list(_value_counts.keys()), rng=rng, return_dtype=self.schema[col], p=[v / _total_cnts for v in _value_counts.values()] if _impute_null_method == 'weighted_uniform' else None)
                        else:  # INTEGER or FLOAT
                            assert isinstance(_null_lower_value_abs, (float, int)), f'Missing null_lower_value_abs for {col}'
                            assert isinstance(_null_upper_value_abs, (float, int)), f'Missing null_upper_value_abs for {col}'
                            # Generate random values for all rows
                            null_then_exp = get_random_uniform_exp(n_ext=self.length, low=_null_lower_value_abs, high=_null_upper_value_abs, rng=rng)
                    else:
                        null_then_exp = pl.lit(None)

                elif _impute_null_method in [ 'normal', 'truncated_normal', 'median_mad_gaussian',  'median_mad_truncated_gausian']:
                    # These methods should only be assigned to numeric types due to upfront validation
                    assert isinstance(_null_center_value_abs, (float, int)), f'Missing null_center value for col {col} expected to be of type {_impute_null_method}'
                    
                    _sigma = stat_dict.get('mad') if _impute_null_method in ['median_mad_gaussian', 'median_mad_truncated_gaussian'] else stat_dict.get('std')
                    assert isinstance(_sigma, (float, int)), f'Missing sigma (std/mad) for col {col} with method {_impute_null_method}'

                    n_samples: int = (self._df.select(null_con_exp.sum()).collect() if isinstance(self._df, pl.LazyFrame) else self._df.select(null_con_exp.sum())).item()
                    if n_samples > 0:
                        if _impute_null_method in ['normal', 'median_mad_gaussian']:
                            null_then_exp = get_random_normal_exp(n_ext=self.length, mu=_null_center_value_abs, sigma=_sigma, rng=rng)
                        else:  # truncated_normal or median_mad_truncated_gausian
                            null_then_exp = get_random_truncated_normal_exp(n_ext=self.length, mu=_null_center_value_abs, sigma=_sigma, lower_z=-1, upper_z=1, random_seed=_random_seed)
                    else:
                        null_then_exp = pl.lit(None)

                elif _impute_null_method is None:
                    # Skipping imputation - null_then_exp remains as pl.lit(None)
                    pass
                else:
                    # Any other imputation method not explicitly handled
                    raise ValueError(f'Unhandled imputation method {_impute_null_method} for col {col}')
                
        

            # Build the expression - always create the full when/then chain even if some conditions are False
            # Polars will optimize away the unnecessary conditions
            exprs.append(pl.when(upper_con_exp)
                                    .then(upper_then_exp)
                                    .when(lower_con_exp)
                                    .then(lower_then_exp)
                                    .when(other_exp)
                                    .then(other_then_exp)
                                    .when(null_con_exp)
                                    .then(null_then_exp)
                                    .otherwise(pl.col(col))
                                    .alias(col))
            exprs.append(null_con_exp.alias(f'{col}_null_indicator'))
            
        df = self._df.with_columns(exprs)
        
        master_stats['__final_stats__'] = generate_smart_stats(df=df,
                                        group_by=cohort_col,
                                        columns=None,
                                        prefix="",
                                        numeric_config=None,
                                        datetime_config=None,
                                        string_config=None,
                                        categorical_config=None,
                                        boolean_config=None,
                                        other_config=None,
                                        numeric_quantiles=default_quantiles,
                                        stack_results=True,
                                        return_type='dictionary')

        return df, master_stats
    

    def scale_encode(self,
                     encoder_dir: str | Path,
                     id_column: Optional[str] = None,
                     cohort_col: Optional[str] = None,
                     columns: Optional[List[str]] = None,
                     train_mode: bool = False,
                     one_hot_threshold: Optional[Dict[str, int]] = None,
                     default_one_hot_threshold: int = 10,
                     stat_dict: Optional[Dict[str, Any]] = None,
                     scalar_column_map: Optional[Dict[str, Literal['StandardScaler', 'MinMaxScaler', 'RobustScaler', 'MaxAbsScaler', 'QuantileTransformer',
                                                                   'PowerTransformer', 'LabelEncoder', 'OneHotEncoder', 'OrdinalEncoder']]] = None,
                    default_numeric_scaler: Literal['StandardScaler', 'MinMaxScaler', 'RobustScaler', 'MaxAbsScaler', 'QuantileTransformer',
                                                      'PowerTransformer'] = 'StandardScaler',
                     **kwargs) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        
        results: List[pl.DataFrame] = []
        ml_meta: Dict[str, Any] = {}

        df = self._df.collect() if isinstance(self._df, pl.LazyFrame) else self._df

        columns = [x for x in (columns if isinstance(columns, list) and len(columns) > 0 else df.columns) if (x not in (id_column, cohort_col)) and (x in df.columns)]

        for col in df.columns:
            if col not in columns:
                results.append(df[[col]])
                ml_meta[col] = {'dtype': str(df[col].dtype), 'ml_dtype': 'index_column'}
                continue
            _tp = CoreDataType.get_core_type(cast(Type, df[col].dtype))

            if col in (scalar_column_map or []):
                _scaler = cast(dict, scalar_column_map)[col]
            elif _tp in [CoreDataType.CATEGORICAL, CoreDataType.STRING]:
                _level_dict = (stat_dict or {}).get(col, {}).get('value_counts')
                if isinstance(_level_dict, dict):
                    _levels = sum(list(_level_dict.values()))
                else:
                    _levels = df[col].n_unique()
                _threshold = (one_hot_threshold or {}).get(col, default_one_hot_threshold)

                if _levels > _threshold:
                    _scaler = 'LabelEncoder'
                else:
                    _scaler = 'OneHotEncoder'
            elif _tp.is_numeric:
                _scaler = default_numeric_scaler
            else:
                ml_meta[col] = {'dtype': str(df[col].dtype), 'ml_dtype': 'boolean_indicator' if (_tp == CoreDataType.BOOLEAN and col.endswith('_null_indicator')) else 'boolean' if _tp == CoreDataType.BOOLEAN else 'index_column'}
                results.append(df[[col]])
                continue

            ml_meta[col] = {'dtype': str(df[col].dtype), 'ml_dtype': ('cat_one_hot' if _scaler == 'OneHotEncoder' else
                                                                      'cat_embedding' if _scaler == 'LabelEncoder' else
                                                                      'weighted_count_indicator' if col.endswith('_meta_count') else
                                                                       'numeric')}

            series_udf = df[col].epl.scale_encode(path=Path(encoder_dir) / f'{col}_{_scaler}.joblib', # type: ignore
                                                    scaler_type=_scaler,
                                                    train_mode=train_mode,
                                                    **kwargs)
            if isinstance(series_udf, pl.DataFrame):
                # ml_meta[col]['derived_columns'] = series_udf.columns
                for _col in series_udf.columns:
                    ml_meta[_col] = {'dtype': str(series_udf[_col].dtype), 'ml_dtype': ml_meta[col]['ml_dtype'], 'derived_from': col}
                ml_meta.pop(col, None)
                results.append(series_udf)
            else:
                results.append(series_udf.to_frame())
        
        return pl.concat(results, how='horizontal'), ml_meta
    

    def make_ml_ready(self,
                      encoder_dir: str | Path,
                      columns: Optional[List[str]] = None,
                      replacement_dict: Optional[Dict[Any, Any]] = None,
                      replacement_regex: Optional[Dict[Any, Any]] = None,
                      str_case_standardization: Literal['lower', 'upper', 'title'] = 'upper',
                      na_values: Optional[Dict[str, list[Any]] | list[Any]] = ["", "NA", "N/A", "n/a", "nan", "NULL", "None",
                                                                "#N/A", "#VALUE!", "?", ".", "MISSING", '??'],
                      case_sensitive_repl: bool = False,
                      attempt_downcast: bool = True,
                      attempt_numeric_to_datetime: bool = False,
                      type_analysis_confidence: float = 1.0,
                      type_analysis_n: Optional[int] = None,
                      type_analysis_sample_strat: Literal['first', 'random'] = 'random',
                      random_seed: int = 42,
                      cohort_col: Optional[str] = None,
                      
                      one_hot_threshold: Optional[Dict[str, int]] = None,
                      default_one_hot_threshold: int = 10,
                      scalar_column_map: Optional[Dict[str, Literal['StandardScaler', 'MinMaxScaler', 'RobustScaler', 'MaxAbsScaler', 'QuantileTransformer',
                                                                    'PowerTransformer', 'LabelEncoder', 'OneHotEncoder', 'OrdinalEncoder']]] = None,
                      default_numeric_scaler: Literal['StandardScaler', 'MinMaxScaler', 'RobustScaler', 'MaxAbsScaler', 'QuantileTransformer',
                                                      'PowerTransformer'] = 'StandardScaler',
                      scalar_kwargs: Optional[Dict[str, Any]] = None,
                      id_column: Optional[str] = None,
                      time_column: Optional[str] = None,
                      time_series_operations: Optional[List[str]] = None,
                      time_series_kwargs: Optional[Dict[str, Any]] = None,
                      default_quantiles: List[float] = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99],
                      **clip_and_impute_kwargs
                      ) -> Tuple[pl.DataFrame, Dict[str, Any]]:
        df = self.standardize(columns=columns, replacement_dict=replacement_dict,
                              replacement_regex=replacement_regex, metadata_columns=[id_column, cohort_col, time_column], # type: ignore
                              str_case_standardization=str_case_standardization,
                              na_values=na_values,
                              case_sensitive_repl=case_sensitive_repl)

        df, og_meta = PolarsMLPipeline(df).optimize_dtypes_and_get_meta(attempt_downcast=attempt_downcast,
                               attempt_numeric_to_datetime=attempt_numeric_to_datetime,
                               confidence=type_analysis_confidence,
                               n=type_analysis_n,
                               sample_strat=type_analysis_sample_strat,
                               collect_precision_scale=False,
                               columns=columns,
                               seed=random_seed)
        
        df, ml_meta = PolarsMLPipeline(df).clip_and_impute(random_seed=random_seed,  default_quantiles=default_quantiles, cohort_col=cohort_col,
                                                           skip_impute=isinstance(time_column, str),
                                                           columns=columns,
                                                           id_col=id_column, **clip_and_impute_kwargs)

        if isinstance(time_series_operations, list) and len(time_series_operations) > 0:
            assert isinstance(time_column, str) and time_column in self.columns, 'A valid time_column must be specified for time series operations'
            assert isinstance(id_column, str) and id_column in self.columns, 'A valid id_column must be specified for time series operations'

            # Preserve metadata columns during time series operations
            preserve_columns = [id_column]
            if cohort_col is not None and cohort_col in df.columns:
                preserve_columns.append(cohort_col)
            
            df = PolarsDataFrameInterpolationExtension(df).process_time_series_v2(time_column=time_column,
                                operations=time_series_operations,
                                group_by=preserve_columns,
                                target_columns=columns,
                                simple_column_names=True,
                                **(time_series_kwargs or {}))
            
            _meta_cols = [col for col in df.columns if col.endswith('_meta_count')]
            if len(_meta_cols) > 0:
                df = df.with_columns([(pl.col(col).fill_null(0).cast(pl.Int32) == 0).alias(col.replace('_meta_count', '_null_indicator')) for col in _meta_cols])

            
            ml_meta['__final_stats__pre_time_series__'] = ml_meta['__final_stats__']

            ml_meta['ts_kwargs'] = {'time_column': time_column,
                                    'operations': time_series_operations,
                                    'group_by': [id_column],
                                    'target_columns': columns,
                                    'simple_column_names': True,
                                    **(time_series_kwargs or {})}
            
            # Exclude metadata columns from stats generation after time series processing
            stats_columns = [col for col in df.columns if col not in [id_column, time_column, cohort_col, '_lower_boundary', '_upper_boundary']]
            
            ml_meta['__final_stats__'] =  generate_smart_stats(df=df,
                                        group_by=cohort_col,
                                        columns=stats_columns,
                                        prefix="",
                                        numeric_config=None,
                                        datetime_config=None,
                                        string_config=None,
                                        categorical_config=None,
                                        boolean_config=None,
                                        other_config=None,
                                        numeric_quantiles=default_quantiles,
                                        stack_results=True,
                                        return_type='dictionary')


        df, col_meta = PolarsMLPipeline(df).scale_encode(encoder_dir=encoder_dir,
                                               id_column=id_column,
                     cohort_col=cohort_col,
                     train_mode=not isinstance(clip_and_impute_kwargs.get('inference_stat_config_dict'), dict),
                     one_hot_threshold=one_hot_threshold,
                     columns=columns,
                     default_one_hot_threshold=default_one_hot_threshold,
                     scalar_column_map=scalar_column_map,
                     stat_dict=ml_meta['__final_stats__'], # type: ignore
                     default_numeric_scaler=default_numeric_scaler,
                     **(scalar_kwargs or {}))
        
        return df, {'type_optimization_meta': og_meta, 'ml_preprocess_meta': ml_meta, 'col_meta': col_meta}




@pl.api.register_series_namespace('epl')
class SeriesMLUtils:

    def __init__(self, series: pl.Series):
        self._series = series
        self._dtype = series.dtype
        self._core_dtype: CoreDataType = CoreDataType.get_core_type(cast(Type, series.dtype))

    def isnull(self) -> pl.Series:
        """
        TRUE if null OR (float and NaN).
        """
        if self._core_dtype == CoreDataType.FLOAT:
            return self._series.is_null() | self._series.is_nan()
        else:
            return self._series.is_null()
    
    def notnull(self) -> pl.Series:
        """
        Logical inverse of is_null_or_nan.
        """
        return ~self.isnull()
    
    def isnull_expr(self) -> pl.Expr:
        """
        Create a dtype-aware expression for null/NaN detection on this series.
        Use this when you need the expression for DataFrame operations.
        
        Returns:
            Expression that checks null OR NaN (for float types only)
        """
        if self._core_dtype == CoreDataType.FLOAT:
            return pl.col(self._series.name).is_null() | pl.col(self._series.name).is_nan()
        else:
            return pl.col(self._series.name).is_null()
    
    def notnull_expr(self) -> pl.Expr:
        """
        Create a dtype-aware expression for non-null/non-NaN detection on this series.
        Use this when you need the expression for DataFrame operations.
        
        Returns:
            Expression that checks NOT null AND NOT NaN (for float types only)
        """
        if self._core_dtype == CoreDataType.FLOAT:
            return (pl.col(self._series.name).is_not_null()) & (~pl.col(self._series.name).is_not_nan())
        else:
            return pl.col(self._series.name).is_not_null()

    def dropna(self) -> pl.Series:
        """
        Drop null/NaN values from the series.
        """
        if self._core_dtype == CoreDataType.FLOAT:
            return self._series.filter(self.notnull())
        return self._series.drop_nulls()

    def scale_encode(self, 
              path: str | Path,
              scaler_type: Literal['StandardScaler', 'MinMaxScaler', 'RobustScaler', 'MaxAbsScaler', 'QuantileTransformer',
                                   'PowerTransformer', 'LabelEncoder', 'OneHotEncoder', 'OrdinalEncoder'] = 'StandardScaler',
              train_mode: bool = False,
              **kwargs) -> pl.Series | pl.DataFrame:
        """
        Apply scaling transformation to the series using various scikit-learn scalers.
        
        Args:
            path: File path to save/load the fitted scaler
            scaler_type: Type of scaler to apply. Default is 'StandardScaler'. Options are:
                - 'StandardScaler': Standardize features by removing the mean and scaling to unit variance.
                  Use when: Data is normally distributed, you need zero mean and unit variance,
                  features have different scales, and you're using algorithms sensitive to scale (SVM, neural networks).
                  Formula: (x - mean) / std
                  
                - 'MinMaxScaler': Transform features to a given range (usually 0-1).
                  Use when: You need bounded values in a specific range, data has outliers that you want to preserve,
                  or you're working with neural networks that benefit from [0,1] input range.
                  Formula: (x - min) / (max - min)
                  
                - 'RobustScaler': Scale features using statistics that are robust to outliers.
                  Use when: Data contains many outliers, you want to preserve outlier information,
                  or standard scaling is too sensitive to extreme values.
                  Formula: (x - median) / IQR where IQR = Q3 - Q1
                  
                - 'MaxAbsScaler': Scale each feature by its maximum absolute value.
                  Use when: Data is sparse (many zeros), you want to preserve sparsity,
                  or you need values in [-1, 1] range without shifting the data.
                  Formula: x / |max(x)|
                  
                - 'QuantileTransformer': Transform features to follow a uniform or normal distribution.
                  Use when: You want to reduce impact of outliers, need to transform to uniform/normal distribution,
                  or data has complex non-linear relationships.
                  Non-linear transformation based on quantiles.
                  
                - 'PowerTransformer': Apply a power transformation to make data more Gaussian-like.
                  Use when: Data is skewed and you need it to be more normally distributed,
                  you're using algorithms that assume normality (linear regression, LDA).
                  Uses Box-Cox or Yeo-Johnson transformation.

                - 'OneHotEncoder': Convert categorical variables into a format that works better with machine learning algorithms.
                  Use when: You have categorical features and want to avoid ordinal encoding pitfalls.
                  Formula: Creates binary columns for each category.

                - 'OrdinalEncoder': Convert categorical variables into ordinal integers.
                  Use when: You have ordinal categorical features and want to preserve their order.
                  Formula: Maps each category to an integer based on its order.

                - 'LabelEncoder': Convert categorical variables into labels.
                  Use when: You have categorical features and want to convert them into a format suitable for ML algorithms.
                  Formula: Maps each category to a unique integer.

            train_mode: If True, fit the scaler on current data and save it. If False, load existing scaler and transform.
            **kwargs: Additional keyword arguments passed to the scaler constructor. Examples:
                - StandardScaler: with_mean=True, with_std=True
                - MinMaxScaler: feature_range=(0, 1), clip=False
                - RobustScaler: quantile_range=(25.0, 75.0), with_centering=True, with_scaling=True
                - MaxAbsScaler: copy=True
                - QuantileTransformer: n_quantiles=1000, output_distribution='uniform', subsample=100000
                - PowerTransformer: method='yeo-johnson', standardize=True
        
        Returns:
            Self: The scaled series
            
        Raises:
            ValueError: If scaler_type is not supported or series contains non-numeric data
            FileNotFoundError: If train_mode=False and scaler file doesn't exist
            
        """
        assert SKLEARN_AVAILABLE, f'Scikit-learn is not available. Please install it to use this method.'

        

        if self._core_dtype not in [CoreDataType.FLOAT, CoreDataType.INTEGER, CoreDataType.CATEGORICAL, CoreDataType.STRING]:
            msg: str = f"Scaling/encoding can only be applied to numeric or categorical/string data. Series dtype is {self._core_dtype}"
            logger.error(msg)
            raise ValueError(msg)
        
        # Log start of scaling
        if logger:
            logger.info(f"Starting scaling/encoding with {scaler_type}, train_mode={train_mode}")
            logger.debug(f"Scaler/Encoder path: {path}")
            if kwargs:
                logger.debug(f"Scaler/Encoder kwargs: {kwargs}")
        
        # Create scaler instance based on type
        scaler_mapping = {
            'StandardScaler': StandardScaler, # type: ignore
            'MinMaxScaler': MinMaxScaler, # type: ignore
            'RobustScaler': RobustScaler, # type: ignore
            'MaxAbsScaler': MaxAbsScaler, # type: ignore
            'QuantileTransformer': QuantileTransformer, # type: ignore
            'PowerTransformer': PowerTransformer, # type: ignore
            'LabelEncoder': LabelEncoder, # type: ignore
            'OneHotEncoder': OneHotEncoder, # type: ignore
            'OrdinalEncoder': OrdinalEncoder # type: ignore
        }
        
        if scaler_type not in scaler_mapping:
            error_msg = f"Unsupported scaler type: {scaler_type}. Must be one of {list(scaler_mapping.keys())}"
            if logger:
                logger.error(error_msg)
            raise ValueError(error_msg)
        
       
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if logger:
                logger.debug(f"Created directory for scaler path: {os.path.dirname(path)}")
        except Exception as e:
            error_msg = f"Failed to create directory for path {path}: {e}"
            if logger:
                logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Convert series to numpy array and reshape for sklearn (needs 2D array)
        assert self.notnull().any(), "Cannot scale series with all null values. Please impute before scaling." # type: ignore

        if train_mode:
            # Create, fit, and save scaler
            if logger:
                logger.info(f"Training {scaler_type} scaler")
            
            scaler = scaler_mapping[scaler_type](**kwargs)
            fit_data = self.dropna().to_numpy()
            # LabelEncoder expects 1D array, other scalers expect 2D
            if scaler_type == 'LabelEncoder':
                scaler.fit(fit_data.ravel())
            else:
                scaler.fit(fit_data.reshape(-1, 1))  # type: ignore
            
            if logger:
                try:
                    non_null_count = len(self.dropna())  # type: ignore
                    logger.debug(f"Fitted {scaler_type} on {non_null_count} non-null values")
                except:
                    logger.debug(f"Fitted {scaler_type} scaler successfully")
            
            # Save the fitted scaler
            joblib.dump(scaler, path)
            
            if logger:
                logger.info(f"Saved fitted {scaler_type} to {path}")

        else:
            # Load existing scaler and transform
            if not os.path.exists(path):
                error_msg = f"Scaler file not found at {path}. Run in train_mode=True first to create the scaler."
                if logger:
                    logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            scaler = joblib.load(path)
            
            if logger:
                logger.info(f"Loaded {scaler_type} scaler from {path}")
        
        # Transform and return new Series
        if logger:
            logger.debug(f"Applying transformation to series with {len(self._series)} values")
        
        try:
            if scaler_type == 'OneHotEncoder':
                # OneHotEncoder always returns sparse matrix, convert to dense
                result = pl.DataFrame(scaler.transform(self._series.to_numpy().reshape(-1, 1)).toarray().astype('int8'), schema=scaler.get_feature_names_out([self._series.name]).tolist())
            elif scaler_type == 'LabelEncoder':
                # LabelEncoder expects 1D array and returns 1D array
                result = pl.Series(values=scaler.transform(self._series.to_numpy().ravel()).astype('int32'), name=self._series.name)
            else:
                # Numeric scalers return floats, OrdinalEncoder returns ints
                result = pl.Series(values=scaler.transform(self._series.to_numpy().reshape(-1, 1)).flatten().astype('int32' if scaler_type == 'OrdinalEncoder' else 'float32'), name=self._series.name)  # type: ignore

            if logger:
                logger.info(f"Successfully completed {scaler_type} scaling/encoding")
                if self._core_dtype in [CoreDataType.FLOAT, CoreDataType.INTEGER]:
                    logger.debug(f"Transformed series stats - Mean: {result.mean():.4f}, Std: {result.std():.4f}")
            
            return result
        except Exception as e:
            error_msg = f"Failed to transform data with {scaler_type}: {e}"
            if logger:
                logger.error(error_msg)
            raise RuntimeError(error_msg)

    def format_for_sql(
        self,
        column_specification: str,
        dialect: "SQLDialect"
    ) -> pl.Series:
        """
        Format this Series for SQL insertion based on column specification.

        Parameters
        ----------
        column_specification : str
            SQL column type specification (e.g., 'VARCHAR(100)', 'INTEGER').
        dialect : SQLDialect
            Target database dialect.

        Returns
        -------
        pl.Series
            Formatted series ready for SQL insertion.

        Examples
        --------
        >>> s = pl.Series("name", ["Alice", "Bob", "Charlie"])
        >>> formatted = s.epl.format_for_sql('VARCHAR(10)', SQLDialect.POSTGRES)
        """
        from .to_sql import format_column_expr_for_sql
        col_name = self._series.name or "_col"
        expr = format_column_expr_for_sql(col_name, column_specification, dialect)
        return pl.DataFrame({col_name: self._series}).select(expr).to_series()

