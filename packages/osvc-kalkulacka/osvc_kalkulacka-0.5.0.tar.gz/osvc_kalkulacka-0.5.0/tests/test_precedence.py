import os

import pytest
from click.testing import CliRunner

from osvc_kalkulacka import cli


def _write_toml(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _defaults_toml(year: int, avg_wage: int) -> str:
    return "\n".join(
        [
            f'["{year}"]',
            f"avg_wage_czk = {avg_wage}",
            "min_wage_czk = 1",
            "taxpayer_credit = 1",
            "spouse_allowance = 0",
            "sp_vym_base_share = 0.55",
            "sp_min_base_share = 0.35",
            "child_bonus_annual_tiers = [1, 2, 3]",
            "",
        ]
    )


def _presets_toml(year: int, income: int) -> str:
    return "\n".join(
        [
            f'["{year}"]',
            f"income_czk = {income}",
            "child_months_by_order = [12]",
            "spouse_allowance = false",
            "",
        ]
    )


def test_load_year_defaults_cli_over_env_and_override(tmp_path, monkeypatch):
    cli_path = tmp_path / "cli_defaults.toml"
    env_path = tmp_path / "env_defaults.toml"
    override_path = tmp_path / "year_defaults.override.toml"

    _write_toml(cli_path, _defaults_toml(2030, 111))
    _write_toml(env_path, _defaults_toml(2030, 222))
    _write_toml(override_path, _defaults_toml(2030, 333))

    monkeypatch.setenv("OSVC_DEFAULTS_PATH", str(env_path))

    data = cli.load_year_defaults(str(cli_path), str(tmp_path))
    assert data[2030]["avg_wage_czk"] == 111


def test_load_year_defaults_env_over_override(tmp_path, monkeypatch):
    env_path = tmp_path / "env_defaults.toml"
    override_path = tmp_path / "year_defaults.override.toml"

    _write_toml(env_path, _defaults_toml(2031, 444))
    _write_toml(override_path, _defaults_toml(2031, 555))

    monkeypatch.setenv("OSVC_DEFAULTS_PATH", str(env_path))

    data = cli.load_year_defaults(None, str(tmp_path))
    assert data[2031]["avg_wage_czk"] == 444


def test_load_year_defaults_override_over_package(tmp_path, monkeypatch):
    override_path = tmp_path / "year_defaults.override.toml"
    _write_toml(override_path, _defaults_toml(2032, 666))
    monkeypatch.delenv("OSVC_DEFAULTS_PATH", raising=False)

    data = cli.load_year_defaults(None, str(tmp_path))
    assert data[2032]["avg_wage_czk"] == 666


def test_load_year_presets_cli_over_env_and_user(tmp_path, monkeypatch):
    cli_path = tmp_path / "cli_presets.toml"
    env_path = tmp_path / "env_presets.toml"
    user_path = tmp_path / "year_presets.toml"

    _write_toml(cli_path, _presets_toml(2030, 111))
    _write_toml(env_path, _presets_toml(2030, 222))
    _write_toml(user_path, _presets_toml(2030, 333))

    monkeypatch.setenv("OSVC_PRESETS_PATH", str(env_path))

    data = cli.load_year_presets(str(cli_path), str(tmp_path))
    assert data[2030]["income_czk"] == 111


def test_load_year_presets_env_over_user(tmp_path, monkeypatch):
    env_path = tmp_path / "env_presets.toml"
    user_path = tmp_path / "year_presets.toml"

    _write_toml(env_path, _presets_toml(2031, 444))
    _write_toml(user_path, _presets_toml(2031, 555))

    monkeypatch.setenv("OSVC_PRESETS_PATH", str(env_path))

    data = cli.load_year_presets(None, str(tmp_path))
    assert data[2031]["income_czk"] == 444


def test_load_year_presets_user_dir(tmp_path, monkeypatch):
    user_path = tmp_path / "year_presets.toml"
    _write_toml(user_path, _presets_toml(2032, 666))
    monkeypatch.delenv("OSVC_PRESETS_PATH", raising=False)

    data = cli.load_year_presets(None, str(tmp_path))
    assert data[2032]["income_czk"] == 666


def test_load_year_presets_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("OSVC_PRESETS_PATH", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        cli.load_year_presets(None, str(tmp_path))
    assert "osvc init" in str(excinfo.value)


def test_preset_invalid_spouse_allowance_raises(tmp_path, monkeypatch):
    year = 2033
    defaults_path = tmp_path / "defaults.toml"
    presets_path = tmp_path / "year_presets.toml"

    _write_toml(defaults_path, _defaults_toml(year, 111))
    _write_toml(
        presets_path,
        "\n".join(
            [
                f'["{year}"]',
                "income_czk = 1000",
                "child_months_by_order = [12]",
                'spouse_allowance = "yes"',
                "",
            ]
        ),
    )

    monkeypatch.setenv("OSVC_USER_PATH", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--year", str(year), "--defaults", str(defaults_path), "--format", "json"],
    )
    assert result.exit_code != 0
    assert "spouse_allowance" in result.output
