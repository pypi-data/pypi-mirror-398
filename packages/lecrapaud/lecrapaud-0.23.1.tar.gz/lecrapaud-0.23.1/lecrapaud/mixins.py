"""
Sklearn-compatible mixins for LeCrapaud components.

This module provides base classes and mixins that ensure components are compatible
with scikit-learn conventions and can be used in sklearn pipelines.
"""

from sklearn.base import BaseEstimator, TransformerMixin
from abc import ABC, abstractmethod
from lecrapaud.models import Experiment


class LeCrapaudTransformerMixin(BaseEstimator, TransformerMixin):
    """
    Base mixin for LeCrapaud transformers that ensures sklearn compatibility.

    This mixin provides the basic structure that all LeCrapaud transformers
    should follow to be compatible with sklearn pipelines.
    """

    def __init__(self, experiment: Experiment = None, **kwargs):
        """
        Initialize the transformer.

        Args:
            experiment: LeCrapaud experiment context
            **kwargs: Additional parameters (take priority over experiment.context)
        """
        self.experiment = experiment

        # First, set parameters from experiment context if available
        if experiment and hasattr(experiment, "context") and experiment.context:
            for key, value in experiment.context.items():
                setattr(self, key, value)

        # Then override with explicit kwargs (kwargs have priority)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_params(self, deep=True):
        """
        Get parameters for this estimator (sklearn compatibility).

        Args:
            deep (bool): If True, will return the parameters for this estimator
                        and contained subobjects that are estimators.

        Returns:
            dict: Parameter names mapped to their values.
        """
        params = {}
        for key in dir(self):
            if not key.startswith("_") and not callable(getattr(self, key)):
                value = getattr(self, key)
                if deep and hasattr(value, "get_params"):
                    deep_items = value.get_params().items()
                    params.update((f"{key}__{k}", v) for k, v in deep_items)
                params[key] = value
        return params

    def set_params(self, **params):
        """
        Set the parameters of this estimator (sklearn compatibility).

        Args:
            **params: Estimator parameters

        Returns:
            self: Estimator instance
        """
        for key, value in params.items():
            if "__" in key:
                # Handle nested parameters
                obj_name, param_name = key.split("__", 1)
                obj = getattr(self, obj_name)
                obj.set_params(**{param_name: value})
            else:
                setattr(self, key, value)
        return self

    def _set_fitted(self):
        """Mark the transformer as fitted (sklearn compatibility helper)."""
        self.is_fitted_ = True

    def _check_is_fitted(self):
        """Ensure the estimator has been fitted before usage."""
        if not getattr(self, "is_fitted_", False):
            raise ValueError("This estimator has not been fitted yet.")

    def _validate_data(self, X, y=None, reset=True):
        """Basic validation helper mirroring sklearn signature."""
        if X is None:
            raise ValueError("Input X cannot be None")
        return X, y

    @abstractmethod
    def fit(self, X, y=None):
        """
        Fit the transformer.

        Args:
            X: Input data
            y: Target values (optional)

        Returns:
            self: Returns self for chaining
        """
        pass

    @abstractmethod
    def transform(self, X):
        """
        Transform the input data.

        Args:
            X: Input data to transform

        Returns:
            Transformed data
        """
        pass

    def fit_transform(self, X, y=None):
        """
        Fit and transform in one step (provided by TransformerMixin).

        Args:
            X: Input data
            y: Target values (optional)

        Returns:
            Transformed data
        """
        return self.fit(X, y).transform(X)


class LeCrapaudEstimatorMixin(BaseEstimator):
    """
    Base mixin for LeCrapaud estimators (like selectors) that only have fit().
    """

    def __init__(self, experiment: Experiment = None, **kwargs):
        """
        Initialize the estimator.

        Args:
            experiment: LeCrapaud experiment context
            **kwargs: Additional parameters (take priority over experiment.context)
        """
        self.experiment = experiment

        # First, set parameters from experiment context if available
        if experiment and hasattr(experiment, "context") and experiment.context:
            for key, value in experiment.context.items():
                setattr(self, key, value)

        # Then override with explicit kwargs (kwargs have priority)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_params(self, deep=True):
        """Get parameters for this estimator (sklearn compatibility)."""
        params = {}
        for key in dir(self):
            if not key.startswith("_") and not callable(getattr(self, key)):
                value = getattr(self, key)
                if deep and hasattr(value, "get_params"):
                    deep_items = value.get_params().items()
                    params.update((f"{key}__{k}", v) for k, v in deep_items)
                params[key] = value
        return params

    def set_params(self, **params):
        """Set the parameters of this estimator (sklearn compatibility)."""
        for key, value in params.items():
            if "__" in key:
                # Handle nested parameters
                obj_name, param_name = key.split("__", 1)
                obj = getattr(self, obj_name)
                obj.set_params(**{param_name: value})
            else:
                setattr(self, key, value)
        return self

    def _set_fitted(self):
        """Mark the estimator as fitted."""
        self.is_fitted_ = True

    def _check_is_fitted(self):
        """Ensure the estimator has been fitted."""
        if not getattr(self, "is_fitted_", False):
            raise ValueError("This estimator has not been fitted yet.")

    def _validate_data(self, X, y=None, reset=True):
        """Basic validation helper mirroring sklearn signature."""
        if X is None:
            raise ValueError("Input X cannot be None")
        return X, y

    @abstractmethod
    def fit(self, X, y=None):
        """
        Fit the estimator.

        Args:
            X: Input data
            y: Target values (optional)

        Returns:
            self: Returns self for chaining
        """
        pass


class LeCrapaudPipelineCompatible:
    """
    Mixin for components that can be used in sklearn Pipeline.

    This ensures proper parameter passing and state management.
    """

    def _validate_data(self, X, y=None, reset=True):
        """
        Validate input data (sklearn convention).

        Args:
            X: Input data
            y: Target data (optional)
            reset (bool): Whether to reset internal state

        Returns:
            tuple: (X, y) validated data
        """
        # Basic validation - can be extended as needed
        if X is None:
            raise ValueError("Input X cannot be None")

        return X, y

    def _check_is_fitted(self):
        """Check if the transformer has been fitted."""
        if not hasattr(self, "is_fitted_") or not self.is_fitted_:
            raise ValueError("This transformer has not been fitted yet.")

    def _set_fitted(self):
        """Mark the transformer as fitted."""
        self.is_fitted_ = True
