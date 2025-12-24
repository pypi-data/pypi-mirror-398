# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Common definitions for the media-type-version library."""

from __future__ import annotations

import dataclasses
import typing


if typing.TYPE_CHECKING:
    import logging
    from typing import Final


VERSION: Final = "0.2.1"
"""The media-type-version library version, semver-like."""


FEATURES: Final = {
    "media-type-version": VERSION,
    "cmd-features": "0.1",
    "cmd-json": "0.1",
    "cmd-lines": "0.1",
    "cmd-toml": "0.1",
    "extract": "0.1",
    "extract-from-table": "0.1",
}
"""The list of features supported by the media-type-version library."""


@dataclasses.dataclass
class MTVError(Exception):
    """An error that occurred while parsing the media type string."""

    def __str__(self) -> str:
        """Provide a human-readable description of the error."""
        return f"Could not parse a media type string: {self!r}"


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration for the media-type-version library."""

    log: logging.Logger
    """The logger to send diagnostic, informational, and error messages to."""

    prefix: str
    """The prefix to expect in the media type string."""

    suffix: str
    """The optional suffix in the media type string."""
