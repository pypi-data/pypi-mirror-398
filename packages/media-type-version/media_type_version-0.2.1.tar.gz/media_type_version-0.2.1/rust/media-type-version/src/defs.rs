// SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
// SPDX-License-Identifier: BSD-2-Clause
//! Common definitions for the media-type-version library.

#[cfg(any(feature = "alloc", feature = "toml-boml1"))]
extern crate alloc;

use core::error::Error as CoreError;
use core::fmt::{Display, Error as FmtError, Formatter};
use core::num::ParseIntError;

#[cfg(feature = "alloc")]
use alloc::{borrow::ToOwned as _, string::String};

#[cfg(all(feature = "alloc", feature = "toml-boml1"))]
use alloc::format;

#[cfg(any(feature = "facet030-unstable", feature = "facet032-unstable"))]
use facet::Facet;

#[cfg(feature = "toml-boml1")]
use boml::TomlError;

/// An error that occurred while processing the media type string.
#[derive(Debug)]
#[non_exhaustive]
#[expect(clippy::error_impl_error, reason = "common enough convention")]
pub enum Error<'data> {
    /// No prefix specified for the config builder.
    BuildNoPrefix,

    /// Something went really wrong.
    Internal(u32),

    /// The media type did not have the specified prefix.
    NoPrefix(&'data str, &'data str),

    /// The media type did not have the specified suffix.
    NoSuffix(&'data str, &'data str),

    /// The media type did not have the ".v" part.
    NoVDot(&'data str),

    #[cfg(feature = "extract-from-table")]
    /// The hierarchical structure did not contain the specified element.
    TableNoChild(&'data str),

    #[cfg(feature = "extract-from-table")]
    /// The hierarchical structure contained something that was not a table.
    TableNotTable,

    #[cfg(feature = "toml-boml1")]
    /// Could not parse a TOML document.
    TomlParse(TomlError<'data>),

    /// The media type's version part did not consist of two dot-separated components.
    TwoComponentsExpected(&'data str),

    /// The media type contained an invalid version component.
    UIntExpected(&'data str, &'data str, ParseIntError),
}

impl Display for Error<'_> {
    /// Describe the error that occurred.
    #[inline]
    fn fmt(&self, f: &mut Formatter<'_>) -> Result<(), FmtError> {
        match *self {
            Self::BuildNoPrefix => write!(
                f,
                "No prefix specified for the media-type-version config builder"
            ),
            Self::Internal(code) => write!(f, "media-type-version internal error: code {code}"),
            Self::NoPrefix(value, prefix) => {
                write!(
                    f,
                    "The '{value}' media type does not have the expected prefix '{prefix}'"
                )
            }
            Self::NoSuffix(value, suffix) => {
                write!(
                    f,
                    "The '{value}' media type does not have the expected suffix '{suffix}'"
                )
            }
            Self::NoVDot(value) => write!(
                f,
                "The '{value}' media type does not have the expected '.v' part"
            ),
            Self::TwoComponentsExpected(value) => write!(
                f,
                "The '{value}' media type does not have two dot-separated version components"
            ),
            #[cfg(feature = "extract-from-table")]
            Self::TableNoChild(comp) => {
                write!(f, "The parsed structure did not contain the '{comp}' child")
            }
            #[cfg(feature = "extract-from-table")]
            Self::TableNotTable => write!(
                f,
                "The parsed structure did not contain an expected table or string"
            ),
            #[cfg(feature = "toml-boml1")]
            Self::TomlParse(ref err) => write!(f, "Could not parse a TOML document: {err}"),
            Self::UIntExpected(value, comp, _) => write!(
                f,
                "The '{value}' media type contains an invalid unsigned integer '{comp}'"
            ),
        }
    }
}

impl CoreError for Error<'_> {
    #[inline]
    fn source(&self) -> Option<&(dyn CoreError + 'static)> {
        match *self {
            Self::BuildNoPrefix
            | Self::Internal(_)
            | Self::NoPrefix(_, _)
            | Self::NoSuffix(_, _)
            | Self::NoVDot(_)
            | Self::TwoComponentsExpected(_) => None,
            #[cfg(feature = "extract-from-table")]
            Self::TableNoChild(_) | Self::TableNotTable => None,
            #[cfg(feature = "toml-boml1")]
            Self::TomlParse(_) => None,
            Self::UIntExpected(_, _, ref err) => Some(err),
        }
    }
}

#[cfg(feature = "alloc")]
impl Error<'_> {
    /// Store the error strings into an owned object.
    #[inline]
    #[must_use]
    pub fn into_owned_error(self) -> OwnedError {
        match self {
            Self::BuildNoPrefix => OwnedError::BuildNoPrefix,
            Self::Internal(code) => OwnedError::Internal(code),
            Self::NoPrefix(value, prefix) => {
                OwnedError::NoPrefix(value.to_owned(), prefix.to_owned())
            }
            Self::NoSuffix(value, suffix) => {
                OwnedError::NoSuffix(value.to_owned(), suffix.to_owned())
            }
            Self::NoVDot(value) => OwnedError::NoVDot(value.to_owned()),
            #[cfg(feature = "extract-from-table")]
            Self::TableNoChild(comp) => OwnedError::TableNoChild(comp.to_owned()),
            #[cfg(feature = "extract-from-table")]
            Self::TableNotTable => OwnedError::TableNotTable,
            #[cfg(feature = "toml-boml1")]
            Self::TomlParse(err) => OwnedError::TomlBoml(format!("{err}")),
            Self::TwoComponentsExpected(value) => {
                OwnedError::TwoComponentsExpected(value.to_owned())
            }
            Self::UIntExpected(value, comp, err) => {
                OwnedError::UIntExpected(value.to_owned(), comp.to_owned(), err)
            }
        }
    }
}

/// An equivalent to [`Error`] that owns the error parameters.
#[cfg(feature = "alloc")]
#[derive(Debug)]
#[non_exhaustive]
pub enum OwnedError {
    /// No prefix specified for the config builder.
    BuildNoPrefix,

    /// Something went really, really wrong...
    Internal(u32),

    /// The media type did not have the specified prefix.
    NoPrefix(String, String),

    /// The media type did not have the specified suffix.
    NoSuffix(String, String),

    /// The media type did not have the ".v" part.
    NoVDot(String),

    #[cfg(feature = "extract-from-table")]
    /// The hierarchical structure did not contain the specified element.
    TableNoChild(String),

    #[cfg(feature = "extract-from-table")]
    /// The hierarchical structure did not contain the expected table or string.
    TableNotTable,

    #[cfg(feature = "toml-boml1")]
    /// Could not parse a TOML document.
    TomlBoml(String),

    /// The media type's version part did not consist of two dot-separated components.
    TwoComponentsExpected(String),

    /// The media type contained an invalid version component.
    UIntExpected(String, String, ParseIntError),
}

#[cfg(feature = "alloc")]
impl Display for OwnedError {
    /// Describe the error that occurred.
    #[inline]
    fn fmt(&self, f: &mut Formatter<'_>) -> Result<(), FmtError> {
        match *self {
            Self::BuildNoPrefix => Error::BuildNoPrefix.fmt(f),
            Self::Internal(ref code) => Error::Internal(*code).fmt(f),
            Self::NoPrefix(ref value, ref prefix) => Error::NoPrefix(value, prefix).fmt(f),
            Self::NoSuffix(ref value, ref suffix) => Error::NoSuffix(value, suffix).fmt(f),
            Self::NoVDot(ref value) => Error::NoVDot(value).fmt(f),
            #[cfg(feature = "extract-from-table")]
            Self::TableNoChild(ref comp) => Error::TableNoChild(comp).fmt(f),
            #[cfg(feature = "extract-from-table")]
            Self::TableNotTable => Error::TableNotTable.fmt(f),
            #[cfg(feature = "toml-boml1")]
            Self::TomlBoml(ref err) => write!(f, "Could not parse a TOML document: {err}"),
            Self::TwoComponentsExpected(ref value) => Error::TwoComponentsExpected(value).fmt(f),
            Self::UIntExpected(ref value, ref comp, ref err) => {
                Error::UIntExpected(value, comp, (*err).clone()).fmt(f)
            }
        }
    }
}

#[cfg(feature = "alloc")]
impl CoreError for OwnedError {
    #[inline]
    fn source(&self) -> Option<&(dyn CoreError + 'static)> {
        match *self {
            Self::BuildNoPrefix
            | Self::Internal(_)
            | Self::NoPrefix(_, _)
            | Self::NoSuffix(_, _)
            | Self::NoVDot(_)
            | Self::TwoComponentsExpected(_) => None,
            #[cfg(feature = "extract-from-table")]
            Self::TableNoChild(_) | Self::TableNotTable => None,
            #[cfg(feature = "toml-boml1")]
            Self::TomlBoml(_) => None,
            Self::UIntExpected(_, _, ref err) => Some(err),
        }
    }
}

/// The extracted format version.
#[cfg_attr(
    any(feature = "facet030-unstable", feature = "facet032-unstable"),
    derive(Facet)
)]
pub struct Version {
    /// The major version number.
    major: u32,

    /// The minor version number.
    minor: u32,
}

impl Version {
    /// The major version number.
    #[inline]
    #[must_use]
    pub const fn major(&self) -> u32 {
        self.major
    }

    /// The minor version number.
    #[inline]
    #[must_use]
    pub const fn minor(&self) -> u32 {
        self.minor
    }

    /// Return a (major, minor) tuple.
    #[inline]
    #[must_use]
    pub const fn as_tuple(&self) -> (u32, u32) {
        (self.major, self.minor)
    }
}

impl From<(u32, u32)> for Version {
    /// Build a [`Version`] object from the major and minor version numbers.
    #[inline]
    fn from(value: (u32, u32)) -> Self {
        Self {
            major: value.0,
            minor: value.1,
        }
    }
}

impl From<Version> for (u32, u32) {
    /// Break a [`Version`] object down into the major and minor version numbers.
    #[inline]
    fn from(value: Version) -> Self {
        value.as_tuple()
    }
}

/// Runtime configuration for the media-type-version library.
#[cfg_attr(
    any(feature = "facet030-unstable", feature = "facet032-unstable"),
    derive(Facet)
)]
pub struct Config<'data> {
    /// The prefix to strip from the media type string.
    prefix: &'data str,

    /// The suffix (possibly empty) to strip from the media type string.
    suffix: &'data str,
}

impl<'data> Config<'data> {
    /// The prefix to strip from the media type string.
    #[inline]
    #[must_use]
    pub const fn prefix(&self) -> &str {
        self.prefix
    }

    /// The suffix (possibly empty) to strip from the media type string.
    #[inline]
    #[must_use]
    pub const fn suffix(&self) -> &str {
        self.suffix
    }

    /// Start building a configuration object.
    #[inline]
    #[must_use]
    pub fn builder() -> ConfigBuilder<'data> {
        ConfigBuilder::default()
    }

    /// For test porpoises only, build something out of things.
    #[cfg(test)]
    #[inline]
    #[must_use]
    pub const fn from_parts(prefix: &'data str, suffix: &'data str) -> Self {
        Self { prefix, suffix }
    }
}

/// Build the runtime configuration.
#[derive(Default)]
pub struct ConfigBuilder<'data> {
    /// The prefix to strip from the media type string.
    prefix: Option<&'data str>,

    /// The suffix (possibly empty) to strip from the media type string.
    suffix: Option<&'data str>,
}

impl<'data> ConfigBuilder<'data> {
    /// Set the prefix to strip from the media type string.
    #[inline]
    #[must_use]
    pub const fn prefix(self, value: &'data str) -> Self {
        Self {
            prefix: Some(value),
            ..self
        }
    }

    /// Set the suffix (possibly empty) to strip from the media type string.
    #[inline]
    #[must_use]
    pub const fn suffix(self, value: &'data str) -> Self {
        Self {
            suffix: Some(value),
            ..self
        }
    }

    /// Build a [`Config`] object with the specified settings.
    ///
    /// # Errors
    ///
    /// [`Error::BuildNoPrefix`] if [`ConfigBuilder::prefix`] was not called.
    #[inline]
    pub fn build(self) -> Result<Config<'data>, Error<'data>> {
        Ok(Config {
            prefix: self.prefix.ok_or(Error::BuildNoPrefix)?,
            suffix: self.suffix.unwrap_or_default(),
        })
    }
}

#[cfg(test)]
#[expect(clippy::unwrap_used, reason = "this is a test suite")]
mod tests {
    extern crate alloc;

    use alloc::format;
    use alloc::string::String;

    #[cfg(any(feature = "facet030-unstable", feature = "facet032-unstable"))]
    use alloc::string::ToString as _;

    #[cfg(feature = "alloc")]
    use core::str::FromStr as _;

    use eyre::{Result, WrapErr as _};
    use facet_testhelpers::test;
    use log::{info, trace};

    #[cfg(feature = "facet030-unstable")]
    use facet_pretty030::FacetPretty as _;

    #[cfg(feature = "facet032-unstable")]
    use facet_pretty032::FacetPretty as _;

    use super::Config;

    #[cfg(feature = "alloc")]
    use super::Error;

    #[cfg(any(feature = "facet030-unstable", feature = "facet032-unstable"))]
    use super::Version;

    #[cfg(any(feature = "facet030-unstable", feature = "facet032-unstable"))]
    fn pretty_cfg(cfg: &Config<'_>) -> String {
        format!("{cfg}", cfg = cfg.pretty())
    }

    #[cfg(not(any(feature = "facet030-unstable", feature = "facet032-unstable")))]
    fn pretty_cfg(cfg: &Config<'_>) -> String {
        format!(
            "Config {{ prefix = {prefix:?}, suffix = {suffix:?} }}",
            prefix = cfg.prefix(),
            suffix = cfg.suffix()
        )
    }

    /// Make sure the builder, well, builds a [`Config`] object.
    #[test]
    fn builder() -> Result<()> {
        info!("Building a config builder");
        let cfg = Config::builder()
            .prefix("hello")
            .suffix("goodbye")
            .build()
            .context("build")?;
        trace!("{cfg}", cfg = pretty_cfg(&cfg));
        assert_eq!(cfg.prefix(), "hello");
        assert_eq!(cfg.suffix(), "goodbye");
        Ok(())
    }

    /// Make sure the error message does not change.
    #[cfg(feature = "alloc")]
    #[test]
    fn error_to_owned() {
        let check_to_owned_msg = |err: Error<'_>| {
            let msg = format!("{err}");
            trace!("{msg}");
            let owned = err.into_owned_error();
            let owned_msg = format!("{owned}");
            trace!("{owned_msg}");
            assert_eq!(msg, owned_msg);
        };

        check_to_owned_msg(Error::BuildNoPrefix);
        check_to_owned_msg(Error::NoPrefix("some value", "some prefix"));
        check_to_owned_msg(Error::NoSuffix("some value", "some suffix"));
        check_to_owned_msg(Error::NoVDot("stuff"));
        check_to_owned_msg(Error::TwoComponentsExpected("some kind of thing"));
        check_to_owned_msg(Error::UIntExpected(
            "something",
            "something else",
            u32::from_str("?").unwrap_err(),
        ));
    }

    /// Make sure the [`Facet`] trait for [`Version`] works.
    #[cfg(any(feature = "facet030-unstable", feature = "facet032-unstable"))]
    #[test]
    fn facet_pretty_contains_things() {
        let major = 42;
        let minor = 616;
        let ver = Version::from((major, minor));
        let repr = format!("{ver}", ver = ver.pretty());
        assert!(
            repr.contains("Version"),
            "no Version in the pretty representation: {repr:?}"
        );
        assert!(
            repr.contains(&major.to_string()),
            "no '{major}' in the pretty representation: {repr:?}"
        );
        assert!(
            repr.contains(&minor.to_string()),
            "no '{minor}' in the pretty representation: {repr:?}"
        );
        assert!(
            repr.contains('\n'),
            "no newline in the pretty representation: {repr:?}"
        );
    }
}
