from __future__ import annotations

from enum import IntEnum
from typing import Literal, NamedTuple

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


class Version(NamedTuple):  # pragma: no cover
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


VALID_BUMP_TYPES: list[str] = VersionParts.choices()  # pragma: no cover
ALL_PARTS: int = VersionParts.parts()  # pragma: no cover


def cli_bump(b: BumpType, v: str | tuple[int, ...]) -> ExitCode:  # pragma: no cover
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
