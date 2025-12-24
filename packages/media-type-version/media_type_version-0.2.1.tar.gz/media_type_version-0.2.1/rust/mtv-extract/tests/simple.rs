#![deny(missing_docs)]
#![deny(clippy::missing_docs_in_private_items)]
// SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
// SPDX-License-Identifier: BSD-2-Clause
//! Run a couple of tests for the `mtv-extract` command-line utility.

#![expect(clippy::tests_outside_test_module, reason = "integration test")]

use core::str::FromStr as _;
use std::env::{self, VarError};
use std::fs;
use std::process::{Command, Stdio};
use std::sync::LazyLock;

use camino::Utf8PathBuf;
use eyre::{Result, WrapErr as _, bail, eyre};
use facet_testhelpers::test;
use feature_check::defs::{Config as FcConfig, Obtained as FcObtained};
use feature_check::obtain as fc_obtain;
use feature_check::version::Version as FcVersion;
use log::info;

fn get_exe_path() -> Result<Utf8PathBuf> {
    static PATH: LazyLock<Result<Utf8PathBuf>> = LazyLock::new(|| {
        let current = Utf8PathBuf::from_path_buf(
            env::current_exe().context("Could not get the current executable file's path")?,
        )
        .map_err(|path| {
            eyre!(
                "Could not represent {path} as valid UTF-8",
                path = path.display()
            )
        })?;
        let exe_dir = {
            let basedir = current
                .parent()
                .ok_or_else(|| eyre!("Could not get the parent directory of {current}"))?;
            if basedir
                .file_name()
                .ok_or_else(|| eyre!("Could not get the base name of {basedir}"))?
                == "deps"
            {
                basedir
                    .parent()
                    .ok_or_else(|| eyre!("Could not get the parent directory of {basedir}"))?
            } else {
                basedir
            }
        };
        let exe_path = exe_dir.join("mtv-extract");
        if !exe_path.is_file() {
            bail!("Not a regular file: {exe_path}");
        }
        Ok(exe_path)
    });

    match *PATH {
        Ok(ref res) => Ok(res.clone()),
        Err(ref err) => bail!("Could not determine the path to the test program: {err}"),
    }
}

#[test]
fn stdin_ok() -> Result<()> {
    let tempd_obj = tempfile::tempdir().context("tempd")?;
    let tempd = Utf8PathBuf::from_path_buf(tempd_obj.path().to_path_buf())
        .map_err(|err| eyre!("tempd UTF-8: {err}", err = err.display()))?;
    let testfile = tempd.join("data.txt");
    fs::write(
        &testfile,
        "vnd.ringlet.test/config.v0.3+plain\nvnd.ringlet.test/config.v1.6+plain\n",
    )
    .context("testfile write")?;

    let exe_path = get_exe_path().context("get exe path")?;
    let output = Command::new(&exe_path)
        .args([
            "lines",
            "-p",
            "vnd.ringlet.test/config",
            "-s",
            "+plain",
            "--",
            testfile.as_ref(),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .output()
        .context("run")?;
    if !output.status.success() {
        bail!("{output:?}");
    }
    let versions = String::from_utf8(output.stdout).context("output UTF-8")?;
    assert_eq!(versions, "0\t3\n1\t6\n");
    Ok(())
}

fn find_uvoxen() -> Result<Option<String>> {
    let uvoxen_prog = match env::var("UVOXEN") {
        Ok(value) => value,
        Err(VarError::NotPresent) => "uvoxen".to_owned(),
        Err(err) => {
            return Err(err).context("Could not examine the `UVOXEN` environment variable");
        }
    };

    info!("Trying to obtain the features supported by `{uvoxen_prog}`");
    let fc_cfg = FcConfig::default().with_program(uvoxen_prog.clone());
    let FcObtained::Features(features) = fc_obtain::obtain_features(&fc_cfg)
        .with_context(|| format!("Could not query `{uvoxen_prog}` for supported features"))?
    else {
        info!("Could not parse the output of `{uvoxen_prog} --features`, skipping the test");
        return Ok(None);
    };
    let Some(fc_ver) = features.get("uvoxen") else {
        info!("No 'uvoxen' feature in the output of `{uvoxen_prog} --features`, skipping the test");
        return Ok(None);
    };

    let ref_ver_min = FcVersion::from_str("0.2").context("Could not parse 0.2 as a version")?;
    let ref_ver_max = FcVersion::from_str("0.3").context("Could not parse 0.3 as a version")?;
    if *fc_ver < ref_ver_min {
        bail!("Unsupported version for `{uvoxen_prog}`: {fc_ver} < {ref_ver_min}");
    }
    if *fc_ver >= ref_ver_max {
        bail!("Unsupported version for `{uvoxen_prog}`: {fc_ver} >= {ref_ver_max}");
    }
    info!("Supported version {fc_ver} for `{uvoxen_prog}`");
    Ok(Some(uvoxen_prog))
}

#[test]
fn python_test_prog_via_uvoxen() -> Result<()> {
    let Some(uvoxen) = find_uvoxen()? else {
        return Ok(());
    };

    // Well, here goes nothing...
    let top_dir = format!("{proj_dir}/../..", proj_dir = env!("CARGO_MANIFEST_DIR"));
    info!("Running `{uvoxen} uv run ...` in {top_dir}");
    if !Command::new(&uvoxen)
        .args(["uv", "run", "-e", "unit-tests-cli"])
        .current_dir(&top_dir)
        .env(
            "TEST_MTV_EXTRACT_PROG",
            &get_exe_path().context("get exe path")?,
        )
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .status()
        .with_context(|| format!("Could not run `{uvoxen} uv run`"))?
        .success()
    {
        bail!("`{uvoxen} uv run` failed");
    }
    Ok(())
}
