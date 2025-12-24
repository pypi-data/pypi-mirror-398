import pandas as pd
import numpy as np
import joblib
from typing import Optional
import os

from sklearn.preprocessing import StandardScaler

from lecrapaud.utils import logger
from lecrapaud.search_space import all_models
from lecrapaud.mixins import LeCrapaudTransformerMixin
from lecrapaud.models import Experiment


class ModelPreprocessor(LeCrapaudTransformerMixin):

    def __init__(
        self,
        experiment=None,
        **kwargs,
    ):
        # The mixin will automatically set all experiment.context parameters as attributes
        super().__init__(experiment=experiment, **kwargs)

        # Set defaults for required parameters if not provided
        if not hasattr(self, "target_numbers"):
            self.target_numbers = []
        if not hasattr(self, "target_clf"):
            self.target_clf = []
        if not hasattr(self, "models_idx"):
            self.models_idx = []
        if not hasattr(self, "time_series"):
            self.time_series = False
        if not hasattr(self, "max_timesteps"):
            self.max_timesteps = 120
        if not hasattr(self, "group_column"):
            self.group_column = None
        if not hasattr(self, "date_column"):
            self.date_column = None

        # Set paths if experiment is available
        if self.experiment:
            self.experiment_dir = self.experiment.path
            self.data_dir = f"{self.experiment_dir}/data"
            self.preprocessing_dir = f"{self.experiment_dir}/preprocessing"

            self.all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )

    def fit(self, X, y=None):
        """
        Fit the model preprocessor (learns scaling parameters).

        Args:
            X (pd.DataFrame): Training data
            y: Target values (ignored)

        Returns:
            self: Returns self for chaining
        """
        X, y = self._validate_data(X, y)

        # Filter columns to keep only features and targets
        if hasattr(self, "all_features"):
            columns_to_keep = self.all_features + [
                f"TARGET_{i}" for i in self.target_numbers
            ]
            duplicates = [
                col for col in set(columns_to_keep) if columns_to_keep.count(col) > 1
            ]
            if duplicates:
                raise ValueError(
                    f"Doublons détectés dans columns_to_keep: {duplicates}"
                )
            X = X[columns_to_keep]

        # Determine if we need scaling
        self.need_scaling_ = any(
            t not in self.target_clf for t in self.target_numbers
        ) and any(all_models[i].get("need_scaling") for i in self.models_idx)

        if self.need_scaling_:
            logger.info("Fitting scalers...")
            _, self.scaler_x_, self.scalers_y_ = self.scale_data(X)

            # Save scalers if experiment is available
            if self.experiment:
                joblib.dump(self.scaler_x_, f"{self.preprocessing_dir}/scaler_x.pkl")
                # Save target scalers
                for target_number in self.target_numbers:
                    if target_number not in self.target_clf:
                        target_dir = f"{self.experiment_dir}/TARGET_{target_number}"
                        scaler_y = self.scalers_y_[f"scaler_y_{target_number}"]
                        joblib.dump(scaler_y, f"{target_dir}/scaler_y.pkl")

        self._set_fitted()
        self.data = X
        return self

    def get_data(self):
        """
        Get the transformed data after model preprocessing.

        Returns:
            pd.DataFrame: The transformed data
        """
        self._check_is_fitted()
        return self.data

    def transform(self, X):
        """
        Transform the input data (apply scaling if fitted).

        Args:
            X (pd.DataFrame): Input data

        Returns:
            pd.DataFrame: Scaled data (or original if no scaling needed)
        """
        # Allow loading persisted artifacts even in a fresh instance
        if not getattr(self, "is_fitted_", False) and self.experiment:
            scaler_path = f"{self.preprocessing_dir}/scaler_x.pkl"
            if os.path.exists(scaler_path):
                self.is_fitted_ = True

        self._check_is_fitted()
        X, _ = self._validate_data(X, reset=False)

        # Filter columns if needed
        if hasattr(self, "all_features"):
            columns_to_keep = self.all_features + [
                f"TARGET_{i}" for i in self.target_numbers if f"TARGET_{i}" in X.columns
            ]
            X = X[columns_to_keep]

        # Load scalers if not in memory
        if not hasattr(self, "scaler_x_") and self.experiment:
            scaler_path = f"{self.preprocessing_dir}/scaler_x.pkl"
            if os.path.exists(scaler_path):
                self.scaler_x_ = joblib.load(scaler_path)

        # Apply scaling if needed
        if (
            hasattr(self, "need_scaling_")
            and self.need_scaling_
            and hasattr(self, "scaler_x_")
        ):
            X_scaled, _, _ = self.scale_data(
                X, scaler_x=self.scaler_x_, scalers_y=getattr(self, "scalers_y_", None)
            )
            return X_scaled

        return X

    # scaling
    def scale_data(
        self,
        df: pd.DataFrame,
        scaler_x=None,
        scalers_y: Optional[list] = None,
    ):
        logger.info("Scale data...")
        X = df.loc[:, ~df.columns.str.contains("^TARGET_")]

        if scaler_x:
            X_scaled = pd.DataFrame(
                scaler_x.transform(X), columns=list(X.columns), index=X.index
            )
        else:
            scaler_x = StandardScaler()  # MinMaxScaler(feature_range=(-1,1))
            X_scaled = pd.DataFrame(
                scaler_x.fit_transform(X), columns=list(X.columns), index=X.index
            )

        # Determine which targets need to be scaled
        targets_numbers_to_scale = [
            i for i in self.target_numbers if i not in self.target_clf
        ]

        # Dictionary to store scaled target data
        scaled_targets = {}

        if scalers_y:
            for target_number in targets_numbers_to_scale:
                y = df[[f"TARGET_{target_number}"]]
                scaled_targets[target_number] = pd.DataFrame(
                    scalers_y[f"scaler_y_{target_number}"].transform(y.values),
                    columns=y.columns,
                    index=y.index,
                )
        else:
            scalers_y = {}
            for target_number in targets_numbers_to_scale:
                scaler_y = StandardScaler()
                y = df[[f"TARGET_{target_number}"]]

                scaled_y = pd.DataFrame(
                    scaler_y.fit_transform(y.values),
                    columns=y.columns,
                    index=y.index,
                )
                target_dir = f"{self.experiment_dir}/TARGET_{target_number}"
                joblib.dump(scaler_y, f"{target_dir}/scaler_y.pkl")

                scalers_y[f"scaler_y_{target_number}"] = scaler_y
                scaled_targets[target_number] = scaled_y

        # Reconstruct y_scaled in the original order
        y_scaled = pd.concat(
            [
                scaled_targets[target_number]
                for target_number in targets_numbers_to_scale
            ],
            axis=1,
        )
        y_not_scaled = df[
            df.columns.intersection([f"TARGET_{i}" for i in self.target_clf])
        ]

        # Ensure the final DataFrame keeps the original order
        df_scaled = pd.concat(
            [X_scaled, y_scaled, y_not_scaled],
            axis=1,
        )[
            df.columns
        ]  # Reorder columns to match original `df`

        if not df_scaled.columns.equals(df.columns):
            raise Exception("Columns are not in the same order after scaling.")

        return df_scaled, scaler_x, scalers_y


# Reshape into 3D tensors for recurrent models
def reshape_time_series(
    experiment: Experiment,
    features: list,
    train: pd.DataFrame,
    val: pd.DataFrame = None,
    test: pd.DataFrame = None,
    timesteps: int = 120,
):
    # always scale for recurrent layers : train should be scaled
    group_column = experiment.context.group_column

    target_columns = train.columns.intersection(
        [f"TARGET_{i}" for i in experiment.context.target_numbers]
    )

    data = pd.concat([train, val, test], axis=0)

    def reshape_df(df: pd.DataFrame, group_series: pd.Series, timesteps: int):
        fill_value = [[[0] * len(df.columns)]]

        def shiftsum(x, timesteps: int):
            tmp = x.copy()
            for i in range(1, timesteps):
                tmp = x.shift(i, fill_value=fill_value) + tmp
            return tmp

        logger.info("Grouping each feature in a unique column with list...")
        df_reshaped = df.apply(list, axis=1).apply(lambda x: [list(x)])
        df_reshaped = pd.concat([df_reshaped, group_series], axis=1)

        logger.info("Grouping features and creating timesteps...")
        df_reshaped = (
            df_reshaped.groupby(group_column)[0]
            .apply(lambda x: shiftsum(x, timesteps))
            .reset_index(group_column, drop=True)
            .rename("RECURRENT_FEATURES")
        )
        df_reshaped = pd.DataFrame(df_reshaped)

        return df_reshaped

    data_reshaped = reshape_df(data[features], data[group_column], timesteps)

    data_reshaped[target_columns] = data[target_columns]

    logger.info("Separating train, val, test data and creating np arrays...")
    train_reshaped = data_reshaped.loc[train.index]

    x_train_reshaped = np.array(train_reshaped["RECURRENT_FEATURES"].values.tolist())
    y_train_reshaped = np.array(train_reshaped[target_columns].reset_index())

    reshaped_data = {
        "x_train_reshaped": x_train_reshaped,
        "y_train_reshaped": y_train_reshaped,
    }

    if val is not None:
        val_reshaped = data_reshaped.loc[val.index]
        x_val_reshaped = np.array(val_reshaped["RECURRENT_FEATURES"].values.tolist())
        y_val_reshaped = np.array(val_reshaped[target_columns].reset_index())
        reshaped_data["x_val_reshaped"] = x_val_reshaped
        reshaped_data["y_val_reshaped"] = y_val_reshaped

    if test is not None:
        test_reshaped = data_reshaped.loc[test.index]
        x_test_reshaped = np.array(test_reshaped["RECURRENT_FEATURES"].values.tolist())
        y_test_reshaped = np.array(test_reshaped[target_columns].reset_index())
        reshaped_data["x_test_reshaped"] = x_test_reshaped
        reshaped_data["y_test_reshaped"] = y_test_reshaped

    return reshaped_data
