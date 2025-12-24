# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Helper functions for the media_type_version library."""

from __future__ import annotations

import functools
import logging
import sys
import typing


if typing.TYPE_CHECKING:
    from typing import Final


@functools.lru_cache
def build_logger(*, quiet: bool = False, verbose: bool = False) -> logging.Logger:
    """Build a logger that outputs to the standard output and error streams.

    Messages of level `WARNING` and higher go to the standard error stream.
    If `quiet` is false, messages of level `INFO` also go to the standard error stream.
    If `verbose` is true, messages of level `DEBUG` also go to the standard error stream.
    """
    logger: Final = logging.getLogger("media_type_version")
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO)
    logger.propagate = False

    diag_handler: Final = logging.StreamHandler(sys.stderr)
    diag_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)
    if not quiet:
        diag_handler.addFilter(lambda rec: rec.levelno != logging.INFO)
    logger.addHandler(diag_handler)

    if not quiet:
        info_handler: Final = logging.StreamHandler(sys.stderr)
        info_handler.setLevel(logging.INFO)
        info_handler.addFilter(lambda rec: rec.levelno == logging.INFO)
        logger.addHandler(info_handler)

    return logger
