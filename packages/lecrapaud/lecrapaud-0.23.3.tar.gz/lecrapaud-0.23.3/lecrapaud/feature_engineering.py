"""
Feature engineering module for data preprocessing and transformation.

Process
-------
FEAT ENG
- utiliser business_analysis > get_table_summary pour voir quels sont les champs null à + de 90%
- utiliser remove_constant_columns pour supprimer les colonnes constantes
- utiliser summarize_dataframe pour supprimer de nouvelles colonnes inutiles (date, id, donnée future à la prédiction, misc not useful)
- caster en numeric ce qui peut être casté en numeric

- definir columns_boolean
- definir groupby_columns_list et target_column pour le target encoding
- créer la/les targets
- définir columns_pca
- définir columns_one_hot, columns_binary, columns_ordinal, columns_frequency


Todo
----
- DONE: drop meaningless identifier columns
- DONE: PCA on embedding of deck
- DONE: maybe cyclic encoding for date columns

- DONE: ordinal/label encode (only 1 column) for tree based method when not too big number of categories
- DONE: frequency encoding for some categorical columns
- DONE: one hot encoding for categorical columns
- DONE: binary encoding if big number of category

- DONE: create other other embedding column for textual data ?
- DONE: create some boolean like has_website, has_linkedin_company_url, etc...

- target/mean encoding with a groupby on a very interesting categorical column
- faire du "vrai" target encoding avec du leave one out encoding par exemple, sur la target variable ?

- better categorize some stuff like country ? for sourcing we do position, ext_position, company, ext_company, country, source, but only country is relevant here


Development
-----------
- utiliser le PCA pour définir combien de variable explique la variance pour la feature selection max_feature
- could be nice to get linkedin info of founders (need to search reps in rails first) - and score !
- add created_from, utm_source, referrer when we will have more data
- could be nice to get team_count, or dealroom info but at the moment of submission...
"""

import pandas as pd
import numpy as np
import os
from itertools import product

from lecrapaud.integrations.openai_integration import (
    truncate_text,
    get_openai_embeddings,
)
from lecrapaud.utils import logger
from lecrapaud.mixins import LeCrapaudEstimatorMixin


# main function
class FeatureEngineer(LeCrapaudEstimatorMixin):
    """
    Feature engineering pipeline

    Params needed
    -------------
    data
    columns_boolean
    columns_date
    columns_te_groupby
    columns_te_target
    """

    def __init__(
        self,
        experiment=None,
        **kwargs,
    ):
        # The mixin will automatically set all experiment.context parameters as attributes
        # and kwargs will override them if provided
        super().__init__(experiment=experiment, **kwargs)

        # Set defaults for required parameters if not provided
        if not hasattr(self, "columns_drop"):
            self.columns_drop = []
        if not hasattr(self, "columns_boolean"):
            self.columns_boolean = []
        if not hasattr(self, "columns_date"):
            self.columns_date = []
        if not hasattr(self, "columns_te_groupby"):
            self.columns_te_groupby = []
        if not hasattr(self, "columns_te_target"):
            self.columns_te_target = []
        if not hasattr(self, "fourier_order"):
            self.fourier_order = 1

        if self.experiment:
            self.experiment_dir = self.experiment.path
            self.preprocessing_dir = f"{self.experiment_dir}/preprocessing"

    def fit(self, X, y=None):
        """
        Fit the feature engineering estimator.

        Args:
            X (pd.DataFrame): Input data
            y: Target values (ignored)

        Returns:
            Transformed data (for compatibility with existing code)
        """
        self.data = X.copy()

        # drop columns
        self.data = self.data.drop(columns=self.columns_drop, errors="ignore")

        # convert object columns to numeric if possible
        self.data = convert_object_columns_that_are_numeric(self.data)

        # handle boolean features
        self.data = self.boolean_encode_columns()

        # handle missing values
        self.data = self.fillna_at_training()

        # target encoding
        self.data = self.generate_target_encodings()

        # Cyclic encode dates
        self.data = self.cyclic_encode_date(fourier_order=self.fourier_order)

        self._set_fitted()
        return self

    def transform(self, X):
        """
        Transform the input data using the fitted feature engineering pipeline.

        Args:
            X (pd.DataFrame): Input data to transform

        Returns:
            pd.DataFrame: Transformed data with engineered features
        """
        # Allow loading persisted artifacts even in a fresh instance
        if not getattr(self, "is_fitted_", False) and self.experiment:
            if os.path.exists(f"{self.preprocessing_dir}/column_transformer.pkl"):
                self.is_fitted_ = True

        self._check_is_fitted()

        # Create a copy of input data
        data = X.copy()

        # Apply the same transformations as in fit
        # drop columns
        data = data.drop(columns=self.columns_drop, errors="ignore")

        # convert object columns to numeric if possible
        data = convert_object_columns_that_are_numeric(data)

        # handle boolean features
        self.data = data
        data = self.boolean_encode_columns()

        # handle missing values (use inference method for transform)
        self.data = data
        data = self.fillna_at_inference()

        # target encoding
        self.data = data
        data = self.generate_target_encodings()

        # Cyclic encode dates
        self.data = data
        if os.path.exists(
            f"{self.preprocessing_dir}/all_features_before_encoding.pkl"
        ):  # backward compatibility
            data = self.cyclic_encode_date(fourier_order=self.fourier_order)
        else:
            data = self.cyclic_encode_date_old()

        return data

    def get_data(self):
        """
        Get the transformed data after feature engineering.

        Returns:
            pd.DataFrame: The transformed data with engineered features
        """
        self._check_is_fitted()
        return self.data

    def cyclic_encode_date(self, fourier_order: int = 1) -> pd.DataFrame:
        """
        Adds Fourier features (sine and cosine) encoding for common date parts with configurable harmonics order.

        Parameters:
            df (pd.DataFrame): Input dataframe
            columns (list[str]): List of datetime columns to encode
            fourier_order (int): Number of Fourier harmonics to generate (default=1)

        Returns:
            pd.DataFrame: Updated dataframe with new cyclic features
        """

        df: pd.DataFrame = self.data
        columns: list[str] = self.columns_date

        # always encode date column if time series
        if self.time_series and self.date_column not in columns:
            columns.append(self.date_column)

        def fourier_encode(series, period, order=1):
            """Generate Fourier features up to specified order"""
            features = {}
            for i in range(1, order + 1):
                features[f"sin{i}"] = np.sin(2 * np.pi * i * series / period)
                features[f"cos{i}"] = np.cos(2 * np.pi * i * series / period)
            return features

        for col in columns:

            df[col] = pd.to_datetime(df[col]).dt.normalize()

            # ===== BASIC DATE COMPONENTS =====
            # Store date components before converting to ordinal
            date_col = pd.to_datetime(df[col])
            df[f"{col}_year"] = date_col.dt.isocalendar().year
            df[f"{col}_month"] = date_col.dt.month
            df[f"{col}_day"] = date_col.dt.day
            df[f"{col}_week"] = date_col.dt.isocalendar().week
            df[f"{col}_weekday"] = date_col.dt.weekday
            df[f"{col}_yearday"] = date_col.dt.dayofyear
            df[f"{col}_quarter"] = date_col.dt.quarter

            # ===== TREND FEATURES =====
            # Linear trend
            df[col] = date_col.map(pd.Timestamp.toordinal)

            # Reference ordinal for 1980-01-01 to normalize squared values
            reference_ordinal = pd.Timestamp("1980-01-01").toordinal()

            # Non-linear trends
            df[f"{col}_log"] = np.log1p(df[col])
            df[f"{col}_squared"] = (df[col] / reference_ordinal) ** 2

            # ===== SEASONALITY FEATURES (FOURIER) =====
            # Generate Fourier features for different periods
            # Month (12-month period)
            month_features = fourier_encode(df[f"{col}_month"], 12, fourier_order)
            for order_name, values in month_features.items():
                # Backward compatibility: use old naming for order 1
                if order_name == "sin1":
                    df[f"{col}_month_sin"] = values
                elif order_name == "cos1":
                    df[f"{col}_month_cos"] = values
                else:
                    df[f"{col}_month_{order_name}"] = values

            # Week (52-week period)
            week_features = fourier_encode(df[f"{col}_week"], 52, fourier_order)
            for order_name, values in week_features.items():
                if order_name == "sin1":
                    df[f"{col}_week_sin"] = values
                elif order_name == "cos1":
                    df[f"{col}_week_cos"] = values
                else:
                    df[f"{col}_week_{order_name}"] = values

            # Weekday (7-day period)
            weekday_features = fourier_encode(df[f"{col}_weekday"], 7, fourier_order)
            for order_name, values in weekday_features.items():
                if order_name == "sin1":
                    df[f"{col}_weekday_sin"] = values
                elif order_name == "cos1":
                    df[f"{col}_weekday_cos"] = values
                else:
                    df[f"{col}_weekday_{order_name}"] = values

            # Day of month (31-day period) - only first harmonic as higher orders rarely useful
            day_features = fourier_encode(df[f"{col}_day"], 31, min(fourier_order, 1))
            for order_name, values in day_features.items():
                if order_name == "sin1":
                    df[f"{col}_day_sin"] = values
                elif order_name == "cos1":
                    df[f"{col}_day_cos"] = values
                else:
                    df[f"{col}_day_{order_name}"] = values

            # Year day (365-day period) - only first harmonic as higher orders rarely useful
            yearday_features = fourier_encode(
                df[f"{col}_yearday"], 365, min(fourier_order, 1)
            )
            for order_name, values in yearday_features.items():
                if order_name == "sin1":
                    df[f"{col}_yearday_sin"] = values
                elif order_name == "cos1":
                    df[f"{col}_yearday_cos"] = values
                else:
                    df[f"{col}_yearday_{order_name}"] = values

            # Quarter (4-quarter period)
            quarter_features = fourier_encode(df[f"{col}_quarter"], 4, fourier_order)
            for order_name, values in quarter_features.items():
                if order_name == "sin1":
                    df[f"{col}_quarter_sin"] = values
                elif order_name == "cos1":
                    df[f"{col}_quarter_cos"] = values
                else:
                    df[f"{col}_quarter_{order_name}"] = values

            # ===== SPECIAL PERIOD INDICATORS =====
            df[f"{col}_is_weekend"] = df[f"{col}_weekday"].isin([5, 6]).astype(int)
            df[f"{col}_is_month_start"] = (df[f"{col}_day"] <= 7).astype(int)
            df[f"{col}_is_month_end"] = (
                df[f"{col}_day"] >= date_col.dt.days_in_month - 7
            ).astype(int)
            df[f"{col}_is_quarter_start"] = date_col.dt.is_quarter_start.astype(int)
            df[f"{col}_is_quarter_end"] = date_col.dt.is_quarter_end.astype(int)

            # ===== SEASONALITY × TREND INTERACTIONS =====
            df[f"{col}_month_year_interaction"] = df[f"{col}_month"] * df[f"{col}_year"]
            df[f"{col}_weekday_month_interaction"] = (
                df[f"{col}_weekday"] * df[f"{col}_month"]
            )
            df[f"{col}_quarter_year_interaction"] = (
                df[f"{col}_quarter"] * df[f"{col}_year"]
            )

        return df

    # keep for legacy experiemnt at inference
    def cyclic_encode_date_old(self) -> pd.DataFrame:
        """
        Adds cyclic (sine and cosine) encoding for common date parts: day of week, day of month, and month.

        Parameters:
            df (pd.DataFrame): Input dataframe
            columns (list[str]): List of datetime columns to encode
            prefix (str): Optional prefix for new columns. If None, uses column names.

        Returns:
            pd.DataFrame: Updated dataframe with new cyclic features
        """

        df: pd.DataFrame = self.data
        columns: list[str] = self.columns_date

        def cyclic_encode(series, max_value):
            sin_values = np.sin(2 * np.pi * series / max_value)
            cos_values = np.cos(2 * np.pi * series / max_value)
            return sin_values, cos_values

        for col in columns:

            df[col] = pd.to_datetime(df[col]).dt.normalize()
            df[f"{col}_year"] = df[col].dt.isocalendar().year
            df[f"{col}_month"] = df[col].dt.month
            df[f"{col}_day"] = df[col].dt.day
            df[f"{col}_week"] = df[col].dt.isocalendar().week
            df[f"{col}_weekday"] = df[col].dt.weekday
            df[f"{col}_yearday"] = df[col].dt.dayofyear
            df[col] = pd.to_datetime(df[col]).map(pd.Timestamp.toordinal)

            df[f"{col}_month_sin"], df[f"{col}_month_cos"] = cyclic_encode(
                df[f"{col}_month"], 12
            )
            df[f"{col}_day_sin"], df[f"{col}_day_cos"] = cyclic_encode(
                df[f"{col}_day"], 31
            )
            df[f"{col}_week_sin"], df[f"{col}_week_cos"] = cyclic_encode(
                df[f"{col}_week"], 52
            )
            df[f"{col}_weekday_sin"], df[f"{col}_weekday_cos"] = cyclic_encode(
                df[f"{col}_weekday"], 7
            )
            df[f"{col}_yearday_sin"], df[f"{col}_yearday_cos"] = cyclic_encode(
                df[f"{col}_yearday"], 365
            )

            # Drop the original column TODO: not sure if we should drop it for time series
            # df.drop(col, axis=1, inplace=True)

        return df

    def boolean_encode_columns(self) -> pd.DataFrame:
        """
        Applies boolean encoding to a list of columns:
        - Leaves column as-is if already int with only 0 and 1
        - Otherwise: sets 1 if value is present (notna), 0 if null/NaN/None

        Parameters:
            df (pd.DataFrame): Input dataframe
            columns (list): List of column names to encode

        Returns:
            pd.DataFrame: Updated dataframe with encoded columns
        """

        df: pd.DataFrame = self.data
        columns: list[str] = self.columns_boolean

        for column in columns:
            col = df[column]
            if pd.api.types.is_integer_dtype(col) and set(
                col.dropna().unique()
            ).issubset({0, 1}):
                continue  # already valid binary
            df[column] = col.notna().astype(int)
        return df

    def generate_target_encodings(self) -> pd.DataFrame:
        """
        Generate target encoding features (e.g., mean, median) for specified targets and group-by combinations.

        Parameters:
            df (pd.DataFrame): Input dataframe
            columns_te_groupby (list of list): Grouping keys, e.g., [["SECTOR", "DATE"], ["SUBINDUSTRY", "DATE"]]
            columns_te_target (list): Target columns to aggregate (e.g., ["RET", "VOLUME", "RSI_14"])
            statistics (list): List of aggregation statistics (e.g., ["mean", "median"])

        Returns:
            pd.DataFrame: Original dataframe with new encoded columns added
        """
        # TODO: target encoding needs to be fit / transform based at transform time.
        df: pd.DataFrame = self.data
        columns_te_groupby: list[list[str]] = self.columns_te_groupby
        columns_te_target: list[str] = self.columns_te_target
        statistics: list[str] = ["mean", "median"]

        df = df.copy()
        new_feature_cols = {}
        for group_cols, stat, target_col in product(
            columns_te_groupby, statistics, columns_te_target
        ):
            df[target_col] = pd.to_numeric(
                df[target_col].replace("", "0"), errors="coerce"
            ).fillna(0)
            col_name = f"{target_col}_{'_'.join(group_cols)}_{stat.upper()}"
            new_feature_cols[col_name] = df.groupby(group_cols)[target_col].transform(
                stat
            )

        # merge all at once to improve performance
        df = pd.concat([df, pd.DataFrame(new_feature_cols)], axis=1)
        return df

    def fillna_at_training(self) -> pd.DataFrame:
        """
        Fill missing values in a DataFrame:
        - Numeric columns: fill with mean
        - Categorical columns: fill with mode
        Handles both NaN and None.

        Parameters:
            df (pd.DataFrame): Input DataFrame

        Returns:
            pd.DataFrame: Cleaned DataFrame with missing values filled
        """

        df: pd.DataFrame = self.data.copy()

        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
                    logger.info(
                        f"Filled {missing_count} NaN values in numeric column '{col}' with mean."
                    )
                else:
                    mode = df[col].mode()
                    if not mode.empty:
                        mode_value = mode[0]
                        mode_count = (df[col] == mode_value).sum()
                        if mode_count > 100:
                            fill_value = mode_value
                        else:
                            fill_value = "unknown"
                    else:
                        fill_value = "unknown"

                    df[col] = df[col].fillna(fill_value)
                    logger.info(
                        f"Filled {missing_count} NaN values in categorical column '{col}' with '{fill_value}'."
                    )

        return df

    def fillna_at_inference(self) -> pd.DataFrame:

        df: pd.DataFrame = self.data

        missing_cols = df.columns[df.isnull().any()].tolist()

        if missing_cols:
            numeric_cols = [
                col for col in missing_cols if pd.api.types.is_numeric_dtype(df[col])
            ]
            non_numeric_cols = [col for col in missing_cols if col not in numeric_cols]

            logger.warning(
                f"Missing values found in transform data."
                f"Filling with 0 for numeric columns: {numeric_cols}, "
                f"and 'unknown' for non-numeric columns: {non_numeric_cols}"
            )

            df[numeric_cols] = df[numeric_cols].fillna(0)
            df[non_numeric_cols] = df[non_numeric_cols].fillna("unknown")

        return df


# analysis & utils
def convert_object_columns_that_are_numeric(df: pd.DataFrame) -> list:
    """
    Detect object columns that can be safely converted to numeric (float or int).

    Returns:
        List of column names that are object type but contain numeric values.
    """

    numeric_candidates = []

    for col in df.select_dtypes(include=["object"]).columns:
        try:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() / len(df) > 0.9:  # at least 90% convertible
                numeric_candidates.append(col)
        except Exception:
            continue

    for col in numeric_candidates:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def traditional_descriptive_analysis(df: pd.DataFrame, group_column: str | None = None):
    with pd.option_context("display.max_rows", None):
        results = {}

        # Shape
        results["Shape"] = f"{df.shape[0]} rows × {df.shape[1]} columns"

        # Create a copy of the DataFrame to avoid modifying the original
        df_check = df.copy()

        # Convert numpy arrays to tuples for hashing
        for col in df_check.columns:
            if df_check[col].apply(lambda x: isinstance(x, np.ndarray)).any():
                df_check[col] = df_check[col].apply(
                    lambda x: tuple(x) if isinstance(x, np.ndarray) else x
                )

        # Duplicated rows
        results["Duplicated rows"] = int(df_check.duplicated().sum())

        # Check for duplicated columns
        try:
            # Try to find duplicated columns
            duplicated_cols = []
            cols = df_check.columns
            for i, col1 in enumerate(cols):
                for col2 in cols[i + 1 :]:
                    if df_check[col1].equals(df_check[col2]):
                        duplicated_cols.append(f"{col1} = {col2}")

            results["Duplicated columns"] = (
                ", ".join(duplicated_cols) if duplicated_cols else "None"
            )
        except Exception as e:
            results["Duplicated columns"] = f"Could not check: {str(e)}"

        # Missing values
        missing = df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=False)
        if len(missing) > 0:
            results["Missing values"] = missing.to_frame("Missing Count").to_markdown()
        else:
            results["Missing values"] = "No missing values"

        # Infinite values
        inf = df.replace([np.inf, -np.inf], np.nan)
        inf_count = inf.isnull().sum() - df.isnull().sum()
        inf_count = inf_count[inf_count > 0].sort_values(ascending=False)
        if len(inf_count) > 0:
            results["Infinite values"] = inf_count.to_frame("Inf Count").to_markdown()
        else:
            results["Infinite values"] = "No infinite values"

        # Constant columns
        constant_cols = [col for col in df.columns if df[col].nunique() == 1]
        results["Constant columns"] = (
            ", ".join(constant_cols) if len(constant_cols) > 0 else "None"
        )

        # Data types
        dtypes = df.dtypes.astype(str).sort_index()
        results["Data types"] = dtypes.to_frame("Type").to_markdown()

        # Unique values in group_column
        if group_column is not None:
            if group_column in df.columns:
                results[f"Unique values in '{group_column}'"] = int(
                    df[group_column].nunique()
                )
            else:
                results[f"Unique values in '{group_column}'"] = (
                    f"❌ Column '{group_column}' not found"
                )

        # Log all results
        for title, content in results.items():
            print(f"\n### {title}\n{content}")


def print_missing_values(df: pd.DataFrame):

    if len(df.isnull().sum().where(df.isnull().sum() != 0).dropna()):
        logger.info(
            f"Missing values : \n{df.isnull().sum().where(df.isnull().sum() != 0).dropna().sort_values(ascending=False).to_string()}"
        )
    else:
        logger.info("No missing values found")
