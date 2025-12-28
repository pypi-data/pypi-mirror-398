import os
from pathlib import Path

import pytest
from pydantic_settings_manager import load_user_configs

import kiarina.utils.file as kf


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent / "tests" / "data"


@pytest.fixture(scope="session")
def load_settings():
    env_var = "KIARINA_LIB_GOOGLE_CLOUD_STORAGE_TEST_SETTINGS_FILE"

    if env_var not in os.environ:
        pytest.skip(f"Environment variable {env_var} not set, skipping tests.")

    test_settings_file = os.environ[env_var]
    test_settings_file = os.path.expanduser(test_settings_file)

    if not os.path.exists(test_settings_file):
        raise FileNotFoundError(f"Settings file not found: {test_settings_file}")

    user_configs = kf.read_yaml_dict(test_settings_file)

    if not user_configs:
        raise ValueError(f"Settings file is empty or invalid: {test_settings_file}")

    load_user_configs(user_configs)
