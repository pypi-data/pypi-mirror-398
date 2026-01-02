"""
Absfuyu: Tax calculator
-----------------------
Tax calculator

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["PersonalIncomeTaxCalculator"]


# Library
# ---------------------------------------------------------------------------
from dataclasses import dataclass
from typing import Literal, TypedDict, overload

from absfuyu.core.baseclass import BaseClass, BaseDataclass

# Class
# ---------------------------------------------------------------------------
type TaxLevel = list[tuple[float | int | None, float]]


@dataclass
class TaxLevelResult(BaseDataclass):
    """
    Result for a single tax level.

    Parameters
    ----------
    lower : float
        Lower bound

    upper : float | None
        Upper bound. ``None`` means +infinite

    rate : float
        Tax percentage in decimal (0.1 for 10%)

    amount_taxed : float
        Amount to calculate in current tax level

    tax : float
        Tax amount in current tax level
    """

    lower: float
    upper: float | None
    rate: float
    amount_taxed: float
    tax: float


class TaxCalculationResult(TypedDict):
    """
    Tax calculation result.

    Parameters
    ----------
    gross_income : float
        The input gross income for the calculation.

    deductions : float, optional
        Amount to subtract from gross income before tax.

    taxable_income : float
        Gross income minus deductions.

    per_tax_level : list[TaxLevelResult]
        Detailed breakdown of income taxed at each tax level.

    gross_tax : float
        Total tax before credits.

    tax_credits : float, optional
        Amount subtracted from the computed tax after calculation.

    net_tax : float
        Total tax after applying credits.

    effective_rate : float
        Ratio of net tax to gross income (net_tax / gross_income).

    marginal_rate : float
        Tax rate applied to the last amount of money of taxable income.
    """

    gross_income: float
    deductions: float
    taxable_income: float
    per_tax_level: list[TaxLevelResult]
    gross_tax: float
    tax_credits: float
    net_tax: float
    effective_rate: float
    marginal_rate: float


class TaxCalculationResultRaw(TypedDict):
    """
    Tax calculation result.

    Parameters
    ----------
    gross_income : float
        The input gross income for the calculation.

    deductions : float, optional
        Amount to subtract from gross income before tax.

    taxable_income : float
        Gross income minus deductions.

    per_tax_level : list[TaxLevelResult]
        Detailed breakdown of income taxed at each tax level.

    gross_tax : float
        Total tax before credits.

    tax_credits : float, optional
        Amount subtracted from the computed tax after calculation.

    net_tax : float
        Total tax after applying credits.

    effective_rate : float
        Ratio of net tax to gross income (net_tax / gross_income).

    marginal_rate : float
        Tax rate applied to the last amount of money of taxable income.
    """

    gross_income: float
    deductions: float
    taxable_income: float
    per_tax_level: list[dict[str, float | None]]
    gross_tax: float
    tax_credits: float
    net_tax: float
    effective_rate: float
    marginal_rate: float


class PersonalIncomeTaxCalculator(BaseClass):
    """
    Progressive personal income tax calculator.

    Parameters
    ----------
    tax_levels : list[tuple[float | int | None, float]], optional
        Ordered list of tax levels.
        Each tax level is represented as a tuple of (upper_bound, rate),
        where ``upper_bound`` is the cumulative upper limit of the tax level.
        Use ``None`` for the last tax level (no upper limit).
        Example: ``[(10000, 0.10), (50000, 0.2), (None, 0.3)]``.
        Set to ``None`` to have 0% tax rate, by default ``None``

    deductions : float, optional
        Amount to subtract from gross income before tax, by default 0.0

    tax_credits : float, optional
        Amount subtracted from the computed tax after calculation, by default 0.0

    Attributes
    ----------
    gross_income : float
        The input gross income for the calculation.

    taxable_income : float
        Gross income minus deductions.

    per_tax_level : list[TaxLevelResult]
        Detailed breakdown of income taxed at each tax level.

    gross_tax : float
        Total tax before credits.

    net_tax : float
        Total tax after applying credits.

    effective_rate : float
        Ratio of net tax to gross income.

    marginal_rate : float
        Tax rate applied to the last amount of money of taxable income.


    Example:
    --------
    >>> tax_levels = [(100, 0.05), (None, 0.1)]
    >>> cal = PersonalIncomeTaxCalculator(tax_levels)
    >>> cal.calculate(500)
    >>> cal.to_dict(raw=True)
    {...}

    >>> cal.interpret_result()
    ===== Tax information =====
    Taxable income: 500.00 (500.00 - 0.00)
    - Level 1: 0.00 - 100.00 @ 5.0%: 100.00 -> tax 5.00
    - Level 2: 100.00 - 500.00 @ 10.0%: 400.00 -> tax 40.00
    Net tax: 45.00 (45.00 - 0.00)
    Effective rate: 9.00%
    Marginal rate: 10.0%
    """

    def __init__(self, tax_levels: TaxLevel | None = None, deductions: float = 0.0, tax_credits: float = 0.0) -> None:
        """
        Progressive personal income tax calculator.

        Parameters
        ----------
        tax_levels : list[tuple[float | int | None, float]], optional
            Ordered list of tax levels.
            Each tax level is represented as a tuple of (upper_bound, rate),
            where ``upper_bound`` is the cumulative upper limit of the tax level.
            Use ``None`` for the last tax level (no upper limit).
            Example: ``[(10000, 0.10), (50000, 0.2), (None, 0.3)]``.
            Set to ``None`` to have 0% tax rate, by default ``None``

        deductions : float, optional
            Amount to subtract from gross income before tax, by default 0.0

        tax_credits : float, optional
            Amount subtracted from the computed tax after calculation, by default 0.0
        """
        self.tax_levels = [] if tax_levels is None else tax_levels
        self.deductions = deductions
        self.tax_credits = tax_credits

        # Results populated after calculation
        self.gross_income: float = 0.0
        self.taxable_income: float = 0.0
        self.per_tax_level: list[TaxLevelResult] = []
        self.gross_tax: float = 0.0
        self.net_tax: float = 0.0
        self.effective_rate: float = 0.0
        self.marginal_rate: float = 0.0

    def calculate(self, gross_income: float) -> None:
        """
        Compute tax for a given gross income.

        Parameters
        ----------
        gross_income : float
            Total gross income (unless tax levels are defined otherwise).
        """
        if gross_income < 0:
            raise ValueError("gross_income must be non-negative")

        self.gross_income = gross_income
        self.taxable_income = max(0.0, gross_income - max(0.0, self.deductions))

        self.per_tax_level = []
        prev_upper = 0.0
        remaining = self.taxable_income
        self.gross_tax = 0.0
        self.marginal_rate = 0.0

        for upper, rate in self.tax_levels:
            lower = prev_upper
            if upper is None:
                amount_taxed = remaining
            else:
                band = upper - prev_upper
                amount_taxed = min(band, max(0.0, remaining))
            tax = max(0.0, amount_taxed) * rate
            self.per_tax_level.append(TaxLevelResult(lower, upper, rate, amount_taxed, tax))
            self.gross_tax += tax
            remaining -= amount_taxed
            prev_upper = upper if upper is not None else prev_upper
            if remaining <= 1e-9:
                self.marginal_rate = rate
                break
            self.marginal_rate = rate

        self.net_tax = max(0.0, self.gross_tax - max(0.0, self.tax_credits))
        self.effective_rate = self.net_tax / gross_income if gross_income > 0 else 0.0

    @overload
    def to_dict(self) -> TaxCalculationResult: ...  # type: ignore

    @overload
    def to_dict(self, *, raw: Literal[True] = ...) -> TaxCalculationResultRaw: ...

    def to_dict(self, *, raw: bool = False) -> TaxCalculationResult | TaxCalculationResultRaw:
        """
        Returns calculation result in dict format

        Parameters
        ----------
        raw : bool, optional
            Convert every value to dict, by default ``False``

        Returns
        -------
        TaxCalculationResult
            Tax calculation result
        """
        result: TaxCalculationResult = {
            "gross_income": self.gross_income,
            "deductions": self.deductions,
            "taxable_income": self.taxable_income,
            "per_tax_level": self.per_tax_level,
            "gross_tax": self.gross_tax,
            "tax_credits": self.tax_credits,
            "net_tax": self.net_tax,
            "effective_rate": self.effective_rate,
            "marginal_rate": self.marginal_rate,
        }
        if raw:
            result_raw: TaxCalculationResultRaw = result  # type: ignore
            result_raw["per_tax_level"] = [x.to_dict() for x in result["per_tax_level"]]
            return result
        return result

    def interpret_result(self) -> str:
        result = self.to_dict()
        text = ["===== Tax information ====="]

        # text.append(f"Gross income: {result['gross_income']:,}")
        # text.append(f"Deduction: {result['deductions']:,}")
        # text.append(f"Taxable income: {result['taxable_income']:,}")
        text.append(
            f"Taxable income: {result['taxable_income']:,.2f} ({result['gross_income']:,.2f} - {result['deductions']:,.2f})"
        )

        for idx, tax_level in enumerate(result["per_tax_level"], start=1):
            upper = f"{tax_level.upper:,.2f}" if tax_level.upper is not None else f"{self.gross_income:,.2f}"
            text.append(
                f"- Level {idx}: {tax_level.lower:,.2f} - {upper} @ {tax_level.rate*100:.1f}%: {tax_level.amount_taxed:,.2f} -> tax {tax_level.tax:,.2f}"
            )

        # text.append(f"Gross tax: {result['gross_tax']:,}")
        # text.append(f"Tax credits: {result['tax_credits']:,}")
        # text.append(f"Net tax: {result['net_tax']:,}")
        text.append(f"Net tax: {result['net_tax']:,.2f} ({result['gross_tax']:,.2f} - {result['tax_credits']:,.2f})")

        text.append(f"Effective rate: {result['effective_rate']*100:.2f}%")
        text.append(f"Marginal rate: {result['marginal_rate']*100:.1f}%")
        return "\n".join(text)
