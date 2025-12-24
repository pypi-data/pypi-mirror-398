# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Make sure that `media-type-version run` starts up at least."""

from __future__ import annotations

import dataclasses
import itertools
import json
import os
import subprocess  # noqa: S404
import sys
import tempfile
import typing

import feature_check
import pytest
import tomli_w
from feature_check import parser as fc_parser

from media_type_version import defs

from . import util


if typing.TYPE_CHECKING:
    from typing import Final


@dataclasses.dataclass
class GlobalCache:
    """Some values cached between test executions."""

    test_prog: list[str]
    """The test program to run."""

    features: dict[str, feature_check.Version]
    """The features supported by the test program."""

    def __init__(self) -> None:
        """Examine the program to be tested."""
        env_prog: Final = os.environ.get("TEST_MTV_EXTRACT_PROG")
        self.test_prog = (
            [env_prog] if env_prog is not None else [sys.executable, "-m", "media_type_version"]
        )

        output: Final = subprocess.check_output([*self.test_prog, "features"], encoding="UTF-8")  # noqa: S603
        match output.splitlines():
            case [first]:
                features_list: Final = first.removeprefix("Features: ")
                print(f"Got features line {first!r}")
                assert features_list != first, "Expected a 'Features: ' prefix"
                print(f"Got features list {features_list!r}")
                self.features = fc_parser.parse_features_line(features_list)

            case _:
                raise RuntimeError(repr((self.test_prog, output)))


_CACHE: Final = GlobalCache()


def get_prog() -> list[str]:
    """Determine the test program to run."""
    return _CACHE.test_prog


def get_features() -> dict[str, feature_check.Version]:
    """Obtain the list of features supported by the tested program."""
    return _CACHE.features


def get_feature(name: str) -> feature_check.Version | None:
    """Get the specified program feature's version if it is available."""
    return get_features().get(name)


def assert_cmd_lines() -> None:
    """Make sure the "lines" feature is always supported."""
    assert get_feature("cmd-lines") is not None


def test_features() -> None:
    """Make sure that `mtv-extract features` works."""
    features: Final = get_features()
    assert features["media-type-version"] == feature_check.parse_version(
        defs.FEATURES["media-type-version"],
    )


def get_lines_output(prog: list[str], *, contents: str, from_stdin: bool) -> str:
    """Run `mtv-extract lines`, return the output."""
    if from_stdin:
        return subprocess.check_output(  # noqa: S603
            [*prog, "lines", "-p", util.PREFIX, "-s", util.SUFFIX, "--", "-"],
            encoding="UTF-8",
            input=contents,
        )

    with tempfile.NamedTemporaryFile(
        encoding="UTF-8",
        mode="wt",
        prefix="mtv-test-",
        suffix=".txt",
    ) as tempf_obj:
        print(contents, file=tempf_obj, end="")
        tempf_obj.flush()
        return subprocess.check_output(  # noqa: S603
            [*prog, "lines", "-p", util.PREFIX, "-s", util.SUFFIX, "--", tempf_obj.name],
            encoding="UTF-8",
        )


@pytest.mark.parametrize(
    ("from_stdin", "ver_tuple"),
    itertools.product([False, True], util.VERSIONS),
)
def test_lines_one_by_one(*, from_stdin: bool, ver_tuple: tuple[int, int]) -> None:
    """Make sure that `mtv-extract lines -` can parse a string."""
    assert_cmd_lines()
    major, minor = ver_tuple
    output: Final = get_lines_output(
        get_prog(),
        contents=util.build_media_type(ver_tuple),
        from_stdin=from_stdin,
    )
    assert output == f"{major}\t{minor}\n"


@pytest.mark.parametrize("from_stdin", [False, True])
def test_lines_all_at_once(*, from_stdin: bool) -> None:
    """Make sure that `mtv-extract lines -` can parse several strings at once."""
    assert_cmd_lines()
    output: Final = get_lines_output(
        get_prog(),
        contents="".join(util.build_media_type(ver) + "\n" for ver in util.VERSIONS),
        from_stdin=from_stdin,
    )
    assert output == "".join(f"{major}\t{minor}\n" for major, minor in util.VERSIONS)


def get_toml_output(prog: list[str], *, contents: str, from_stdin: bool, path: list[str]) -> str:
    """Run `mtv-extract lines`, return the output."""
    opts_path: Final = ["-P", ".".join(path)] if path else []
    if from_stdin:
        return subprocess.check_output(  # noqa: S603
            [*prog, "-v", "toml", "-p", util.PREFIX, "-s", util.SUFFIX, *opts_path, "--", "-"],
            encoding="UTF-8",
            input=contents,
        )

    with tempfile.NamedTemporaryFile(
        encoding="UTF-8",
        mode="wt",
        prefix="mtv-test-",
        suffix=".txt",
    ) as tempf_obj:
        print(contents, file=tempf_obj, end="")
        tempf_obj.flush()
        return subprocess.check_output(  # noqa: S603
            [*prog, "toml", "-p", util.PREFIX, "-s", util.SUFFIX, *opts_path, "--", tempf_obj.name],
            encoding="UTF-8",
        )


@pytest.mark.skipif(get_feature("cmd-toml") is None, reason="No cmd-toml support")
@pytest.mark.parametrize(
    ("from_stdin", "path", "ver_tuple"),
    itertools.product([False, True], util.PATHS, util.VERSIONS),
)
def test_toml_one_by_one(*, from_stdin: bool, path: list[str], ver_tuple: tuple[int, int]) -> None:
    """Make sure that `mtv-extract lines -` can parse a string."""
    major, minor = ver_tuple
    contents: Final = tomli_w.dumps(util.build_document(path, ver_tuple))
    output: Final = get_toml_output(
        get_prog(),
        contents=contents,
        from_stdin=from_stdin,
        path=path,
    )
    assert output == f"{major}\t{minor}\n"


@pytest.mark.skipif(get_feature("cmd-toml") is None, reason="No cmd-toml support")
def test_toml_pyproject() -> None:
    """Read the two version strings from the `pyproject.toml` file."""
    output_publync: Final = subprocess.check_output(  # noqa: S603
        [
            *get_prog(),
            "-v",
            "toml",
            "-P",
            "tool.publync",
            "-p",
            "vnd.ringlet.misc.publync.config/publync",
            "-s",
            "+toml",
            "pyproject.toml",
        ],
        encoding="UTF-8",
    )
    assert output_publync == "0\t1\n"

    output_uvoxen: Final = subprocess.check_output(  # noqa: S603
        [
            *get_prog(),
            "-v",
            "toml",
            "-P",
            "tool.uvoxen",
            "-p",
            "vnd.ringlet.devel.uvoxen.config/uvoxen",
            "-s",
            "+toml",
            "pyproject.toml",
        ],
        encoding="UTF-8",
    )
    assert output_uvoxen == "0\t3\n"


def get_json_output(prog: list[str], *, contents: str, from_stdin: bool, path: list[str]) -> str:
    """Run `mtv-extract lines`, return the output."""
    opts_path: Final = ["-P", ".".join(path)] if path else []
    if from_stdin:
        return subprocess.check_output(  # noqa: S603
            [*prog, "-v", "json", "-p", util.PREFIX, "-s", util.SUFFIX, *opts_path, "--", "-"],
            encoding="UTF-8",
            input=contents,
        )

    with tempfile.NamedTemporaryFile(
        encoding="UTF-8",
        mode="wt",
        prefix="mtv-test-",
        suffix=".txt",
    ) as tempf_obj:
        print(contents, file=tempf_obj, end="")
        tempf_obj.flush()
        return subprocess.check_output(  # noqa: S603
            [*prog, "json", "-p", util.PREFIX, "-s", util.SUFFIX, *opts_path, "--", tempf_obj.name],
            encoding="UTF-8",
        )


@pytest.mark.skipif(get_feature("cmd-json") is None, reason="No cmd-json support")
@pytest.mark.parametrize(
    ("from_stdin", "path", "ver_tuple"),
    itertools.product([False, True], util.PATHS, util.VERSIONS),
)
def test_json_one_by_one(*, from_stdin: bool, path: list[str], ver_tuple: tuple[int, int]) -> None:
    """Make sure that `mtv-extract lines -` can parse a string."""
    major, minor = ver_tuple
    contents: Final = json.dumps(util.build_document(path, ver_tuple))
    output: Final = get_json_output(
        get_prog(),
        contents=contents,
        from_stdin=from_stdin,
        path=path,
    )
    assert output == f"{major}\t{minor}\n"
