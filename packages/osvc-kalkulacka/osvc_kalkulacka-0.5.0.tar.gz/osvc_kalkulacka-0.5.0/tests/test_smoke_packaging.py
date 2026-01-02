import os
import subprocess
import sys
from importlib import resources
from pathlib import Path

import pytest

pytest.importorskip("build", reason="Packaging smoke tests require the 'build' module.")

def test_package_importable() -> None:
    __import__("osvc_kalkulacka")


def test_embedded_year_defaults_loads() -> None:
    data = resources.files("osvc_kalkulacka.data").joinpath("year_defaults.toml").read_bytes()
    assert data


def test_cli_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "osvc_kalkulacka.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "osvc" in result.stdout


def _build_dist(dist_dir: Path, kind: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "build", f"--{kind}", "--outdir", str(dist_dir)],
        check=True,
        capture_output=True,
        text=True,
    )


def _install_and_check(dist_path: Path, tmp_path: Path) -> None:
    target_dir = tmp_path / "site"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(target_dir), str(dist_path)],
        check=True,
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(target_dir)
    result = subprocess.run(
        [sys.executable, "-m", "osvc_kalkulacka.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )
    assert "osvc" in result.stdout


def test_sdist_install_and_cli_works(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    _build_dist(dist_dir, "sdist")

    sdists = list(dist_dir.glob("*.tar.gz"))
    assert sdists, "sdist not found in build output"
    _install_and_check(sdists[0], tmp_path)


def test_wheel_install_and_cli_works(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    _build_dist(dist_dir, "wheel")

    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "wheel not found in build output"
    _install_and_check(wheels[0], tmp_path)
