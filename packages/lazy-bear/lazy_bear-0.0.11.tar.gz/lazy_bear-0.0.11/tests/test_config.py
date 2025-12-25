from os import getenv

from lazy_bear import METADATA


def test_config_works() -> None:
    """Test to ensure the env was set"""
    assert getenv(METADATA.env_variable) == "test", "Environment variable not set correctly"


def test_metadata() -> None:
    """Test to ensure metadata is correctly set."""
    assert METADATA.name == "lazy-bear", "Metadata name does not match"
    assert METADATA.version != "0.0.0", "Metadata version should not be '0.0.0'"
    assert METADATA.description != "No description available.", "Metadata description should not be empty"
    assert METADATA.project_name == "lazy_bear", "Project name does not match"
