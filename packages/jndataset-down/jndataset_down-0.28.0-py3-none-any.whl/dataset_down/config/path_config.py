import os
from dataset_down.config import constants


def get_config_dir() -> str:
    return constants.DEFAULT_CONFIG_DIR

def get_version_file_name() -> str:
    return constants.DEFAULT_CLI_VERSION_FILE_NAME


def get_token_file_name() -> str:
    return constants.DEFAULT_CLI_TOKEN_FILE_NAME


def get_config_file_name() -> str:
    return constants.DEFAULT_CLI_CONFIG_FILE_NAME


def get_dataset_file_name() -> str:
    return constants.DEFAULT_CLI_DATASET_FILE_NAME


def get_config_path() -> str:
    return os.path.join(get_config_dir(), get_config_file_name())


def get_token_path() -> str:
    return os.path.join(get_config_dir(), get_token_file_name())


def get_dataset_path() -> str:
    return os.path.join(get_config_dir(), get_dataset_file_name())


def get_version_path() -> str:
    return os.path.join(get_config_dir(), get_version_file_name())


def clear_dataset_json():
    try:
        with open(get_dataset_path(), "w") as f:
            f.truncate(0)
    except Exception as e:
        raise (e)