from __future__ import annotations

import json
import os
from importlib import resources
import tomllib

import click

from osvc_kalkulacka.core import (
    D,
    Inputs,
    USER_DEFAULTS,
    compute,
)
from osvc_kalkulacka.epo import compare_epo_to_calc, parse_epo_xml


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def print_row(label: str, value: int | str, *, suffix: str = "Kč", label_width: int = 40) -> None:
    """
    Print a row with aligned value column. Integers are formatted with thousands separators
    and optional suffix (default Kč); strings are printed as-is.
    """
    if isinstance(value, int):
        value_str = f"{fmt(value)} {suffix}" if suffix else fmt(value)
    else:
        value_str = value
    print(f"{label:<{label_width}}{value_str}")


def print_row_text(label: str, value: str, *, label_width: int = 40) -> None:
    """Print a row where value is already formatted text (no suffix)."""
    print_row(label, value, suffix="", label_width=label_width)


def get_user_dir() -> str:
    env_path = os.getenv("OSVC_USER_PATH")
    if env_path:
        return env_path
    return click.get_app_dir("osvc-kalkulacka")


def _load_toml(path: str) -> dict[str, object]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_package_toml(filename: str) -> dict[str, object]:
    try:
        with resources.files("osvc_kalkulacka.data").joinpath(filename).open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Chybí defaultní {filename}. Zadej --defaults nebo nastav OSVC_DEFAULTS_PATH."
        ) from exc


def load_year_presets(path: str | None, user_dir: str) -> dict[int, dict[str, object]]:
    """
    Načte roční presety z TOML. Priorita:
    1) explicitní cesta (CLI), 2) OSVC_PRESETS_PATH, 3) {user_dir}/year_presets.toml
    """
    if path:
        data = _load_toml(path)
    else:
        env_path = os.getenv("OSVC_PRESETS_PATH")
        if env_path:
            data = _load_toml(env_path)
        else:
            preset_path = os.path.join(user_dir, "year_presets.toml")
            if not os.path.exists(preset_path):
                raise SystemExit(
                    f"Chybí preset soubor: {preset_path}. Spusť `osvc init` nebo zadej --presets."
                )
            data = _load_toml(preset_path)

    out: dict[int, dict[str, object]] = {}
    for key, value in data.items():
        try:
            year_key = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            out[year_key] = value
    return out


def _ensure_int(value: object, *, name: str, year: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SystemExit(f"Rok {year}: {name} musí být celé číslo.")
    if value < 0:
        raise SystemExit(f"Rok {year}: {name} nesmí být záporné.")
    return value


def _ensure_decimal_0_1(value: object, *, name: str, year: int) -> D:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SystemExit(f"Rok {year}: {name} musí být číslo (0.0–1.0).")
    dec = D(str(value))
    if not (D("0") <= dec <= D("1")):
        raise SystemExit(f"Rok {year}: {name} musí být v intervalu 0.0–1.0.")
    return dec


def _ensure_bool(value: object, *, name: str, year: int) -> bool:
    if not isinstance(value, bool):
        raise SystemExit(f"Rok {year}: {name} musí být true/false.")
    return value


def _ensure_activity(value: object, *, year: int) -> str:
    if not isinstance(value, str):
        raise SystemExit(f"Rok {year}: activity musí být 'primary' nebo 'secondary'.")
    activity = value.strip().lower()
    if activity not in ("primary", "secondary"):
        raise SystemExit(f"Rok {year}: activity musí být 'primary' nebo 'secondary'.")
    return activity


def _ensure_child_months(value: object, *, year: int) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise SystemExit(f"Rok {year}: child_months_by_order musí být seznam čísel.")
    months: list[int] = []
    for idx, item in enumerate(value, start=1):
        month = _ensure_int(item, name="child_months_by_order", year=year)
        if not 0 <= month <= 12:
            raise SystemExit(f"Rok {year}: child_months_by_order[{idx}] musí být 0–12.")
        months.append(month)
    return tuple(months)


def _build_inputs(
    *,
    year: int,
    income: int | None,
    presets: str | None,
    defaults: str | None,
    section_15_allowances: int | None,
    child_months_by_order: str | None,
    spouse_allowance: bool | None,
    activity: str | None,
) -> Inputs:
    user_dir = get_user_dir()

    year_defaults = load_year_defaults(defaults, user_dir)
    year_cfg = year_defaults.get(year)
    if year_cfg is None:
        known_years = ", ".join(str(y) for y in sorted(year_defaults))
        raise SystemExit(f"Neznám daňové parametry pro rok {year}. Známé roky: {known_years}")
    if year_cfg["min_wage_czk"] <= 0:
        raise SystemExit(f"Chybí min_wage_czk pro rok {year}. Doplň year_defaults.toml.")

    year_presets = load_year_presets(presets, user_dir)
    preset = year_presets.get(year, {})
    if income is not None:
        income_czk = income
    else:
        preset_income = preset.get("income_czk")
        if preset_income is None:
            raise SystemExit("Chybí příjmy. Zadej --income nebo doplň preset pro daný rok.")
        income_czk = _ensure_int(preset_income, name="income_czk", year=year)

    if section_15_allowances is not None:
        section_15_allowances_czk = section_15_allowances
    else:
        section_15_allowances_czk = _ensure_int(
            preset.get("section_15_allowances_czk", 0),
            name="section_15_allowances_czk",
            year=year,
        )
    child_months_by_order_tuple = None
    if child_months_by_order:
        child_months_by_order_tuple = _parse_child_months(child_months_by_order)
    elif "child_months_by_order" in preset:
        child_months_by_order_tuple = _ensure_child_months(
            preset.get("child_months_by_order"),
            year=year,
        )

    if child_months_by_order_tuple is None:
        raise SystemExit("Chybí child_months_by_order. Zadej --child-months-by-order nebo nastav preset.")
    if spouse_allowance is True:
        spouse_allowance = True
    elif spouse_allowance is False:
        spouse_allowance = False
    else:
        if "spouse_allowance" in preset:
            spouse_allowance = _ensure_bool(preset.get("spouse_allowance"), name="spouse_allowance", year=year)
        else:
            spouse_allowance = False

    if activity is None:
        if "activity" in preset:
            activity = _ensure_activity(preset.get("activity"), year=year)
        else:
            activity = "primary"
    activity = activity.lower()
    if activity not in ("primary", "secondary"):
        raise SystemExit("activity musí být primary nebo secondary.")

    return Inputs(
        income_czk=income_czk,
        child_months_by_order=child_months_by_order_tuple,
        min_wage_czk=year_cfg["min_wage_czk"],
        expense_rate=USER_DEFAULTS["expense_rate"],
        section_15_allowances_czk=section_15_allowances_czk,
        tax_rate=USER_DEFAULTS["tax_rate"],
        taxpayer_credit_czk=year_cfg["taxpayer_credit"],
        spouse_allowance_czk=year_cfg["spouse_allowance"] if spouse_allowance else 0,
        child_bonus_annual_tiers_czk=year_cfg["child_bonus_annual_tiers"],
        avg_wage_czk=year_cfg["avg_wage_czk"],
        zp_min_base_share=D("0.50"),
        sp_min_base_share=year_cfg["sp_min_base_share"],
        sp_vym_base_share=year_cfg["sp_vym_base_share"],
        sp_min_base_share_secondary=year_cfg["sp_min_base_share_secondary"],
        sp_threshold_secondary_czk=year_cfg["sp_threshold_secondary_czk"],
        activity_type=activity,
    )


def load_year_defaults(path: str | None, user_dir: str) -> dict[int, dict[str, object]]:
    """
    Načte roční tabulky z TOML. Priorita:
    1) explicitní cesta (CLI), 2) OSVC_DEFAULTS_PATH, 3) {user_dir}/year_defaults.override.toml (pokud existuje),
    4) default v balíčku.
    """
    if path:
        data = _load_toml(path)
    else:
        env_path = os.getenv("OSVC_DEFAULTS_PATH")
        if env_path:
            data = _load_toml(env_path)
        else:
            override_path = os.path.join(user_dir, "year_defaults.override.toml")
            if os.path.exists(override_path):
                data = _load_toml(override_path)
            else:
                data = _load_package_toml("year_defaults.toml")

    required_keys = {
        "avg_wage_czk",
        "min_wage_czk",
        "taxpayer_credit",
        "child_bonus_annual_tiers",
        "spouse_allowance",
        "sp_vym_base_share",
        "sp_min_base_share",
        "sp_min_base_share_secondary",
        "sp_threshold_secondary_czk",
    }

    out: dict[int, dict[str, object]] = {}
    for key, value in data.items():
        try:
            year_key = int(key)
        except (TypeError, ValueError):
            raise SystemExit(f"Neplatný klíč roku: {key!r}")
        if not isinstance(value, dict):
            raise SystemExit(f"Rok {year_key}: očekávám tabulku s hodnotami.")

        unknown_keys = set(value.keys()) - required_keys
        if unknown_keys:
            unknown_list = ", ".join(sorted(unknown_keys))
            raise SystemExit(f"Rok {year_key}: neznámé klíče: {unknown_list}")

        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            missing_list = ", ".join(sorted(missing_keys))
            raise SystemExit(f"Rok {year_key}: chybí klíče: {missing_list}")

        avg_wage_czk = _ensure_int(value["avg_wage_czk"], name="avg_wage_czk", year=year_key)
        min_wage_czk = _ensure_int(value["min_wage_czk"], name="min_wage_czk", year=year_key)
        taxpayer_credit = _ensure_int(value["taxpayer_credit"], name="taxpayer_credit", year=year_key)
        spouse_allowance = _ensure_int(value["spouse_allowance"], name="spouse_allowance", year=year_key)

        tiers = value["child_bonus_annual_tiers"]
        if not isinstance(tiers, list) or len(tiers) != 3:
            raise SystemExit(f"Rok {year_key}: child_bonus_annual_tiers musí být pole se 3 čísly.")
        child_tiers = tuple(_ensure_int(item, name="child_bonus_annual_tiers", year=year_key) for item in tiers)

        sp_vym_base_share = _ensure_decimal_0_1(value["sp_vym_base_share"], name="sp_vym_base_share", year=year_key)
        sp_min_base_share = _ensure_decimal_0_1(value["sp_min_base_share"], name="sp_min_base_share", year=year_key)
        sp_min_base_share_secondary = _ensure_decimal_0_1(
            value["sp_min_base_share_secondary"], name="sp_min_base_share_secondary", year=year_key
        )
        sp_threshold_secondary_czk = _ensure_int(
            value["sp_threshold_secondary_czk"], name="sp_threshold_secondary_czk", year=year_key
        )

        out[year_key] = {
            "avg_wage_czk": avg_wage_czk,
            "min_wage_czk": min_wage_czk,
            "taxpayer_credit": taxpayer_credit,
            "spouse_allowance": spouse_allowance,
            "child_bonus_annual_tiers": child_tiers,
            "sp_vym_base_share": sp_vym_base_share,
            "sp_min_base_share": sp_min_base_share,
            "sp_min_base_share_secondary": sp_min_base_share_secondary,
            "sp_threshold_secondary_czk": sp_threshold_secondary_czk,
        }

    return out


def _parse_child_months(raw: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in raw.split(",") if item.strip())


def _json_dump(payload: object) -> None:
    click.echo(json.dumps(payload, ensure_ascii=True, indent=2, default=str))


def _results_as_dict(inp: Inputs, res) -> dict[str, object]:
    return {
        "inputs": {
            "activity_type": inp.activity_type,
            "income_czk": inp.income_czk,
            "child_months_by_order": list(inp.child_months_by_order),
            "min_wage_czk": inp.min_wage_czk,
            "expense_rate": str(inp.expense_rate),
            "section_15_allowances_czk": inp.section_15_allowances_czk,
            "tax_rate": str(inp.tax_rate),
            "taxpayer_credit_czk": inp.taxpayer_credit_czk,
            "spouse_allowance_czk": inp.spouse_allowance_czk,
            "child_bonus_annual_tiers_czk": list(inp.child_bonus_annual_tiers_czk),
            "avg_wage_czk": inp.avg_wage_czk,
            "zp_rate": str(inp.zp_rate),
            "sp_rate": str(inp.sp_rate),
            "zp_vym_base_share": str(inp.zp_vym_base_share),
            "sp_vym_base_share": str(inp.sp_vym_base_share),
            "zp_min_base_share": str(inp.zp_min_base_share),
            "sp_min_base_share": str(inp.sp_min_base_share),
            "sp_min_base_share_secondary": str(inp.sp_min_base_share_secondary),
            "sp_threshold_secondary_czk": inp.sp_threshold_secondary_czk,
        },
        "tax": {
            "expenses_czk": res.tax.expenses_czk,
            "base_profit_czk": res.tax.base_profit_czk,
            "section_15_allowances_czk": res.tax.section_15_allowances_czk,
            "base_after_deductions_czk": res.tax.base_after_deductions_czk,
            "base_rounded_czk": res.tax.base_rounded_czk,
            "tax_before_credits_czk": res.tax.tax_before_credits_czk,
            "tax_after_taxpayer_credit_czk": res.tax.tax_after_taxpayer_credit_czk,
            "tax_after_spouse_credit_czk": res.tax.tax_after_spouse_credit_czk,
            "spouse_credit_applied_czk": res.tax.spouse_credit_applied_czk,
            "child_bonus_czk": res.tax.child_bonus_czk,
            "child_bonus_eligible": res.tax.child_bonus_eligible,
            "child_bonus_min_income_czk": res.tax.child_bonus_min_income_czk,
            "tax_final_czk": res.tax.tax_final_czk,
            "bonus_to_pay_czk": res.tax.bonus_to_pay_czk,
        },
        "insurance": {
            "vym_base_czk": res.ins.vym_base_czk,
            "min_zp_monthly_czk": res.ins.min_zp_monthly_czk,
            "min_sp_monthly_czk": res.ins.min_sp_monthly_czk,
            "zp_annual_czk": res.ins.zp_annual_czk,
            "zp_monthly_calc_czk": res.ins.zp_monthly_calc_czk,
            "zp_monthly_payable_czk": res.ins.zp_monthly_payable_czk,
            "zp_annual_payable_czk": res.ins.zp_annual_payable_czk,
            "sp_annual_czk": res.ins.sp_annual_czk,
            "sp_monthly_calc_czk": res.ins.sp_monthly_calc_czk,
            "sp_monthly_payable_czk": res.ins.sp_monthly_payable_czk,
            "sp_annual_payable_czk": res.ins.sp_annual_payable_czk,
        },
    }


def _render_calc_output(inp: Inputs, res, year: int, output_format: str) -> None:
    if output_format == "json":
        _json_dump(_results_as_dict(inp, res))
        return

    print("OSVČ kalkulačka – DPFO + pojistné (zjednodušený výpočet)")
    print("-" * 70)
    activity_label = "primary (hlavní)" if inp.activity_type == "primary" else "secondary (vedlejší)"
    print_row_text("Typ činnosti:", activity_label)
    print()

    print("DPFO (daň z příjmů)")
    print_row("Příjmy (§7):", inp.income_czk)
    print_row(f"Výdaje paušálem ({(inp.expense_rate * 100)}%):", res.tax.expenses_czk)
    print_row("Zisk / základ (§7):", res.tax.base_profit_czk)
    print()
    print_row("Nezdanitelné části základu daně (§15):", res.tax.section_15_allowances_czk)
    print_row("Základ po odpočtu §15:", res.tax.base_after_deductions_czk)
    print_row("Základ daně zaokrouhlený:", res.tax.base_rounded_czk)
    print()
    print_row("Daň z příjmů před odečtením slev:", res.tax.tax_before_credits_czk)
    print_row("Sleva na poplatníka:", inp.taxpayer_credit_czk)
    print_row("Sleva na manžela/ku (nárok):", inp.spouse_allowance_czk)
    print_row("Sleva na manžela/ku (uplatněno):", res.tax.spouse_credit_applied_czk)
    total_credits_claimed = inp.taxpayer_credit_czk + inp.spouse_allowance_czk
    total_credits_applied = inp.taxpayer_credit_czk + res.tax.spouse_credit_applied_czk
    print_row("Slevy celkem (nárok):", total_credits_claimed)
    print_row("Slevy celkem (uplatněno):", total_credits_applied)
    print_row("Daň po slevách na poplatníka a manžela/ku:", res.tax.tax_after_spouse_credit_czk)
    print()
    if not res.tax.child_bonus_eligible:
        min_income = fmt(res.tax.child_bonus_min_income_czk)
        print(f"VAROVÁNÍ: Daňové zvýhodnění na děti neuplatněno (příjmy < {min_income} Kč).")
    child_used_for_tax = min(res.tax.child_bonus_czk, res.tax.tax_after_spouse_credit_czk)
    print_row("Zvýhodnění na děti (uplatněno):", res.tax.child_bonus_czk)
    print_row("  Z toho použito na snížení daně:", child_used_for_tax)
    print_row("Daňový bonus vyplacený (-):", res.tax.bonus_to_pay_czk)
    print_row("Daň k úhradě po dětech:", res.tax.tax_final_czk)

    print("-" * 70)

    print("Pojistné (ZP/SP) – odhad z ročního zisku")
    if inp.activity_type == "primary":
        print("(Pozn.: pokud výpočet vychází pod minimem, platí se minimální zálohy.)")
    else:
        print("(Pozn.: vedlejší činnost – ZP bez minima, SP jen nad rozhodnou částku.)")
    print_row("Vyměřovací základ (50 % zisku):", res.ins.vym_base_czk)
    print()

    print("Zdravotní pojištění (ZP)")
    print_row("  Ročně (13,5 % z VZ):", res.ins.zp_annual_czk)
    print_row("  Měsíčně vypočteno (roční/12):", res.ins.zp_monthly_calc_czk)
    print_row(f"  Minimální záloha ({year}):", res.ins.min_zp_monthly_czk)
    print_row("  Měsíční záloha k placení:", res.ins.zp_monthly_payable_czk)
    print_row("  Ročně zaplaceno na zálohách:", res.ins.zp_annual_payable_czk)
    print()

    print("Sociální pojištění (SP)")
    if inp.activity_type == "secondary":
        print_row("  Rozhodná částka (limit):", inp.sp_threshold_secondary_czk)
    print_row("  Ročně (29,2 % z VZ):", res.ins.sp_annual_czk)
    print_row("  Měsíčně vypočteno (roční/12):", res.ins.sp_monthly_calc_czk)
    print_row(f"  Minimální záloha ({year}):", res.ins.min_sp_monthly_czk)
    print_row("  Měsíční záloha k placení:", res.ins.sp_monthly_payable_czk)
    print_row("  Ročně zaplaceno na zálohách:", res.ins.sp_annual_payable_czk)

    print("-" * 70)

    total_out = res.tax.tax_final_czk + res.ins.zp_annual_payable_czk + res.ins.sp_annual_payable_czk
    total_net = total_out - res.tax.bonus_to_pay_czk

    print("Souhrn (ročně)")
    print_row("Daň k úhradě:", res.tax.tax_final_czk)
    print_row("ZP – zálohy zaplacené za rok:", res.ins.zp_annual_payable_czk)
    print_row("SP – zálohy zaplacené za rok:", res.ins.sp_annual_payable_czk)
    print_row("Celkem k platbě:", total_out)
    print_row("Bonus k výplatě (odečteno):", res.tax.bonus_to_pay_czk)
    print_row("Čisté zatížení (odvody - bonus):", total_net)


@click.group(invoke_without_command=True)
@click.version_option(package_name="osvc-kalkulacka")
@click.option("--year", type=int, required=False, help="Rok daňového přiznání (zdaňovací období).")
@click.option("--income", type=int, default=None, help="Příjmy (§7) v Kč za rok.")
@click.option(
    "--presets",
    type=str,
    default=None,
    help="Cesta k TOML s ročními presety. Alternativně lze použít OSVC_PRESETS_PATH.",
)
@click.option(
    "--defaults",
    type=str,
    default=None,
    help="Cesta k TOML s ročními tabulkami. Alternativně lze použít OSVC_DEFAULTS_PATH.",
)
@click.option(
    "--section-15-allowances",
    type=int,
    default=None,
    help="Nezdanitelné části základu daně (§15) v Kč za rok.",
)
@click.option(
    "--child-months-by-order",
    type=str,
    default=None,
    help="Měsíce nároku podle pořadí dětí (např. 6,6,12 pro 1., 2., 3. dítě).",
)
@click.option(
    "--spouse-allowance/--no-spouse-allowance",
    default=None,
    help="Uplatnit/neuplnit slevu na manžela/ku (přepíše preset).",
)
@click.option(
    "--activity",
    type=click.Choice(["primary", "secondary"], case_sensitive=False),
    default=None,
    help="Typ samostatné výdělečné činnosti (primary/secondary).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Výstupní formát.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    year: int | None,
    income: int | None,
    presets: str | None,
    defaults: str | None,
    section_15_allowances: int | None,
    child_months_by_order: str | None,
    spouse_allowance: bool | None,
    activity: str | None,
    output_format: str,
) -> None:
    """OSVČ kalkulačka (DPFO + ZP/SP), zjednodušený výpočet."""
    if ctx.invoked_subcommand:
        return
    if year is None:
        raise click.UsageError("Chybí --year. Zadej rok výpočtu.")

    inp = _build_inputs(
        year=year,
        income=income,
        presets=presets,
        defaults=defaults,
        section_15_allowances=section_15_allowances,
        child_months_by_order=child_months_by_order,
        spouse_allowance=spouse_allowance,
        activity=activity,
    )
    res = compute(inp)
    _render_calc_output(inp, res, year, output_format)


@cli.command()
@click.option("--year", type=int, required=True, help="Rok daňového přiznání (zdaňovací období).")
@click.option("--epo", "epo_path", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--income", type=int, default=None, help="Příjmy (§7) v Kč za rok.")
@click.option(
    "--presets",
    type=str,
    default=None,
    help="Cesta k TOML s ročními presety. Alternativně lze použít OSVC_PRESETS_PATH.",
)
@click.option(
    "--defaults",
    type=str,
    default=None,
    help="Cesta k TOML s ročními tabulkami. Alternativně lze použít OSVC_DEFAULTS_PATH.",
)
@click.option(
    "--section-15-allowances",
    type=int,
    default=None,
    help="Nezdanitelné části základu daně (§15) v Kč za rok.",
)
@click.option(
    "--child-months-by-order",
    type=str,
    default=None,
    help="Měsíce nároku podle pořadí dětí (např. 6,6,12 pro 1., 2., 3. dítě).",
)
@click.option(
    "--spouse-allowance/--no-spouse-allowance",
    default=None,
    help="Uplatnit/neuplnit slevu na manžela/ku (přepíše preset).",
)
@click.option(
    "--activity",
    type=click.Choice(["primary", "secondary"], case_sensitive=False),
    default=None,
    help="Typ samostatné výdělečné činnosti (primary/secondary).",
)
def verify(
    year: int,
    epo_path: str,
    income: int | None,
    presets: str | None,
    defaults: str | None,
    section_15_allowances: int | None,
    child_months_by_order: str | None,
    spouse_allowance: bool | None,
    activity: str | None,
) -> None:
    inp = _build_inputs(
        year=year,
        income=income,
        presets=presets,
        defaults=defaults,
        section_15_allowances=section_15_allowances,
        child_months_by_order=child_months_by_order,
        spouse_allowance=spouse_allowance,
        activity=activity,
    )
    res = compute(inp)
    epo = parse_epo_xml(epo_path)
    diffs = compare_epo_to_calc(epo, inp, res, expected_year=year)

    def fmt_value(value: object) -> str:
        if isinstance(value, int):
            return fmt(value)
        return str(value)

    print(f"EPO formulář: {epo.form}")
    if epo.year is not None:
        print(f"Rok v EPO: {epo.year}")
    if not diffs:
        print("OK: Výpočty odpovídají EPO.")
        return

    print("NESHODA: nalezeny rozdíly:")
    for diff in diffs:
        epo_value = fmt_value(diff.epo) if diff.epo is not None else "-"
        calc_value = fmt_value(diff.calc) if diff.calc is not None else "-"
        print(f"- {diff.field}: EPO={epo_value} vs kalkulačka={calc_value}")

@cli.command()
@click.option("--force", is_flag=True, help="Přepsat existující preset soubor.")
def init(force: bool) -> None:
    """Vytvoří year_presets.toml v uživatelském adresáři ze šablony."""
    user_dir = get_user_dir()
    os.makedirs(user_dir, exist_ok=True)
    target_path = os.path.join(user_dir, "year_presets.toml")
    if os.path.exists(target_path) and not force:
        raise SystemExit(f"Soubor už existuje: {target_path}. Použij --force.")
    data = resources.files("osvc_kalkulacka.data").joinpath("year_presets.example.toml").read_bytes()
    with open(target_path, "wb") as f:
        f.write(data)
    click.echo(f"Vytvořeno: {target_path}")


@cli.group()
def config() -> None:
    """Konfigurace a cesty."""


@config.command("path")
def config_path() -> None:
    """Vypíše user dir a očekávané cesty."""
    user_dir = get_user_dir()
    preset_path = os.path.join(user_dir, "year_presets.toml")
    defaults_override = os.path.join(user_dir, "year_defaults.override.toml")
    click.echo(f"user_dir: {user_dir}")
    click.echo(f"presets: {preset_path}")
    click.echo(f"defaults_override: {defaults_override}")
    if os.getenv("OSVC_USER_PATH"):
        click.echo(f"OSVC_USER_PATH: {os.getenv('OSVC_USER_PATH')}")
    if os.getenv("OSVC_PRESETS_PATH"):
        click.echo(f"OSVC_PRESETS_PATH: {os.getenv('OSVC_PRESETS_PATH')}")
    if os.getenv("OSVC_DEFAULTS_PATH"):
        click.echo(f"OSVC_DEFAULTS_PATH: {os.getenv('OSVC_DEFAULTS_PATH')}")


@cli.group()
def defaults() -> None:
    """Práce s vestavěnými defaults."""


@defaults.command("dump")
@click.option("--output", type=click.Path(dir_okay=False, writable=True), default=None)
def defaults_dump(output: str | None) -> None:
    """Vyexportuje vestavěné year_defaults.toml."""
    data = resources.files("osvc_kalkulacka.data").joinpath("year_defaults.toml").read_bytes()
    if output:
        with open(output, "wb") as f:
            f.write(data)
        click.echo(f"Zapsáno: {output}")
    else:
        click.echo(data.decode("utf-8"), nl=True)


if __name__ == "__main__":
    cli()
