from dataclasses import dataclass, field
from typing import Literal, NamedTuple

from ._version import __commit_id__, __version__, __version_tuple__

PACKAGE_NAME: Literal["bear-shelf"] = "bear-shelf"
PROJECT_NAME: Literal["bear_shelf"] = "bear_shelf"
PROJECT_UPPER: Literal["BEAR_SHELF"] = "BEAR_SHELF"
ENV_VARIABLE: Literal["BEAR_SHELF_ENV"] = "BEAR_SHELF_ENV"


class _Package(NamedTuple):
    """Dataclass to store package information."""

    name: str
    """Package name."""
    version: str = "0.0.0"
    """Package version."""
    description: str = "No description available."
    """Package description."""

    def __str__(self) -> str:
        """String representation of the package information."""
        return f"{self.name} v{self.version}: {self.description}"


def _get_package_info(dist: str) -> _Package:
    """Get package information for the given distribution.

    Parameters:
        dist: A distribution name.

    Returns:
        Package information with version, name, and description.
    """
    return _Package(name=dist, version=_get_version(dist), description=_get_description(dist))


def _get_version(dist: str) -> str:
    """Get version of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A version number.
    """
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(dist)
    except PackageNotFoundError:
        return "0.0.0"


def _get_description(dist: str) -> str:
    """Get description of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A description string.
    """
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        return distribution(dist).metadata.get("summary", "No description available.")
    except PackageNotFoundError:
        return "No description available."


def project_version() -> str:
    """Get the current project version.

    Returns:
        The current project version string.
    """
    return __version__ if __version__ != "0.0.0" else _get_version(PACKAGE_NAME)


@dataclass(slots=True)
class _ProjectMetadata:
    """Dataclass to store the current project metadata."""

    version: str = field(default_factory=project_version)
    version_tuple: tuple[int, int, int] = field(default=__version_tuple__)
    commit_id: str = field(default=__commit_id__)

    def __str__(self) -> str:
        """String representation of the project metadata."""
        return f"{self.full_version}: {self.description}"

    @property
    def full_version(self) -> str:
        """Get the full version string."""
        return f"{self.name} v{self.version}"

    @property
    def description(self) -> str:
        """Get the project description from the distribution metadata."""
        return _get_description(self.name)

    @property
    def name(self) -> Literal["bear-shelf"]:
        """Get the package distribution name."""
        return PACKAGE_NAME

    @property
    def name_upper(self) -> Literal["BEAR_SHELF"]:
        """Get the project name in uppercase with underscores."""
        return PROJECT_UPPER

    @property
    def project_name(self) -> Literal["bear_shelf"]:
        """Get the project name."""
        return PROJECT_NAME

    @property
    def env_variable(self) -> Literal["BEAR_SHELF_ENV"]:
        """Get the environment variable name for the project.

        Used to check if the project is running in a specific environment.
        """
        return ENV_VARIABLE


METADATA = _ProjectMetadata()


__all__ = ["METADATA"]

# ruff: noqa: PLC0415
