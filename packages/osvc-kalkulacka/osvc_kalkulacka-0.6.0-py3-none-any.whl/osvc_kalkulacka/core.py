from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING

D = Decimal

USER_DEFAULTS = {
    "tax_rate": D("0.15"),
    "expense_rate": D("0.60"),
}


def round_czk_half_up(x: Decimal) -> int:
    """Zaokrouhlení na celé Kč matematicky (0.5 nahoru)."""
    return int(x.quantize(D("1"), rounding=ROUND_HALF_UP))


def ceil_czk(x: Decimal) -> int:
    """Zaokrouhlení na celé Kč nahoru."""
    return int(x.to_integral_value(rounding=ROUND_CEILING))


def floor_to_hundreds(x: int) -> int:
    """Zaokrouhlení základu daně dolů na celé stovky Kč. Očekává nezáporný vstup."""
    return (x // 100) * 100


def nonneg_int(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} nesmí být záporné.")


def validate_rate_0_1(name: str, value: Decimal) -> None:
    if not (D("0") <= value <= D("1")):
        raise ValueError(f"{name} musí být v intervalu 0.0–1.0.")


def compute_child_bonus_from_months(
    months_by_order: tuple[int, ...],
    tiers: tuple[int, int, int],
) -> int:
    """Spočítá zvýhodnění podle pořadí dětí a měsíců nároku na každé dítě."""
    total = 0
    for idx, months in enumerate(months_by_order, start=1):
        if months <= 0:
            continue
        annual = tiers[0] if idx == 1 else tiers[1] if idx == 2 else tiers[2]
        total += round_czk_half_up(D(annual) * D(months) / D(12))
    return total


@dataclass(frozen=True)
class Inputs:
    # §7
    income_czk: int
    child_months_by_order: tuple[int, ...]
    min_wage_czk: int
    expense_rate: Decimal = D("0.60")

    # §15 - nezdanitelné části základu daně
    section_15_allowances_czk: int = 0

    # DPFO
    tax_rate: Decimal = D("0.15")
    taxpayer_credit_czk: int = 30_840
    spouse_allowance_czk: int = 0

    # Dítě (zjednodušeně fixní roční částka na dítě)
    child_bonus_annual_tiers_czk: tuple[int, int, int] = (15_204, 22_320, 27_840)

    # ZP/SP
    avg_wage_czk: int = 0  # informační; používá se pro minima
    zp_rate: Decimal = D("0.135")
    sp_rate: Decimal = D("0.292")
    zp_vym_base_share: Decimal = D("0.50")  # 50 % zisku
    sp_vym_base_share: Decimal = D("0.55")  # 55 % zisku (hlavní činnost 2024+)
    zp_min_base_share: Decimal = D("0.50")
    sp_min_base_share: Decimal = D("0.35")
    sp_min_base_share_secondary: Decimal = D("0.11")
    sp_threshold_secondary_czk: int = 0
    activity_type: str = "primary"


@dataclass(frozen=True)
class TaxResults:
    expenses_czk: int
    base_profit_czk: int
    section_15_allowances_czk: int
    base_after_deductions_czk: int
    base_rounded_czk: int
    tax_before_credits_czk: int
    tax_after_taxpayer_credit_czk: int
    tax_after_spouse_credit_czk: int
    spouse_credit_applied_czk: int
    child_bonus_czk: int
    child_bonus_eligible: bool
    child_bonus_min_income_czk: int
    tax_final_czk: int
    bonus_to_pay_czk: int


@dataclass(frozen=True)
class InsuranceResults:
    vym_base_czk: int  # pro přehled uvádíme ZP vyměřovací základ

    min_zp_monthly_czk: int
    min_sp_monthly_czk: int

    zp_annual_czk: int
    zp_monthly_calc_czk: int
    zp_monthly_payable_czk: int
    zp_annual_payable_czk: int

    sp_annual_czk: int
    sp_monthly_calc_czk: int
    sp_monthly_payable_czk: int
    sp_annual_payable_czk: int


@dataclass(frozen=True)
class Results:
    tax: TaxResults
    ins: InsuranceResults


def compute_tax(inp: Inputs) -> TaxResults:
    nonneg_int("income_czk", inp.income_czk)
    nonneg_int("section_15_allowances_czk", inp.section_15_allowances_czk)
    nonneg_int("taxpayer_credit_czk", inp.taxpayer_credit_czk)
    nonneg_int("spouse_allowance_czk", inp.spouse_allowance_czk)

    if len(inp.child_bonus_annual_tiers_czk) != 3:
        raise ValueError("child_bonus_annual_tiers_czk musí mít tři položky (1., 2., 3+ dítě).")
    for idx, amount in enumerate(inp.child_bonus_annual_tiers_czk, start=1):
        nonneg_int(f"child_bonus_tier_{idx}_czk", amount)
    validate_rate_0_1("expense_rate", inp.expense_rate)
    validate_rate_0_1("tax_rate", inp.tax_rate)

    expenses = round_czk_half_up(D(inp.income_czk) * inp.expense_rate)
    base_profit = inp.income_czk - expenses
    base_profit = max(0, base_profit)

    base_after = max(0, base_profit - inp.section_15_allowances_czk)

    base_rounded = floor_to_hundreds(base_after)
    tax_before = round_czk_half_up(D(base_rounded) * inp.tax_rate)
    tax_after_taxpayer = max(0, tax_before - inp.taxpayer_credit_czk)

    spouse_credit = min(inp.spouse_allowance_czk, tax_after_taxpayer)
    tax_after_spouse = max(0, tax_after_taxpayer - spouse_credit)

    for idx, months in enumerate(inp.child_months_by_order, start=1):
        if not 0 <= months <= 12:
            raise ValueError(f"child_months_by_order[{idx}] musí být 0–12.")
    has_child_claim = any(months > 0 for months in inp.child_months_by_order)
    min_income_for_bonus = inp.min_wage_czk * 6
    child_bonus_eligible = not has_child_claim or inp.income_czk >= min_income_for_bonus
    if child_bonus_eligible:
        child_bonus = compute_child_bonus_from_months(inp.child_months_by_order, inp.child_bonus_annual_tiers_czk)
    else:
        child_bonus = 0

    tax_final = max(0, tax_after_spouse - child_bonus)
    bonus_to_pay = max(0, child_bonus - tax_after_spouse)

    return TaxResults(
        expenses_czk=expenses,
        base_profit_czk=base_profit,
        section_15_allowances_czk=inp.section_15_allowances_czk,
        base_after_deductions_czk=base_after,
        base_rounded_czk=base_rounded,
        tax_before_credits_czk=tax_before,
        tax_after_taxpayer_credit_czk=tax_after_taxpayer,
        tax_after_spouse_credit_czk=tax_after_spouse,
        child_bonus_czk=child_bonus,
        child_bonus_eligible=child_bonus_eligible,
        child_bonus_min_income_czk=min_income_for_bonus,
        tax_final_czk=tax_final,
        bonus_to_pay_czk=bonus_to_pay,
        spouse_credit_applied_czk=spouse_credit,
    )


def compute_insurance(inp: Inputs, base_profit_czk: int) -> InsuranceResults:
    validate_rate_0_1("zp_vym_base_share", inp.zp_vym_base_share)
    validate_rate_0_1("sp_vym_base_share", inp.sp_vym_base_share)
    validate_rate_0_1("zp_min_base_share", inp.zp_min_base_share)
    validate_rate_0_1("sp_min_base_share", inp.sp_min_base_share)
    validate_rate_0_1("sp_min_base_share_secondary", inp.sp_min_base_share_secondary)
    validate_rate_0_1("zp_rate", inp.zp_rate)
    validate_rate_0_1("sp_rate", inp.sp_rate)
    nonneg_int("sp_threshold_secondary_czk", inp.sp_threshold_secondary_czk)

    zp_vym_base = round_czk_half_up(D(base_profit_czk) * inp.zp_vym_base_share)
    sp_vym_base = round_czk_half_up(D(base_profit_czk) * inp.sp_vym_base_share)

    zp_annual = round_czk_half_up(D(zp_vym_base) * inp.zp_rate)
    sp_annual = ceil_czk(D(sp_vym_base) * inp.sp_rate)

    zp_monthly_calc = round_czk_half_up(D(zp_annual) / D(12))
    sp_monthly_calc = round_czk_half_up(D(sp_annual) / D(12))

    if inp.activity_type not in ("primary", "secondary"):
        raise ValueError("activity_type musí být primary nebo secondary.")

    if inp.activity_type == "secondary":
        zp_annual_min = 0
        sp_annual_min = ceil_czk(
            D(inp.avg_wage_czk) * inp.sp_min_base_share_secondary * inp.sp_rate * D("12")
        )
        sp_due = base_profit_czk > inp.sp_threshold_secondary_czk
        if not sp_due:
            sp_annual = 0
            sp_monthly_calc = 0
    else:
        zp_annual_min = ceil_czk(D(inp.avg_wage_czk) * inp.zp_min_base_share * inp.zp_rate * D("12"))
        sp_annual_min = ceil_czk(D(inp.avg_wage_czk) * inp.sp_min_base_share * inp.sp_rate * D("12"))

    zp_annual_payable = max(zp_annual_min, zp_annual)
    if inp.activity_type == "secondary" and base_profit_czk <= inp.sp_threshold_secondary_czk:
        sp_annual_payable = 0
        min_sp_monthly = 0
    else:
        sp_annual_payable = max(sp_annual_min, sp_annual)
        min_sp_monthly = ceil_czk(D(sp_annual_min) / D("12"))

    min_zp_monthly = ceil_czk(D(zp_annual_min) / D("12")) if zp_annual_min else 0
    zp_monthly_payable = ceil_czk(D(zp_annual_payable) / D(12)) if zp_annual_payable else 0
    sp_monthly_payable = ceil_czk(D(sp_annual_payable) / D(12)) if sp_annual_payable else 0

    return InsuranceResults(
        vym_base_czk=zp_vym_base,  # pro ZP/SP máme rozdílný VZ; reportujeme ZP VZ pro přehled
        min_zp_monthly_czk=min_zp_monthly,
        min_sp_monthly_czk=min_sp_monthly,
        zp_annual_czk=zp_annual,
        zp_monthly_calc_czk=zp_monthly_calc,
        zp_monthly_payable_czk=zp_monthly_payable,
        zp_annual_payable_czk=zp_annual_payable,
        sp_annual_czk=sp_annual,
        sp_monthly_calc_czk=sp_monthly_calc,
        sp_monthly_payable_czk=sp_monthly_payable,
        sp_annual_payable_czk=sp_annual_payable,
    )


def compute(inp: Inputs) -> Results:
    tax = compute_tax(inp)
    ins = compute_insurance(inp, tax.base_profit_czk)
    return Results(tax=tax, ins=ins)
