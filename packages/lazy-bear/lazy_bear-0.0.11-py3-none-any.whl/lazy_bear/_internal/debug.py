from __future__ import annotations

from importlib.metadata import distributions
from os import environ, getenv
import platform
import sys
from typing import TYPE_CHECKING, NamedTuple

from ._info import METADATA, _get_package_info, _Package

if TYPE_CHECKING:
    from collections.abc import Callable


class _Variable(NamedTuple):
    """A container for environment variable information."""

    name: str
    """Variable name."""
    value: str
    """Variable value."""


class _Environment(NamedTuple):
    """A container for environment/debug information."""

    interpreter_name: str
    """Python interpreter name."""
    interpreter_version: str
    """Python interpreter version."""
    interpreter_path: str
    """Path to Python executable."""
    platform: str
    """Operating System."""
    packages: list[_Package]
    """Installed packages."""
    variables: list[_Variable]
    """Environment variables."""


def _interpreter_name_version() -> _Variable:  # pragma: no cover
    impl: sys._version_info = sys.implementation.version
    name: str = sys.implementation.name
    return _Variable(name, f"{impl.major}.{impl.minor}.{impl.micro}")


def _get_installed_packages() -> list[_Package]:  # pragma: no cover
    """Get all installed packages in current environment"""
    packages: list[_Package] = []
    for dist in distributions():
        packages.append(_get_package_info(dist.metadata["Name"]))
    return packages


def _get_debug_info() -> _Environment:  # pragma: no cover
    """Get debug/environment information.

    Returns:
        Environment information.
    """
    python_version: _Variable = _interpreter_name_version()
    environ[f"{METADATA.name_upper}_DEBUG"] = "1"
    variables: list[str] = ["PYTHONPATH", *[var for var in environ if var.startswith(METADATA.name_upper)]]
    return _Environment(
        interpreter_name=python_version.name,
        interpreter_version=python_version.value,
        interpreter_path=sys.executable,
        platform=platform.platform(),
        variables=[_Variable(var, val) for var in variables if (val := getenv(var))],
        packages=_get_installed_packages(),
    )


def _get_printer(no_color: bool = False) -> Callable[..., None]:  # pragma: no cover
    """Get a print function that supports colored output if possible.

    Args:
        no_color: Whether to disable colored output.

    Returns:
        A print function.
    """
    try:
        from rich.console import Console  # noqa: PLC0415

        return Console(highlight=True, markup=True, no_color=no_color).print
    except ImportError:

        def _print_func(*args, **kwargs) -> None:
            kwargs.pop("style", "")
            print(*args, **kwargs)

        return _print_func


def _print_debug_info(no_color: bool = False) -> None:
    """Print debug/environment information with minimal clean formatting."""
    info: _Environment = _get_debug_info()
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "SYSTEM",
            [
                ("Platform", info.platform),
                ("Python", f"{info.interpreter_name} {info.interpreter_version}"),
                ("Location", info.interpreter_path),
            ],
        ),
        ("ENVIRONMENT", [(var.name, var.value) for var in info.variables]),
        ("PACKAGES", [(pkg.name, f"v{pkg.version}") for pkg in info.packages]),
    ]

    print_func: Callable[..., None] = _get_printer(no_color=no_color)

    for i, (section_name, items) in enumerate(sections):
        if items:
            print_func(f"{section_name}", style="bold red")
            for key, value in items:
                print_func(key, style="bold blue", end=": ")
                print_func(value, style="bold green")
            if i != len(sections) - 1:
                print_func()


if __name__ == "__main__":
    _print_debug_info()  # pragma: no cover
