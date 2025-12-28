from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal

from ._exit_code import ExitCode

type BumpType = Literal["major", "minor", "patch"]


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


@dataclass(slots=True)
class Version:  # pragma: no cover
    """Model to represent a version string."""

    major: int = field(default=0)
    minor: int = field(default=0)
    patch: int = field(default=0)
    post: str | None = field(default=None)

    def increment(self, attr_name: str) -> None:
        """Increment the specified part of the version."""
        if hasattr(self, attr_name.lower()):
            current_value: int = getattr(self, attr_name.lower())
            setattr(self, attr_name.lower(), current_value + 1)

    def default(self, part: str) -> None:
        """Clear the specified part of the version.

        Args:
            part: The part of the version to clear.
        """
        if hasattr(self, part):
            setattr(self, part, 0)

    def new_version(self, bump_type: str) -> Version:
        """Return a new version string based on the bump type."""
        bump_part: VersionParts = VersionParts[bump_type.upper()]
        self.increment(bump_part.name)
        for part in VersionParts:
            if part.value > bump_part.value:
                self.default(part.name.lower())
        return self

    def __repr__(self) -> str:
        """Return a string representation of the Version instance."""
        return (
            f"{self.major}.{self.minor}.{self.patch}.{self.post}"
            if self.post
            else f"{self.major}.{self.minor}.{self.patch}"
        )

    def __str__(self) -> str:
        """Return a string representation of the Version instance."""
        return self.__repr__()


VALID_BUMP_TYPES: list[str] = VersionParts.choices()  # pragma: no cover
ALL_PARTS: int = VersionParts.parts()  # pragma: no cover


def cli_bump(b: BumpType, v: str | tuple[int, int, int]) -> ExitCode:  # pragma: no cover
    """Bump the version of the current package.

    Args:
        b: The type of bump ("major", "minor", or "patch").
        p: The name of the package.
        v: The current version string or tuple of version parts.

    Returns:
        An ExitCode indicating success or failure.
    """
    if b not in VALID_BUMP_TYPES:
        print(f"Invalid argument '{b}'. Use one of: {', '.join(VALID_BUMP_TYPES)}.")
        return ExitCode.FAILURE
    if not isinstance(v, tuple):
        raise TypeError("Version must be a tuple of integers.")
    try:
        parts: list[int] = list(v)
        version: Version = Version(
            major=parts[0],
            minor=parts[1] if ALL_PARTS > 1 else 0,
            patch=parts[2] if ALL_PARTS > 2 else 0,  # noqa: PLR2004
        )
        new_version: Version = version.new_version(b)
        print(str(new_version))
        return ExitCode.SUCCESS
    except ValueError:
        print(f"Invalid version tuple: {v}")
        return ExitCode.FAILURE


__all__ = ["Version", "VersionParts"]
