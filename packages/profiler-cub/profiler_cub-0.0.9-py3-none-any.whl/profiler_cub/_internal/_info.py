from importlib.metadata import PackageNotFoundError, distribution, version
from typing import Literal, NamedTuple

try:
    from profiler_cub._internal._version import __commit_id__, __version__, __version_tuple__
except (ModuleNotFoundError, ImportError):
    __version__ = "0.0.0"
    __version_tuple__ = (0, 0, 0)
    __commit_id__ = "unknown"

PACKAGE_NAME: Literal["profiler-cub"] = "profiler-cub"
PROJECT_NAME: Literal["profiler_cub"] = "profiler_cub"
PROJECT_UPPER: Literal["PROFILER_CUB"] = "PROFILER_CUB"
ENV_VARIABLE: Literal["PROFILER_CUB_ENV"] = "PROFILER_CUB_ENV"


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


class _ProjectMetadata(NamedTuple):
    """Dataclass to store the current project metadata."""

    version: str = __version__ if __version__ != "0.0.0" else _get_version(PACKAGE_NAME)
    version_tuple: tuple[int, int, int] = __version_tuple__
    commit_id: str = __commit_id__

    def __str__(self) -> str:
        """String representation of the project metadata."""
        return f"{self.full_version}: {self.description}"

    @property
    def _internal(self) -> str:
        """Get the internal module path."""
        return "profiler_cub._internal"

    @property
    def cmds(self) -> str:
        """Get the commands module path."""
        return f"{self._internal}._cmds"

    @property
    def full_version(self) -> str:
        """Get the full version string."""
        return f"{self.name} v{self.version}"

    @property
    def description(self) -> str:
        """Get the project description from the distribution metadata."""
        return _get_description(self.name)

    @property
    def name(self) -> Literal["profiler-cub"]:
        """Get the package distribution name."""
        return PACKAGE_NAME

    @property
    def name_upper(self) -> Literal["PROFILER_CUB"]:
        """Get the project name in uppercase with underscores."""
        return PROJECT_UPPER

    @property
    def project_name(self) -> Literal["profiler_cub"]:
        """Get the project name."""
        return PROJECT_NAME

    @property
    def env_variable(self) -> Literal["PROFILER_CUB_ENV"]:
        """Get the environment variable name for the project.

        Used to check if the project is running in a specific environment.
        """
        return ENV_VARIABLE


METADATA = _ProjectMetadata()


__all__ = ["METADATA"]
