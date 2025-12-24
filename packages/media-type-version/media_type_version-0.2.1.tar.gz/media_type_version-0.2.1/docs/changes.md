<!--
SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
SPDX-License-Identifier: BSD-2-Clause
-->

# Changelog

All notable changes to the media-type-version project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2025-12-20

### Semi-incompatible changes

- Python implementation:
    - `mtv-extract`:
        - move the CLI dependencies to a separate `cli` dependency group;
          this means e.g. packaging systems must now install them separately
- Rust implementation:
    - `media-type-version`:
        - switch to versioned names for the `facet` unstable features so
          that, with the 0.32.x addition, the features are now named
          `facet030-unstable` and `facet032-unstable`
        - switch to a versioned name for the `json-serialzero0-unstable` feature

### Fixes

- Python implementation:
    - test suite:
        - drop the unneeded `uvoxen` dependency from the `unit-tests` group
- Rust implementation:
    - `mtv-extract`:
        - pin the version of the `media-type-version` dependency
- Documentation:
    - bump some dependency versions for `uv --resolution=lowest`

### Additions

- Python implementation:
    - test suite:
        - also run `ty` 0.0.4 for type checking
- Rust implementation:
    - `media-type-version`:
        - add the `facet032-unstable` feature

### Other changes

- Python implementation:
    - `mtv-extract`:
        - allow `cappa` 0.31.x with no changes
    - test suite:
        - use `ruff` 0.14.10 with no changes
        - allow `pytest` 9.x, invoke it with the `--strict` option
- Rust implementation:
    - `media-type-version`:
        - internally import `facet` 0.30.x as `facet030`, `facet` 0.32.x as
          `facet032`, and `serialzero` 0.x as `serialzero0`
    - test suite:
        - use `facet-testhelpers` 0.32.x with no changes
        - drop the isolated feature sets for `cargo-feature-combinations`
- Documentation:
    - allow `mkdocstrings` 1.x and `mkdocstrings-python` 2.x

## [0.2.0] - 2025-10-09

### Incompatible changes

- The `mtv-extract` command-line tool now expects a subcommand; both the Python and
  Rust implementations currently support the `features`, `json`, `lines`, and `toml`
  subcommands.

### Fixes

- Rust implementation:
    - `media-type-version`:
        - expose the `ConfigBuilder` struct at top level
        - pin the versions of the `facet` dependencies
    - `mtv-extract`:
        - bump the version of the `feature-check` test dependency to 2.3.0 for
          `-Zminimal-versions`

### Additions

- Python implementation:
    - `media-type-version`:
        - add the `extract_from_table()` function
    - `mtv-extract`:
        - switch to subcommands; implement `features`, `json`, `lines`, and `toml`
- Rust implementation:
    - `media-type-version`:
        - add configuration for the `cargo-feature-combinations` test runner
        - add the `Table` trait and the `extract_from_table()` function enabled by
          the new `extract-from-table` feature
        - implement the `Table` trait for `boml::table::TomlTable` enabled by
          the new `toml-boml1` feature
        - implement the `Table` trait for `serialzero::JsonValue` enabled by
          the new `json-serialzero-unstable` feature
    - `mtv-extract`:
        - switch to subcommands; implement `features`, `json`, `lines`, and `toml`
        - add a trivial stdin unit test
        - run the Python test framework against the built `mtv-extract` executable

### Other changes

- Python implementation:
    - bump the `uvoxen` dependency to 0.2.2 to support our version 0.2.x
    - use `ruff` 0.14.0 and `reuse` 6.x with no changes
    - allow `cappa` up to 0.30.x and `mkdocstrings` up to 0.30.x with no changes
- Rust implementation:
    - `media-type-version`:
        - allow `facet` up to 0.29.x
    - `mtv-extract`:
        - allow `facet` up to 0.29.x

## [0.1.3] - 2025-06-16

### Semi-incompatible changes

- Rust implementation:
    - `media-type-version`:
        - make the `defs` module private; we expose everything we should via `pub use`

### Fixes

- Rust implementation:
    - `mtv-extract`:
        - fix the invalid "media type" Cargo metadata keyword
- Documentation:
    - fix the download URLs

### Additions

- Rust implementation:
    - `media-type-version`:
        - expose the `OwnedError` type at crate top-level
        - expose the source error for `Error::UIntExpected`
        - add a unit test for the `Facet` trait

### Other changes

- Python implementation:
    - refresh the `uv.lock` file
- Rust implementation:
    - `media-type-version`:
        - use `facet` 0.27.13 with no changes
    - push the `run-clippy.sh` test tool down into the `rust/` subdirectory
    - refresh the `Cargo.lock` file

## [0.1.2] - 2025-06-08

### Additions

- Rust implementation:
    - `media-type-version`:
        - add the documentation base URL for the `crates-io` index

### Other changes

- Python implementation:
    - allow `cappa` 0.28 with no changes
    - test suite:
        - use `uvoxen` 0.2 and switch to a `mediaType` format version
        - use `ruff` 0.11.13 with no changes
- Rust implementation:
    - `media-type-version`:
        - use `facet` 0.27.12 for the `facet-unstable` feature
        - minor refactoring
    - `mtv-extract`:
        - switch from `anyhow` to `eyre`
    - test suite:
        - switch from `anyhow` to `eyre`
        - switch from `test-log` to `facet-testhelpers`

## [0.1.1] - 2025-05-23

### Fixes

- Rust implementation:
    - replace the invalid "media type" crate keyword with "media-type"

### Other changes

- Python implementation:
    - refresh the `uv.lock` file
- Rust implementation:
    - constify some missed functions

## [0.1.0] - 2025-05-23

### Started

- First public release.

[Unreleased]: https://gitlab.com/ppentchev/media-type-version/-/compare/release%2F0.2.1...main
[0.2.1]: https://gitlab.com/ppentchev/media-type-version/-/compare/release%2F0.2.0...release/0.2.1
[0.2.0]: https://gitlab.com/ppentchev/media-type-version/-/compare/release%2F0.1.3...release/0.2.0
[0.1.3]: https://gitlab.com/ppentchev/media-type-version/-/compare/release%2F0.1.2...release/0.1.3
[0.1.2]: https://gitlab.com/ppentchev/media-type-version/-/compare/release%2F0.1.1...release/0.1.2
[0.1.1]: https://gitlab.com/ppentchev/media-type-version/-/compare/release%2F0.1.0...release/0.1.1
[0.1.0]: https://gitlab.com/ppentchev/media-type-version/-/tags/release%2F0.1.0
