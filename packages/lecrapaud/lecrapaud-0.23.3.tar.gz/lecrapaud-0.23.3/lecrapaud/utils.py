import pandas as pd
import logging
from logging.handlers import RotatingFileHandler
import shutil
import os
import subprocess
from datetime import datetime, date
from ftfy import fix_text
import unicodedata
import re
import string

from lecrapaud.directories import logger_dir
from lecrapaud.config import LOGGING_LEVEL, PYTHON_ENV


_LECRAPAUD_LOGGER_ALREADY_CONFIGURED = False


def setup_logger():

    name = "lecrapaud"

    global _LECRAPAUD_LOGGER_ALREADY_CONFIGURED
    if _LECRAPAUD_LOGGER_ALREADY_CONFIGURED:  # ← bail out if done before
        return logging.getLogger(name if PYTHON_ENV != "Worker" else "")

    print(
        f"Setting up logger for {name} with PYTHON_ENV {PYTHON_ENV} and LOGGING_LEVEL {LOGGING_LEVEL}"
    )
    # ------------------------------------------------------------------ #
    #  Real configuration happens only on the FIRST call                 #
    # ------------------------------------------------------------------ #
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=fmt, datefmt=datefmt)  # root format
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    logger = logging.getLogger("" if PYTHON_ENV == "Worker" else "lecrapaud")

    log_level = getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # pick a file according to environment
    env_file = {
        "Development": "dev.log",
        "Production": "prod.log",
        "Test": "test.log",
        "Worker": "worker.log",
    }.get(PYTHON_ENV, "app.log")

    if logger_dir:
        file_handler = RotatingFileHandler(
            f"{logger_dir}/{env_file}",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    try:
        from lecrapaud.integrations.sentry_integration import init_sentry

        if init_sentry():
            logger.info("Sentry logging enabled")
    except Exception as exc:
        logger.info(f"Sentry logging disabled: {exc}")

    _LECRAPAUD_LOGGER_ALREADY_CONFIGURED = True
    return logger


logger = setup_logger()


def get_df_name(obj, namespace):
    return [name for name in namespace if namespace[name] is obj][0]


def pprint(item):
    with pd.option_context("display.max_rows", None):
        logger.info(item)


def object_to_dict(obj):
    if isinstance(obj, dict):
        return {k: object_to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        return {k: object_to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [object_to_dict(i) for i in obj]
    else:
        return obj


def copy_any(src, dst):
    if os.path.isdir(src):
        # Copy folder using copytree
        shutil.copytree(src, dst)
    else:
        # Copy file using copy2 (which preserves metadata)
        shutil.copy2(src, dst)


def contains_best(folder_path):
    # Iterate over all files and folders in the specified directory
    for root, dirs, files in os.walk(folder_path):
        # Check each file and folder name for '.best' or '.keras'
        for name in files + dirs:
            if ".best" in name or ".keras" in name:
                return True
    return False


def get_folder_sizes(directory=os.path.expanduser("~")):
    folder_sizes = {}

    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            try:
                size = (
                    subprocess.check_output(["du", "-sk", folder_path])
                    .split()[0]
                    .decode("utf-8")
                )
                folder_sizes[folder] = int(size)
            except subprocess.CalledProcessError:
                logger.info(f"Skipping {folder_path}: Permission Denied")

    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"{'Folder':<50}{'Size (MB)':>10}")
    logger.info("=" * 60)
    for folder, size in sorted_folders:
        logger.info(f"{folder:<50}{size / (1024*1024):>10.2f}")


def create_cron_job(
    script_path,
    venv_path,
    log_file,
    pythonpath,
    cwd,
    job_frequency="* * * * *",
    cron_name="My Custom Cron Job",
):
    """
    Creates a cron job to run a Python script with a virtual environment, logging output, and setting PYTHONPATH and CWD.

    Parameters:
    - script_path (str): Path to the Python script to run.
    - venv_path (str): Path to the virtual environment's Python interpreter.
    - log_file (str): Path to the log file for output.
    - pythonpath (str): Value for the PYTHONPATH environment variable.
    - cwd (str): Working directory from which the script should run.
    - job_frequency (str): Cron timing syntax (default is every minute).
    - cron_name (str): Name to identify the cron job.
    """
    # Construct the cron command
    cron_command = (
        f"{job_frequency} /bin/zsh -c 'pgrep -fl python | grep -q {os.path.basename(script_path)} "
        f'|| (echo -e "Cron job {cron_name} started at $(date)" >> {log_file} && cd {cwd} && '
        f"PYTHONPATH={pythonpath} {venv_path}/bin/python {script_path} >> {log_file} 2>&1)'"
    )

    # Check existing cron jobs and remove any with the same comment
    subprocess.run(f"(crontab -l | grep -v '{cron_name}') | crontab -", shell=True)

    # Add the new cron job with the comment
    full_cron_job = f"{cron_command} # {cron_name}\n"
    subprocess.run(f'(crontab -l; echo "{full_cron_job}") | crontab -', shell=True)
    logger.info(f"Cron job created: {full_cron_job}")


def remove_all_cron_jobs():
    """
    Removes all cron jobs for the current user.
    """
    try:
        # Clear the user's crontab
        subprocess.run("crontab -r", shell=True, check=True)
        logger.info("All cron jobs have been removed successfully.")
    except subprocess.CalledProcessError:
        logger.info(
            "Failed to remove cron jobs. There may not be any cron jobs to remove, or there could be a permissions issue."
        )


def serialize_timestamp(dict: dict):
    def convert(obj):
        if isinstance(obj, (datetime, date, pd.Timestamp)):
            return obj.isoformat()

        return obj

    return [{k: convert(v) for k, v in item.items()} for item in dict]


def remove_accents(text: str) -> str:
    """
    Cleans the text of:
    - Broken Unicode
    - Accents
    - Control characters (including \x00, \u0000, etc.)
    - Escape sequences
    - Non-printable characters
    - Excessive punctuation (like ........ or !!!!)
    """

    # Step 1: Fix mojibake and broken Unicode
    text = fix_text(text)

    # Step 2 bis: Normalize accents
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("utf8")

    # Step 3: Remove known weird tokens
    text = text.replace("<|endoftext|>", "")
    text = text.replace("\u0000", "").replace("\x00", "")

    # Step 4: Remove raw control characters (e.g., \x1f)
    text = "".join(c for c in text if unicodedata.category(c)[0] != "C" or c == "\n")

    # Step 5: Remove literal escape sequences like \xNN
    text = re.sub(r"\\x[0-9a-fA-F]{2}", "", text)

    # Step 6: Remove non-printable characters
    printable = set(string.printable)
    text = "".join(c for c in text if c in printable)

    # Step 7: Collapse repeated punctuation (e.g., ........ → .)
    text = re.sub(r"([!?.])\1{2,}", r"\1", text)  # !!!!!! → !
    text = re.sub(r"([-—])\1{1,}", r"\1", text)  # ------ → -
    text = re.sub(r"([,.]){4,}", r"\1", text)  # ...... → .

    return text.strip()


def serialize_for_json(obj):
    """
    Recursively convert any object into a JSON-serializable structure.
    Handles NumPy types, datetime objects, and class instances.
    """
    import numpy as np
    from datetime import datetime, date
    import pandas as pd

    # Handle NumPy types
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)

    # Handle datetime types
    elif isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()

    # Handle basic Python types
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {str(k): serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [serialize_for_json(v) for v in obj]
    elif isinstance(obj, type):
        # A class/type object like int, str, etc.
        return obj.__name__
    elif hasattr(obj, "__class__"):
        # For other objects, return their string representation
        return f"{obj.__class__.__name__}()"
    else:
        return str(obj)


def strip_timestamp_suffix(name: str) -> str:
    # Matches an underscore followed by 8 digits, another underscore, then 6 digits at the end
    return re.sub(r"_\d{8}_\d{6}$", "", name)
