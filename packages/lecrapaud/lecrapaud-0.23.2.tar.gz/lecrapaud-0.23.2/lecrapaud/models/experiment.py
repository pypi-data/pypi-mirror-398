from itertools import chain
import joblib
import pandas as pd
import os

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    JSON,
    Table,
    ForeignKey,
    BigInteger,
    TIMESTAMP,
    UniqueConstraint,
    func,
    event,
)
from sqlalchemy.orm import relationship, aliased, mapper
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from statistics import fmean as mean
from lecrapaud.models.model_selection import ModelSelection
from lecrapaud.models.model_selection_score import ModelSelectionScore

from lecrapaud.models.base import Base, with_db
from lecrapaud.models.utils import create_association_table
from lecrapaud.utils import logger, contains_best, strip_timestamp_suffix

# jointures
lecrapaud_experiment_target_association = create_association_table(
    name="experiment_target_association",
    table1="experiments",
    column1="experiment",
    table2="targets",
    column2="target",
)


class Experiment(Base):

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    path = Column(String(255))  # we do not have this at creation time
    size = Column(Integer, nullable=False)
    train_size = Column(Integer)
    val_size = Column(Integer)
    test_size = Column(Integer)
    number_of_groups = Column(Integer)
    list_of_groups = Column(JSON)
    number_of_targets = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    train_start_date = Column(DateTime)
    train_end_date = Column(DateTime)
    val_start_date = Column(DateTime)
    val_end_date = Column(DateTime)
    test_start_date = Column(DateTime)
    test_end_date = Column(DateTime)
    context = Column(JSON)

    feature_selections = relationship(
        "FeatureSelection",
        back_populates="experiment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    targets = relationship(
        "Target",
        secondary=lecrapaud_experiment_target_association,
        back_populates="experiments",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_experiments_composite",
        ),
    )

    # Relationships
    model_selections = relationship(
        "ModelSelection",
        back_populates="experiment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Hooks
    # @event.listens_to(Experiment, "after_commit")
    # def set_score(mapper, connection, target):
    #     target.score = target.score

    # Properties
    @hybrid_property
    def rmse_scores(self):
        """best RMSE scores across all model selections, for each targets."""
        # Get the minimum RMSE for each model selection
        min_scores = [
            min(mss.rmse for mss in ms.model_selection_scores if mss.rmse is not None)
            for ms in self.model_selections
            if any(mss.rmse is not None for mss in ms.model_selection_scores)
        ]

        if not min_scores:
            # fallback to path if no model_selection_scores found
            for target in self.targets:
                path = f"{self.path}/{target.name}/scores_tracking.csv"
                if not os.path.exists(path):
                    continue
                score = pd.read_csv(path)
                if "RMSE" not in score.columns:
                    continue
                min_scores.append(min(score["RMSE"]))

        return min_scores

    @hybrid_property
    def logloss_scores(self):
        """best LogLoss scores across all model selections, for each targets."""
        # Get the minimum LogLoss for each model selection
        min_scores = [
            min(
                mss.logloss
                for mss in ms.model_selection_scores
                if mss.logloss is not None
            )
            for ms in self.model_selections
            if any(mss.logloss is not None for mss in ms.model_selection_scores)
        ]

        if not min_scores:
            # fallback to path if no model_selection_scores found
            for target in self.targets:
                path = f"{self.path}/{target.name}/scores_tracking.csv"
                if not os.path.exists(path):
                    continue
                score = pd.read_csv(path)
                if "LOGLOSS" not in score.columns:
                    continue
                min_scores.append(min(score["LOGLOSS"]))

        return min_scores

    @hybrid_property
    def best_rmse(self):
        """Best RMSE score within targets, across all model selections."""
        return min(self.rmse_scores) if self.rmse_scores else None

    @hybrid_property
    def best_logloss(self):
        """Best LogLoss score within targets, across all model selections."""
        return min(self.logloss_scores) if self.logloss_scores else None

    @hybrid_property
    def score(self):
        # Calculate a combined score: average of normalized best RMSE and LogLoss per targets
        # This ensures we're comparing apples to apples by normalizing the scores

        if not self.rmse_scores and not self.logloss_scores:
            logger.error("No experiments found with RMSE or LogLoss scores.")
            return None

        # Normalize scores (subtract min and divide by range)
        # Guard against division by zero when only one observation or all equal
        # Let's gather all the data from similar experiments to calculate the range

        similar_experiments = Experiment.get_all_by_name(name=self.name)
        if not similar_experiments:
            similar_experiments = [self]
        rmse_scores = [
            score for exp in similar_experiments for score in exp.rmse_scores or []
        ]
        logloss_scores = [
            score for exp in similar_experiments for score in exp.logloss_scores or []
        ]

        min_rmse = min(rmse_scores)
        max_rmse = max(rmse_scores)
        range_rmse = max_rmse - min_rmse
        min_logloss = min(logloss_scores)
        max_logloss = max(logloss_scores)
        range_logloss = max_logloss - min_logloss

        # Calculate combined score for each experiment
        normed_scores = []
        for rmse_score in self.rmse_scores:

            # Normalize both scores (safe when range == 0)
            norm_rmse = 0.0 if range_rmse == 0 else (rmse_score - min_rmse) / range_rmse
            normed_scores.append(norm_rmse)

        for logloss_score in self.logloss_scores:
            norm_logloss = (
                0.0
                if range_logloss == 0
                else (logloss_score - min_logloss) / range_logloss
            )
            normed_scores.append(norm_logloss)

        # Calculate score (average of normalized scores)
        score = sum(normed_scores) / len(normed_scores)

        return score

    @hybrid_property
    def avg_rmse(self):
        """Average within targets of best RMSE score across all model selections ."""
        return mean(self.rmse_scores) if self.rmse_scores else None

    @hybrid_property
    def avg_logloss(self):
        """Average within targets of best LogLoss score across all model selections ."""
        return mean(self.logloss_scores) if self.logloss_scores else None

    # Class methods
    @classmethod
    @with_db
    def get_all_by_name(cls, name: str | None = None, limit: int = 1000, db=None):
        """
        Find the most recently created experiment that contains the given name string.

        Args:
            session: SQLAlchemy session
            name (str): String to search for in experiment names

        Returns:
            Experiment or None: The most recent matching experiment or None if not found
        """
        base_name = strip_timestamp_suffix(name)
        if name is not None:
            return (
                db.query(cls)
                .filter(cls.name.ilike(f"%{base_name}%"))
                .order_by(cls.created_at.desc())
                .limit(limit)
                .all()
            )
        return db.query(cls).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    @with_db
    def get_last_by_name(cls, name: str, db=None):
        """
        Find the most recently created experiment that contains the given name string.

        Args:
            session: SQLAlchemy session
            name (str): String to search for in experiment names

        Returns:
            Experiment or None: The most recent matching experiment or None if not found
        """
        base_name = strip_timestamp_suffix(name)
        return (
            db.query(cls)
            .filter(cls.name.ilike(f"%{base_name}%"))
            .order_by(cls.created_at.desc())
            .first()
        )

    @classmethod
    @with_db
    def get_best_by_score(cls, name: str, db=None):
        """
        Find the experiment with the best normalized score across RMSE and LogLoss.

        Returns:
            Experiment or None: The experiment with the best score or None if not found
        """
        experiments = Experiment.get_all_by_name(name=name)
        if not experiments:
            logger.error(f"No experiments found with the given name: {name}")
            return None

        experiments = [
            exp
            for exp in experiments
            if all(
                [contains_best(f"{exp.path}/{target.name}") for target in exp.targets]
            )
        ]
        if not experiments:
            logger.error(
                f"No fully trained experiments found with the given name: {name}"
            )
            return None

        scored_experiments = []
        for experiment in experiments:
            score = experiment.score
            if score is not None:
                scored_experiments.append((experiment, score))

        if not scored_experiments:
            logger.error(
                f"No experiments with calculable scores found with the given name: {name}"
            )
            return None

        scored_experiments.sort(key=lambda x: x[1])
        return scored_experiments[0][0]

    # Instance methods
    def best_score(self, target_number: int) -> dict:
        """
        Returns the scores for the best model of the specified target.

        Args:
            target_number (int): The target number to get scores for

        Returns:
            dict: A dictionary containing the experiment name, target number, and the best model's scores
        """
        # Find the target
        target_name = f"TARGET_{target_number}"
        target = next((t for t in self.targets if t.name == target_name), None)

        if not target:
            return {
                "experiment_name": self.name,
                "target_number": target_number,
                "error": f"Target {target_name} not found in this experiment",
                "scores": {},
            }

        # Find the best model selection for this target
        best_model_selection = next(
            (ms for ms in self.model_selections if ms.target_id == target.id), None
        )

        if not best_model_selection or not best_model_selection.model_selection_scores:
            return {
                "experiment_name": self.name,
                "target_number": target_number,
                "error": "No model found for this target",
                "scores": {},
            }

        # Get the best model score based on lowest logloss or rmse
        model_scores = best_model_selection.model_selection_scores

        # Determine if we should use logloss or rmse based on what's available
        if any(ms.logloss is not None for ms in model_scores):
            # Classification: find lowest logloss
            best_score = min(
                (ms for ms in model_scores if ms.logloss is not None),
                key=lambda x: x.logloss,
            )
        elif any(ms.rmse is not None for ms in model_scores):
            # Regression: find lowest rmse
            best_score = min(
                (ms for ms in model_scores if ms.rmse is not None), key=lambda x: x.rmse
            )
        else:
            return {
                "experiment_name": self.name,
                "target_number": target_number,
                "error": "No scores found for the best model",
                "scores": {},
            }

        # Use the best score found
        score = best_score
        available_metrics = [
            "rmse",
            "mae",
            "r2",
            "logloss",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
        ]

        scores = {}
        for metric in available_metrics:
            value = getattr(score, metric, None)
            if value is not None:
                scores[metric] = value

        # Get the model info
        model_info = {
            "model_type": (score.model.model_type if score.model else "unknown"),
            "model_name": (score.model.name if score.model else "unknown"),
            "training_time_seconds": score.training_time,
        }

        return {
            "experiment_name": self.name,
            "target_number": target_number,
            "model": model_info,
            "scores": scores,
        }

    @with_db
    def get_features(self, target_number: int, db=None):
        # Ensure we have a fresh instance attached to the session
        self = db.merge(self)
        targets = [t for t in self.targets if t.name == f"TARGET_{target_number}"]
        if targets:
            target_id = targets[0].id
            feature_selection = [
                fs for fs in self.feature_selections if fs.target_id == target_id
            ]
            if feature_selection:
                feature_selection = feature_selection[0]
                features = [f.name for f in feature_selection.features]
                return features

        # fallback to path if no features found
        features = joblib.load(f"{self.path}/TARGET_{target_number}/features.pkl")
        return features

    @with_db
    def get_all_features(
        self, date_column: str = None, group_column: str = None, db=None
    ):
        # Ensure we have a fresh instance attached to the session
        self = db.merge(self)
        target_idx = [target.id for target in self.targets]
        _all_features = chain.from_iterable(
            [f.name for f in fs.features]
            for fs in self.feature_selections
            if fs.target_id in target_idx
        )
        _all_features = list(_all_features)

        # fallback to path if no features found
        if len(_all_features) == 0:
            _all_features = joblib.load(f"{self.path}/preprocessing/all_features.pkl")

        all_features = []
        if date_column:
            all_features.append(date_column)
        if group_column:
            all_features.append(group_column)
        all_features += _all_features
        all_features = list(dict.fromkeys(all_features))

        return all_features
