import os
from pathlib import Path

import pandas as pd
import joblib
from datetime import datetime

# Set up coverage file path
os.environ["COVERAGE_FILE"] = str(Path(".coverage").resolve())

# Internal imports
from lecrapaud.directories import tmp_dir
from lecrapaud.models import Experiment, Target
from lecrapaud.db.session import get_db


def create_experiment(
    data: pd.DataFrame | str,
    experiment_name,
    date_column=None,
    group_column=None,
    **kwargs,
):
    if "target_numbers" not in kwargs or "target_clf" not in kwargs:
        raise ValueError(
            "You should specify context in kwargs to create experiment from folder. Especially, target_clf and target_numbers must be present"
        )

    # if data is a path, load from path
    # only works locally as we do not save full.pkl outside development env
    if isinstance(data, str):
        path = f"{data}/data/full.pkl"
        data = joblib.load(path)
        keys = kwargs.keys()
        date_column = kwargs["date_column"] if "date_column" in keys else None
        group_column = keys["group_column"] if "group_column" in keys else None
        targets = []
        for target_number in kwargs["target_numbers"]:
            target_name = f"TARGET_{target_number}"
            target_type = (
                "classification"
                if target_number in kwargs["target_clf"]
                else "regression"
            )
            targets.append({"name": target_name, "type": target_type})
        Target.bulk_upsert(targets)
    else:
        experiment_name = (
            f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    if kwargs.get("time_series") and not date_column:
        raise ValueError("date_column must be provided for time series experiments")

    if experiment_name is None:
        raise ValueError("experiment_name must be provided")

    dates = {}
    if date_column:
        dates["start_date"] = pd.to_datetime(data[date_column].iat[0])
        dates["end_date"] = pd.to_datetime(data[date_column].iat[-1])

    groups = {}
    if group_column:
        groups["number_of_groups"] = data[group_column].nunique()
        groups["list_of_groups"] = sorted(data[group_column].unique().tolist())

    with get_db() as db:
        all_targets = Target.get_all(db=db)
        targets = [
            target
            for target in all_targets
            if int(target.name.split("_")[-1]) in kwargs["target_numbers"]
        ]
        number_of_targets = len(targets)

        experiment_dir = f"{tmp_dir}/{experiment_name}"
        preprocessing_dir = f"{experiment_dir}/preprocessing"
        data_dir = f"{experiment_dir}/data"
        os.makedirs(preprocessing_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        # Create or update experiment (without targets relation)
        experiment = Experiment.upsert(
            db=db,
            name=experiment_name,
            path=Path(experiment_dir).resolve(),
            size=data.shape[0],
            number_of_targets=number_of_targets,
            **groups,
            **dates,
            context={
                "date_column": date_column,
                "group_column": group_column,
                "experiment_name": experiment_name,
                **kwargs,
            },
        )

        # Set targets relationship after creation/update
        experiment.targets = targets
        experiment.save(db=db)

        return experiment
