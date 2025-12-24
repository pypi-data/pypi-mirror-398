# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Helper functions for the `media-type-version` Python unit tests."""

from __future__ import annotations

import functools
import logging
import typing

import pytest

import media_type_version


if typing.TYPE_CHECKING:
    from typing import Any, Final


PREFIX: Final = "vnd.ringlet.something/else"
"""The prefix for the media type string before the .vX.Y part."""

SUFFIX: Final = "+toml"
"""The expected suffix."""

VERSIONS: Final = [
    (42, 616),
    (0, 0),
    (0, 1),
    (3, 0),
]
"""The version combinations to test with."""

PATHS: Final[list[list[str]]] = [
    [],
    ["prog"],
    ["tool", "media"],
]
"""The paths to put the `mediaType` element in for TOML, JSON, et al tests."""


@functools.lru_cache
def build_test_config() -> media_type_version.Config:
    """Build the runtime configuration for parsing our test media type strings."""
    return media_type_version.Config(log=logging.getLogger(), prefix=PREFIX, suffix=SUFFIX)


@functools.lru_cache
def build_media_type(ver_tuple: tuple[int, int]) -> str:
    """Build a media type string with our test prefix and suffix."""
    return f"{PREFIX}.v{ver_tuple[0]}.{ver_tuple[1]}{SUFFIX}"


def build_document(
    path: list[str],
    ver_tuple: tuple[int, int],
) -> dict[str, Any]:  # ty: ignore[invalid-return-type]  # GitHub ty #1112
    """Build a document to be encoded into TOML, JSON, etc."""
    match path:
        case []:
            return {"mediaType": build_media_type(ver_tuple), "media-type": [1, 2, 7]}

        case [single]:
            return {
                single: {"nothing": 0, "mediaType": build_media_type(ver_tuple)},
                "something": "else",
            }

        case [first, second]:
            return {
                first: {
                    "hello": ["there"],
                    second: {"mediatype": "knock-knock", "mediaType": build_media_type(ver_tuple)},
                },
            }

        case _:
            pytest.fail(f"Internal error: {path=!r}")
