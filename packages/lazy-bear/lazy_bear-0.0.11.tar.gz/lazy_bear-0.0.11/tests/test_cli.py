"""Tests for the CLI."""

from __future__ import annotations

from unittest import mock

import pytest

from lazy_bear import METADATA, main
from lazy_bear._internal.debug import _get_installed_packages, _interpreter_name_version, _Variable


@mock.patch("sys.argv", new=[METADATA.project_name])
def test_main() -> None:
    """Basic CLI test."""
    with pytest.raises(SystemExit):
        assert main([]) == 0


@mock.patch("sys.argv", new=[METADATA.project_name, "bump", "patch"])
def test_bump_no_version(capsys: pytest.CaptureFixture) -> None:
    """Test bump command with no version specified.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    main()
    captured = capsys.readouterr()
    version_tuple: tuple[int, int, int] = METADATA.version_tuple
    expected_version: str = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2] + 1}"
    assert expected_version in captured.out


@mock.patch("sys.argv", new=[METADATA.project_name, "--help"])
def test_show_help(capsys: pytest.CaptureFixture) -> None:
    """Show help.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "lazy-bear" in captured.out


@mock.patch("sys.argv", new=[METADATA.project_name, "version"])
def test_show_version(capsys: pytest.CaptureFixture) -> None:
    """Show version.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    main()
    captured = capsys.readouterr()
    assert METADATA.version in captured.out


@mock.patch("sys.argv", new=[METADATA.project_name, "debug", "--no-color"])
def test_show_debug_info(capsys: pytest.CaptureFixture) -> None:
    """Show debug information.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    main()
    captured = capsys.readouterr().out.lower()
    assert "python" in captured
    assert "system" in captured
    assert "environment" in captured
    assert "packages" in captured


def test_interpreter_name_version() -> None:
    """Test interpreter name and version retrieval."""
    name_version: _Variable = _interpreter_name_version()
    assert isinstance(name_version, tuple)
    assert len(name_version) == 2
    assert isinstance(name_version.name, str)
    assert "python" in name_version.name.lower()
    assert isinstance(name_version.value, str)
    assert name_version.value.startswith("3.")
    assert len(name_version.name) > 0
    assert len(name_version.value) > 0


def test_installed_packages() -> None:
    """Test installed packages retrieval."""
    packages = _get_installed_packages()
    assert isinstance(packages, list)
    for package in packages:
        assert hasattr(package, "name")
        assert hasattr(package, "version")
        assert isinstance(package.name, str)
        assert isinstance(package.version, str)
