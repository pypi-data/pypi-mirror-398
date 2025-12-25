from __future__ import annotations

from enum import IntEnum
from importlib.metadata import PackageNotFoundError, distribution, version
from typing import Literal, NamedTuple

try:
    from lazy_bear._internal._version import __commit_id__, __version__, __version_tuple__
except (ImportError, ModuleNotFoundError):
    __version__ = "0.0.0"
    __commit_id__ = "unknown"
    __version_tuple__ = (0, 0, 0)

PACKAGE_NAME: Literal["lazy-bear"] = "lazy-bear"
PROJECT_NAME: Literal["lazy_bear"] = "lazy_bear"
PROJECT_UPPER: Literal["LAZY_BEAR"] = "LAZY_BEAR"
ENV_VARIABLE: Literal["LAZY_BEAR_ENV"] = "LAZY_BEAR_ENV"
INTERNAL_PATH: Literal["lazy_bear._internal"] = "lazy_bear._internal"


class VersionParts(IntEnum):  # pragma: no cover
    """Enumeration for version parts."""

    MAJOR = 0
    MINOR = 1
    PATCH = 2

    @classmethod
    def choices(cls) -> list[str]:
        """Return a list of valid version parts."""
        return [part.name.lower() for part in cls]

    @classmethod
    def parts(cls) -> int:
        """Return the total number of version parts."""
        return len(cls.choices())


class Version(NamedTuple):
    """Model to represent a version string."""

    major: int
    minor: int
    patch: int

    def new_version(self, bump_type: str) -> Version:
        """Return a new version string based on the bump type."""
        bump_part: VersionParts = VersionParts[bump_type.upper()]
        match bump_part:
            case VersionParts.MAJOR:
                return Version(major=self.major + 1, minor=0, patch=0)
            case VersionParts.MINOR:
                return Version(major=self.major, minor=self.minor + 1, patch=0)
            case VersionParts.PATCH:
                return Version(major=self.major, minor=self.minor, patch=self.patch + 1)
            case _:
                raise ValueError(f"Invalid bump type: {bump_type}")

    def __repr__(self) -> str:
        """Return a string representation of the Version instance."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:
        """Return a string representation of the Version instance."""
        return self.__repr__()


class _Package(NamedTuple):  # pragma: no cover
    """A container for package information."""

    name: str
    """Package name."""
    version: str = "0.0.0"
    """Package version."""
    description: str = "No description available."
    """Package description."""

    def __str__(self) -> str:  # pragma: no cover
        """String representation of the package information."""
        return f"{self.name} v{self.version}: {self.description}"


def _get_version(dist: str) -> str:  # pragma: no cover
    """Get version of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A version number.
    """
    try:
        return version(dist)
    except PackageNotFoundError:
        return "0.0.0"


def _get_description(dist: str) -> str:  # pragma: no cover
    """Get description of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A description string.
    """
    try:
        return distribution(dist).metadata.get("summary", "No description available.")
    except PackageNotFoundError:
        return "No description available."


def _get_package_info(dist: str) -> _Package:  # pragma: no cover
    """Get package information for the given distribution.

    Parameters:
        dist: A distribution name.

    Returns:
        Package information with version, name, and description.
    """
    return _Package(name=dist, version=_get_version(dist), description=_get_description(dist))


PACKAGE_INFO: _Package = _get_package_info(PACKAGE_NAME)


class _ProjectMetadata(NamedTuple):  # pragma: no cover
    """A container for project metadata."""

    version: str = __version__ if __version__ != "0.0.0" else PACKAGE_INFO.version
    version_tuple: Version = Version(*__version_tuple__)
    commit_id: str = __commit_id__

    @property
    def cmds(self) -> str:
        """Get the commands module path."""
        return f"{INTERNAL_PATH}._cmds"

    @property
    def full_version(self) -> str:
        """Get the full version string."""
        return f"{PACKAGE_NAME} v{self.version}"

    @property
    def description(self) -> str:
        """Get the project description from the distribution metadata."""
        return PACKAGE_INFO.description

    @property
    def name(self) -> Literal["lazy-bear"]:
        """Get the package distribution name."""
        return PACKAGE_NAME

    @property
    def name_upper(self) -> Literal["LAZY_BEAR"]:
        """Get the project name in uppercase with underscores."""
        return PROJECT_UPPER

    @property
    def project_name(self) -> Literal["lazy_bear"]:
        """Get the project name."""
        return PROJECT_NAME

    @property
    def env_variable(self) -> Literal["LAZY_BEAR_ENV"]:
        """Get the environment variable name for the project.

        Used to check if the project is running in a specific environment.
        """
        return ENV_VARIABLE

    def __str__(self) -> str:
        """String representation of the project metadata."""
        return f"{self.full_version}: {self.description}"


METADATA = _ProjectMetadata()


__all__ = ["METADATA"]
