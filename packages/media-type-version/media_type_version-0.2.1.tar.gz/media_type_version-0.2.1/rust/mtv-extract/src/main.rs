#![deny(missing_docs)]
#![deny(clippy::missing_docs_in_private_items)]
// SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
// SPDX-License-Identifier: BSD-2-Clause
//! mtv-extract - read media type strings, extract the format versions from them

use std::fs::{self, File};
use std::io::{self, BufRead as _, BufReader, Error as IoError, Read as _};

use argh::FromArgs;
use eyre::{Result, WrapErr as _, bail, eyre};
use itertools::Itertools as _;
use log::{LevelFilter, info};
use simple_logger::SimpleLogger;

use media_type_version::{Config, Error, FEATURES};

/// The features supported by the command-line tool.
const CMD_FEATURES: [(&str, &str); 4] = [
    ("cmd-features", "0.1"),
    ("cmd-json", "0.1"),
    ("cmd-lines", "0.1"),
    ("cmd-toml", "0.1"),
];

/// list the features supported by the program
#[derive(Debug, FromArgs)]
#[argh(subcommand, name = "features")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh does not support unit structs yet"
)]
struct CmdFeatures {}

/// extract format versions from a JSON file
#[derive(Debug, FromArgs)]
#[argh(subcommand, name = "json")]
struct CmdJson {
    /// the prefix to expect in the media type string
    #[argh(option, short = 'p')]
    prefix: String,

    /// the optional suffix in the media type string
    #[argh(option, short = 's', default = "String::new()")]
    suffix: String,

    /// the optional dot-separated path to the section containing the `mediaType` string
    #[argh(option, short = 'P', default = "String::new()")]
    path: String,

    /// the files to parse; `-` denotes the standard input stream
    #[argh(positional)]
    files: Vec<String>,
}

/// extract format versions from a series of text lines
#[derive(Debug, FromArgs)]
#[argh(subcommand, name = "lines")]
struct CmdLines {
    /// the prefix to expect in the media type string
    #[argh(option, short = 'p')]
    prefix: String,

    /// the optional suffix in the media type string
    #[argh(option, short = 's', default = "String::new()")]
    suffix: String,

    /// the files to parse; `-` denotes the standard input stream
    #[argh(positional)]
    files: Vec<String>,
}

/// extract format versions from a series of text lines
#[derive(Debug, FromArgs)]
#[argh(subcommand, name = "toml")]
struct CmdToml {
    /// the prefix to expect in the media type string
    #[argh(option, short = 'p')]
    prefix: String,

    /// the optional suffix in the media type string
    #[argh(option, short = 's', default = "String::new()")]
    suffix: String,

    /// the optional dot-separated path to the section containing the `mediaType` string
    #[argh(option, short = 'P', default = "String::new()")]
    path: String,

    /// the files to parse; `-` denotes the standard input stream
    #[argh(positional)]
    files: Vec<String>,
}

/// What to do, what to do?
#[derive(Debug, FromArgs)]
#[argh(subcommand)]
enum CliCommand {
    /// list the features supported by the program
    Features(CmdFeatures),

    /// extract the media type format version from a JSON file
    Json(CmdJson),

    /// extract format versions from a series of text lines
    Lines(CmdLines),

    /// extract the media type format version from a TOML file
    Toml(CmdToml),
}

/// Read media type strings, extract the format versions from them.
#[derive(Debug, FromArgs)]
struct MtvLines {
    /// quiet operation; only display warnings and error messages
    #[argh(switch, short = 'q')]
    quiet: bool,

    /// verbose operation; display diagnostic messages
    #[argh(switch, short = 'v')]
    verbose: bool,

    /// what to do, what to do?
    #[argh(subcommand)]
    cmd: CliCommand,
}

/// List the features supported by the program.
#[expect(clippy::print_stdout, reason = "this is the whole point")]
fn show_features() {
    println!(
        "Features: {features}",
        features = FEATURES
            .iter()
            .chain(CMD_FEATURES.iter())
            .map(|&(name, value)| format!("{name}={value}"))
            .join(" ")
    );
}

/// Prepare the runtime configuration when parsing tables.
fn build_config<'data>(prefix: &'data str, suffix: &'data str) -> Result<Config<'data>> {
    Config::builder()
        .prefix(prefix)
        .suffix(suffix)
        .build()
        .map_err(Error::into_owned_error)
        .context("Could not build the MTConfig")
}

/// Prepare the runtime configuration when parsing tables.
fn build_path_vec(path: &str) -> Result<Vec<&str>> {
    if path.is_empty() {
        return Ok(Vec::new());
    }

    let path_vec: Vec<_> = path.split('.').collect();
    if path_vec.iter().any(|comp| comp.is_empty()) {
        bail!("Empty component in the section path");
    }
    Ok(path_vec)
}

/// Read a file into a single string.
fn read_to_single_string(fname: &str) -> Result<String> {
    if fname == "-" {
        info!("Reading from the standard input");
        let mut contents = String::new();
        io::stdin()
            .read_to_string(&mut contents)
            .context("Could not read from the standard input stream")?;
        return Ok(contents);
    }

    info!("Reading from the {fname} file");
    fs::read_to_string(fname).with_context(|| format!("Could not read from {fname}"))
}

/// Handle the "json" subcommand.
#[expect(clippy::print_stdout, reason = "this is the whole point")]
fn cmd_json(cmd: CmdJson) -> Result<()> {
    if cmd.files.is_empty() {
        bail!("No files to process");
    }
    let cfg = build_config(&cmd.prefix, &cmd.suffix)?;
    let path_vec = build_path_vec(&cmd.path)?;
    for fname in cmd.files {
        let contents = read_to_single_string(&fname)?;
        let raw = serialzero::parse(&contents)
            .map_err(|err| eyre!("Could not parse {fname} as valid JSON: {err}"))?;
        let ver = media_type_version::extract_from_table(&cfg, &raw, &path_vec)
            .map_err(Error::into_owned_error)
            .with_context(|| {
                format!("Could not extract the JSON `mediaType` version from {fname}")
            })?;
        println!("{major}\t{minor}", major = ver.major(), minor = ver.minor());
    }
    Ok(())
}

/// Read lines from a file, extract the data from them."""
#[expect(clippy::print_stdout, reason = "this is the whole point")]
fn process_lines<L>(cfg: &Config<'_>, fname: &str, lines: L) -> Result<()>
where
    L: Iterator<Item = Result<String, IoError>>,
{
    for line_res in lines {
        let line = line_res.with_context(|| format!("Could not read a line from {fname}"))?;
        let ver = media_type_version::extract(cfg, &line)
            .map_err(Error::into_owned_error)
            .with_context(|| format!("Could not parse a line read from {fname}: {line}"))?;
        println!("{major}\t{minor}", major = ver.major(), minor = ver.minor());
    }
    Ok(())
}

/// Handle the "lines" subcommand.
fn cmd_lines(cmd: CmdLines) -> Result<()> {
    if cmd.files.is_empty() {
        bail!("No files to process");
    }
    let cfg = build_config(&cmd.prefix, &cmd.suffix)?;
    for fname in cmd.files {
        if fname == "-" {
            info!("Reading from the standard input");
            process_lines(&cfg, "(standard input)", io::stdin().lines())?;
        } else {
            info!("Reading from the {fname} file");
            let infile = File::open(&fname)
                .with_context(|| format!("Could not open the {fname} file for reading"))?;
            process_lines(&cfg, &fname, BufReader::new(infile).lines())?;
        }
    }
    Ok(())
}

/// Handle the "toml" subcommand.
#[expect(clippy::print_stdout, reason = "this is the whole point")]
fn cmd_toml(cmd: CmdToml) -> Result<()> {
    if cmd.files.is_empty() {
        bail!("No files to process");
    }
    let cfg = build_config(&cmd.prefix, &cmd.suffix)?;
    let path_vec = build_path_vec(&cmd.path)?;
    for fname in cmd.files {
        let contents = read_to_single_string(&fname)?;
        let raw = boml::parse(&contents)
            .map_err(|err| eyre!("Could not parse {fname} as valid TOML: {err}"))?;
        let ver = media_type_version::extract_from_table(&cfg, &*raw, &path_vec)
            .map_err(Error::into_owned_error)
            .with_context(|| {
                format!("Could not extract the TOML `mediaType` version from {fname}")
            })?;
        println!("{major}\t{minor}", major = ver.major(), minor = ver.minor());
    }
    Ok(())
}

fn main() -> Result<()> {
    let args: MtvLines = argh::from_env();
    SimpleLogger::new()
        .with_level(if args.verbose {
            LevelFilter::Trace
        } else if args.quiet {
            LevelFilter::Warn
        } else {
            LevelFilter::Info
        })
        .init()
        .context("Could not set up logging")?;

    match args.cmd {
        CliCommand::Features(_) => show_features(),
        CliCommand::Json(cmd) => cmd_json(cmd)?,
        CliCommand::Lines(cmd) => cmd_lines(cmd)?,
        CliCommand::Toml(cmd) => cmd_toml(cmd)?,
    }
    Ok(())
}
