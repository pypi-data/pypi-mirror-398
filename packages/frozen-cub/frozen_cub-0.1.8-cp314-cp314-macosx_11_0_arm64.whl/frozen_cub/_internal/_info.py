from importlib.metadata import PackageNotFoundError, distribution, version
from typing import Literal, NamedTuple

try:
    from ._version import __commit_id__, __version__, __version_tuple__
except ModuleNotFoundError:
    __commit_id__ = "unknown"
    __version__ = "0.0.0"
    __version_tuple__ = (0, 0, 0)

PACKAGE_NAME: Literal["frozen-cub"] = "frozen-cub"
PROJECT_NAME: Literal["frozen_cub"] = "frozen_cub"
PROJECT_NAME_UPPER: Literal["FROZEN_CUB"] = "FROZEN_CUB"
ENV_VARIABLE: Literal["FROZEN_CUB_ENV"] = "FROZEN_CUB_ENV"


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
    try:
        return distribution(dist).metadata.get("summary", "No description available.")
    except PackageNotFoundError:
        return "No description available."


def get_tuple_version() -> tuple[int, ...]:
    """Get the current package version as a tuple."""
    return (
        __version_tuple__
        if __version_tuple__ != (0, 0, 0)
        else tuple(int(part) for part in _get_version(PACKAGE_NAME).split(".")[:3])
    )


class _ProjectMetadata(NamedTuple):
    """Dataclass to store the current project metadata."""

    internal: str = f"{PROJECT_NAME}._internal"
    cmds: str = f"{PROJECT_NAME}._internal._cmds"
    version: str = __version__ if __version__ != "0.0.0" else _get_version(PACKAGE_NAME)
    version_tuple: tuple[int, ...] = get_tuple_version()
    commit_id: str = __commit_id__

    description: str = _get_description(PACKAGE_NAME)

    @property
    def full_version(self) -> str:
        """Get the full version string including commit ID."""
        return f"{self.name} v{self.version}"

    @property
    def name(self) -> Literal["frozen-cub"]:
        """Get the package distribution name."""
        return PACKAGE_NAME

    @property
    def name_upper(self) -> Literal["FROZEN_CUB"]:
        """Get the project name in uppercase with underscores."""
        return PROJECT_NAME_UPPER

    @property
    def project_name(self) -> Literal["frozen_cub"]:
        """Get the project name."""
        return PROJECT_NAME

    @property
    def env_variable(self) -> Literal["FROZEN_CUB_ENV"]:
        """Get the environment variable name for the project.

        Used to check if the project is running in a specific environment.
        """
        return ENV_VARIABLE

    def __str__(self) -> str:
        """String representation of the project metadata."""
        return f"{self.full_version}: {self.description}"


METADATA = _ProjectMetadata()


__all__ = ["METADATA"]
