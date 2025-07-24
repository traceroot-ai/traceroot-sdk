from pathlib import Path
from typing import Any

import yaml

from traceroot.utils.io import list_parent_folders, list_sub_folders


def find_traceroot_config() -> dict[str, Any] | None:
    """Find and load the .traceroot-config.yaml file.

    Searches the current directory for the configuration file.

    Returns:
        Dictionary containing the configuration, or None if no file found.
    """
    config_filename = ".traceroot-config.yaml"

    # Check current working directory
    current_path = Path.cwd()
    config_path = current_path / config_filename

    if config_path.exists():
        try:
            with open(config_path) as file:
                config_data = yaml.safe_load(file)
                return config_data if config_data else {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Error reading config file {config_path}: {e}")

    # Check subfolders for config file up to 4 levels
    sub_folders = list_sub_folders(4, config_filename, current_path)
    for config_path in sub_folders:
        try:
            with open(config_path) as file:
                config_data = yaml.safe_load(file)
                return config_data if config_data else {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Error reading config file "
                             f"{config_path}: {e}")

    # Check parent folders for config file up to 4 levels
    parent_folders = list_parent_folders(4, config_filename, current_path)
    for config_path in parent_folders:
        try:
            with open(config_path) as file:
                config_data = yaml.safe_load(file)
                return config_data if config_data else {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Error reading config file "
                             f"{config_path}: {e}")
    return None
