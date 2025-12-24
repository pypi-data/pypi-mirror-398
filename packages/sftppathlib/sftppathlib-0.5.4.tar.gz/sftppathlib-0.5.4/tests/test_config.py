import pytest
from sftppathlib import get_config_path, load_configs


def test_config():
    config_path = get_config_path()
    config = load_configs(config_path)

    assert "example.com" in config
