import pandas as pd
import numpy as np
import joblib
import os

from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from category_encoders import BinaryEncoder, CountEncoder
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.model_selection import train_test_split

from lecrapaud.integrations.openai_integration import (
    truncate_text,
    get_openai_embeddings,
)
from lecrapaud.feature_selection import get_features_by_types
from lecrapaud.utils import logger
from lecrapaud.models import Target, Feature, Experiment
from lecrapaud.config import PYTHON_ENV, LECRAPAUD_SAVE_FULL_TRAIN_DATA
from lecrapaud.feature_engineering import convert_object_columns_that_are_numeric
from lecrapaud.mixins import LeCrapaudTransformerMixin


class FeaturePreprocessor(LeCrapaudTransformerMixin):

    def __init__(
        self,
        experiment=None,
        **kwargs,
    ):
        # The mixin will automatically set all experiment.context parameters as attributes
        super().__init__(experiment=experiment, **kwargs)

        # Set defaults for attributes not automatically set by mixin
        if not hasattr(self, "time_series"):
            self.time_series = False
        if not hasattr(self, "date_column"):
            self.date_column = None
        if not hasattr(self, "group_column"):
            self.group_column = None
        if not hasattr(self, "val_size"):
            self.val_size = 0.2
        if not hasattr(self, "test_size"):
            self.test_size = 0.2
        if not hasattr(self, "target_numbers"):
            self.target_numbers = []
        if not hasattr(self, "target_clf"):
            self.target_clf = []

        # Handle list parameters with uppercase conversion
        if not hasattr(self, "columns_pca"):
            self.columns_pca = []
        else:
            self.columns_pca = [col.upper() for col in self.columns_pca]
        if not hasattr(self, "pca_temporal"):
            self.pca_temporal = []
        if not hasattr(self, "pca_cross_sectional"):
            self.pca_cross_sectional = []
        if not hasattr(self, "columns_onehot"):
            self.columns_onehot = []
        else:
            self.columns_onehot = [col.upper() for col in self.columns_onehot]
        if not hasattr(self, "columns_binary"):
            self.columns_binary = []
        else:
            self.columns_binary = [col.upper() for col in self.columns_binary]
        if not hasattr(self, "columns_ordinal"):
            self.columns_ordinal = []
        else:
            self.columns_ordinal = [col.upper() for col in self.columns_ordinal]
        if not hasattr(self, "columns_frequency"):
            self.columns_frequency = []
        else:
            self.columns_frequency = [col.upper() for col in self.columns_frequency]

        # Set experiment-related paths if experiment is available
        if self.experiment:
            self.experiment_dir = self.experiment.path
            self.experiment_id = self.experiment.id
            self.data_dir = f"{self.experiment_dir}/data"
            self.preprocessing_dir = f"{self.experiment_dir}/preprocessing"

    def fit(self, X, y=None):
        """
        Fit the preprocessor (learns PCA components, encoders, etc.).

        Args:
            X (pd.DataFrame): Input data
            y: Target values (ignored)

        Returns:
            self: Returns self for chaining
        """
        X, y = self._validate_data(X, y)

        # Store data and make columns uppercase
        data = X.copy()
        data.columns = data.columns.str.upper()

        joblib.dump(
            list(data.columns),
            f"{self.preprocessing_dir}/all_features_before_encoding.pkl",
        )

        # Fit PCA components
        data, self.pcas_ = self.add_pca_features(data)
        data, self.pcas_cross_sectional_ = self.add_pca_feature_cross_sectional(data)
        data, self.pcas_temporal_ = self.add_pca_feature_temporal(data)

        # Fit encoding transformer
        data, self.transformer_ = self.encode_categorical_features(data)

        # Save fitted transformers if experiment is available
        if self.experiment:
            joblib.dump(self.pcas_, f"{self.preprocessing_dir}/pcas.pkl")
            joblib.dump(
                self.pcas_cross_sectional_,
                f"{self.preprocessing_dir}/pcas_cross_sectional.pkl",
            )
            joblib.dump(
                self.pcas_temporal_, f"{self.preprocessing_dir}/pcas_temporal.pkl"
            )
            joblib.dump(
                self.transformer_, f"{self.preprocessing_dir}/column_transformer.pkl"
            )

            # Save features and summary
            joblib.dump(
                list(data.columns),
                f"{self.preprocessing_dir}/all_features_before_selection.pkl",
            )

            if LECRAPAUD_SAVE_FULL_TRAIN_DATA:
                joblib.dump(data, f"{self.data_dir}/full.pkl")

            summary = summarize_dataframe(data)
            summary.to_csv(f"{self.experiment_dir}/feature_summary.csv", index=False)

        self._set_fitted()
        return self

    def transform(self, X):
        """
        Transform the input data using fitted components.

        Args:
            X (pd.DataFrame): Input data

        Returns:
            pd.DataFrame: Transformed data
        """
        # Allow loading persisted artifacts even in a fresh instance
        if not getattr(self, "is_fitted_", False) and self.experiment:
            if os.path.exists(f"{self.preprocessing_dir}/column_transformer.pkl"):
                self.is_fitted_ = True

        self._check_is_fitted()
        X, _ = self._validate_data(X, reset=False)

        # Transform data
        data = X.copy()
        data.columns = data.columns.str.upper()

        if os.path.exists(f"{self.preprocessing_dir}/all_features_before_encoding.pkl"):
            all_features = joblib.load(
                f"{self.preprocessing_dir}/all_features_before_encoding.pkl"
            )
            data = data[all_features]

        # Load fitted components if not already in memory
        if not hasattr(self, "pcas_") and self.experiment:
            if os.path.exists(f"{self.preprocessing_dir}/pcas.pkl"):
                self.pcas_ = joblib.load(f"{self.preprocessing_dir}/pcas.pkl")

        if not hasattr(self, "pcas_cross_sectional_") and self.experiment:
            if os.path.exists(f"{self.preprocessing_dir}/pcas_cross_sectional.pkl"):
                self.pcas_cross_sectional_ = joblib.load(
                    f"{self.preprocessing_dir}/pcas_cross_sectional.pkl"
                )

        if not hasattr(self, "pcas_temporal_") and self.experiment:
            if os.path.exists(f"{self.preprocessing_dir}/pcas_temporal.pkl"):
                self.pcas_temporal_ = joblib.load(
                    f"{self.preprocessing_dir}/pcas_temporal.pkl"
                )

        if not hasattr(self, "transformer_") and self.experiment:
            if os.path.exists(f"{self.preprocessing_dir}/column_transformer.pkl"):
                self.transformer_ = joblib.load(
                    f"{self.preprocessing_dir}/column_transformer.pkl"
                )

        # Apply PCA transformations using fitted components
        if hasattr(self, "pcas_"):
            data, _ = self.add_pca_features(data, pcas=self.pcas_)
        if hasattr(self, "pcas_cross_sectional_"):
            data, _ = self.add_pca_feature_cross_sectional(
                data, pcas=self.pcas_cross_sectional_
            )
        if hasattr(self, "pcas_temporal_"):
            data, _ = self.add_pca_feature_temporal(data, pcas=self.pcas_temporal_)

        # Apply encoding using fitted transformer
        if hasattr(self, "transformer_"):
            data, _ = self.encode_categorical_features(
                data, transformer=self.transformer_
            )

        return data

    # embedding and pca
    def add_pca_features(
        self, df: pd.DataFrame, n_components: int = 5, pcas=None
    ) -> tuple[pd.DataFrame, dict]:
        """
        Adds PCA components as new columns to a DataFrame from a column containing numpy arrays.
        NEED TRAIN/TEST SPLIT BEFORE APPLYING - LIKE ENCODING CATEGORICAL VARIABLES

        Parameters:
            df (pd.DataFrame): Input DataFrame
            column (str): Name of the column containing np.ndarray
            n_components (int): Number of PCA components to keep

        Returns:
            pd.DataFrame: DataFrame with new PCA columns added
        """
        columns: list[str] = self.columns_pca

        pcas_dict = {}
        for column in columns:
            # Convert text to embeddings if necessary
            if not isinstance(df[column].iloc[0], (np.ndarray, list)):
                sentences = df[column].astype(str).tolist()
                logger.info(
                    f"Total sentences to embed for column {column}: {len(sentences)}"
                )

                # Truncate each sentence
                truncate_sentences = [truncate_text(sentence) for sentence in sentences]

                # embedding
                embedding_matrix = get_openai_embeddings(truncate_sentences)
            else:
                logger.info(f"Column {column} is already embeddings")
                # Stack the vectors into a 2D array
                embedding_matrix = np.vstack(df[column].values)

            # Apply PCA
            if pcas:
                pca = pcas[column]
                pca_features = pca.transform(embedding_matrix)
            else:
                pca = PCA(n_components=n_components)
                pca_features = pca.fit_transform(embedding_matrix)

            # Add PCA columns
            for i in range(n_components):
                df[f"{column}_pca_{i+1}"] = pca_features[:, i]

            # Drop the original column
            df.drop(column, axis=1, inplace=True)
            pcas_dict.update({column: pca})

        return df, pcas_dict

    def add_pca_feature_cross_sectional_old(
        self,
        df: pd.DataFrame,
        *,
        n_components: int = 5,
        pcas: dict[str, Pipeline] | None = None,  # si fourni: transform only
        impute_strategy: str = "median",
        standardize: bool = True,
    ) -> tuple[pd.DataFrame, dict[str, Pipeline]]:
        """
        Construit un pivot (index=index_col, columns=columns_col, values=value_col),
        fit (ou réutilise) un Pipeline Imputer(+Scaler)+PCA, puis merge les scores
        (par index_col) dans df. Renvoie (df_avec_features, pipe).
        """

        pcas_dict = {}
        index_saved = df.index

        for pca_cross_sectional in self.pca_cross_sectional:
            name, index_col, columns_col, value_col = (
                pca_cross_sectional[k] for k in ("name", "index", "columns", "value")
            )
            prefix = f"CS_PC_{name}"

            pivot = df.pivot_table(
                index=index_col, columns=columns_col, values=value_col
            ).sort_index()

            # Pipeline à réutiliser entre train et test
            if pcas is None:
                steps = [("imputer", SimpleImputer(strategy=impute_strategy))]
                if standardize:
                    steps.append(
                        ("scaler", StandardScaler(with_mean=True, with_std=True))
                    )
                pca = PCA(n_components=n_components, random_state=0)
                steps.append(("pca", pca))
                pipe = Pipeline(steps)
                pipe.fit(pivot)  # <- fit sur TRAIN uniquement
            else:
                pipe = pcas[name]  # <- TEST : on réutilise le pipe existant

            scores = pipe.transform(pivot)  # shape: (n_index, n_components)
            cols = [f"{prefix}_{i}" for i in range(n_components)]
            scores_df = pd.DataFrame(scores, index=pivot.index, columns=cols)

            df = df.merge(scores_df.reset_index(), on=index_col, how="left")
            df.index = index_saved
            pcas_dict.update({name: pipe})

        return df, pcas_dict

    def add_pca_feature_cross_sectional(
        self,
        df: pd.DataFrame,
        *,
        n_components: int = 5,
        pcas: dict[str, Pipeline] | None = None,  # si fourni: transform only
        impute_strategy: str = "median",
        standardize: bool = True,
        lookback_days: int = 365,  # nombre de jours à regarder en arrière pour le fit
        refresh_frequency: int = 90,  # refresh la PCA tous les X jours
    ) -> tuple[pd.DataFrame, dict[str, Pipeline]]:
        """
        Construit un pivot (index=index_col, columns=columns_col, values=value_col),
        fit (ou réutilise) un Pipeline Imputer(+Scaler)+PCA, puis merge les scores
        (par index_col) dans df. Renvoie (df_avec_features, pipe).

        Pour les séries temporelles : fit la PCA uniquement sur les données passées
        pour éviter le leakage, avec refresh périodique.

        Gère le cas des données panel où on a plusieurs séries temporelles
        (ex: plusieurs stocks avec les mêmes dates).
        """

        pcas_dict = {}
        index_saved = df.index

        for pca_cross_sectional in self.pca_cross_sectional:
            name, index_col, columns_col, value_col = (
                pca_cross_sectional[k] for k in ("name", "index", "columns", "value")
            )
            prefix = f"CS_PC_{name}"

            # Vérifier si c'est une série temporelle avec index = date
            # Les dates sont déjà en ordinal après cyclic_encode_date
            is_time_series = self.time_series and index_col == self.date_column

            if is_time_series:
                # Cas spécial : PCA cross-sectional sur des données de panel time series
                # Par exemple : PCA sur les returns de tous les stocks à chaque date
                # pour capturer le régime de marché

                all_scores = []

                # Les dates sont déjà en ordinal
                unique_dates = sorted(df[index_col].unique())

                # Pour l'inference, utiliser la PCA fournie
                if pcas is not None:
                    pipe = pcas[name]
                    pivot = df.pivot_table(
                        index=index_col, columns=columns_col, values=value_col
                    ).sort_index()
                    scores = pipe.transform(pivot)
                    cols = [f"{prefix}_{i}" for i in range(n_components)]
                    scores_df = pd.DataFrame(scores, index=pivot.index, columns=cols)
                else:
                    # Training : fit PCA de manière expanding avec refresh périodique
                    pipe = None
                    last_fit_date = None

                    for i, current_date_ordinal in enumerate(unique_dates):
                        # Convertir l'ordinal en date pour les calculs de temps
                        current_date = pd.Timestamp.fromordinal(
                            int(current_date_ordinal)
                        )

                        # Déterminer si on doit refitter la PCA
                        should_refit = pipe is None or (  # Première fois
                            last_fit_date is not None
                            and (current_date - last_fit_date).days >= refresh_frequency
                        )

                        if (
                            should_refit and i > 30
                        ):  # Attendre au moins 30 jours de données
                            # Prendre les données des 'lookback_days' derniers jours
                            lookback_start_date = current_date - pd.Timedelta(
                                days=lookback_days
                            )
                            lookback_start_ordinal = pd.Timestamp.toordinal(
                                lookback_start_date
                            )

                            # Masque pour les dates passées uniquement (éviter le leakage)
                            mask_fit = (df[index_col] >= lookback_start_ordinal) & (
                                df[index_col] < current_date_ordinal
                            )
                            df_fit = df[mask_fit]

                            if len(df_fit) > 0:
                                # Créer le pivot pour la période de lookback
                                pivot_fit = df_fit.pivot_table(
                                    index=index_col,
                                    columns=columns_col,
                                    values=value_col,
                                ).sort_index()

                                # Vérifier qu'on a assez de dates et de colonnes
                                if (
                                    len(pivot_fit) >= n_components
                                    and pivot_fit.shape[1] >= n_components
                                ):
                                    # Créer nouveau pipeline
                                    steps = [
                                        (
                                            "imputer",
                                            SimpleImputer(strategy=impute_strategy),
                                        )
                                    ]
                                    if standardize:
                                        steps.append(
                                            (
                                                "scaler",
                                                StandardScaler(
                                                    with_mean=True, with_std=True
                                                ),
                                            )
                                        )
                                    pca = PCA(n_components=n_components, random_state=0)
                                    steps.append(("pca", pca))
                                    pipe = Pipeline(steps)
                                    pipe.fit(pivot_fit)
                                    last_fit_date = current_date

                                    logger.debug(
                                        f"PCA {name} refitted at date {current_date.strftime('%Y-%m-%d')} "
                                        f"using {len(pivot_fit)} dates and {pivot_fit.shape[1]} columns"
                                    )

                        # Transform pour la date courante uniquement
                        if pipe is not None:
                            df_current = df[df[index_col] == current_date_ordinal]
                            if len(df_current) > 0:
                                pivot_current = df_current.pivot_table(
                                    index=index_col,
                                    columns=columns_col,
                                    values=value_col,
                                )
                                try:
                                    scores_current = pipe.transform(pivot_current)
                                    scores_dict = {
                                        index_col: [current_date_ordinal],
                                        **{
                                            f"{prefix}_{j}": [scores_current[0, j]]
                                            for j in range(n_components)
                                        },
                                    }
                                    all_scores.append(pd.DataFrame(scores_dict))
                                except Exception as e:
                                    # En cas d'erreur (ex: nouvelles colonnes), créer des valeurs manquantes
                                    logger.debug(
                                        f"PCA transform error at date {current_date}: {str(e)}"
                                    )
                                    scores_dict = {
                                        index_col: [current_date_ordinal],
                                        **{
                                            f"{prefix}_{j}": [np.nan]
                                            for j in range(n_components)
                                        },
                                    }
                                    all_scores.append(pd.DataFrame(scores_dict))
                        else:
                            # Pas encore de PCA fittée, créer des NaN
                            scores_dict = {
                                index_col: [current_date_ordinal],
                                **{
                                    f"{prefix}_{j}": [np.nan]
                                    for j in range(n_components)
                                },
                            }
                            all_scores.append(pd.DataFrame(scores_dict))

                    # Combiner tous les scores
                    if all_scores:
                        scores_df = pd.concat(all_scores, ignore_index=True)
                    else:
                        # Créer un DataFrame vide avec les bonnes colonnes
                        cols = [f"{prefix}_{i}" for i in range(n_components)]
                        scores_df = pd.DataFrame(columns=[index_col] + cols)

                # Merger les scores
                df = df.merge(scores_df, on=index_col, how="left")
                df.index = index_saved

                # Forward fill puis 0 pour éviter les NaN
                pca_cols = [col for col in df.columns if col.startswith(prefix)]
                df[pca_cols] = df[pca_cols].fillna(method="ffill").fillna(0)

                pcas_dict.update({name: pipe})

            else:
                # Approche classique (non time series ou index != date)
                pivot = df.pivot_table(
                    index=index_col, columns=columns_col, values=value_col
                ).sort_index()

                # Pipeline à réutiliser entre train et test
                if pcas is None:
                    steps = [("imputer", SimpleImputer(strategy=impute_strategy))]
                    if standardize:
                        steps.append(
                            ("scaler", StandardScaler(with_mean=True, with_std=True))
                        )
                    pca = PCA(n_components=n_components, random_state=0)
                    steps.append(("pca", pca))
                    pipe = Pipeline(steps)
                    pipe.fit(pivot)  # <- fit sur TRAIN uniquement
                else:
                    pipe = pcas[name]  # <- TEST : on réutilise le pipe existant

                scores = pipe.transform(pivot)  # shape: (n_index, n_components)
                cols = [f"{prefix}_{i}" for i in range(n_components)]
                scores_df = pd.DataFrame(scores, index=pivot.index, columns=cols)

                df = df.merge(scores_df.reset_index(), on=index_col, how="left")
                df.index = index_saved
                pcas_dict.update({name: pipe})

        return df, pcas_dict

    # ----------------- 2) PCA TEMPORELLE (liste de colonnes lags) ----------------
    def add_pca_feature_temporal_old(
        self,
        df: pd.DataFrame,
        *,
        n_components: int = 5,
        pcas: dict[str, Pipeline] | None = None,  # si fourni: transform only
        impute_strategy: (
            str | None
        ) = None,  # None = on exige toutes les colonnes présentes
        standardize: bool = True,
    ) -> tuple[pd.DataFrame, dict[str, Pipeline]]:
        """
        Applique une PCA sur une matrice (rows = lignes df, cols = lags).
        Fit le Pipeline sur TRAIN si pcas=None; sinon, utilise pcas et fait transform.
        Ajoute les colonnes f"{prefix}_{i}" dans df. Renvoie (df, pipe).
        """
        pcas_dict = {}

        for pca_temporal in self.pca_temporal:
            name, cols = (pca_temporal[k] for k in ("name", "columns"))
            prefix = f"TMP_PC_{name}"

            # Masque des lignes utilisables
            if impute_strategy is None:
                mask = (
                    df[cols].notna().all(axis=1)
                )  # on n'impute pas → lignes complètes
                X_fit = df.loc[mask, cols]
            else:
                mask = df[cols].notna().any(axis=1)  # on imputera → au moins une valeur
                X_fit = df.loc[mask, cols]

            # Pipeline
            if pcas is None:
                steps = []
                if impute_strategy is not None:
                    steps.append(("imputer", SimpleImputer(strategy=impute_strategy)))
                if standardize:
                    steps.append(
                        ("scaler", StandardScaler(with_mean=True, with_std=True))
                    )
                pca = PCA(n_components=n_components, random_state=0)
                steps.append(("pca", pca))
                pipe = Pipeline(steps)
                if not X_fit.empty:
                    pipe.fit(X_fit)  # <- fit sur TRAIN uniquement
            else:
                pipe = pcas[name]  # <- TEST

            # Transform uniquement sur lignes valides (mask)
            if not df.loc[mask, cols].empty:
                Z = pipe.transform(df.loc[mask, cols])
                for i in range(n_components):
                    df.loc[mask, f"{prefix}_{i}"] = Z[:, i]
            else:
                # crée les colonnes vides si aucune ligne valide (cohérence de schéma)
                for i in range(n_components):
                    df[f"{prefix}_{i}"] = pd.NA

            pcas_dict.update({name: pipe})

        return df, pcas_dict

    def add_pca_feature_temporal(
        self,
        df: pd.DataFrame,
        *,
        n_components: int = 5,
        pcas: dict[str, Pipeline] | None = None,
        impute_strategy: str = "median",
        standardize: bool = True,
        lookback_days: int = 365,
        refresh_frequency: int = 90,
    ) -> tuple[pd.DataFrame, dict[str, Pipeline]]:
        """
        PCA temporelle pour time series avec support panel data.
        Crée automatiquement les colonnes de lags et évite le look-ahead bias.

        Format pca_temporal simplifié:
        [{"name": "LAST_20_RET", "column": "RET", "lags": 20}]
        """
        pcas_dict = {}

        for pca_config in self.pca_temporal:
            # Support both old and new format
            if "columns" in pca_config:
                # Old format: use existing columns
                name = pca_config["name"]
                lag_columns = pca_config["columns"]
                base_column = None
                num_lags = len(lag_columns)
            else:
                # New format: create lag columns
                name = pca_config["name"]
                base_column = pca_config["column"].upper()
                num_lags = pca_config.get("lags", 20)

                # Create lag columns if they don't exist
                if self.group_column:
                    # Panel data: create lags by group
                    for lag in range(1, num_lags + 1):
                        lag_col = f"{base_column}_-{lag}"
                        if lag_col not in df.columns:
                            df[lag_col] = df.groupby(self.group_column)[
                                base_column
                            ].shift(lag)
                else:
                    # Simple time series
                    for lag in range(1, num_lags + 1):
                        lag_col = f"{base_column}_-{lag}"
                        if lag_col not in df.columns:
                            df[lag_col] = df[base_column].shift(lag)

                lag_columns = [f"{base_column}_-{i}" for i in range(1, num_lags + 1)]

            prefix = f"TMP_PC_{name}"

            # For time series: avoid look-ahead bias
            if self.time_series and self.date_column:
                all_scores = []
                unique_dates = sorted(df[self.date_column].unique())

                if pcas is not None:
                    # transform: use provided PCA
                    pipe = pcas[name]

                    # Apply to all data at once
                    mask = df[lag_columns].notna().all(axis=1)
                    if mask.any():
                        X_transform = df.loc[mask, lag_columns]
                        scores = pipe.transform(X_transform)

                        for i in range(n_components):
                            df.loc[mask, f"{prefix}_{i}"] = scores[:, i]

                    # Fill NaN with forward fill then 0
                    pca_cols = [f"{prefix}_{i}" for i in range(n_components)]
                    df[pca_cols] = df[pca_cols].fillna(method="ffill").fillna(0)

                else:
                    # Training: expanding window with periodic refresh
                    pipe = None
                    last_fit_date = None

                    for current_date_ordinal in unique_dates:
                        current_date = pd.Timestamp.fromordinal(
                            int(current_date_ordinal)
                        )

                        # Determine if we should refit
                        should_refit = pipe is None or (
                            last_fit_date is not None
                            and (current_date - last_fit_date).days >= refresh_frequency
                        )

                        if (
                            should_refit
                            and len(df[df[self.date_column] < current_date_ordinal])
                            > num_lags * 2
                        ):
                            # Get historical data for fitting
                            lookback_start = current_date - pd.Timedelta(
                                days=lookback_days
                            )
                            lookback_start_ordinal = pd.Timestamp.toordinal(
                                lookback_start
                            )

                            mask_fit = (
                                (df[self.date_column] >= lookback_start_ordinal)
                                & (df[self.date_column] < current_date_ordinal)
                                & df[lag_columns].notna().all(axis=1)
                            )

                            if mask_fit.sum() >= n_components:
                                X_fit = df.loc[mask_fit, lag_columns]

                                # Create pipeline
                                steps = []
                                if impute_strategy is not None:
                                    steps.append(
                                        (
                                            "imputer",
                                            SimpleImputer(strategy=impute_strategy),
                                        )
                                    )
                                if standardize:
                                    steps.append(("scaler", StandardScaler()))
                                steps.append(
                                    (
                                        "pca",
                                        PCA(n_components=n_components, random_state=0),
                                    )
                                )

                                pipe = Pipeline(steps)
                                pipe.fit(X_fit)
                                last_fit_date = current_date

                                logger.debug(
                                    f"Temporal PCA {name} refitted at {current_date.strftime('%Y-%m-%d')} "
                                    f"using {len(X_fit)} samples"
                                )

                        # Transform current date data
                        if pipe is not None:
                            mask_current = (
                                df[self.date_column] == current_date_ordinal
                            ) & df[lag_columns].notna().all(axis=1)

                            if mask_current.any():
                                X_current = df.loc[mask_current, lag_columns]
                                scores = pipe.transform(X_current)

                                for i in range(n_components):
                                    df.loc[mask_current, f"{prefix}_{i}"] = scores[:, i]

                    # Fill NaN with forward fill then 0
                    pca_cols = [f"{prefix}_{i}" for i in range(n_components)]
                    for col in pca_cols:
                        if col not in df.columns:
                            df[col] = 0
                    df[pca_cols] = df[pca_cols].fillna(method="ffill").fillna(0)

                pcas_dict[name] = pipe

            else:
                # Non time-series: use original approach
                mask = df[lag_columns].notna().all(axis=1)

                if pcas is None and mask.any():
                    X_fit = df.loc[mask, lag_columns]

                    steps = []
                    if impute_strategy is not None:
                        steps.append(
                            ("imputer", SimpleImputer(strategy=impute_strategy))
                        )
                    if standardize:
                        steps.append(("scaler", StandardScaler()))
                    steps.append(
                        ("pca", PCA(n_components=n_components, random_state=0))
                    )

                    pipe = Pipeline(steps)
                    pipe.fit(X_fit)
                    pcas_dict[name] = pipe
                elif pcas is not None:
                    pipe = pcas[name]
                    pcas_dict[name] = pipe
                else:
                    continue

                if mask.any():
                    X_transform = df.loc[mask, lag_columns]
                    scores = pipe.transform(X_transform)

                    for i in range(n_components):
                        df.loc[mask, f"{prefix}_{i}"] = scores[:, i]

                # Fill missing values
                pca_cols = [f"{prefix}_{i}" for i in range(n_components)]
                for col in pca_cols:
                    if col not in df.columns:
                        df[col] = 0
                df[pca_cols] = df[pca_cols].fillna(0)

        return df, pcas_dict

    # encoding categorical features
    def encode_categorical_features(
        self,
        df: pd.DataFrame,
        transformer: ColumnTransformer | None = None,
    ) -> tuple[pd.DataFrame, ColumnTransformer]:
        """
        Encodes categorical columns using one-hot, binary, ordinal, and frequency encoding.

        Parameters:
            df (pd.DataFrame): Input DataFrame
            columns_onehot (list[str]) Creates one binary column per category forLow-cardinality categorical features
            columns_binary (list[str]) Converts categories into binary and splits bits across columns for Mid-to-high cardinality (e.g., 10–100 unique values)
            columns_ordinal (list[str]) Assigns integer ranks to categories When order matters (e.g., low < medium < high)
            columns_frequency (list[str]) Replaces each category with its frequency count, normalized to proportion. High-cardinality features with meaning in frequency
            transformer (ColumnTransformer, optional): if provided, applies transform only

        Returns:
            tuple: (transformed DataFrame, ColumnTransformer)
        """
        columns_onehot: list[str] = self.columns_onehot
        columns_binary: list[str] = self.columns_binary
        columns_ordinal: list[str] = self.columns_ordinal
        columns_frequency: list[str] = self.columns_frequency

        X = df.loc[:, ~df.columns.str.contains("^TARGET_")]
        y = df.loc[:, df.columns.str.contains("^TARGET_")]
        save_in_db = False

        all_columns = (
            columns_onehot + columns_binary + columns_ordinal + columns_frequency
        )

        if transformer:
            transformed = transformer.transform(X)
        else:
            transformer = ColumnTransformer(
                transformers=[
                    (
                        "onehot",
                        OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        columns_onehot,
                    ),
                    (
                        "ordinal",
                        OrdinalEncoder(
                            handle_unknown="use_encoded_value", unknown_value=-1
                        ),
                        columns_ordinal,
                    ),
                    ("binary", BinaryEncoder(handle_unknown="value"), columns_binary),
                    ("freq", CountEncoder(normalize=True), columns_frequency),
                ],
                remainder="passthrough",
            )
            transformed = transformer.fit_transform(X)
            save_in_db = True

        # Build output column names
        column_names = []

        if columns_onehot:
            column_names.extend(
                transformer.named_transformers_["onehot"]
                .get_feature_names_out(columns_onehot)
                .tolist()
            )

        if columns_ordinal:
            column_names.extend(columns_ordinal)

        if columns_binary:
            column_names.extend(
                transformer.named_transformers_["binary"]
                .get_feature_names_out(columns_binary)
                .tolist()
            )

        if columns_frequency:
            column_names.extend(columns_frequency)

        # Add passthrough (non-encoded) columns
        passthrough_columns = [col for col in X.columns if col not in all_columns]
        column_names.extend(passthrough_columns)

        X_transformed = pd.DataFrame(transformed, columns=column_names, index=df.index)

        # Try to convert columns to best possible dtypes
        X_transformed = X_transformed.convert_dtypes()

        # Insert features in db
        if save_in_db:
            # Get feature types from transformed data
            categorical_features, numerical_features = get_features_by_types(
                X_transformed
            )

            # Get column names from DataFrames
            cat_feature_names = categorical_features.columns.tolist()
            num_feature_names = numerical_features.columns.tolist()

            # Combine all feature names and their types
            all_feature_names = cat_feature_names + num_feature_names
            all_feature_types = ["categorical"] * len(cat_feature_names) + [
                "numerical"
            ] * len(num_feature_names)

            # Upsert features in bulk if we have any features
            if all_feature_names:
                Feature.bulk_upsert(
                    name=all_feature_names,
                    type=all_feature_types,
                )

            # Upsert targets in bulk
            target_names = y.columns.tolist()
            target_types = [
                (
                    "classification"
                    if int(target.split("_")[1]) in self.target_clf
                    else "regression"
                )
                for target in target_names
            ]

            Target.bulk_upsert(name=target_names, type=target_types)

            # Get all the upserted objects
            targets = Target.filter(name__in=target_names)

            # Update experiment with targets
            experiment = Experiment.get(self.experiment_id)
            if experiment:
                experiment.targets = targets
                experiment.save()

        return pd.concat([X_transformed, y], axis=1), transformer


# utils
def summarize_dataframe(
    df: pd.DataFrame, sample_categorical_threshold: int = 15
) -> pd.DataFrame:
    summary = []

    def is_hashable_series(series: pd.Series) -> bool:
        try:
            _ = series.dropna().unique()
            return True
        except TypeError:
            return False

    df = convert_object_columns_that_are_numeric(df)
    df = df.convert_dtypes()

    for col in df.columns:
        total_missing = df[col].isna().sum()
        col_data = df[col].dropna()
        dtype = col_data.dtype

        if col_data.empty:
            summary.append(
                {
                    "Column": col,
                    "Dtype": dtype,
                    "Type": "unknown",
                    "Detail": "No non-null values",
                    "Missing": total_missing,
                }
            )
            continue

        # Case 1: Numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            unique_vals = col_data.nunique()

            if set(col_data.unique()).issubset({0, 1}):
                col_type = "binary-categorical"
                detail = "0/1 values only"
            elif (
                pd.api.types.is_integer_dtype(col_data)
                and unique_vals <= sample_categorical_threshold
            ):
                col_type = "multi-categorical"
                top_vals = col_data.value_counts().head(10)
                detail = ", ".join(f"{k} ({v})" for k, v in top_vals.items())
            else:
                col_type = "numeric"
                q = col_data.quantile([0, 0.25, 0.5, 0.75, 1])
                detail = (
                    f"Min: {q.iloc[0]:.2f}, Q1: {q.iloc[1]:.2f}, Median: {q.iloc[2]:.2f}, "
                    f"Q3: {q.iloc[3]:.2f}, Max: {q.iloc[4]:.2f}"
                )

        # Case 2: Object or other hashable columns
        elif is_hashable_series(col_data):
            unique_vals = col_data.nunique()
            if unique_vals <= sample_categorical_threshold:
                col_type = "object-categorical"
                top_vals = col_data.value_counts().head(10)
                detail = ", ".join(f"{k} ({v})" for k, v in top_vals.items())
            else:
                col_type = "high-cardinality-categorical"
                detail = f"{unique_vals} unique values"

        # Case 3: Unusable columns
        else:
            col_type = "non-hashable"
            detail = f"Non-hashable type: {type(col_data.iloc[0])}"

        summary.append(
            {
                "Column": col,
                "Dtype": dtype,
                "Type": col_type,
                "Detail": detail,
                "Missing": total_missing,
            }
        )

    return pd.DataFrame(summary)


# Utility functions for data splitting
# ===================================


def split_data(
    data,
    experiment=None,
    time_series=None,
    date_column=None,
    group_column=None,
    val_size=None,
    test_size=None,
    target_numbers=None,
    target_clf=None,
    experiment_id=None,
):
    """
    Utility function to split data into train, validation, and test sets.

    Args:
        data (pd.DataFrame): Input data to split
        experiment: LeCrapaud experiment instance (preferred - extracts all params automatically)
        time_series (bool): Whether to use time series splitting (overrides experiment)
        date_column (str): Date column for time series splitting (overrides experiment)
        group_column (str): Group column for time series splitting (overrides experiment)
        val_size (float): Validation set size (0.0-1.0) (overrides experiment)
        test_size (float): Test set size (0.0-1.0) (overrides experiment)
        target_numbers (list): List of target numbers for stratification (overrides experiment)
        target_clf (list): List of classification target numbers (overrides experiment)
        experiment_id (int): Optional experiment ID to update sizes in database

    Returns:
        tuple: (train, val, test) DataFrames
    """
    # Extract parameters from experiment if provided
    if experiment is not None:
        # Check if it's a BaseExperiment or just the experiment database object
        if hasattr(experiment, "context") and experiment.context:
            # It's a database experiment object with context
            context = experiment.context
            if time_series is None:
                time_series = context.get("time_series", False)
            if date_column is None:
                date_column = context.get("date_column")
            if group_column is None:
                group_column = context.get("group_column")
            if val_size is None:
                val_size = context.get("val_size", 0.2)
            if test_size is None:
                test_size = context.get("test_size", 0.2)
            if target_numbers is None:
                target_numbers = context.get("target_numbers", [])
            if target_clf is None:
                target_clf = context.get("target_clf", [])
            if experiment_id is None:
                experiment_id = experiment.id

    # Set defaults if still None
    if time_series is None:
        time_series = False
    if val_size is None:
        val_size = 0.2
    if test_size is None:
        test_size = 0.2
    if target_numbers is None:
        target_numbers = []
    if target_clf is None:
        target_clf = []

    dates = {}
    if time_series:
        (train, val, test), dates = _split_time_series(
            data, date_column, group_column, val_size, test_size
        )
    else:
        # Use first target for stratification if it's a classification target
        stratify_col = None
        if target_numbers and target_clf and target_numbers[0] in target_clf:
            stratify_col = f"TARGET_{target_numbers[0]}"
        train, val, test = _split_standard(data, val_size, test_size, stratify_col)

    # Update experiment with sizes if experiment_id provided
    if experiment_id:
        Experiment.update(
            id=experiment_id,
            train_size=len(train),
            val_size=len(val),
            test_size=len(test),
            **dates,
        )

    return train, val, test


def _split_time_series(data, date_column, group_column, val_size, test_size):
    """Time series splitting preserving temporal order."""
    if not date_column:
        raise ValueError("Please specify a date_column for time series")

    df = data.copy()
    if group_column:
        df.sort_values([date_column, group_column], inplace=True)
    else:
        df.sort_values(date_column, inplace=True)

    dates = df[date_column].unique()

    val_first_id = int(len(dates) * (1 - val_size - test_size)) + 1
    test_first_id = int(len(dates) * (1 - test_size)) + 1

    train = df[df[date_column].isin(dates[:val_first_id])]
    val = df[df[date_column].isin(dates[val_first_id:test_first_id])]
    test = df[df[date_column].isin(dates[test_first_id:])]

    dates = {}
    for name, data in zip(["train", "val", "test"], [train, val, test]):
        dates[f"{name}_start_date"] = (
            data[date_column].map(pd.Timestamp.fromordinal).iat[0]
        )
        dates[f"{name}_end_date"] = (
            data[date_column].map(pd.Timestamp.fromordinal).iat[-1]
        )

        logger.info(
            f"{data.shape} {name} data from {dates[f'{name}_start_date'].strftime('%d/%m/%Y')} to {dates[f'{name}_end_date'].strftime('%d/%m/%Y')}"
        )

    return (
        train.reset_index(drop=True),
        val.reset_index(drop=True),
        test.reset_index(drop=True),
    ), dates


def _split_standard(data, val_size, test_size, stratify_col=None, random_state=42):
    """Standard random splitting with optional stratification."""
    from sklearn.model_selection import train_test_split

    df = data.copy()

    stratify_vals = (
        df[stratify_col] if stratify_col and stratify_col in df.columns else None
    )

    # First split: train + (val + test)
    train, temp = train_test_split(
        df,
        test_size=val_size + test_size,
        random_state=random_state,
        stratify=stratify_vals,
    )

    # Adjust stratify target for val/test split
    stratify_temp = (
        temp[stratify_col] if stratify_col and stratify_col in df.columns else None
    )

    # Compute val and test sizes relative to temp
    val_ratio = val_size / (val_size + test_size)

    val, test = train_test_split(
        temp,
        test_size=1 - val_ratio,
        random_state=random_state,
        stratify=stratify_temp,
    )

    for name, data in zip(["train", "val", "test"], [train, val, test]):
        logger.info(f"{data.shape} {name} data")

    return (
        train.reset_index(drop=True),
        val.reset_index(drop=True),
        test.reset_index(drop=True),
    )
