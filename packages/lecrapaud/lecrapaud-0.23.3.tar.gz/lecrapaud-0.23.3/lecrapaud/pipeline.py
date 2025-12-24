"""
LeCrapaud Pipeline for sklearn integration.

This module provides a sklearn-compatible pipeline that can be used
in sklearn workflows while incorporating LeCrapaud's custom components.
"""

from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from typing import List, Tuple, Optional, Dict, Any
import pandas as pd

from lecrapaud.models import Experiment
from lecrapaud.feature_engineering import FeatureEngineer
from lecrapaud.feature_preprocessing import FeaturePreprocessor, split_data
from lecrapaud.feature_selection import FeatureSelector
from lecrapaud.model_preprocessing import ModelPreprocessor, reshape_time_series
from lecrapaud.model_selection import ModelSelector
from lecrapaud.search_space import all_models


class DataSplitterTransformer(BaseEstimator, TransformerMixin):
    """
    Transformer that handles train/val/test data splitting for LeCrapaud pipelines.

    This component splits data and can be used in sklearn pipelines while maintaining
    the ability to access individual splits.
    """

    def __init__(
        self,
        experiment: Experiment,
        time_series: bool = False,
        date_column: str = None,
        group_column: str = None,
        val_size: float = 0.2,
        test_size: float = 0.2,
        target_numbers: List[int] = None,
        target_clf: List[int] = None,
    ):
        self.experiment = experiment
        self.time_series = time_series
        self.date_column = date_column
        self.group_column = group_column
        self.val_size = val_size
        self.test_size = test_size
        self.target_numbers = target_numbers or []
        self.target_clf = target_clf or []

    def fit(self, X, y=None):
        """Fit the splitter (no-op, just validates parameters)."""
        return self

    def transform(self, X):
        """Transform data by splitting it and returning train split."""
        train, val, test = split_data(X, experiment=self.experiment)

        # Store splits as attributes for later access
        self.train_ = train
        self.val_ = val
        self.test_ = test

        return train

    def get_splits(self):
        """Get all data splits."""
        if not hasattr(self, "train_"):
            raise ValueError("Must call transform() first to create splits")
        return self.train_, self.val_, self.test_


class DataReshaper(BaseEstimator, TransformerMixin):
    """
    Transformer that handles time series data reshaping for recurrent models.

    This component checks if reshaping is needed and applies it when appropriate.
    """

    def __init__(
        self,
        experiment: Experiment,
        models_idx: List[int] = None,
        time_series: bool = False,
        max_timesteps: int = 120,
        group_column: str = None,
    ):
        self.experiment = experiment
        self.models_idx = models_idx or []
        self.time_series = time_series
        self.max_timesteps = max_timesteps
        self.group_column = group_column

    def fit(self, X, y=None):
        """Fit the reshaper (determines if reshaping is needed)."""
        # Check if any model requires recurrent processing
        self.need_reshaping_ = (
            any(all_models[i].get("recurrent") for i in self.models_idx)
            and self.time_series
        )
        return self

    def transform(self, X):
        """Transform data by reshaping for time series if needed."""
        if not self.need_reshaping_:
            return X

        # Sanity check: make sure we have enough data for max_timesteps
        if (
            self.group_column
            and X.groupby(self.group_column).size().min() < self.max_timesteps
        ) or X.shape[0] < self.max_timesteps:
            raise ValueError(
                f"Not enough data for group_column {self.group_column} to reshape data for recurrent models"
            )

        # Get features for reshaping
        all_features = self.experiment.get_all_features(
            date_column=getattr(self, "date_column", None),
            group_column=self.group_column,
        )

        # Reshape the data
        reshaped_data = reshape_time_series(
            self.experiment, all_features, X, timesteps=self.max_timesteps
        )

        # Store reshaped data as attribute
        self.reshaped_data_ = reshaped_data

        return (
            X  # Return original data, reshaped data accessible via get_reshaped_data()
        )

    def get_reshaped_data(self):
        """Get the reshaped data."""
        if not hasattr(self, "reshaped_data_"):
            return None
        return self.reshaped_data_


class FullPipelineTransformer(BaseEstimator, TransformerMixin):
    """
    Complete LeCrapaud pipeline transformer that handles all steps including
    data splitting, preprocessing, and reshaping in a sklearn-compatible way.
    """

    def __init__(
        self,
        experiment: Experiment,
        target_numbers: List[int] = None,
        include_model_selection: bool = False,
        **pipeline_params,
    ):
        self.experiment = experiment
        self.target_numbers = target_numbers or []
        self.include_model_selection = include_model_selection
        self.pipeline_params = pipeline_params

        # Extract parameters from experiment context
        if experiment and hasattr(experiment, "context"):
            for key, value in experiment.context.items():
                if not hasattr(self, key):
                    setattr(self, key, value)

        # Set defaults
        self._set_defaults()

    def _set_defaults(self):
        """Set default values for pipeline parameters."""
        defaults = {
            "time_series": False,
            "date_column": None,
            "group_column": None,
            "val_size": 0.2,
            "test_size": 0.2,
            "target_clf": [],
            "models_idx": [],
            "max_timesteps": 120,
        }

        for key, default_value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, default_value)

    def fit(self, X, y=None):
        """Fit the complete pipeline."""
        # Step 1: Feature Engineering
        self.feature_eng_ = FeatureEngineer(experiment=self.experiment)
        self.feature_eng_.fit(X)
        data_eng = self.feature_eng_.get_data()

        # Step 2: Data Splitting
        self.data_splitter_ = DataSplitterTransformer(experiment=self.experiment)
        train = self.data_splitter_.transform(data_eng)
        val = self.data_splitter_.val_
        test = self.data_splitter_.test_

        # Step 3: Feature Preprocessing
        self.feature_prep_ = FeaturePreprocessor(experiment=self.experiment)
        self.feature_prep_.fit(train)
        train_prep = self.feature_prep_.transform(train)
        val_prep = self.feature_prep_.transform(val) if val is not None else None
        test_prep = self.feature_prep_.transform(test) if test is not None else None

        # Step 4: Feature Selection (for each target)
        self.feature_selectors_ = {}
        for target_number in self.target_numbers:
            selector = FeatureSelector(
                experiment=self.experiment, target_number=target_number
            )
            selector.fit(train_prep)
            self.feature_selectors_[target_number] = selector

        # Step 5: Model Preprocessing
        self.model_prep_ = ModelPreprocessor(experiment=self.experiment)
        self.model_prep_.fit(train_prep)
        train_scaled = self.model_prep_.transform(train_prep)
        val_scaled = (
            self.model_prep_.transform(val_prep) if val_prep is not None else None
        )
        test_scaled = (
            self.model_prep_.transform(test_prep) if test_prep is not None else None
        )

        # Step 6: Data Reshaping (if needed)
        self.data_reshaper_ = DataReshaper(
            experiment=self.experiment,
            models_idx=self.models_idx,
            time_series=self.time_series,
            max_timesteps=self.max_timesteps,
            group_column=self.group_column,
        )
        self.data_reshaper_.fit(train_scaled)
        self.data_reshaper_.transform(train_scaled)

        # Step 7: Model Selection (optional)
        if self.include_model_selection:
            self.model_selectors_ = {}
            std_data = {"train": train_scaled, "val": val_scaled, "test": test_scaled}
            reshaped_data = self.data_reshaper_.get_reshaped_data()

            for target_number in self.target_numbers:
                model_selector = ModelSelector(
                    experiment=self.experiment, target_number=target_number
                )
                model_selector.fit(std_data, reshaped_data=reshaped_data)
                self.model_selectors_[target_number] = model_selector

        return self

    def transform(self, X):
        """Transform new data through the fitted pipeline."""
        # Apply feature engineering
        data_eng = self.feature_eng_.transform(X)  # Refit for new data

        # Apply feature preprocessing
        data_prep = self.feature_prep_.transform(data_eng)

        # Apply model preprocessing
        data_scaled = self.model_prep_.transform(data_prep)

        # Apply reshaping if needed
        self.data_reshaper_.transform(data_scaled)

        return data_scaled

    def get_training_splits(self):
        """Get the training data splits."""
        if not hasattr(self, "data_splitter_"):
            raise ValueError("Must call fit() first")
        return self.data_splitter_.get_splits()

    def get_reshaped_data(self):
        """Get the reshaped data for recurrent models."""
        if not hasattr(self, "data_reshaper_"):
            raise ValueError("Must call fit() first")
        return self.data_reshaper_.get_reshaped_data()

    def get_models(self):
        """Get the trained models."""
        if not hasattr(self, "model_selectors_"):
            return {}
        return {
            num: selector.get_best_model()
            for num, selector in self.model_selectors_.items()
        }


class PipelineLeCrapaud(Pipeline):
    """
    LeCrapaud pipeline that extends sklearn Pipeline for ML workflows.

    This pipeline provides pre-configured steps for the typical LeCrapaud workflow:
    1. Feature Engineering
    2. Feature Preprocessing
    3. Feature Selection
    4. Model Preprocessing
    5. Model Selection

    It can be used as a drop-in replacement for sklearn Pipeline while
    leveraging LeCrapaud's experiment tracking and domain-specific features.
    """

    def __init__(
        self,
        experiment: Experiment,
        steps: Optional[List[Tuple[str, BaseEstimator]]] = None,
        memory=None,
        verbose=False,
        target_number: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize LeCrapaud pipeline.

        Args:
            experiment: LeCrapaud experiment instance
            steps: List of (name, estimator) tuples. If None, uses default workflow
            memory: Caching parameter (passed to sklearn Pipeline)
            verbose: Whether to output progress info
            target_number: Target number for model selection (if using default steps)
            **kwargs: Additional parameters passed to default estimators
        """
        self.experiment = experiment
        self.target_number = target_number
        self.step_kwargs = kwargs

        if steps is None:
            steps = self._create_default_steps()

        super().__init__(steps=steps, memory=memory, verbose=verbose)

    def _create_default_steps(self) -> List[Tuple[str, BaseEstimator]]:
        """Create default LeCrapaud pipeline steps."""
        steps = [
            (
                "feature_engineering",
                FeatureEngineer(
                    experiment=self.experiment,
                    **self.step_kwargs.get("feature_engineering", {}),
                ),
            ),
            (
                "feature_preprocessing",
                FeaturePreprocessor(
                    experiment=self.experiment,
                    **self.step_kwargs.get("feature_preprocessing", {}),
                ),
            ),
            (
                "feature_selection",
                FeatureSelector(
                    experiment=self.experiment,
                    target_number=self.target_number,
                    **self.step_kwargs.get("feature_selection", {}),
                ),
            ),
            (
                "model_preprocessing",
                ModelPreprocessor(
                    experiment=self.experiment,
                    **self.step_kwargs.get("model_preprocessing", {}),
                ),
            ),
        ]

        # Add model selection if target_number is specified
        if self.target_number is not None:
            steps.append(
                (
                    "model_selection",
                    ModelSelector(
                        experiment=self.experiment,
                        target_number=self.target_number,
                        **self.step_kwargs.get("model_selection", {}),
                    ),
                )
            )

        return steps

    @classmethod
    def create_feature_pipeline(
        cls,
        experiment: Experiment,
        include_selection: bool = True,
        target_number: Optional[int] = None,
        **kwargs,
    ) -> "PipelineLeCrapaud":
        """
        Create a pipeline focused on feature processing only.

        Args:
            experiment: LeCrapaud experiment instance
            include_selection: Whether to include feature selection step
            target_number: Target number for feature selection
            **kwargs: Additional parameters for estimators

        Returns:
            PipelineLeCrapaud: Feature processing pipeline
        """
        steps = [
            (
                "feature_engineering",
                FeatureEngineer(
                    experiment=experiment, **kwargs.get("feature_engineering", {})
                ),
            ),
            (
                "feature_preprocessing",
                FeaturePreprocessor(
                    experiment=experiment, **kwargs.get("feature_preprocessing", {})
                ),
            ),
        ]

        if include_selection and target_number is not None:
            steps.append(
                (
                    "feature_selection",
                    FeatureSelector(
                        experiment=experiment,
                        target_number=target_number,
                        **kwargs.get("feature_selection", {}),
                    ),
                )
            )

        return cls(experiment=experiment, steps=steps)

    @classmethod
    def create_model_pipeline(
        cls, experiment: Experiment, target_number: int, **kwargs
    ) -> "PipelineLeCrapaud":
        """
        Create a pipeline focused on model preprocessing and selection.

        Args:
            experiment: LeCrapaud experiment instance
            target_number: Target number for model selection
            **kwargs: Additional parameters for estimators

        Returns:
            PipelineLeCrapaud: Model pipeline
        """
        steps = [
            (
                "model_preprocessing",
                ModelPreprocessor(
                    experiment=experiment, **kwargs.get("model_preprocessing", {})
                ),
            ),
            (
                "model_selection",
                ModelSelector(
                    experiment=experiment,
                    target_number=target_number,
                    **kwargs.get("model_selection", {}),
                ),
            ),
        ]

        return cls(experiment=experiment, steps=steps)

    def get_feature_names_out(self, input_features=None):
        """Get output feature names for transformation."""
        # Try to get from the last transformer that has this method
        for name, estimator in reversed(self.steps):
            if hasattr(estimator, "get_feature_names_out"):
                return estimator.get_feature_names_out(input_features)
            # For FeatureSelector, try to get selected features
            elif hasattr(estimator, "get_selected_features"):
                return estimator.get_selected_features()

        return input_features

    def get_experiment(self) -> Experiment:
        """Get the experiment instance."""
        return self.experiment

    def get_step_results(self, step_name: str) -> Any:
        """
        Get results from a specific pipeline step.

        Args:
            step_name: Name of the pipeline step

        Returns:
            Results from the specified step
        """
        if step_name not in self.named_steps:
            raise ValueError(f"Step '{step_name}' not found in pipeline")

        estimator = self.named_steps[step_name]

        # Try common result methods
        if hasattr(estimator, "get_data"):
            return estimator.get_data()
        elif hasattr(estimator, "get_selected_features"):
            return estimator.get_selected_features()
        elif hasattr(estimator, "get_best_model"):
            return estimator.get_best_model()
        else:
            return estimator


class LeCrapaudTransformer(BaseEstimator, TransformerMixin):
    """
    A transformer wrapper that makes any LeCrapaud estimator compatible
    with sklearn transformers, allowing them to be used in standard sklearn pipelines.
    """

    def __init__(self, estimator_class, experiment: Experiment, **estimator_params):
        """
        Initialize the transformer wrapper.

        Args:
            estimator_class: The LeCrapaud estimator class to wrap
            experiment: LeCrapaud experiment instance
            **estimator_params: Parameters to pass to the estimator
        """
        self.estimator_class = estimator_class
        self.experiment = experiment
        self.estimator_params = estimator_params
        self.estimator_ = None

    def fit(self, X, y=None):
        """Fit the wrapped estimator."""
        self.estimator_ = self.estimator_class(
            experiment=self.experiment, **self.estimator_params
        )
        self.estimator_.fit(X, y)
        return self

    def transform(self, X):
        """Transform using the fitted estimator."""
        if self.estimator_ is None:
            raise ValueError("Transformer has not been fitted yet.")

        # For estimators that don't have transform, use get_data or return X
        if hasattr(self.estimator_, "transform"):
            return self.estimator_.transform(X)
        elif hasattr(self.estimator_, "get_data"):
            return self.estimator_.get_data()
        else:
            return X

    def get_params(self, deep=True):
        """Get parameters for this transformer."""
        params = {
            "estimator_class": self.estimator_class,
            "experiment": self.experiment,
        }
        if deep and self.estimator_params:
            for key, value in self.estimator_params.items():
                params[key] = value
        return params

    def set_params(self, **params):
        """Set parameters for this transformer."""
        estimator_params = {}
        base_params = {}

        for key, value in params.items():
            if key in ["estimator_class", "experiment"]:
                base_params[key] = value
            else:
                estimator_params[key] = value

        for key, value in base_params.items():
            setattr(self, key, value)

        self.estimator_params.update(estimator_params)
        return self
