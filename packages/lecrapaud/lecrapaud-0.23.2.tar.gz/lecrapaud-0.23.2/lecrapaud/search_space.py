from typing import Optional

# ML models
from sklearn.linear_model import (
    SGDRegressor,
    LinearRegression,
    SGDClassifier,
    LogisticRegression,
)
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.svm import LinearSVR, LinearSVC
from sklearn.naive_bayes import GaussianNB

# Ensemble models
from lightgbm import LGBMRegressor, LGBMClassifier
from xgboost import XGBRegressor, XGBClassifier
from catboost import CatBoostRegressor, CatBoostClassifier
from sklearn.ensemble import (
    RandomForestRegressor,
    AdaBoostRegressor,
    RandomForestClassifier,
    AdaBoostClassifier,
    BaggingClassifier,
)
import lightgbm as lgb
import xgboost as xgb

# DL models
from keras import Model, Input
from keras.layers import (
    Dense,
    LSTM,
    Bidirectional,
    GRU,
    LayerNormalization,
    RepeatVector,
    MultiHeadAttention,
    Add,
    GlobalAveragePooling1D,
    Dropout,
    Activation,
    TimeDistributed,
)
from tcn import TCN
from keras.initializers import Identity
from keras.regularizers import L2
from keras.activations import sigmoid

# Search spaces
from ray import tune
import pandas as pd

# we cannot use tune.sample_from function to make conditionnal search space,
# because hyperopt and bayesian opt need a fixed search space

ml_models = [
    {
        "model_name": "linear",
        "recurrent": False,
        "need_scaling": True,
        "classification": {
            "create_model": LogisticRegression,
            "search_params": {
                "penalty": tune.choice(
                    ["l2"]
                ),  # None is not compatible with liblinear, and l1/elasticnet not compatible with most solvers
                "C": tune.loguniform(1e-4, 1e2),
                "l1_ratio": tune.quniform(0.2, 0.8, 0.1),
                "solver": tune.choice(
                    [
                        "sag",
                        "saga",
                        "liblinear",
                        "lbfgs",
                        "newton-cg",
                        "newton-cholesky",
                    ]
                ),
                "max_iter": tune.randint(100, 1000),
                "n_jobs": -1,
                "random_state": 42,
            },
        },
        "regression": {
            "create_model": LinearRegression,
            "search_params": {
                "n_jobs": -1,
                "fit_intercept": tune.choice([True, False]),
            },
        },
    },
    {
        "model_name": "sgd",
        "recurrent": False,
        "need_scaling": True,
        "classification": {
            "create_model": SGDClassifier,
            "search_params": {
                "loss": tune.choice(
                    [
                        "hinge",
                        "log_loss",
                        "modified_huber",
                        "squared_hinge",
                    ]
                ),
                "penalty": tune.choice(["l1", "l2", "elasticnet"]),
                "alpha": tune.loguniform(1e-6, 1e-2),
                "l1_ratio": tune.quniform(0.2, 0.8, 0.1),
                "max_iter": tune.randint(1000, 5000),
                "shuffle": tune.choice([True, False]),
                "random_state": 42,
            },
        },
        "regression": {
            "create_model": SGDRegressor,
            "search_params": {
                "penalty": tune.choice(["l1", "l2", "elasticnet"]),
                "alpha": tune.loguniform(1e-6, 1e-2),
                "l1_ratio": tune.quniform(0.2, 0.8, 0.1),
                "max_iter": tune.randint(1000, 5000),
                "random_state": 42,
            },
        },
    },
    {
        "model_name": "naive_bayes",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": GaussianNB,  # Naive Bayes classifier for classification
            "search_params": {
                "var_smoothing": tune.loguniform(
                    1e-9, 1e-6
                )  # Smoothing parameter to deal with zero probabilities
            },
        },
        "regression": None,
    },
    {
        "model_name": "bagging_naive_bayes",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": BaggingClassifier,
            "search_params": {
                "estimator": GaussianNB(),  # Base model for bagging
                "n_estimators": tune.randint(10, 100),  # Number of base estimators
                "max_samples": tune.uniform(
                    0.5, 1.0
                ),  # Proportion of samples to draw for each base estimator
                "max_features": tune.uniform(
                    0.5, 1.0
                ),  # Proportion of features to draw for each base estimator
                "bootstrap": tune.choice(
                    [True, False]
                ),  # Whether samples are drawn with replacement
                "bootstrap_features": tune.choice(
                    [True, False]
                ),  # Whether features are drawn with replacement
                "random_state": 42,  # Fixed random state for reproducibility
            },
        },
        "regression": None,
    },
    {
        "model_name": "svm",
        "recurrent": False,
        "need_scaling": True,
        "classification": {
            "create_model": LinearSVC,
            "search_params": {
                # "penalty": tune.choice(["l1", "l2"]), # issue with l1 + hinge
                "C": tune.loguniform(1e-4, 1e2),  # Regularization strength
                "max_iter": tune.randint(100, 2000),  # Maximum number of iterations
                "tol": tune.loguniform(1e-5, 1e-2),  # Tolerance for stopping criteria
                "fit_intercept": tune.choice(
                    [True, False]
                ),  # Whether to calculate intercept
                "loss": tune.choice(["hinge", "squared_hinge"]),  # Loss function
                "dual": "auto",  # Dual only when hinge loss is not used and samples < features
                "random_state": 42,  # Fixed random state for reproducibility
            },
        },
        "regression": {
            "create_model": LinearSVR,
            "search_params": {
                "C": tune.loguniform(1e-4, 1e2),  # Regularization strength
                "max_iter": tune.randint(100, 2000),  # Maximum number of iterations
                "tol": tune.loguniform(1e-5, 1e-2),  # Tolerance for stopping criteria
                "epsilon": tune.loguniform(
                    1e-4, 1e-1
                ),  # Epsilon in the epsilon-insensitive loss function
                "fit_intercept": tune.choice(
                    [True, False]
                ),  # Whether to calculate intercept
                "loss": tune.choice(
                    ["epsilon_insensitive", "squared_epsilon_insensitive"]
                ),  # Loss function
                "dual": "auto",  # Dual is not applicable for certain configurations in SVR
                "random_state": 42,  # Fixed random state for reproducibility
            },
        },
    },
    {
        "model_name": "tree",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": DecisionTreeClassifier,
            "search_params": {
                "criterion": tune.choice(["gini", "entropy", "log_loss"]),
                "max_depth": tune.randint(8, 64),
                "min_samples_split": tune.randint(2, 10),
                "min_samples_leaf": tune.randint(1, 4),
                "max_features": tune.uniform(
                    0.5, 1.0
                ),  # Proportion of features to draw for each base estimator
                "random_state": 42,
            },
        },
        "regression": {
            "create_model": DecisionTreeRegressor,
            "search_params": {
                "max_depth": tune.randint(8, 64),
                "min_samples_split": tune.randint(2, 10),
                "min_samples_leaf": tune.randint(1, 4),
                "max_features": tune.uniform(
                    0.5, 1.0
                ),  # Proportion of features to draw for each base estimator
                "random_state": 42,
            },
        },
    },
    {
        "model_name": "forest",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": RandomForestClassifier,
            "search_params": {
                "n_estimators": tune.randint(50, 1000),  # Number of trees in the forest
                "max_depth": tune.randint(8, 64),  # Maximum depth of the trees
                "min_samples_split": tune.randint(
                    2, 20
                ),  # Minimum samples required to split a node
                "min_samples_leaf": tune.randint(
                    1, 10
                ),  # Minimum samples required at a leaf node
                "max_features": tune.choice(
                    ["sqrt", "log2", None]
                ),  # Number of features to consider at each split
                "bootstrap": tune.choice(
                    [True, False]
                ),  # Whether to use bootstrap sampling
                "criterion": tune.choice(
                    ["gini", "entropy", "log_loss"]
                ),  # The function to measure the quality of a split
                # "oob_score": tune.choice(
                #     [True, False]
                # ),  # Whether to use out-of-bag samples to estimate generalization accuracy: not working if bootstrap = False
                "n_jobs": -1,  # Use all processors
                "random_state": 42,  # Fixed random state for reproducibility
            },
        },
        "regression": {
            "create_model": RandomForestRegressor,
            "search_params": {
                "n_estimators": tune.randint(50, 1000),  # Number of trees in the forest
                "max_depth": tune.randint(5, 30),  # Maximum depth of the trees
                "min_samples_split": tune.randint(
                    2, 20
                ),  # Minimum samples required to split a node
                "min_samples_leaf": tune.randint(
                    1, 10
                ),  # Minimum samples required at a leaf node
                "max_features": tune.choice(
                    ["sqrt", "log2", None]
                ),  # Number of features to consider at each split
                "bootstrap": tune.choice(
                    [True, False]
                ),  # Whether to use bootstrap sampling
                "criterion": tune.choice(
                    ["squared_error", "absolute_error", "friedman_mse"]
                ),  # Loss function to use
                # "oob_score": tune.choice(
                #     [True, False]
                # ),  # Whether to use out-of-bag samples to estimate generalization accuracy: not working if bootstrap = False
                "n_jobs": -1,  # Use all processors
                "random_state": 42,  # Fixed random state for reproducibility
            },
        },
    },
    {
        "model_name": "adaboost",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": AdaBoostClassifier,
            "search_params": {
                "n_estimators": tune.randint(50, 1000),  # Number of boosting stages
                "learning_rate": tune.loguniform(
                    1e-4, 1
                ),  # Learning rate shrinks the contribution of each classifier
                "random_state": 42,  # Fixed random state for reproducibility
                "estimator": tune.choice(
                    [
                        DecisionTreeClassifier(max_depth=2**i, random_state=42)
                        for i in range(1, 6)
                    ]
                ),  # Base estimators are decision trees with varying depths
            },
        },
        "regression": {
            "create_model": AdaBoostRegressor,
            "search_params": {
                "n_estimators": tune.randint(50, 1000),  # Number of boosting stages
                "learning_rate": tune.loguniform(1e-4, 1),  # Learning rate
                "loss": tune.choice(
                    ["linear", "square", "exponential"]
                ),  # Loss function to use when updating weights
                "random_state": 42,  # Fixed random state for reproducibility
                "estimator": tune.choice(
                    [
                        DecisionTreeRegressor(max_depth=2**i, random_state=42)
                        for i in range(1, 6)
                    ]
                ),  # Base estimators are decision trees with varying depths
            },
        },
    },
    {
        "model_name": "xgb",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": "xgb",
            "search_params": {
                "num_boost_round": tune.randint(
                    50, 1000
                ),  # Number of boosting rounds (trees)
                "early_stopping_rounds": tune.randint(5, 50),
                "model_params": {
                    "max_depth": tune.randint(3, 10),  # Maximum depth of trees
                    "eta": tune.loguniform(
                        1e-4, 0.5
                    ),  # Learning rate, note 'eta' is used instead of 'learning_rate'
                    "subsample": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Subsample ratio of training instances
                    "colsample_bytree": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Subsample ratio of columns for each tree
                    "gamma": tune.uniform(
                        0, 10
                    ),  # Minimum loss reduction for further partitioning
                    "min_child_weight": tune.loguniform(
                        1, 10
                    ),  # Minimum sum of instance weights in a child
                    "alpha": tune.loguniform(
                        1e-5, 1
                    ),  # L1 regularization term on weights
                    "lambda": tune.loguniform(
                        1e-5, 1
                    ),  # L2 regularization term on weights
                    "random_state": 42,  # Fixed random state
                    "n_jobs": -1,  # Number of parallel threads for computation
                },
            },
        },
        "regression": {
            "create_model": "xgb",
            "search_params": {
                "num_boost_round": tune.randint(
                    50, 1000
                ),  # Number of boosting rounds (trees)
                "early_stopping_rounds": tune.randint(5, 50),
                "model_params": {
                    "max_depth": tune.randint(3, 10),  # Maximum depth of trees
                    "eta": tune.loguniform(1e-4, 0.5),  # Learning rate (eta)
                    "subsample": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Subsample ratio of training instances
                    "colsample_bytree": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Subsample ratio of columns for each tree
                    "gamma": tune.uniform(
                        0, 10
                    ),  # Minimum loss reduction for further partitioning
                    "min_child_weight": tune.loguniform(
                        1, 10
                    ),  # Minimum sum of instance weights in a child
                    "alpha": tune.loguniform(
                        1e-5, 1
                    ),  # L1 regularization term on weights
                    "lambda": tune.loguniform(
                        1e-5, 1
                    ),  # L2 regularization term on weights
                    "random_state": 42,  # Fixed random state
                    "n_jobs": -1,  # Number of parallel threads for computation
                },
            },
        },
    },
    {
        "model_name": "lgb",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": "lgb",
            "search_params": {
                "num_boost_round": tune.randint(
                    50, 1000
                ),  # Number of boosting rounds (trees)
                "early_stopping_rounds": tune.randint(5, 50),
                "model_params": {
                    "max_depth": tune.randint(3, 10),  # Maximum depth of trees
                    "learning_rate": tune.loguniform(1e-4, 0.5),  # Learning rate
                    "num_leaves": tune.randint(
                        20, 150
                    ),  # Maximum number of leaves in one tree
                    "subsample": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Fraction of training data for each boosting round
                    "colsample_bytree": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Fraction of features to use per tree
                    "min_data_in_leaf": tune.randint(
                        20, 100
                    ),  # Minimum number of data points in a leaf
                    "lambda_l1": tune.loguniform(1e-5, 1),  # L1 regularization
                    "lambda_l2": tune.loguniform(1e-5, 1),  # L2 regularization
                    "random_state": 42,  # Fixed random state for reproducibility
                    "n_jobs": -1,  # Use all cores for parallel computation
                },
            },
        },
        "regression": {
            "create_model": "lgb",
            "search_params": {
                "num_boost_round": tune.randint(
                    50, 1000
                ),  # Number of boosting rounds (trees)
                "early_stopping_rounds": tune.randint(5, 50),
                "model_params": {
                    "max_depth": tune.randint(3, 10),  # Maximum depth of trees
                    "learning_rate": tune.loguniform(1e-4, 0.5),  # Learning rate
                    "num_leaves": tune.randint(
                        20, 150
                    ),  # Maximum number of leaves in one tree
                    "subsample": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Fraction of training data for each boosting round
                    "colsample_bytree": tune.quniform(
                        0.6, 1, 0.05
                    ),  # Fraction of features to use per tree
                    "min_data_in_leaf": tune.randint(
                        20, 100
                    ),  # Minimum number of data points in a leaf
                    "lambda_l1": tune.loguniform(1e-5, 1),  # L1 regularization
                    "lambda_l2": tune.loguniform(1e-5, 1),  # L2 regularization
                    "random_state": 42,  # Fixed random state for reproducibility
                    "n_jobs": -1,  # Use all cores for parallel computation
                },
            },
        },
    },
    {
        "model_name": "catboost",
        "recurrent": False,
        "need_scaling": False,
        "classification": {
            "create_model": CatBoostClassifier,
            "search_params": {
                "iterations": tune.randint(50, 1000),
                "num_boost_round": tune.randint(50, 1000),
                "early_stopping_rounds": tune.randint(5, 50),
                "learning_rate": tune.loguniform(1e-4, 0.5),
                "depth": tune.randint(3, 10),
                "l2_leaf_reg": tune.loguniform(1e-5, 10),
                "bagging_temperature": tune.uniform(0.0, 1.0),
                "rsm": tune.quniform(0.6, 1.0, 0.05),
                "random_state": 42,
                "verbose": False,
            },
        },
        "regression": {
            "create_model": CatBoostRegressor,
            "search_params": {
                "iterations": tune.randint(50, 1000),
                "num_boost_round": tune.randint(50, 1000),
                "early_stopping_rounds": tune.randint(5, 50),
                "learning_rate": tune.loguniform(1e-4, 0.5),
                "depth": tune.randint(3, 10),
                "l2_leaf_reg": tune.loguniform(1e-5, 10),
                "bagging_temperature": tune.uniform(0.0, 1.0),
                "rsm": tune.quniform(0.6, 1.0, 0.05),
                "random_state": 42,
                "verbose": False,
            },
        },
    },
]


def get_model_constructor(model_name: str):

    def constructor(
        params: dict,
        input_shape: tuple[int, int],
        target_type: str,
        num_class: Optional[int] = None,
    ):
        """
        Builds the recurrent model based on the initialized parameters and model name.
        :return: A Keras Model object.
        """
        inputs = Input(shape=input_shape)

        # Model selection logic
        if model_name == "LSTM-1":
            x = LSTM(**params["model_params"])(inputs)

        elif model_name == "LSTM-2":
            x = LSTM(**params["model_params"], return_sequences=True)(inputs)
            x = LSTM(**params["model_params"])(x)

        elif model_name == "LSTM-2-Deep":
            x = LSTM(**params["model_params"], return_sequences=True)(inputs)
            x = LSTM(**params["model_params"])(x)
            x = Dense(50)(x)

        elif model_name == "BiLSTM-1":
            x = Bidirectional(LSTM(**params["model_params"]))(inputs)

        elif model_name == "BiLSTM-2":  # TODO: create search params ?
            x = Bidirectional(LSTM(**params["model_params"], return_sequences=True))(
                inputs
            )
            x = Bidirectional(LSTM(**params["model_params"]))(x)

        elif model_name == "GRU-1":
            x = GRU(**params["model_params"])(inputs)

        elif model_name == "GRU-2":  # TODO: create search params ?
            x = GRU(**params["model_params"], return_sequences=True)(inputs)
            x = GRU(**params["model_params"])(x)

        elif model_name == "GRU-2-Deep":  # TODO: create search params ?
            x = GRU(**params["model_params"], return_sequences=True)(inputs)
            x = GRU(**params["model_params"])(x)
            x = Dense(50)(x)

        elif model_name == "BiGRU-1":
            x = Bidirectional(GRU(**params["model_params"]))(inputs)

        elif model_name == "BiGRU-2":  # TODO: create search params ?
            x = Bidirectional(GRU(**params["model_params"], return_sequences=True))(
                inputs
            )
            x = Bidirectional(GRU(**params["model_params"]))(x)

        elif model_name == "TCN-1":
            x = TCN(**params["model_params"])(inputs)

        elif model_name == "TCN-2":  # TODO: create search params ?
            x = TCN(**params["model_params"], return_sequences=True)(inputs)
            x = TCN(**params["model_params"])(x)

        elif model_name == "TCN-2-Deep":  # TODO: create search params ?
            x = TCN(**params["model_params"], return_sequences=True)(inputs)
            x = TCN(**params["model_params"])(x)
            x = Dense(50)(x)

        elif model_name == "BiTCN-1":  # TODO: create search params ?
            x = Bidirectional(TCN(**params["model_params"], return_sequences=False))(
                inputs
            )

        elif model_name == "BiTCN-2":  # TODO: create search params ?
            x = Bidirectional(TCN(**params["model_params"], return_sequences=True))(
                inputs
            )
            x = Bidirectional(TCN(**params["model_params"], return_sequences=False))(x)

        elif model_name == "Seq2Seq":
            # encoder
            encoder_last_h1, encoder_last_h2, encoder_last_c = LSTM(
                **params["model_params"], return_state=True
            )(inputs)
            encoder_last_h1 = LayerNormalization(epsilon=1e-6)(encoder_last_h1)
            encoder_last_c = LayerNormalization(epsilon=1e-6)(encoder_last_c)

            # decoder
            decoder_timesteps = max(int(input_shape[0] / 5), 2)
            decoder = RepeatVector(decoder_timesteps)(encoder_last_h1)
            x = LSTM(**params["model_params"], return_state=False)(
                decoder, initial_state=[encoder_last_h1, encoder_last_c]
            )

        elif model_name == "Transformer":

            def transformer_encoder(
                inputs, num_layers, head_size, num_heads, ff_dim, dropout=0
            ):
                for _ in range(num_layers):
                    # Attention and Normalization
                    x = LayerNormalization(epsilon=1e-6)(inputs)
                    x = MultiHeadAttention(
                        key_dim=head_size, num_heads=num_heads, dropout=dropout
                    )(x, x)
                    x = Add()([x, inputs])

                    # Feed Forward Part
                    y = LayerNormalization(epsilon=1e-6)(x)
                    y = Dense(ff_dim, activation="relu")(y)
                    y = Dropout(dropout)(y)
                    y = Dense(inputs.shape[-1])(y)
                    inputs = Add()([y, x])

                return inputs

            x = transformer_encoder(inputs, **params["model_params"])
            x = GlobalAveragePooling1D()(x)
            x = LayerNormalization(epsilon=1e-6)(x)

        else:
            raise ValueError(f"Invalid model name: {model_name}")

        # Define output layer based on target type
        if num_class is not None and num_class > 2:
            outputs = Dense(
                num_class,
                kernel_initializer=Identity(),
                kernel_regularizer=L2(l2=params["l2"]),
                activation="softmax",
            )(x)
        else:
            outputs = Dense(
                1,
                kernel_initializer=Identity(),
                kernel_regularizer=L2(l2=params["l2"]),
                activation=(sigmoid if target_type == "classification" else "linear"),
            )(x)

        # Build the model
        model = Model(inputs=inputs, outputs=outputs, name=model_name)

        # Set the name of the model based on its parameters
        units = (
            params["model_params"].get("nb_filters")
            or params["model_params"].get("units")
            or params["model_params"].get("head_size")
        )
        nb_params = model.count_params()
        timesteps = input_shape[0]
        model.model_name = model.name

        return model

    return constructor


dl_recurrent_models = [
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "LSTM-1",
        "create_model": get_model_constructor("LSTM-1"),
        "search_params": {
            "model_params": {
                "units": tune.choice([32, 64, 128]),
                "activation": tune.choice(["tanh", "relu"]),
                "recurrent_activation": tune.choice(["sigmoid", "relu"]),
                "kernel_initializer": Identity(),
                "recurrent_initializer": Identity(),
                "dropout": tune.quniform(0.0, 0.5, 0.1),
                "recurrent_dropout": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "LSTM-2",
        "create_model": get_model_constructor("LSTM-2"),
        "search_params": {
            "model_params": {
                "units": tune.choice([32, 64, 128]),
                "activation": tune.choice(["tanh", "relu"]),
                "recurrent_activation": tune.choice(["sigmoid", "relu"]),
                "kernel_initializer": Identity(),
                "recurrent_initializer": Identity(),
                "dropout": tune.quniform(0.0, 0.5, 0.1),
                "recurrent_dropout": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "LSTM-2-Deep",
        "create_model": get_model_constructor("LSTM-2-Deep"),
        "search_params": {
            "model_params": {
                "units": tune.choice([32, 64, 128]),
                "activation": tune.choice(["tanh", "relu"]),
                "recurrent_activation": tune.choice(["sigmoid", "relu"]),
                "kernel_initializer": Identity(),
                "recurrent_initializer": Identity(),
                "dropout": tune.quniform(0.0, 0.5, 0.1),
                "recurrent_dropout": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "BiLSTM-1",
        "create_model": get_model_constructor("BiLSTM-1"),
        "search_params": {
            "model_params": {
                "units": tune.choice([32, 64, 128]),
                "activation": tune.choice(["tanh", "relu"]),
                "recurrent_activation": tune.choice(["sigmoid", "relu"]),
                "kernel_initializer": Identity(),
                "recurrent_initializer": Identity(),
                "dropout": tune.quniform(0.0, 0.5, 0.1),
                "recurrent_dropout": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "GRU-1",
        "create_model": get_model_constructor("GRU-1"),
        "search_params": {
            "model_params": {
                "units": tune.choice([32, 64, 128]),
                "activation": tune.choice(["tanh", "relu"]),
                "recurrent_activation": tune.choice(["sigmoid", "relu"]),
                "kernel_initializer": Identity(),
                "recurrent_initializer": Identity(),
                "dropout": tune.quniform(0.0, 0.5, 0.1),
                "recurrent_dropout": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "BiGRU-1",
        "create_model": get_model_constructor("GRU-1"),
        "search_params": {
            "model_params": {
                "units": tune.choice([32, 64, 128]),
                "activation": tune.choice(["tanh", "relu"]),
                "recurrent_activation": tune.choice(["sigmoid", "relu"]),
                "kernel_initializer": Identity(),
                "recurrent_initializer": Identity(),
                "dropout": tune.quniform(0.0, 0.5, 0.1),
                "recurrent_dropout": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "TCN-1",
        "create_model": get_model_constructor("TCN-1"),
        "search_params": {
            "model_params": {
                "nb_filters": tune.choice([32, 64, 128]),
                "kernel_size": tune.choice([2, 3, 5]),
                "dropout_rate": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "Seq2Seq",
        "create_model": get_model_constructor("Seq2Seq"),
        "search_params": {
            "model_params": {
                "units": tune.choice([32, 64, 128]),
                "kernel_initializer": Identity(),
                "recurrent_initializer": Identity(),
                "dropout": tune.quniform(0.0, 0.5, 0.1),
                "recurrent_dropout": tune.quniform(0.0, 0.5, 0.1),
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
    {
        "recurrent": True,
        "need_scaling": True,
        "model_name": "Transformer",
        "create_model": get_model_constructor("Transformer"),
        "search_params": {
            "model_params": {
                "head_size": tune.choice(
                    [32, 64, 128, 256, 512]
                ),  # Example of different head sizes to explore
                "num_heads": tune.choice(
                    [8, 16, 32]
                ),  # Exploring different number of heads
                "ff_dim": tune.choice(
                    [128, 256, 512, 1024, 2048]
                ),  # Feed-forward dimension options
                "num_layers": tune.choice([6, 12, 24]),  # Number of transformer layers
                "dropout": tune.quniform(
                    0.1, 0.5, 0.1
                ),  # Dropout rate between 0.1 and 0.5
            },
            "learning_rate": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128]),
            "epochs": tune.choice([50, 100, 200]),
            "timesteps": tune.choice([5, 10, 20, 50, 120]),
            "clipnorm": tune.quniform(0.5, 2.0, 0.5),
            "l2": tune.loguniform(1e-6, 1e-1),
        },
    },
]

all_models = ml_models + dl_recurrent_models


def get_models_idx(*model_names):
    matching_idx = [
        i for i, model in enumerate(all_models) if model["model_name"] in model_names
    ]
    return matching_idx


def normalize_models_idx(models_idx: list[int | str]) -> list[int]:
    """
    Convert a list of model identifiers (int or str) to a list of model indices (int).
    If an element is a string, it is resolved using `get_models_idx`.

    Returns:
        List of model indices (ints).
    """
    normalized = []
    for model_idx in models_idx:
        if isinstance(model_idx, int):
            normalized.append(model_idx)
        elif isinstance(model_idx, str):
            resolved = get_models_idx(model_idx)
            if not resolved:
                raise ValueError(f"No model index found for name: {model_idx}")
            normalized.append(resolved[0])
        else:
            raise TypeError(f"Unsupported type: {type(model_idx)}")
    return normalized
