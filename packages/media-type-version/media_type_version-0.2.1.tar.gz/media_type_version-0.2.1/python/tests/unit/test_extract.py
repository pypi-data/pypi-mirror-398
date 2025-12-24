# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Test the various extraction routines in the `media-type-version` library."""

from __future__ import annotations

import itertools
import typing

import pytest

import media_type_version

from . import util


if typing.TYPE_CHECKING:
    from typing import Final


@pytest.mark.parametrize(
    ("path", "ver_tuple"),
    itertools.product(util.PATHS, util.VERSIONS),
)
def test_extract_from_table(*, path: list[str], ver_tuple: tuple[int, int]) -> None:
    """Make sure we can extract the media type version from a TOML document."""
    document: Final = util.build_document(path, ver_tuple)
    res: Final = media_type_version.extract_from_table(util.build_test_config(), document, path)
    assert res == ver_tuple
