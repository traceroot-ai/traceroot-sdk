from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from traceroot.utils.config import find_traceroot_config


def test_find_traceroot_config():
    """Test find_traceroot_config function."""
    # Test data
    config_data = {"key": "value", "debug": True}
    yaml_content = yaml.dump(config_data)

    # Test finding config in current directory
    with patch("pathlib.Path.cwd") as mock_cwd, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=yaml_content)):

        mock_cwd.return_value = Path("/test/path")
        result = find_traceroot_config()

        assert result == config_data

    # Test no config file found
    with patch("pathlib.Path.cwd") as mock_cwd, \
         patch("pathlib.Path.exists", return_value=False), \
         patch("traceroot.utils.config.list_sub_folders", return_value=[]), \
         patch("traceroot.utils.config.list_parent_folders", return_value=[]):

        mock_cwd.return_value = Path("/test/path")
        result = find_traceroot_config()

        assert result is None

    # Test YAML parsing error
    invalid_yaml = "invalid: yaml: content: ["
    with patch("pathlib.Path.cwd") as mock_cwd, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=invalid_yaml)):

        mock_cwd.return_value = Path("/test/path")

        with pytest.raises(ValueError) as exc_info:
            find_traceroot_config()

        assert "Error reading config file" in str(exc_info.value)
