"""LeCrapaud API module.

This module provides the main interface for the LeCrapaud machine learning pipeline.
It allows for end-to-end ML workflows including data preprocessing, feature engineering,
model training, and prediction.

Basic Usage:
    # Create a new experiment
    experiment = LeCrapaud(data=data, target_numbers=[1], target_clf=[1])

    # Train the model
    experiment.fit(data)

    # Make predictions
    predictions, scores_reg, scores_clf = experiment.predict(new_data)

    # Load existing experiment
    experiment = LeCrapaud(id=123)
    predictions = experiment.predict(new_data)

    # Class methods for experiment management
    best_exp = LeCrapaud.get_best_experiment_by_name('my_experiment')
    all_exps = LeCrapaud.list_experiments('my_experiment')
"""

import joblib
import pandas as pd
import ast
import os
import time
import logging
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import lime
import lime.lime_tabular
import shap
from typing import Literal
from lecrapaud.db.session import init_db
from lecrapaud.feature_selection import FeatureSelector
from lecrapaud.model_preprocessing import ModelPreprocessor
from lecrapaud.model_selection import (
    ModelSelector,
    BaseModel,
    evaluate,
    load_model,
    plot_threshold,
    plot_evaluation_for_classification,
)
from lecrapaud.feature_engineering import FeatureEngineer
from lecrapaud.feature_preprocessing import FeaturePreprocessor
from lecrapaud.experiment import create_experiment
from lecrapaud.models import Experiment
from lecrapaud.search_space import normalize_models_idx, all_models
from lecrapaud.utils import logger
from lecrapaud.directories import tmp_dir


class LeCrapaud:
    """
    Unified LeCrapaud class for machine learning experiments.

    This class provides both the ML pipeline functionality and experiment management.
    It can be initialized either with new data to create an experiment or with an
    experiment ID to load an existing one.

    Usage:
        # Create new experiment
        experiment = LeCrapaud(data=df, target_numbers=[1, 2], ...)

        # Load existing experiment
        experiment = LeCrapaud(id=123)

        # Train the model
        experiment.fit(data)

        # Make predictions
        predictions = experiment.predict(new_data)

    Args:
        id (int, optional): ID of an existing experiment to load
        data (pd.DataFrame, optional): Input data for a new experiment
        uri (str, optional): Database connection URI
        **kwargs: Additional configuration parameters
    """

    def __init__(
        self, id: int = None, data: pd.DataFrame = None, uri: str = None, **kwargs
    ):
        """Initialize LeCrapaud with either new or existing experiment."""
        # Initialize database connection
        init_db(uri=uri)

        if id:
            # Load existing experiment
            self.experiment = Experiment.get(id)
            # Context from DB takes precedence over kwargs
            effective_kwargs = {
                **self.DEFAULT_PARAMS,
                **kwargs,
                **self.experiment.context,
            }
        else:
            if data is None:
                raise ValueError(
                    "Either id or data must be provided. Data can be a path to a folder containing trained models"
                )
            # New experiment: merge defaults with provided kwargs
            effective_kwargs = {**self.DEFAULT_PARAMS, **kwargs}

        # Normalize models_idx if present
        if "models_idx" in effective_kwargs:
            effective_kwargs["models_idx"] = normalize_models_idx(
                effective_kwargs["models_idx"]
            )

        # Set all parameters as instance attributes
        for key, value in effective_kwargs.items():
            setattr(self, key, value)

        # Create experiment if new
        if not id:
            self.experiment = create_experiment(data=data, **effective_kwargs)

        # Create directories
        self.preprocessing_dir = f"{self.experiment.path}/preprocessing"
        self.data_dir = f"{self.experiment.path}/data"
        os.makedirs(self.preprocessing_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    # Default values for all experiment parameters
    DEFAULT_PARAMS = {
        # Feature Engineering
        "columns_drop": [],
        "columns_boolean": [],
        "columns_date": [],
        "columns_te_groupby": [],
        "columns_te_target": [],
        "fourier_order": 1,
        # Preprocessing
        "time_series": False,
        "val_size": 0.2,
        "test_size": 0.2,
        "columns_pca": [],
        "pca_temporal": [],
        "pca_cross_sectional": [],
        "columns_onehot": [],
        "columns_binary": [],
        "columns_ordinal": [],
        "columns_frequency": [],
        # Feature Selection
        "percentile": 20,
        "corr_threshold": 80,
        "max_features": 50,
        "max_p_value_categorical": 0.05,
        # Model Selection
        "target_numbers": [],
        "target_clf": [],
        "models_idx": [],
        "max_timesteps": 120,
        "perform_hyperopt": True,
        "number_of_trials": 20,
        "perform_crossval": False,
        "plot": True,
        "preserve_model": True,
        "target_clf_thresholds": {},
        # Data structure
        "date_column": None,
        "group_column": None,
    }

    @classmethod
    def get_default_params(cls):
        """Get the default parameters for experiments."""
        return cls.DEFAULT_PARAMS.copy()

    def get_effective_context(self):
        """Get the effective context (merged defaults + experiment context)."""
        return {k: getattr(self, k, v) for k, v in self.DEFAULT_PARAMS.items()}

    @classmethod
    def get_last_experiment_by_name(cls, name: str, **kwargs):
        """Retrieve the last experiment by name."""
        return cls(id=Experiment.get_last_by_name(name).id, **kwargs)

    @classmethod
    def get_best_experiment_by_name(cls, name: str, **kwargs):
        """Retrieve the best experiment by score."""
        best_exp = Experiment.get_best_by_score(name=name)
        if not best_exp:
            return None
        return cls(id=best_exp.id, **kwargs)

    @classmethod
    def list_experiments(cls, name: str = None, limit: int = 1000):
        """List all experiments in the database."""
        return [
            cls(id=exp.id) for exp in Experiment.get_all_by_name(name=name, limit=limit)
        ]

    @classmethod
    def compare_experiment_scores(cls, name: str):
        """Compare scores of experiments with matching names."""
        experiments = cls.list_experiments(name=name)

        if not experiments:
            return {"error": f"No experiments found with name containing '{name}'"}

        comparison = {}

        for exp in experiments:
            for model_sel in exp.experiment.model_selections:
                if model_sel.best_score:
                    scores = {
                        "rmse": model_sel.best_score["rmse"],
                        "logloss": model_sel.best_score["logloss"],
                        "accuracy": model_sel.best_score["accuracy"],
                        "f1": model_sel.best_score["f1"],
                        "roc_auc": model_sel.best_score["roc_auc"],
                    }
                    target_name = model_sel.target.name
                    comparison[exp.experiment.name][target_name] = scores
                else:
                    logger.warning(
                        f"No best score found for experiment {exp.experiment.name} and target {model_sel.target.name}"
                    )

        return comparison

    # Main ML Pipeline Methods
    # ========================

    def fit(self, data, best_params=None):
        """
        Fit the complete ML pipeline on the provided data.

        Args:
            data (pd.DataFrame): Input training data
            best_params (dict, optional): Pre-defined best parameters

        Returns:
            self: Returns self for chaining
        """
        logger.info("Running training...")

        # Step 1: Feature Engineering
        logger.info("Starting feature engineering...")
        feature_eng = FeatureEngineer(experiment=self.experiment)
        feature_eng.fit(data)
        data_eng = feature_eng.get_data()
        logger.info("Feature engineering done.")

        # Step 2: Feature Preprocessing (split data)
        logger.info("Starting feature preprocessing...")
        from lecrapaud.feature_preprocessing import split_data

        train, val, test = split_data(data_eng, experiment=self.experiment)

        # Apply feature preprocessing transformations
        feature_preprocessor = FeaturePreprocessor(experiment=self.experiment)
        feature_preprocessor.fit(train)
        train = feature_preprocessor.transform(train)
        if val is not None:
            val = feature_preprocessor.transform(val)
        if test is not None:
            test = feature_preprocessor.transform(test)
        logger.info("Feature preprocessing done.")

        # Step 3: Feature Selection (for each target)
        logger.info("Starting feature selection...")
        for target_number in self.target_numbers:
            feature_selector = FeatureSelector(
                experiment=self.experiment, target_number=target_number
            )
            feature_selector.fit(train)

        # Refresh experiment to get updated features
        self.experiment = Experiment.get(self.experiment.id)
        all_features = self.experiment.get_all_features(
            date_column=self.date_column, group_column=self.group_column
        )
        joblib.dump(
            all_features, f"{self.experiment.path}/preprocessing/all_features.pkl"
        )
        logger.info("Feature selection done.")

        # Step 4: Model Preprocessing (scaling)
        logger.info("Starting model preprocessing...")
        model_preprocessor = ModelPreprocessor(experiment=self.experiment)

        # Fit and transform training data, then transform val/test
        model_preprocessor.fit(train)
        train_scaled = model_preprocessor.transform(train)
        val_scaled = model_preprocessor.transform(val) if val is not None else None
        test_scaled = model_preprocessor.transform(test) if test is not None else None

        # Create data dict for model selection (keep both raw and scaled splits)
        std_data = {
            "train": train,
            "val": val,
            "test": test,
            "train_scaled": train_scaled,
            "val_scaled": val_scaled,
            "test_scaled": test_scaled,
        }
        for key, items in std_data.items():
            joblib.dump(items, f"{self.data_dir}/{key}.pkl")

        # Handle time series reshaping if needed
        reshaped_data = None
        # Check if any model requires recurrent processing
        need_reshaping = (
            any(all_models[i].get("recurrent") for i in self.models_idx)
            and self.time_series
        )

        if need_reshaping:
            # Sanity check: make sure we have enough data for max_timesteps
            if (
                self.group_column
                and train_scaled.groupby(self.group_column).size().min()
                < self.max_timesteps
            ) or train_scaled.shape[0] < self.max_timesteps:
                raise ValueError(
                    f"Not enough data for group_column {self.group_column} to reshape data for recurrent models"
                )

            from lecrapaud.model_preprocessing import reshape_time_series

            features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )
            reshaped_data = reshape_time_series(
                self.experiment,
                features,
                train_scaled,
                val_scaled,
                test_scaled,
                timesteps=self.max_timesteps,
            )
        logger.info("Model preprocessing done.")

        # Step 5: Model Selection (for each target)
        logger.info("Starting model selection...")
        self.models_ = {}
        for target_number in self.target_numbers:
            model_selector = ModelSelector(
                experiment=self.experiment, target_number=target_number
            )
            model_selector.fit(
                std_data, reshaped_data=reshaped_data, best_params=best_params
            )
            self.models_[target_number] = model_selector.get_best_model()
        logger.info("Model selection done.")

        return self

    def predict(self, new_data, verbose: int = 0):
        """
        Make predictions on new data using the trained pipeline.

        Args:
            new_data (pd.DataFrame): Input data for prediction
            verbose (int): Verbosity level (0=warnings only, 1=all logs)

        Returns:
            tuple: (predictions_df, scores_regression, scores_classification)
        """
        # for scores if TARGET is in columns
        scores_reg = []
        scores_clf = []

        if verbose == 0:
            logger.setLevel(logging.WARNING)

        logger.warning("Running prediction...")

        # Apply the same preprocessing pipeline as training
        # Step 1: Feature Engineering
        feature_eng = FeatureEngineer(experiment=self.experiment)
        data = feature_eng.transform(new_data)

        # Step 2: Feature Preprocessing (no splitting for prediction)
        feature_preprocessor = FeaturePreprocessor(experiment=self.experiment)
        # Load existing transformations and apply
        data = feature_preprocessor.transform(data)

        # Step 3: Model Preprocessing (scaling)
        model_preprocessor = ModelPreprocessor(experiment=self.experiment)
        # Apply existing scaling
        scaled_data = model_preprocessor.transform(data)

        # Step 4: Time series reshaping if needed
        reshaped_data = None
        # Check if any model requires recurrent processing
        need_reshaping = (
            any(all_models[i].get("recurrent") for i in self.models_idx)
            and self.time_series
        )

        if need_reshaping:
            # Sanity check: make sure we have enough data for max_timesteps
            if (
                self.group_column
                and scaled_data.groupby(self.group_column).size().min()
                < self.max_timesteps
            ) or scaled_data.shape[0] < self.max_timesteps:
                raise ValueError(
                    f"Not enough data for group_column {self.group_column} to reshape data for recurrent models"
                )

            from lecrapaud.model_preprocessing import reshape_time_series

            all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )
            # For prediction, we reshape the entire dataset
            reshaped_data = reshape_time_series(
                self.experiment, all_features, scaled_data, timesteps=self.max_timesteps
            )
            reshaped_data = reshaped_data[
                "x_train_reshaped"
            ]  # Only need X data for prediction

        # Step 5: Predict for each target
        for target_number in self.target_numbers:
            # Load the trained model
            target_dir = f"{self.experiment.path}/TARGET_{target_number}"
            model = BaseModel(path=target_dir, target_number=target_number)

            # Get features for this target
            all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )
            features = self.experiment.get_features(target_number)

            # Prepare prediction data
            if model.recurrent:
                features_idx = [
                    i for i, e in enumerate(all_features) if e in set(features)
                ]
                x_pred = reshaped_data[:, :, features_idx]
            else:
                x_pred = scaled_data[features] if model.need_scaling else data[features]

            # Make prediction
            start = time.time()
            y_pred = model.predict(x_pred)
            end = time.time()
            logger.info(f"⏱️ Prediction took {end - start} seconds")

            # Fix index for recurrent models
            if model.recurrent:
                y_pred.index = new_data.index

            # Unscale prediction if needed
            if (
                model.need_scaling
                and model.target_type == "regression"
                and model.scaler_y is not None
            ):
                y_pred = pd.Series(
                    model.scaler_y.inverse_transform(
                        y_pred.values.reshape(-1, 1)
                    ).flatten(),
                    index=new_data.index,
                )
                y_pred.name = "PRED"

            # Evaluate if target is present in new_data
            target_col = next(
                (
                    col
                    for col in new_data.columns
                    if col.upper() == f"TARGET_{target_number}"
                ),
                None,
            )
            if target_col is not None:
                y_true = new_data[target_col]
                prediction = pd.concat([y_true, y_pred], axis=1)
                prediction.rename(columns={target_col: "TARGET"}, inplace=True)
                score = evaluate(
                    prediction,
                    target_type=model.target_type,
                )
                score["TARGET"] = f"TARGET_{target_number}"

                if model.target_type == "classification":
                    scores_clf.append(score)
                else:
                    scores_reg.append(score)

            # Add predictions to the output dataframe
            if isinstance(y_pred, pd.DataFrame):
                y_pred = y_pred.add_prefix(f"TARGET_{target_number}_")
                new_data = pd.concat([new_data, y_pred], axis=1)
            else:
                y_pred.name = f"TARGET_{target_number}_PRED"
                new_data = pd.concat([new_data, y_pred], axis=1)

        # Format scores
        if len(scores_reg) > 0:
            scores_reg = pd.DataFrame(scores_reg).set_index("TARGET")
        if len(scores_clf) > 0:
            scores_clf = pd.DataFrame(scores_clf).set_index("TARGET")

        return new_data, scores_reg, scores_clf

    def get_scores(self, target_number: int):
        return pd.read_csv(
            f"{self.experiment.path}/TARGET_{target_number}/scores_tracking.csv"
        )

    def get_prediction(self, target_number: int, model_name: str):
        return pd.read_csv(
            f"{self.experiment.path}/TARGET_{target_number}/{model_name}/prediction.csv"
        )

    def get_feature_summary(self):
        return pd.read_csv(f"{self.experiment.path}/feature_summary.csv")

    def get_threshold(self, target_number: int):
        thresholds = joblib.load(
            f"{self.experiment.path}/TARGET_{target_number}/thresholds.pkl"
        )
        if isinstance(thresholds, str):
            thresholds = ast.literal_eval(thresholds)

        return thresholds

    def load_model(self, target_number: int, model_name: str = None):

        if not model_name:
            return load_model(f"{self.experiment.path}/TARGET_{target_number}")

        return load_model(f"{self.experiment.path}/TARGET_{target_number}/{model_name}")

    def plot_feature_importance(
        self, target_number: int, model_name="linear", top_n=30
    ):
        """
        Plot feature importance ranking.

        Args:
            target_number (int): Target variable number
            model_name (str): Name of the model to load
            top_n (int): Number of top features to display
        """
        model = self.load_model(target_number, model_name)
        experiment = self.experiment

        # Get feature names
        feature_names = experiment.get_features(target_number)

        # Get feature importances based on model type
        if hasattr(model, "feature_importances_"):
            # For sklearn tree models
            importances = model.feature_importances_
            importance_type = "Gini"
        elif hasattr(model, "get_score"):
            # For xgboost models
            importance_dict = model.get_score(importance_type="weight")
            importances = np.zeros(len(feature_names))
            for i, feat in enumerate(feature_names):
                if feat in importance_dict:
                    importances[i] = importance_dict[feat]
            importance_type = "Weight"
        elif hasattr(model, "feature_importance"):
            # For lightgbm models
            importances = model.feature_importance(importance_type="split")
            importance_type = "Split"
        elif hasattr(model, "get_feature_importance"):
            importances = model.get_feature_importance()
            importance_type = "Feature importance"
        elif hasattr(model, "coef_"):
            # For linear models
            importances = np.abs(model.coef_.flatten())
            importance_type = "Absolute coefficient"
        else:
            raise ValueError(
                f"Model {model_name} does not support feature importance calculation"
            )

        # Create a DataFrame for easier manipulation
        importance_df = pd.DataFrame(
            {"feature": feature_names[: len(importances)], "importance": importances}
        )

        # Sort features by importance and take top N
        importance_df = importance_df.sort_values("importance", ascending=False).head(
            top_n
        )

        # Create the plot
        plt.figure(figsize=(10, max(6, len(importance_df) * 0.3)))
        ax = sns.barplot(
            data=importance_df,
            x="importance",
            y="feature",
            palette="viridis",
            orient="h",
        )

        # Add value labels
        for i, v in enumerate(importance_df["importance"]):
            ax.text(v, i, f"{v:.4f}", color="black", ha="left", va="center")

        plt.title(f"Feature Importance ({importance_type})")
        plt.tight_layout()
        plt.show()

        return importance_df

    def plot_evaluation_for_classification(
        self, target_number: int, model_name="linear"
    ):
        prediction = self.get_prediction(target_number, model_name)
        thresholds = self.get_threshold(target_number)

        plot_evaluation_for_classification(prediction)

        for class_label, metrics in thresholds.items():
            threshold = metrics["threshold"]
            precision = metrics["precision"]
            recall = metrics["recall"]
            if threshold is not None:
                tmp_pred = prediction[["TARGET", "PRED", class_label]].copy()
                tmp_pred.rename(columns={class_label: 1}, inplace=True)
                print(f"Class {class_label}:")
                plot_threshold(tmp_pred, threshold, precision, recall)
            else:
                print(f"No threshold found for class {class_label}")

    def get_best_params(self, target_number: int = None) -> dict:
        """
        Load the best parameters for the experiment.

        Args:
            target_number (int, optional): If provided, returns parameters for this specific target.
                                         If None, returns parameters for all targets.

        Returns:
            dict: Dictionary containing the best parameters. If target_number is provided,
                  returns parameters for that target only. Otherwise, returns a dictionary
                  with target numbers as keys.
        """
        import json
        import os

        params_file = os.path.join(
            self.experiment.path, "preprocessing", "all_targets_best_params.json"
        )

        if not os.path.exists(params_file):
            raise FileNotFoundError(
                f"Best parameters file not found at {params_file}. "
                "Make sure to fit model training first."
            )

        try:
            with open(params_file, "r") as f:
                all_params = json.load(f)

            # Convert string keys to integers
            all_params = {int(k): v for k, v in all_params.items()}

            if target_number is not None:
                if target_number not in all_params:
                    available_targets = list(all_params.keys())
                    raise ValueError(
                        f"No parameters found for target {target_number}. "
                        f"Available targets: {available_targets}"
                    )
                return all_params[target_number]

            return all_params

        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing best parameters file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading best parameters: {str(e)}")

    def plot_pca_scatter(
        self,
        target_number: int,
        pca_type: str = "all",
        components: tuple = (0, 1),
        figsize: tuple = (12, 5),
    ):
        """
        Visualise les données dans l'espace PCA en 2D avec coloration par classe.
        Fonctionne uniquement pour les tâches de classification.

        Args:
            target_number (int): Numéro de la target à visualiser
            pca_type (str): Type de PCA à visualiser ("embedding", "cross_sectional", "temporal", "all")
            components (tuple): Tuple des composantes à afficher (par défaut (0,1))
            figsize (tuple): Taille de la figure
        """
        # Vérifier que c'est une tâche de classification
        if target_number not in self.target_clf:
            raise ValueError(
                f"Target {target_number} n'est pas une tâche de classification. "
                f"Targets de classification disponibles: {self.target_clf}"
            )

        # Charger les données transformées
        data_path = os.path.join(self.experiment.path, "data", "full.pkl")
        if not os.path.exists(data_path):
            raise FileNotFoundError(
                f"Données non trouvées à {data_path}. Exécutez d'abord fit()."
            )

        data = joblib.load(data_path)
        target_col = f"TARGET_{target_number}"

        if target_col not in data.columns:
            raise ValueError(f"Target {target_number} non trouvée dans les données.")

        # Identifier les colonnes PCA selon le type
        pca_cols = {}
        if pca_type in ["embedding", "all"]:
            pca_cols["embedding"] = [col for col in data.columns if "_pca_" in col]
        if pca_type in ["cross_sectional", "all"]:
            pca_cols["cross_sectional"] = [
                col for col in data.columns if col.startswith("CS_PC_")
            ]
        if pca_type in ["temporal", "all"]:
            pca_cols["temporal"] = [
                col for col in data.columns if col.startswith("TMP_PC_")
            ]

        # Vérifier qu'on a des colonnes PCA
        total_cols = sum(len(cols) for cols in pca_cols.values())
        if total_cols == 0:
            raise ValueError(f"Aucune colonne PCA trouvée pour le type '{pca_type}'")

        # Grouper par type de PCA et créer des groupes logiques
        pca_groups = {}
        for type_name, cols in pca_cols.items():
            if not cols:
                continue

            if type_name == "embedding":
                # Grouper par base_column
                groups = {}
                for col in cols:
                    base_col = col.replace("_pca_", "_").split("_")[0]
                    if base_col not in groups:
                        groups[base_col] = []
                    groups[base_col].append(col)
                pca_groups.update({f"{type_name}_{k}": v for k, v in groups.items()})

            elif type_name in ["cross_sectional", "temporal"]:
                # Grouper par nom PCA (entre les underscores)
                groups = {}
                prefix = "CS_PC_" if type_name == "cross_sectional" else "TMP_PC_"
                for col in cols:
                    parts = col.replace(prefix, "").split("_")
                    if len(parts) >= 2:
                        name = "_".join(
                            parts[:-1]
                        )  # Tout sauf le dernier (numéro composante)
                        if name not in groups:
                            groups[name] = []
                        groups[name].append(col)
                pca_groups.update({f"{type_name}_{k}": v for k, v in groups.items()})

        # Créer les subplots en colonnes pour meilleure lisibilité
        n_groups = len(pca_groups)
        if n_groups == 0:
            raise ValueError("Aucun groupe PCA trouvé")

        # Organiser en colonnes (1 plot par ligne, 1 colonne)
        n_rows = n_groups
        n_cols = 1

        fig, axes = plt.subplots(
            n_rows, n_cols, figsize=(figsize[0], figsize[1] * n_groups)
        )
        if n_groups == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_groups > 1 else [axes]

        # Préparer les données (retirer les NaN)
        data_clean = data.dropna(subset=[target_col])
        y = data_clean[target_col].astype(int)

        # Créer une palette de couleurs flashy et visibles
        class_labels = sorted(y.unique())
        n_classes = len(class_labels)

        # Couleurs flashy : bleu, rouge, vert, orange, violet, cyan, magenta
        flashy_colors = [
            "#1f77b4",  # Bleu vif pour classe 0
            "#ff4444",  # Rouge vif pour classe 1
            "#2ca02c",  # Vert vif pour classe 2
            "#ff7f0e",  # Orange vif pour classe 3
            "#9467bd",  # Violet pour classe 4
            "#17becf",  # Cyan pour classe 5
            "#e377c2",  # Magenta pour classe 6
            "#bcbd22",  # Olive pour classe 7
        ]

        # Mapper chaque classe à sa couleur
        color_map = {}
        for i, class_label in enumerate(class_labels):
            color_map[class_label] = flashy_colors[i % len(flashy_colors)]

        for idx, (group_name, group_cols) in enumerate(pca_groups.items()):
            ax = axes[idx]

            # Vérifier qu'on a au moins les composantes demandées
            if len(group_cols) < max(components) + 1:
                ax.text(
                    0.5,
                    0.5,
                    f"Pas assez de composantes\ndans {group_name}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                ax.set_title(group_name)
                continue

            # Sélectionner les composantes
            group_cols_sorted = sorted(group_cols)
            pc1_col = group_cols_sorted[components[0]]
            pc2_col = group_cols_sorted[components[1]]

            # Données pour ce groupe (retirer NaN)
            subset = data_clean[[pc1_col, pc2_col, target_col]].dropna()
            if len(subset) == 0:
                ax.text(
                    0.5,
                    0.5,
                    f"Pas de données valides\npour {group_name}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                ax.set_title(group_name)
                continue

            X_pc1 = subset[pc1_col]
            X_pc2 = subset[pc2_col]
            y_subset = subset[target_col].astype(int)

            # Scatter plot par classe avec couleurs flashy
            for class_label in sorted(y_subset.unique()):
                mask = y_subset == class_label
                ax.scatter(
                    X_pc1[mask],
                    X_pc2[mask],
                    c=color_map[class_label],
                    label=f"Classe {class_label}",
                    alpha=0.7,
                    s=50,
                    edgecolors="white",
                    linewidth=0.5,
                )

            ax.set_xlabel(f"PC{components[0]+1}")
            ax.set_ylabel(f"PC{components[1]+1}")
            ax.set_title(f'{group_name.replace("_", " ").title()}')
            ax.legend()
            ax.grid(True, alpha=0.3)

        # Plus besoin de cacher des axes car chaque plot a son propre axe

        plt.tight_layout()
        plt.suptitle(
            f"Visualisation PCA 2D - Target {target_number}", y=1.02, fontsize=14
        )
        plt.show()

    def plot_pca_variance(self, pca_type: str = "all", figsize: tuple = (15, 5)):
        """
        Visualise la variance expliquée par les composantes PCA.
        Fonctionne pour classification et régression.

        Args:
            pca_type (str): Type de PCA à visualiser ("embedding", "cross_sectional", "temporal", "all")
            figsize (tuple): Taille de la figure
        """
        # Charger les objets PCA sauvegardés
        pca_objects = {}

        # PCA Embedding
        if pca_type in ["embedding", "all"]:
            embedding_path = os.path.join(self.preprocessing_dir, "pcas.pkl")
            if os.path.exists(embedding_path):
                try:
                    pcas_embedding = joblib.load(embedding_path)
                    pca_objects["embedding"] = pcas_embedding
                except:
                    logger.warning("Impossible de charger les PCA embedding")

        # PCA Cross-sectional
        if pca_type in ["cross_sectional", "all"]:
            cs_path = os.path.join(self.preprocessing_dir, "pcas_cross_sectional.pkl")
            if os.path.exists(cs_path):
                try:
                    pcas_cs = joblib.load(cs_path)
                    pca_objects["cross_sectional"] = pcas_cs
                except:
                    logger.warning("Impossible de charger les PCA cross-sectional")

        # PCA Temporal
        if pca_type in ["temporal", "all"]:
            temporal_path = os.path.join(self.preprocessing_dir, "pcas_temporal.pkl")
            if os.path.exists(temporal_path):
                try:
                    pcas_temporal = joblib.load(temporal_path)
                    pca_objects["temporal"] = pcas_temporal
                except:
                    logger.warning("Impossible de charger les PCA temporal")

        if not pca_objects:
            raise ValueError(
                f"Aucun objet PCA trouvé pour le type '{pca_type}'. "
                "Assurez-vous d'avoir exécuté fit() avec des configurations PCA."
            )

        # Collecter toutes les variances expliquées
        variance_data = []

        for type_name, pca_dict in pca_objects.items():
            for name, pca_obj in pca_dict.items():

                # Récupérer l'objet PCA selon le type
                if type_name == "embedding":
                    # Pour embedding, l'objet est directement une PCA
                    explained_var = pca_obj.explained_variance_ratio_
                    pca_name = f"{type_name}_{name}"
                else:
                    # Pour cross_sectional et temporal, c'est un Pipeline
                    try:
                        if (
                            hasattr(pca_obj, "named_steps")
                            and "pca" in pca_obj.named_steps
                        ):
                            explained_var = pca_obj.named_steps[
                                "pca"
                            ].explained_variance_ratio_
                        else:
                            continue
                        pca_name = f"{type_name}_{name}"
                    except:
                        continue

                # Ajouter les données
                for i, var in enumerate(explained_var):
                    variance_data.append(
                        {
                            "pca_type": type_name,
                            "pca_name": pca_name,
                            "component": i + 1,
                            "explained_variance": var,
                            "cumulative_variance": np.sum(explained_var[: i + 1]),
                        }
                    )

        if not variance_data:
            raise ValueError("Aucune donnée de variance trouvée dans les objets PCA")

        df_var = pd.DataFrame(variance_data)

        # Créer les subplots en colonnes verticales pour meilleure lisibilité
        unique_pcas = df_var["pca_name"].unique()
        n_pcas = len(unique_pcas)

        if n_pcas == 0:
            raise ValueError("Aucune PCA trouvée")

        # Organiser en colonnes (1 plot par ligne, 1 colonne)
        n_rows = n_pcas
        n_cols = 1

        fig, axes = plt.subplots(
            n_rows, n_cols, figsize=(figsize[0], figsize[1] * n_pcas)
        )
        if n_pcas == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_pcas > 1 else [axes]

        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

        for idx, pca_name in enumerate(unique_pcas):
            ax = axes[idx]
            pca_data = df_var[df_var["pca_name"] == pca_name].sort_values("component")

            # Bar plot pour variance individuelle
            bars = ax.bar(
                pca_data["component"],
                pca_data["explained_variance"],
                alpha=0.7,
                color=colors[idx % len(colors)],
                label="Variance individuelle",
            )

            # Line plot pour variance cumulative
            ax2 = ax.twinx()
            line = ax2.plot(
                pca_data["component"],
                pca_data["cumulative_variance"],
                "ro-",
                linewidth=2,
                markersize=4,
                label="Variance cumulative",
            )

            # Annotations
            for i, (comp, var, cum_var) in enumerate(
                zip(
                    pca_data["component"],
                    pca_data["explained_variance"],
                    pca_data["cumulative_variance"],
                )
            ):
                if var > 0.05:  # Seulement si > 5%
                    ax.text(
                        comp,
                        var + 0.01,
                        f"{var:.3f}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )
                if i < 5:  # Seulement les 5 premiers pour la lisibilité
                    ax2.text(
                        comp + 0.1,
                        cum_var,
                        f"{cum_var:.3f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="red",
                    )

            # Styling
            ax.set_xlabel("Composante PCA")
            ax.set_ylabel("Variance expliquée", color="blue")
            ax2.set_ylabel("Variance cumulative", color="red")
            ax.set_title(pca_name.replace("_", " ").title())
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, max(pca_data["explained_variance"]) * 1.1)
            ax2.set_ylim(0, 1.05)

            # Légende
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

        # Plus besoin de cacher des axes car chaque plot a son propre axe

        plt.tight_layout()
        plt.suptitle(f"Variance expliquée par les composantes PCA", y=1.02, fontsize=14)
        plt.show()

        # Retourner un summary
        summary = (
            df_var.groupby("pca_name")
            .agg({"explained_variance": ["sum", "max"], "component": "count"})
            .round(4)
        )
        summary.columns = [
            "variance_totale",
            "variance_max_composante",
            "nb_composantes",
        ]

        return summary

    def plot_lime_explanation(
        self,
        target_number: int,
        instance_idx: int = 0,
        model_name: str = None,
        n_features: int = 10,
        figsize: tuple = (10, 6),
    ):
        """
        Visualise l'explication LIME pour une instance donnée.

        Args:
            target_number (int): Numéro de la target à expliquer
            instance_idx (int): Index de l'instance à expliquer (défaut: 0)
            model_name (str): Nom du modèle à utiliser (défaut: meilleur modèle)
            n_features (int): Nombre de features à afficher
            figsize (tuple): Taille de la figure
        """

        # Charger le modèle
        target_dir = os.path.join(self.experiment.path, f"TARGET_{target_number}")
        model = BaseModel(path=target_dir, target_number=target_number)

        # Charger les features
        features = self.experiment.get_features(target_number)

        # Charger les données preprocessées
        experiment_path = self.experiment.path

        if model.need_scaling:
            X_train_path = os.path.join(experiment_path, "data", "train_scaled.pkl")
            X_test_path = os.path.join(experiment_path, "data", "test_scaled.pkl")
        else:
            X_train_path = os.path.join(experiment_path, "data", "train.pkl")
            X_test_path = os.path.join(experiment_path, "data", "test.pkl")

        if not os.path.exists(X_train_path):
            raise FileNotFoundError(
                f"Données d'entraînement non trouvées: {X_train_path}"
            )
        if not os.path.exists(X_test_path):
            raise FileNotFoundError(f"Données de test non trouvées: {X_test_path}")

        X_train = joblib.load(X_train_path)[features]
        X_test = joblib.load(X_test_path)[features]

        if instance_idx >= len(X_test):
            raise ValueError(
                f"Instance {instance_idx} non trouvée. Max: {len(X_test)-1}"
            )

        # Préparer la fonction de prédiction
        if model.target_type == "classification":
            predict_fn = lambda x: model._model.predict_proba(
                pd.DataFrame(x, columns=features)
            )
            class_names = ["0", "1"]  # Assume binary classification
            mode = "classification"
        else:
            predict_fn = lambda x: model._model.predict(
                pd.DataFrame(x, columns=features)
            ).values.ravel()
            class_names = None
            mode = "regression"

        # Créer l'explainer LIME
        explainer = lime.lime_tabular.LimeTabularExplainer(
            X_train.values,
            feature_names=features,
            class_names=class_names,
            mode=mode,
            discretize_continuous=True,
        )

        # Expliquer l'instance
        instance = X_test.iloc[instance_idx].values
        explanation = explainer.explain_instance(
            instance, predict_fn, num_features=n_features
        )

        # Affichage personnalisé
        fig, ax = plt.subplots(figsize=figsize)

        # Récupérer les données d'explication
        exp_list = explanation.as_list()

        # Séparer features et importances
        feature_names = [item[0] for item in exp_list]
        importances = [item[1] for item in exp_list]

        # Créer le graphique horizontal
        colors = ["red" if x < 0 else "green" for x in importances]
        y_pos = np.arange(len(feature_names))

        bars = ax.barh(y_pos, importances, color=colors, alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(feature_names)
        ax.set_xlabel("Contribution LIME")

        # Ajouter les valeurs sur les barres
        for i, (bar, importance) in enumerate(zip(bars, importances)):
            width = bar.get_width()
            ax.text(
                width + (0.01 if width >= 0 else -0.01),
                bar.get_y() + bar.get_height() / 2,
                f"{importance:.3f}",
                ha="left" if width >= 0 else "right",
                va="center",
                fontsize=9,
            )

        # Titre et grille
        prediction = predict_fn(instance.reshape(1, -1))
        if model.target_type == "classification":
            pred_text = f"Proba classe 1: {prediction[0][1]:.3f}"
        else:
            pred_text = f"Prédiction: {prediction[0]:.3f}"

        ax.set_title(
            f"Explication LIME - Target {target_number} - Instance {instance_idx}\n{pred_text}"
        )
        ax.grid(True, alpha=0.3, axis="x")
        ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)

        plt.show()

        return explanation

    def plot_shap_values(
        self,
        target_number: int,
        plot_type: Literal["bar", "dot", "violin", "beeswarm"] = "dot",
        max_display: int = 20,
        figsize: tuple = (10, 8),
    ):
        """
        Visualise les valeurs SHAP (summary plot).

        Args:
            target_number (int): Numéro de la target à expliquer
            plot_type (Literal["bar", "dot", "violin", "beeswarm"]): Type de plot
                - "bar": Graphique en barres montrant l'importance moyenne absolue de chaque feature.
                         Idéal pour un aperçu rapide de l'importance globale des features.
                - "dot": (défaut) Nuage de points où chaque point est une instance.
                         La position X montre l'impact SHAP, la couleur indique la valeur de la feature.
                         Permet de voir comment les valeurs des features influencent les prédictions.
                - "violin": Similaire à "dot" mais avec des violons pour montrer la distribution.
                         Utile pour voir la densité des valeurs SHAP à différents niveaux.
                - "beeswarm": Comme "dot" mais les points sont arrangés pour éviter le chevauchement.
                              Meilleure visibilité quand beaucoup d'instances ont des valeurs similaires.
            max_display (int): Nombre maximum de features à afficher
            figsize (tuple): Taille de la figure

        Returns:
            numpy.ndarray: Les valeurs SHAP calculées

        Examples:
            # Importance globale des features
            experiment.plot_shap_values(target_number=1, plot_type="bar")

            # Voir l'impact détaillé avec les valeurs des features
            experiment.plot_shap_values(target_number=1, plot_type="dot")

            # Distribution des impacts SHAP
            experiment.plot_shap_values(target_number=1, plot_type="violin")
        """

        # Charger le modèle
        target_dir = os.path.join(self.experiment.path, f"TARGET_{target_number}")
        model = BaseModel(path=target_dir, target_number=target_number)

        # Charger les features
        features = self.experiment.get_features(target_number)

        # Charger les données preprocessées
        experiment_path = self.experiment.path

        if model.need_scaling:
            X_train_path = os.path.join(experiment_path, "data", "train_scaled.pkl")
            X_test_path = os.path.join(experiment_path, "data", "test_scaled.pkl")
        else:
            X_train_path = os.path.join(experiment_path, "data", "train.pkl")
            X_test_path = os.path.join(experiment_path, "data", "test.pkl")

        X_train = joblib.load(X_train_path)[features]
        X_test = joblib.load(X_test_path)[features]

        # Prendre un échantillon si trop de données pour SHAP
        sample_size = min(1000, len(X_test))
        X_sample = X_test.sample(n=sample_size, random_state=42)

        # Convertir les données en float pour SHAP
        X_train = X_train.astype(float)
        X_test = X_test.astype(float)
        X_sample = X_sample.astype(float)

        # Créer l'explainer SHAP directement sur le modèle
        if model.model_name == "catboost":
            actual_model = model._model.model
        else:
            actual_model = model._model
        explainer = shap.Explainer(actual_model, X_train)

        # Calculer les valeurs SHAP
        logger.info(f"Calcul des valeurs SHAP pour {len(X_sample)} instances...")
        shap_values = explainer.shap_values(X_sample)

        # Summary plot
        plt.figure(figsize=figsize)

        # Plot SHAP summary - adaptable aux différents types de modèles
        if model.target_type == "classification":
            # Pour classification binaire, utiliser les valeurs de la classe positive
            if isinstance(shap_values, list) and len(shap_values) > 1:
                # Classification binaire: classe 1 (positive)
                shap.summary_plot(
                    shap_values[1],
                    X_sample,
                    max_display=max_display,
                    show=False,
                    plot_type=plot_type,
                )
            else:
                # Classification avec une seule sortie ou multiclass
                values_to_plot = (
                    shap_values[0] if isinstance(shap_values, list) else shap_values
                )
                shap.summary_plot(
                    values_to_plot,
                    X_sample,
                    max_display=max_display,
                    show=False,
                    plot_type=plot_type,
                )
        else:
            # Régression
            values_to_plot = (
                shap_values[0] if isinstance(shap_values, list) else shap_values
            )
            shap.summary_plot(
                values_to_plot,
                X_sample,
                max_display=max_display,
                show=False,
                plot_type=plot_type,
            )

        plt.title(f"Valeurs SHAP - Target {target_number} ({model.target_type})")
        plt.show()

        return shap_values

    def plot_shap_waterfall(
        self,
        target_number: int,
        instance_idx: int = 0,
        model_name: str = None,
        max_display: int = 20,
        figsize: tuple = (10, 8),
    ):
        """
        Visualise l'explication SHAP waterfall pour une instance donnée.

        Args:
            target_number (int): Numéro de la target à expliquer
            instance_idx (int): Index de l'instance à expliquer
            model_name (str): Nom du modèle à utiliser (défaut: meilleur modèle)
            max_display (int): Nombre maximum de features à afficher
            figsize (tuple): Taille de la figure
        """

        # Charger le modèle
        target_dir = os.path.join(self.experiment.path, f"TARGET_{target_number}")
        model = BaseModel(path=target_dir, target_number=target_number)

        # Charger les features
        features = self.experiment.get_features(target_number)

        # Charger les données preprocessées
        experiment_path = self.experiment.path

        if model.need_scaling:
            X_train_path = os.path.join(experiment_path, "data", "train_scaled.pkl")
            X_test_path = os.path.join(experiment_path, "data", "test_scaled.pkl")
        else:
            X_train_path = os.path.join(experiment_path, "data", "train.pkl")
            X_test_path = os.path.join(experiment_path, "data", "test.pkl")

        X_train = joblib.load(X_train_path)[features]
        X_test = joblib.load(X_test_path)[features]

        if instance_idx >= len(X_test):
            raise ValueError(
                f"Instance {instance_idx} non trouvée. Max: {len(X_test)-1}"
            )

        # Convertir les données en float pour SHAP
        X_train = X_train.astype(float)
        X_test = X_test.astype(float)

        # Créer l'explainer SHAP directement sur le modèle
        if model.model_name == "catboost":
            actual_model = model._model.model
        else:
            actual_model = model._model
        explainer = shap.Explainer(actual_model, X_train)

        # Préparer les données de l'instance
        instance_data = X_test.iloc[instance_idx : instance_idx + 1]

        # Calculer les valeurs SHAP pour l'instance
        logger.info(f"Calcul des valeurs SHAP pour l'instance {instance_idx}...")
        shap_values = explainer.shap_values(instance_data)

        # Waterfall plot
        plt.figure(figsize=figsize)

        # Créer l'objet Explanation pour le waterfall plot
        if model.target_type == "classification":
            # Pour classification binaire, prendre les valeurs de la classe 1
            if isinstance(shap_values, list) and len(shap_values) > 1:
                values = shap_values[1][0]  # Classe 1, première instance
                base_value = explainer.expected_value[1]
            else:
                # Cas où shap_values n'est pas une liste ou une seule classe
                values = (
                    shap_values[0] if isinstance(shap_values, list) else shap_values[0]
                )
                base_value = (
                    explainer.expected_value[0]
                    if isinstance(explainer.expected_value, list)
                    else explainer.expected_value
                )
        else:
            # Pour régression
            values = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
            base_value = (
                explainer.expected_value[0]
                if isinstance(explainer.expected_value, list)
                else explainer.expected_value
            )

        # Créer l'objet Explanation
        explanation = shap.Explanation(
            values=values, base_values=base_value, data=instance_data.iloc[0]
        )

        # Plot waterfall
        shap.waterfall_plot(explanation, max_display=max_display, show=False)

        # Ajouter des informations sur la prédiction
        if model.target_type == "classification":
            prediction = actual_model.predict_proba(instance_data)
            pred_text = f"Proba classe 1: {prediction[0][1]:.3f}"
        else:
            prediction = actual_model.predict(instance_data)
            pred_value = prediction[0] if hasattr(prediction, "__len__") else prediction
            pred_text = f"Prédiction: {pred_value:.3f}"

        plt.title(
            f"SHAP Waterfall - Target {target_number} - Instance {instance_idx}\n{pred_text}"
        )
        plt.show()

        return shap_values

    def plot_tree(
        self,
        target_number: int,
        tree_index: int = 0,
        max_depth: int = None,
        figsize: tuple = (20, 10),
        **kwargs,
    ):
        """
        Visualise un arbre de décision du modèle.

        Args:
            target_number (int): Numéro de la target
            tree_index (int): Index de l'arbre à visualiser (défaut: 0)
            max_depth (int): Profondeur maximale à afficher (défaut: None = tout)
            figsize (tuple): Taille de la figure
            **kwargs: Arguments supplémentaires selon le type de modèle
                - Pour sklearn: filled, rounded, proportion, precision, class_names, etc.
                - Pour XGBoost: rankdir, num_trees, yes_color, no_color
                - Pour LightGBM: show_info, precision, orientation
                - Pour CatBoost: pool (requis pour CatBoost)

        Examples:
            # Arbre sklearn avec couleurs
            experiment.plot_tree(target_number=1, filled=True, rounded=True)

            # Premier arbre XGBoost
            experiment.plot_tree(target_number=1, tree_index=0)

            # Arbre LightGBM horizontal
            experiment.plot_tree(target_number=1, orientation='horizontal')

            # CatBoost nécessite les données
            experiment.plot_tree(target_number=1, pool=Pool(X, y))
        """
        # Charger le modèle
        target_dir = os.path.join(self.experiment.path, f"TARGET_{target_number}")
        model = BaseModel(path=target_dir, target_number=target_number)

        # Charger les features
        features = self.experiment.get_features(target_number)

        # Extraire le modèle réel
        if model.model_name == "catboost":
            actual_model = model._model.model
        else:
            actual_model = model._model

        # Identifier le type de modèle
        model_type = actual_model.__class__.__name__

        plt.figure(figsize=figsize)

        # Visualisation selon le type de modèle
        if (
            "DecisionTree" in model_type
            or "RandomForest" in model_type
            or "ExtraTrees" in model_type
        ):
            # Scikit-learn trees
            from sklearn.tree import plot_tree

            # Pour les ensembles, prendre un estimateur
            if hasattr(actual_model, "estimators_"):
                tree_to_plot = actual_model.estimators_[tree_index]
                if hasattr(tree_to_plot, "tree_"):  # RandomForest avec sklearn trees
                    tree_to_plot = tree_to_plot
                else:  # Peut être un autre type d'estimateur
                    tree_to_plot = tree_to_plot
            else:
                tree_to_plot = actual_model

            # Paramètres par défaut pour sklearn
            default_kwargs = {
                "feature_names": features,
                "filled": True,
                "rounded": True,
                "proportion": False,
                "precision": 2,
                "fontsize": 10,
            }

            # Pour classification, ajouter les noms de classes
            if model.target_type == "classification":
                if "class_names" not in kwargs:
                    # Essayer de récupérer les classes
                    if hasattr(actual_model, "classes_"):
                        default_kwargs["class_names"] = [
                            str(c) for c in actual_model.classes_
                        ]
                    else:
                        default_kwargs["class_names"] = ["0", "1"]  # Défaut binaire

            # Fusionner avec les kwargs utilisateur
            plot_kwargs = {**default_kwargs, **kwargs}

            # Limiter la profondeur si demandé
            if max_depth is not None:
                plot_kwargs["max_depth"] = max_depth

            plot_tree(tree_to_plot, **plot_kwargs)
            plt.title(f"Arbre {tree_index} - {model.model_name.upper()}")

        elif "XGB" in model_type or "xgboost" in model_type.lower():
            # XGBoost trees
            try:
                import xgboost as xgb

                # Paramètres par défaut
                default_kwargs = {
                    "rankdir": "TB",  # Top to bottom
                    "num_trees": tree_index,
                }

                plot_kwargs = {**default_kwargs, **kwargs}

                # XGBoost utilise graphviz, donc on doit gérer différemment
                ax = plt.gca()
                xgb.plot_tree(actual_model, ax=ax, **plot_kwargs)
                plt.title(f"Arbre {tree_index} - XGBoost")

            except ImportError:
                raise ImportError(
                    "XGBoost n'est pas installé ou graphviz manquant. "
                    "Installez avec: pip install xgboost et installez graphviz"
                )

        elif "LGBM" in model_type or "lightgbm" in model_type.lower():
            # LightGBM trees
            try:
                import lightgbm as lgb

                # Paramètres par défaut
                default_kwargs = {
                    "tree_index": tree_index,
                    "show_info": ["split_gain", "leaf_count", "internal_value"],
                    "precision": 3,
                    "orientation": "vertical",
                }

                plot_kwargs = {**default_kwargs, **kwargs}

                # Retirer tree_index des kwargs car il est passé séparément
                plot_kwargs.pop("tree_index", None)

                ax = lgb.plot_tree(
                    actual_model, tree_index=tree_index, figsize=figsize, **plot_kwargs
                )
                plt.title(f"Arbre {tree_index} - LightGBM")

            except ImportError:
                raise ImportError(
                    "LightGBM n'est pas installé ou graphviz manquant. "
                    "Installez avec: pip install lightgbm et installez graphviz"
                )

        elif "CatBoost" in model_type:
            # CatBoost trees
            try:
                # CatBoost nécessite plus de configuration
                if "pool" not in kwargs:
                    # Essayer de charger les données pour créer un Pool
                    logger.warning(
                        "CatBoost nécessite un Pool object. "
                        "Passez pool=Pool(X, y) dans les kwargs."
                    )

                    # Tentative de création automatique du pool
                    experiment_path = self.experiment.path
                    X_train_path = os.path.join(experiment_path, "data", "train.pkl")

                    if os.path.exists(X_train_path):
                        X_train = joblib.load(X_train_path)[features]
                        from catboost import Pool

                        pool = Pool(X_train)
                    else:
                        raise ValueError(
                            "Impossible de créer automatiquement le Pool CatBoost. "
                            "Passez pool=Pool(X, y) dans les arguments."
                        )
                else:
                    pool = kwargs.pop("pool")

                # CatBoost plot_tree retourne une image
                tree_plot = actual_model.plot_tree(tree_index=tree_index, pool=pool)

                # Afficher l'image dans matplotlib
                from IPython.display import Image
                import io
                from PIL import Image as PILImage

                # Convertir en image pour matplotlib
                img = PILImage.open(io.BytesIO(tree_plot))
                plt.imshow(img)
                plt.axis("off")
                plt.title(f"Arbre {tree_index} - CatBoost")

            except ImportError as e:
                raise ImportError(f"CatBoost visualization error: {str(e)}")
            except Exception as e:
                logger.error(f"Erreur CatBoost: {str(e)}")
                raise

        else:
            raise ValueError(
                f"Type de modèle non supporté pour la visualisation d'arbre: {model_type}. "
                "Supportés: DecisionTree, RandomForest, ExtraTrees, XGBoost, LightGBM, CatBoost"
            )

        plt.tight_layout()
        plt.show()

        # Retourner des infos utiles
        info = {
            "model_type": model_type,
            "model_name": model.model_name,
            "tree_index": tree_index,
            "n_features": len(features),
        }

        # Ajouter le nombre d'arbres si ensemble
        if hasattr(actual_model, "n_estimators"):
            info["n_trees"] = actual_model.n_estimators
        elif hasattr(actual_model, "get_params"):
            params = actual_model.get_params()
            if "n_estimators" in params:
                info["n_trees"] = params["n_estimators"]

        return info
