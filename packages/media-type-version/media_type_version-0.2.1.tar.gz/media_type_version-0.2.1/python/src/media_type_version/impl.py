# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Extract the format version from a media type string."""

from __future__ import annotations

import dataclasses
import re
import typing

from . import defs


if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Final


RE_INT: Final = re.compile(r" 0 | [1-9][0-9]* ", re.X)
"""Detect an unsigned integer value."""


@dataclasses.dataclass
class NoPrefixError(defs.MTVError):
    """The expected prefix was not found."""

    value: str
    """The media type string to examine."""

    prefix: str
    """The expected prefix."""

    def __str__(self) -> str:
        """Provide a human-readable description of the error."""
        return f"The expected prefix {self.prefix!r} is not present in {self.value!r}"


@dataclasses.dataclass
class NoSuffixError(defs.MTVError):
    """The expected suffix was not found."""

    value: str
    """The media type string to examine."""

    suffix: str
    """The expected suffix."""

    def __str__(self) -> str:
        """Provide a human-readable description of the error."""
        return f"The expected suffix {self.suffix!r} is not present in {self.value!r}"


@dataclasses.dataclass
class NoVersionError(defs.MTVError):
    """There was no '.v' component."""

    value: str
    """The media type string to examine."""

    prefix: str
    """The expected prefix."""

    suffix: str
    """The expected suffix."""

    def __str__(self) -> str:
        """Provide a human-readable description of the error."""
        return (
            f"No '.v' component in {self.value!r} after removing "
            f"the {self.prefix!r} prefix and the {self.suffix!r} suffix"
        )


@dataclasses.dataclass
class NonIntegerComponentError(defs.MTVError):
    """A version component was not a decimal integer."""

    value: str
    """The media type string to examine."""

    comp: str
    """The version component."""

    def __str__(self) -> str:
        """Provide a human-readable description of the error."""
        return f"The {self.comp!r} component of {self.value!r} is not an unsigned decimal integer"


@dataclasses.dataclass
class TwoComponentsExpectedError(defs.MTVError):
    """The version part did not consist of two components."""

    value: str
    """The media type string to examine."""

    version_part: str
    """The version part of the string."""

    def __str__(self) -> str:
        """Provide a human-readable description of the error."""
        return (
            f"The {self.version_part!r} part of {self.value!r} does not "
            f"consist of two dot-separated parts"
        )


@dataclasses.dataclass
class WrongTypeChildError(defs.MTVError):
    """The expected TOML, JSON, etc. value did not contain a table/object where we expected one."""

    path: list[str]
    """The path where we expected a child."""

    tag: str
    """The type of the child we expected to see."""

    name: str
    """The name of the expected child."""

    def __str__(self) -> str:
        """Provide a human-readable description of the error."""
        level = pathstr(self.path)
        return f"Expected the parsed value to have a '{self.name}' {self.tag} at {level}"


def pathstr(elpath: list[str]) -> str:
    """Return the string representation of a path within a document."""
    if not elpath:
        return "top level"

    joined: Final = ".".join(elpath)
    return f"[{joined}]"


def rm_part(
    value: str,
    part: str,
    rm_func: Callable[[str, str], str],
    error_class: type[NoPrefixError | NoSuffixError],
) -> str:
    """Remove a part of the version string if it is specified."""
    if not part:
        return value

    res: Final = rm_func(value, part)
    if res == value:
        raise error_class(value, part)

    return res


def extract(cfg: defs.Config, value: str) -> tuple[int, int]:
    """Extract the media type format version as a (major, minor) tuple."""

    def parse_int(comp: str) -> int:
        """Parse a version component into a base-10 integer."""
        if not RE_INT.match(comp):
            raise NonIntegerComponentError(value, comp)

        try:
            return int(comp, base=10)
        except ValueError as err:
            raise NonIntegerComponentError(value, comp) from err

    no_pfx: Final = rm_part(value, cfg.prefix, str.removeprefix, NoPrefixError)
    no_sfx: Final = rm_part(no_pfx, cfg.suffix, str.removesuffix, NoSuffixError)
    no_vdot: Final = no_sfx.removeprefix(".v")
    if no_vdot == no_sfx:
        raise NoVersionError(value, cfg.prefix, cfg.suffix)
    cfg.log.debug("Parsing the media type version part %(vers)r", {"vers": no_vdot})

    match no_vdot.split("."):
        case [major, minor]:
            return parse_int(major), parse_int(minor)

        case _:
            raise TwoComponentsExpectedError(value, no_vdot)


def extract_from_table(cfg: defs.Config, raw: dict[str, Any], path: list[str]) -> tuple[int, int]:
    """Recurse into a dict, extract the media type version string, parse it."""
    current_path: list[str] = []
    for comp in path:
        next_raw = raw.get(comp)
        if not isinstance(next_raw, dict):
            raise WrongTypeChildError(current_path, "table", comp)

        raw = next_raw
        current_path.append(comp)

    media_type: Final = raw.get("mediaType")
    if not isinstance(media_type, str):
        raise WrongTypeChildError(path, "string", "mediaType")

    return extract(cfg, media_type)
