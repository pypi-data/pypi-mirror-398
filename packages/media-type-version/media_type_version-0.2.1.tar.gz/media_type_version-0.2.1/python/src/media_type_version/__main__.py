# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Do things, or do other things."""

from __future__ import annotations

import dataclasses
import json
import pathlib
import sys
import tomllib
import typing
from typing import Annotated

import cappa

from . import defs
from . import impl
from . import util


if typing.TYPE_CHECKING:
    from typing import Any, Final


@cappa.command(name="features")
@dataclasses.dataclass(frozen=True)
class CmdFeatures:
    """List the features supported by the program."""


@cappa.command(name="json")
@dataclasses.dataclass(frozen=True)
class CmdJSON:
    """Extract the format version from a JSON document."""

    prefix: Annotated[str, cappa.Arg(short=True, long=True)]
    """The prefix to expect in the media type string."""

    files: list[str]
    """The files to parse; `-` denotes the standard input stream."""

    suffix: Annotated[str, cappa.Arg(short=True, long=True)] = ""
    """The optional suffix in the media type string."""

    path: Annotated[str | None, cappa.Arg(short="-P", long=True)] = None
    """The dot-separated path to the JSON document's section to examine."""


@cappa.command(name="lines")
@dataclasses.dataclass(frozen=True)
class CmdLines:
    """Extract the format version from successive lines of text."""

    prefix: Annotated[str, cappa.Arg(short=True, long=True)]
    """The prefix to expect in the media type string."""

    files: list[str]
    """The files to parse; `-` denotes the standard input stream."""

    suffix: Annotated[str, cappa.Arg(short=True, long=True)] = ""
    """The optional suffix in the media type string."""


@cappa.command(name="toml")
@dataclasses.dataclass(frozen=True)
class CmdTOML:
    """Extract the format version from a TOML document."""

    prefix: Annotated[str, cappa.Arg(short=True, long=True)]
    """The prefix to expect in the media type string."""

    files: list[str]
    """The files to parse; `-` denotes the standard input stream."""

    suffix: Annotated[str, cappa.Arg(short=True, long=True)] = ""
    """The optional suffix in the media type string."""

    path: Annotated[str | None, cappa.Arg(short="-P", long=True)] = None
    """The dot-separated path to the TOML document's section to examine."""


@dataclasses.dataclass(frozen=True)
class MtvExtract:
    """Extract the format version from a media type string."""

    quiet: Annotated[bool, cappa.Arg(short=True, long=True)]
    """Quiet operation; only display warnings and error messages."""

    verbose: Annotated[bool, cappa.Arg(short=True, long=True)]
    """Verbose operation; display diagnostic messages."""

    cmd: cappa.Subcommands[CmdFeatures | CmdJSON | CmdLines | CmdTOML]
    """What to do, what to do?"""


def do_parse_lines(cfg: defs.Config, fname: str, contents: str) -> None:
    """Read media type strings from a file, parse them."""
    for line in contents.splitlines():
        try:
            ver_major, ver_minor = impl.extract(cfg, line)
        except defs.MTVError as err:
            sys.exit(f"Could not parse a {fname} line: {line!r}: {err}")

        print(f"{ver_major}\t{ver_minor}")


def parse_lines(cfg: defs.Config, fname: str) -> None:
    """Parse a single file containing media type strings."""
    if fname == "-":
        cfg.log.info("Reading from the standard input stream")
        contents = sys.stdin.read()
        fname = "(standard input)"
    else:
        cfg.log.info("Reading the contents of %(fname)s", {"fname": fname})
        try:
            contents = pathlib.Path(fname).read_text(encoding="UTF-8")
        except OSError as err:
            sys.exit(f"Could not read {fname}: {err}")

    cfg.log.debug("Read %(count)d characters", {"count": len(contents)})
    do_parse_lines(cfg, fname, contents)


def descend_and_parse(cfg: defs.Config, fname: str, path: list[str], raw: dict[str, Any]) -> None:
    """Parse the `mediaType` field of a TOML document."""
    try:
        ver_major, ver_minor = impl.extract_from_table(cfg, raw, path)
    except defs.MTVError as err:
        level = impl.pathstr([*path, "mediaType"])
        sys.exit(f"Could not parse the {level} value at {fname}: {err}")

    print(f"{ver_major}\t{ver_minor}")


def parse_json(cfg: defs.Config, fname: str, path: list[str]) -> None:
    """Parse the `mediaType` field of a JSON document read from a file or the standard input."""
    if fname == "-":
        cfg.log.info("Reading from the standard input stream")
        contents = sys.stdin.read()
        fname = "(standard input)"
    else:
        cfg.log.info("Reading the contents of %(fname)s", {"fname": fname})
        try:
            contents = pathlib.Path(fname).read_text(encoding="UTF-8")
        except OSError as err:
            sys.exit(f"Could not read {fname}: {err}")

    cfg.log.debug("Read %(count)d characters", {"count": len(contents)})
    try:
        raw: Final = json.loads(contents)
    except ValueError as err:
        sys.exit(f"Could not parse {fname} as valid JSON: {err}")
    if not isinstance(raw, dict):
        sys.exit(f"Expected the TOML document at {fname} to be an object at top level")
    descend_and_parse(cfg, fname, path, raw)


def parse_toml(cfg: defs.Config, fname: str, path: list[str]) -> None:
    """Parse the `mediaType` field of a TOML document read from a file or the standard input."""
    if fname == "-":
        cfg.log.info("Reading from the standard input stream")
        contents = sys.stdin.read()
        fname = "(standard input)"
    else:
        cfg.log.info("Reading the contents of %(fname)s", {"fname": fname})
        try:
            contents = pathlib.Path(fname).read_text(encoding="UTF-8")
        except OSError as err:
            sys.exit(f"Could not read {fname}: {err}")

    cfg.log.debug("Read %(count)d characters", {"count": len(contents)})
    try:
        raw: Final = tomllib.loads(contents)
    except ValueError as err:
        sys.exit(f"Could not parse {fname} as valid TOML: {err}")
    if not isinstance(raw, dict):
        sys.exit(f"Expected the TOML document at {fname} to be a table at top level")
    descend_and_parse(cfg, fname, path, raw)


def show_features() -> None:
    """List the features supported by the program."""
    print(
        f"Features: {' '.join(f'{name}={value}' for name, value in sorted(defs.FEATURES.items()))}",
    )


def main() -> None:
    """Parse command-line options, read files, extract data."""
    args: Final = cappa.parse(MtvExtract, completion=False)
    match args.cmd:
        case CmdFeatures():
            show_features()

        case CmdJSON(prefix, files, suffix, path):
            cfg = defs.Config(
                log=util.build_logger(quiet=args.quiet, verbose=args.verbose),
                prefix=prefix,
                suffix=suffix,
            )
            for fname in files:
                parse_json(cfg, fname, path.split(".") if path else [])

        case CmdLines(prefix, files, suffix):
            cfg = defs.Config(
                log=util.build_logger(quiet=args.quiet, verbose=args.verbose),
                prefix=prefix,
                suffix=suffix,
            )
            for fname in files:
                parse_lines(cfg, fname)

        case CmdTOML(prefix, files, suffix, path):
            cfg = defs.Config(
                log=util.build_logger(quiet=args.quiet, verbose=args.verbose),
                prefix=prefix,
                suffix=suffix,
            )
            for fname in files:
                parse_toml(cfg, fname, path.split(".") if path else [])

        case _:
            raise RuntimeError(repr(args))


if __name__ == "__main__":
    main()
