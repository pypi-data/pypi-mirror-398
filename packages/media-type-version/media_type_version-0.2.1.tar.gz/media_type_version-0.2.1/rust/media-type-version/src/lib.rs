#![deny(missing_docs)]
#![deny(clippy::missing_docs_in_private_items)]
#![no_std]
// SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
// SPDX-License-Identifier: BSD-2-Clause
//! media-type-version - extract the format version from a media type string
//!
//! ## Overview
//!
//! The `media-type-version` library is designed to be used as the first step in
//! parsing structured data, e.g. configuration files, serialized classes, etc.
//! The caller extracts the media type string (e.g. a JSON `"mediaType": "..."` key) and
//! passes it in for parsing.
//! The caller then decides what to do with the extracted version information -
//! is this version supported, what fields are expected to be there, should any
//! extraneous fields produce errors, and so on.
//!
//! The main entry point is the [`extract`] function which is passed two parameters:
//! a [`Config`] object defining the expected media type prefix and suffix, and
//! a media type string to parse.
//! On success, it returns a [`Version`] object, basically a tuple of a major and
//! minor version numbers.
//!
//! ## Media type string format
//!
//! The media type string is expected to be in a `<prefix>.vX.Y<suffix>` format, with
//! a fixed prefix and suffix.
//! The prefix will usually be a vendor-specific media type.
//! The version part consists of two unsigned integer numbers.
//! The suffix, if used, may correspond to the file format.
//!
//! A sample media type string identifying a TOML configuration file for
//! a text-processing program could be
//! `vnd.ringlet.textproc.publync.config/publync.v0.2+toml`
//!
//! ## Crate features
//!
//! - `alloc` - enable the [`Error::into_owned_error`] method
//! - `extract-from-table` - enable the [`Table`] trait and the [`extract_from_table`] method
//! - `facet030-unstable` - [`Config`] and [`Version`] will derive from `Facet` so that
//!   they can be examined or serialized that way.
//! - `facet032-unstable` - [`Config`] and [`Version`] will derive from `Facet` so that
//!   they can be examined or serialized that way.
//! - `toml-boml1` - implement the [`Table`] trait for the `TomlTable` type from
//!   the `boml` crate so that [`extract_from_table`] may be used for values of that type.
//!
//! Note that the `facet032-unstable` feature builds the `facet` crate with
//! its `alloc` feature enabled regardless of whether the `alloc` feature is
//! enabled for the `media-type-version` crate itself.

#![doc(html_root_url = "https://docs.rs/media-type-version/0.2.1")]
#![expect(clippy::pub_use, reason = "re-export common symbols")]

use core::str::FromStr as _;

use log::debug;

#[cfg(feature = "toml-boml1")]
use boml::prelude::TomlGetError as TomlBomlGetError;

#[cfg(feature = "toml-boml1")]
use boml::table::TomlTable as TomlBomlTable;

#[cfg(all(feature = "facet030-unstable", not(feature = "facet032-unstable")))]
extern crate facet030 as facet;

#[cfg(feature = "facet032-unstable")]
extern crate facet032 as facet;

#[cfg(feature = "json-serialzero0-unstable")]
use serialzero0::JsonValue;

mod defs;

pub use defs::{Config, ConfigBuilder, Error, Version};

#[cfg(feature = "alloc")]
pub use defs::OwnedError;

/// The number of features that are always defined.
const FEATURES_COUNT_BASE: usize = 2;

#[cfg(not(feature = "extract-from-table"))]
/// Do not add 1 if `extract-from-table` is not enabled.
const FEATURES_COUNT_EXTRACT_FROM_TABLE: usize = 0;

#[cfg(feature = "extract-from-table")]
/// Add 1 if `extract-from-table` is enabled.
const FEATURES_COUNT_EXTRACT_FROM_TABLE: usize = 1;

/// The number of currently enabled features.
const FEATURES_COUNT: usize = FEATURES_COUNT_BASE + FEATURES_COUNT_EXTRACT_FROM_TABLE;

/// The features supported by this version of the library.
pub const FEATURES: [(&str, &str); FEATURES_COUNT] = [
    ("media-type-version", env!("CARGO_PKG_VERSION")),
    ("extract", "0.1"),
    #[cfg(feature = "extract-from-table")]
    ("extract-from-table", "0.1"),
];

/// Extract the format version from a media type string.
///
/// # Errors
///
/// [`Error::NoPrefix`], [`Error::NoSuffix`], [`Error::NoVDot`] if
/// the media type string does not contain the required string parts at all.
///
/// [`Error::TwoComponentsExpected`] if the version part does not consist of
/// exactly two dot-separated components.
///
/// [`Error::UIntExpected`] if those components are not unsigned integers.
#[inline]
pub fn extract<'data>(
    cfg: &'data Config<'data>,
    value: &'data str,
) -> Result<Version, Error<'data>> {
    debug!(
        "Parsing a media type string '{value}', expecting prefix '{prefix}' and suffix '{suffix}'",
        prefix = cfg.prefix(),
        suffix = cfg.suffix()
    );
    let no_prefix = value
        .strip_prefix(cfg.prefix())
        .ok_or_else(|| Error::NoPrefix(value, cfg.prefix()))?;
    let no_suffix = no_prefix
        .strip_suffix(cfg.suffix())
        .ok_or_else(|| Error::NoSuffix(value, cfg.suffix()))?;
    let no_vdot = no_suffix
        .strip_prefix(".v")
        .ok_or(Error::NoVDot(no_suffix))?;
    let (first, second) = {
        let mut parts_it = no_vdot.split('.');
        let first = parts_it.next().ok_or(Error::TwoComponentsExpected(value))?;
        let second = parts_it.next().ok_or(Error::TwoComponentsExpected(value))?;
        if parts_it.next().is_some() {
            return Err(Error::TwoComponentsExpected(value));
        }
        (first, second)
    };
    let major = u32::from_str(first).map_err(|err| Error::UIntExpected(value, first, err))?;
    let minor = u32::from_str(second).map_err(|err| Error::UIntExpected(value, second, err))?;
    Ok(Version::from((major, minor)))
}

#[cfg(feature = "extract-from-table")]
/// A hierarchical structure that may contain at least child tables and strings.
pub trait Table<'data> {
    /// Is this particular element a key/value table?
    fn is_table(&'data self) -> bool;

    /// Get the child table with the specified key.
    ///
    /// # Errors
    ///
    /// [`Error::TableNoChild`] if there is no child by that name.
    fn get_child_table(&'data self, name: &'data str) -> Result<&'data Self, Error<'data>>;

    /// Get the child string slice with the specified key.
    ///
    /// # Errors
    ///
    /// [`Error::TableNoChild`] if there is no child by that name.
    fn get_child_string(&'data self, name: &'data str) -> Result<&'data str, Error<'data>>;
}

#[cfg(feature = "extract-from-table")]
/// Extract the media type version from a hierarchical data structure.
///
/// # Errors
///
/// [`Error::TableNotTable`] if either the top-level element or something that still has
/// remaining path components is not a table.
///
/// [`Error::TableNoChild`] if some of the path components does not exist.
#[inline]
pub fn extract_from_table<'data, T>(
    cfg: &'data Config<'data>,
    mut value: &'data T,
    path: &'data [&'data str],
) -> Result<Version, Error<'data>>
where
    T: Table<'data>,
{
    if !value.is_table() {
        return Err(Error::TableNotTable);
    }
    value = path
        .iter()
        .try_fold(value, |current_value, comp| -> Result<&T, Error<'data>> {
            current_value.get_child_table(comp)
        })?;
    let media_type = value.get_child_string("mediaType")?;
    extract(cfg, media_type)
}

#[cfg(feature = "json-serialzero0-unstable")]
impl<'data> Table<'data> for JsonValue {
    #[inline]
    fn is_table(&self) -> bool {
        matches!(*self, Self::Object(_))
    }

    #[inline]
    fn get_child_table(&'data self, name: &'data str) -> Result<&'data Self, Error<'data>> {
        let Self::Object(ref map) = *self else {
            return Err(Error::TableNotTable);
        };
        map.get(name).ok_or(Error::TableNoChild(name))
    }

    #[inline]
    fn get_child_string(&'data self, name: &'data str) -> Result<&'data str, Error<'data>> {
        let Self::Object(ref map) = *self else {
            return Err(Error::TableNotTable);
        };
        let child = map.get(name).ok_or(Error::TableNoChild(name))?;
        let Self::String(ref value) = *child else {
            return Err(Error::TableNotTable);
        };
        Ok(value)
    }
}

#[cfg(feature = "toml-boml1")]
impl<'data> Table<'data> for TomlBomlTable<'data> {
    #[inline]
    fn is_table(&self) -> bool {
        true
    }

    #[inline]
    fn get_child_table(&'data self, name: &'data str) -> Result<&'data Self, Error<'data>> {
        self.get_table(name).map_err(|err| match err {
            TomlBomlGetError::InvalidKey => Error::TableNoChild(name),
            TomlBomlGetError::TypeMismatch(_, _) => Error::TableNotTable,
        })
    }

    #[inline]
    fn get_child_string(&'data self, name: &'data str) -> Result<&'data str, Error<'data>> {
        self.get_string(name).map_err(|err| match err {
            TomlBomlGetError::InvalidKey => Error::TableNoChild(name),
            TomlBomlGetError::TypeMismatch(_, _) => Error::TableNotTable,
        })
    }
}

#[cfg(test)]
mod tests {
    extern crate alloc;

    use alloc::format;
    use alloc::string::String;

    use eyre::{Result, WrapErr as _};
    use facet_testhelpers::test;

    #[cfg(feature = "facet030-unstable")]
    use facet_pretty030::FacetPretty as _;

    #[cfg(feature = "facet032-unstable")]
    use facet_pretty032::FacetPretty as _;

    use crate::{Config, Error, Version};

    /// The prefix and suffix to use for testing.
    static CFG: Config<'_> = Config::from_parts("this/and", "+that");

    #[cfg(any(feature = "facet030-unstable", feature = "facet032-unstable"))]
    fn pretty_res(res: &Result<Version, Error<'_>>) -> String {
        match *res {
            Ok(ref ver) => format!("OK: {ver}", ver = ver.pretty()),
            Err(ref err) => format!("Error: {err}"),
        }
    }

    #[cfg(not(any(feature = "facet030-unstable", feature = "facet032-unstable")))]
    fn pretty_res(res: &Result<Version, Error<'_>>) -> String {
        match *res {
            Ok(ref ver) => format!(
                "OK: Version {{ major: {major}, minor: {minor} }}",
                major = ver.major(),
                minor = ver.minor(),
            ),
            Err(ref err) => format!("Error: {err}"),
        }
    }

    /// Make sure [extract][crate::extract] fails on invalid prefix.
    #[test]
    fn extract_fail_no_prefix() {
        let res = crate::extract(&CFG, "nothing");
        assert!(
            matches!(res, Err(Error::NoPrefix(_, _))),
            "expected Error::NoPrefix, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails on invalid suffix.
    #[test]
    fn extract_fail_no_suffix() {
        let res = crate::extract(&CFG, "this/andnothing");
        assert!(
            matches!(res, Err(Error::NoSuffix(_, _))),
            "expected Error::NoSuffix, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails on missing "v.".
    #[test]
    fn extract_fail_no_vdot() {
        let res = crate::extract(&CFG, "this/andnothing+that");
        assert!(
            matches!(res, Err(Error::NoVDot(_))),
            "expected Error::NoVDot, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails if no two components.
    #[test]
    fn extract_fail_two_expected() {
        let res = crate::extract(&CFG, "this/and.vnothing+that");
        assert!(
            matches!(res, Err(Error::TwoComponentsExpected(_))),
            "expected Error::TwoComponentsExpected, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails if not unsigned integers.
    #[test]
    fn extract_fail_uint_expected() {
        let res_first = crate::extract(&CFG, "this/and.va.42+that");
        assert!(
            matches!(res_first, Err(Error::UIntExpected(_, _, _))),
            "expected Error::UIntExpected, got {res_first}",
            res_first = pretty_res(&res_first)
        );

        let res_second = crate::extract(&CFG, "this/and.v42.+that");
        assert!(
            matches!(res_second, Err(Error::UIntExpected(_, _, _))),
            "expected Error::UIntExpected, got {res_second}",
            res_second = pretty_res(&res_second)
        );
    }

    /// Make sure [extract][crate::extract] succeeds on trivial correct data.
    #[test]
    fn extract_ok() -> Result<()> {
        let ver = crate::extract(&CFG, "this/and.v616.42+that").context("extract")?;
        assert_eq!(ver.as_tuple(), (616, 42));
        Ok(())
    }
}
