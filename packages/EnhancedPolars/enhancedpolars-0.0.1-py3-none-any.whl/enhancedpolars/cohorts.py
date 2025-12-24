from .epl import EnhancedPolars as ep
import polars as pl
from typing import Optional, Union, Literal, List, Dict, Any, cast, Tuple
from .base import UniversalPolarsDataFrameExtension
from CoreUtilities.enhanced_logging import get_logger
from math import floor
import pandas as pd

try:
    from sklearn.model_selection import StratifiedShuffleSplit, train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class PolarsCohorts(UniversalPolarsDataFrameExtension):
    """
    Polars DataFrame/LazyFrame extension that provides enhanced merging capabilities with automatic
    dtype conflict resolution.
    
    This extension provides merge, merge_asof, and concat methods that automatically
    handle dtype mismatches by finding compatible types before merging.
    """
    
    def __init__(self, df: Any):
        super().__init__(df)

        self.logger = get_logger(__name__)


    def train_test_val_split(self,
                             project_name: Optional[str] = None,
                                    dev_percent: float = 0.7,
                                    val_percent: float = 0.1,
                                    test_percent: float = 0.2,
                                    split_type: Literal['longitudinal', 'random', 'longitudinal_with_random_fallback'] = 'longitudinal_with_random_fallback',
                                    stratification_columns: Optional[List[str]] = None,
                                    time_index_col: Optional[str] = None,
                                    unique_index_col: str = 'row_id',
                                    random_state: int = 20) -> pl.DataFrame:
            """
            Split a dataframe into development, test, and/or validation cohorts.

            Parameters
            ----------
            project_name : str
                Project name.
            dev_percent : float, optional
                Percentage for development. The default is 0.7.
            split_type : str, optional
                type of split ['longitudinal' or 'random']. The default is 'longitudinal'.
            stratification_columns : list, optional
                columns to stratify the dataframe by first before splitting. The default is None.
            unique_index_col : str, optional
                Column which is unique to each line, if one is not provided one will provided for you. The default is 'row_id'.
            random_state : int, optional
                random sate used to split the data. The default is 20.

            Raises
            ------
            Exception
                DESCRIPTION.

            Returns
            -------
            pl.DataFrame

            """
            assert dev_percent + val_percent + test_percent == 1, 'The development, validation, and test cohorts must add up to 100%%'
            assert (dev_percent > 0) or (test_percent == 1) or (val_percent == 1), 'The development cohort percentage must be greater than 0 if splitting into development, validation, and test cohorts.'

            # create a deep copy with a fresh index
            df = (self._df.collect() if self.is_lazy else self._df).to_pandas() # type: ignore

            if (dev_percent == 1) or (test_percent == 1) or (val_percent == 1):
                only_cohort: str = (f'{project_name}_' if project_name else '') + ('Development' if dev_percent == 1 else 'Test' if test_percent == 1 else 'Validation')
                self.logger.warning(f'Only one cohort specified: {only_cohort} cohort will be created.')
                df['cohort'] = only_cohort
                return pl.from_pandas(df)
            elif df.shape[0] in [0, 1]:
                only_cohort: str = (f'{project_name}_' if project_name else '') + ('Development' if dev_percent > 1 else 'Test' if test_percent == 1 else 'Validation')
                self.logger.warning('DataFrame is empty or has only one row, no split will be performed.')
                df['cohort'] = only_cohort
                return pl.from_pandas(df)

            # create a unique index if one is not specified
            if unique_index_col not in df.columns:
                cols_to_drop: list = [unique_index_col]
                df = df.reset_index(drop=False).rename(columns={'index': unique_index_col})
            else:
                cols_to_drop: list = []

            project_name = f'{project_name}_' if project_name else ''

            # create cohort column
            df['cohort'] = None

            if (split_type == 'longitudinal_with_random_fallback') and isinstance(time_index_col, str) and time_index_col in df.columns:
                # if the time index column is specified, use longitudinal split
                split_type = 'longitudinal'
            elif split_type == 'longitudinal_with_random_fallback':
                # if the time index column is not specified, use random split
                self.logger.warning('Using random split as no time index column was specified for longitudinal split.')
                split_type = 'random'

            # if it is a time split
            if split_type == 'longitudinal':
                assert isinstance(time_index_col, str), 'A time index column must be specified for longitudinal splits.'
                assert time_index_col in df.columns, f'The column: {time_index_col}, was not found in the dataframe: {df.columns.tolist()}'

                # sort by time_index
                df = df.sort_values(time_index_col, ascending=True)

                # stratify split by columns if specified
                if isinstance(stratification_columns, list):
                    valuesets = df[stratification_columns].copy().drop_duplicates()

                    for _, valueset in valuesets.iterrows():
                        vs_label = '_'.join(valueset.astype(str))

                        rows = df.loc[(df[stratification_columns] == valueset).apply(all, axis=1),
                                    [time_index_col, unique_index_col]]\
                            .set_index(unique_index_col)[time_index_col]\
                            .sort_values(ascending=True)

                        max_dev_date = pd.to_datetime('1970-01-01').date() if dev_percent == 0 else rows.iloc[floor(rows.shape[0] * dev_percent)].date()

                        if dev_percent > 0:
                            df.loc[df[unique_index_col].isin(rows[rows.dt.date <= max_dev_date].index),
                                'cohort'] = f'{project_name}Development_{vs_label}_{rows.min().date()}_{max_dev_date}'

                        max_val_date = max(pd.to_datetime('1970-01-02').date(), max_dev_date) if val_percent == 0 else rows.iloc[floor(rows.shape[0] * (dev_percent + val_percent))].date()

                        if val_percent > 0:
                            df.loc[df[unique_index_col].isin(rows[(rows.dt.date > max_dev_date) & (rows.dt.date <= max_val_date)].index),
                                'cohort'] = f'{project_name}Validation_{vs_label}_{rows[rows.dt.date > max_dev_date].min().date()}_{max_val_date}'

                        if test_percent > 0:
                            df.loc[df[unique_index_col].isin(rows[rows.dt.date > max_val_date].index),
                                'cohort'] = f'{project_name}Test_{vs_label}_{rows[rows.dt.date > max_val_date].min().date()}_{rows.dt.date.max()}'

                # split without stratification
                else:

                    max_dev_date = pd.to_datetime('1970-01-01').date() if dev_percent == 0 else df.iloc[floor(df.shape[0] * dev_percent), df.columns.get_loc(time_index_col)].date() # type: ignore

                    if dev_percent > 0:
                        df.loc[df[time_index_col].dt.date <= max_dev_date, 'cohort'] = f'{project_name}Development_{df[time_index_col].min().date()}_{max_dev_date}'

                    max_val_date = max(pd.to_datetime('1970-01-02').date(), max_dev_date) if val_percent == 0 else df.iloc[floor(df.shape[0] * (dev_percent + val_percent)), df.columns.get_loc(time_index_col)].date() # type: ignore

                    if val_percent > 0:
                        df.loc[((df[time_index_col].dt.date > max_dev_date) & (df[time_index_col].dt.date <= max_val_date)),
                            'cohort'] = f'{project_name}Validation_{df.loc[df[time_index_col].dt.date > max_dev_date, time_index_col].min().date()}_{max_val_date}'

                    if test_percent > 0:
                        df.loc[df[time_index_col].dt.date > max_val_date,
                            'cohort'] = f'{project_name}Test_{df.loc[df[time_index_col].dt.date > max_val_date, time_index_col].min().date()}_{df[time_index_col].max().date()}'

            elif split_type == 'random':
                assert SKLEARN_AVAILABLE, 'sklearn is required for random splitting. Please install it to use this feature.'
                if isinstance(stratification_columns, list):
                    sss = StratifiedShuffleSplit(n_splits=1, train_size=dev_percent, random_state=random_state) # type: ignore
                    try:
                        df = PolarsCohorts._sss(df=df,
                                sss=sss, # type: ignore
                                stratification_columns=stratification_columns,
                                train_cohort_name=f'{project_name}Development',
                                test_cohort_name=f'{project_name}Validation' if val_percent > 0 else f'{project_name}Test') # type: ignore
                    except AssertionError as e:
                        self.logger.warning(f"Stratified split failed: {e}. Falling back to random split without stratification.")
                        # Fallback to random split without stratification
                        development, validation = train_test_split(df, # type: ignore
                                                                    train_size=dev_percent,
                                                                    random_state=random_state)

                        development.loc[:, 'cohort'] = f'{project_name}Development'
                        validation.loc[:, 'cohort'] = f'{project_name}Validation' if val_percent > 0 else f'{project_name}Test'

                        df = pd.concat([development, validation], axis=0, sort=False, ignore_index=True)

                    if val_percent > 0:
                        sss2 = StratifiedShuffleSplit(n_splits=1, train_size=(val_percent / (test_percent + val_percent)), random_state=random_state) # type: ignore
                        df2_stage = df[df.cohort == f'{project_name}Validation'].copy(deep=True)
                        df2_stage['cohort'] = None

                        try:
                            df_part2 = PolarsCohorts._sss(df=df2_stage,
                                    sss=sss, # type: ignore
                                    stratification_columns=stratification_columns,
                                    train_cohort_name=f'{project_name}Validation',
                                    test_cohort_name=f'{project_name}Test') # type: ignore
                        except AssertionError as e:
                            self.logger.warning(f"Stratified split failed: {e}. Falling back to random split without stratification.")
                            # Fallback to random split without stratification
                            validation, test = train_test_split(df, # type: ignore
                                                                    train_size=(val_percent / (test_percent + val_percent)),
                                                                    random_state=random_state)

                            validation.loc[:, 'cohort'] = f'{project_name}Validation'
                            test.loc[:, 'cohort'] = f'{project_name}Test'

                            df_part2 = pd.concat([test, validation], axis=0, sort=False, ignore_index=True)

                        # stack the parts back together
                        df = pd.concat([df[df.cohort == f'{project_name}Development'], df_part2], axis=0, sort=False, ignore_index=True)

                else:
                    development, temp = train_test_split(df, # type: ignore
                                                        train_size=dev_percent,
                                                        random_state=random_state)

                    development.loc[:, 'cohort'] = f'{project_name}Development'

                    test, validation = train_test_split(temp, # type: ignore
                                                        train_size=(test_percent / (test_percent + val_percent)),
                                                        random_state=random_state)

                    test.loc[:, 'cohort'] = f'{project_name}Test'
                    validation.loc[:, 'cohort'] = f'{project_name}Validation'

                    df = pd.concat([development, validation, test], axis=0, sort=False)
            else:
                raise Exception('Unsupported slit_type')

            return pl.from_pandas(df.drop(columns=cols_to_drop))
    
    
    @staticmethod
    def _sss(df: pd.DataFrame,
                sss: StratifiedShuffleSplit, # type: ignore
                stratification_columns: List[str],
                train_cohort_name: str = 'train',
                test_cohort_name: str = 'test') -> pd.DataFrame:
        """
        Perform stratified shuffle split on a DataFrame with fallback handling for low-prevalence combinations.
        This function splits a DataFrame into train and test cohorts using stratified sampling based on
        specified columns. When certain stratification combinations have insufficient samples (< 3), 
        the function handles these "orphan" cases by separating them and applying random assignment.
        Args:
            df (pd.DataFrame): Input DataFrame to be split
            sss (StratifiedShuffleSplit): Configured StratifiedShuffleSplit object from sklearn
            stratification_columns (List[str]): List of column names to use for stratification
            train_cohort_name (str, optional): Name for the training cohort. Defaults to 'train'
            test_cohort_name (str, optional): Name for the test cohort. Defaults to 'test'
        Returns:
            pd.DataFrame: Original DataFrame with an additional 'cohort' column indicating 
                            train/test assignment
        Raises:
            AssertionError: If there are insufficient unique combinations of stratification 
                            columns to perform any split (even after handling orphans)
            ValueError: Re-raised from StratifiedShuffleSplit when stratification fails
        Notes:
            - The function resets the DataFrame index to ensure clean positional indexing
            - Combinations with fewer than 3 occurrences are treated as "orphans" and handled separately
            - Orphan cases are randomly assigned to cohorts, with single orphans assigned to training
            - The returned DataFrame maintains all original data with cohort assignments added
        """
        # ensure a clean positional index
        df = df.reset_index(drop=True)
        X = df.drop(columns=stratification_columns)
        y = df[stratification_columns]
        try:
            dev_index, val_index = next(sss.split(X, y)) # type: ignore
            
            # set the cohorts
            df.loc[dev_index, 'cohort'] = train_cohort_name
            df.loc[val_index, 'cohort'] = test_cohort_name
            return df
            
        except ValueError as e:
            # make series of the unique combinations and their counts
            strat_val_counts = y.value_counts()
            
            # filter out the combinations with too low of a prevalence to split via stratification
            orphans = strat_val_counts[strat_val_counts < 3]
            
            assert (strat_val_counts.shape[0] - orphans.shape[0]) > 0, 'There are insufficient combinations of stratification columns. Please either reduce the number of columns to stratify on or use a random split.'
            
            # seperate out the orphans from the rest of the data
            y_orphans = y.reset_index(drop=False).rename(columns={'index': '_orig_idx'})\
                .merge(orphans.index.to_frame().reset_index(drop=True), on=stratification_columns, how='right')\
                .set_index('_orig_idx')
            x_orphans = X.loc[y_orphans.index]
            
            # reset the index of the candidates for the returned index is positional
            y_candidates = y.loc[~y.index.isin(y_orphans.index.values)].reset_index(drop=True)
            X_candidates = X.loc[~X.index.isin(y_orphans.index.values)].reset_index(drop=True)
            
            # re-attempt the split
            dev_index, val_index = next(sss.split(X_candidates, y_candidates)) # type: ignore
            
            # concatenate X and y candidates
            df_part_1: pd.DataFrame = pd.concat([X_candidates, y_candidates], axis=1)
            
            # add cohort column
            df_part_1.loc[dev_index, 'cohort'] = train_cohort_name
            df_part_1.loc[val_index, 'cohort'] = test_cohort_name
            
            
            # merge the orphan dataframes and get rid of the index
            df_part_2: pd.DataFrame = x_orphans.merge(y_orphans, left_index=True, right_index=True).reset_index(drop=True)
            
            if y_orphans.shape[0] > 1:
                # randomly assign the orphans
                orphan_dev_index, orphan_val_index = next(sss.split(list(range(y_orphans.shape[0])), [1]*y_orphans.shape[0])) # type: ignore
                
                # assign the orphans to the cohorts
                df_part_2.loc[orphan_dev_index, 'cohort'] = train_cohort_name
                df_part_2.loc[orphan_val_index, 'cohort'] = test_cohort_name
            else:
                # assign the odd_ball to the dev cohort
                df_part_2['cohort'] = train_cohort_name
                
            # re-stack the two parts
            return pd.concat([df_part_1, df_part_2], ignore_index=True, axis=0)