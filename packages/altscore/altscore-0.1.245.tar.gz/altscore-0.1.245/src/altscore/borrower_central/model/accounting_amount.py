from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
#  Detailed split-bucket money model
#  • Snake-case attribute names for Pythonic access.
#  • camelCase JSON aliases so front-end / API payloads remain idiomatic.
#  • Every numeric value is a STRING to keep original precision and formatting.
# ---------------------------------------------------------------------------


class TaxBreakdown(BaseModel):
    """
    One row per individual tax, withholding, duty, levy, etc.
    """

    # --- identifiers -------------------------------------------------------
    label: str = Field(alias="label", description="Human-readable label")
    code: Optional[str] = Field(default=None, alias="code", description="Short tax code, e.g. 'VAT21'")
    category: Optional[str] = Field(
        default=None,
        alias="category",
        description="Classification bucket: VAT | TURNOVER | EXCISE | WH (withholding) …",
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        alias="jurisdiction",
        description="ISO-3166-2 or custom region code where the tax applies",
    )

    # --- monetary & rate ---------------------------------------------------
    rate: Optional[str] = Field(
        default="0",
        alias="rate",
        description="Rate as string (e.g. '0.21' for 21 %) – string keeps exact decimals",
    )
    base: Optional[str] = Field(
        default="0",
        alias="base",
        description="Taxable base amount (string)",
    )
    amount: str = Field(
        default="0",
        alias="amount",
        description="Tax amount (string) – NEGATIVE for withholdings",
    )

    # --- optional per-row FX ----------------------------------------------
    currency: Optional[str] = Field(
        default=None,
        alias="currency",
        description="Currency for this row if different from document header",
    )
    fx_rate: Optional[str] = Field(
        default=None,
        alias="fxRate",
        description="FX rate applied if row currency ≠ functional currency",
    )

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class Amount(BaseModel):
    """
    Split-bucket monetary object that works for ANY document
    (invoice, credit note, payment order, etc.).

    Math guard-rails:
      gross  = net + tax
      payable = gross − discount − withholding − prepaid
      tax     = sum(tax_breakdown.amount)

    Store values as strings to avoid rounding drift; cast to Decimal as needed.
    """

    # --- always present ----------------------------------------------------
    net: Optional[str] = Field(
        default="0",
        alias="net",
        description="Base amount before taxes or deductions",
    )
    gross: Optional[str] = Field(
        default="0",
        alias="gross",
        description="net + tax (before discounts / withholdings)",
    )
    currency: str = Field(
        ...,
        alias="currency",
        description="ISO-4217 currency code, e.g. 'ARS'",
    )

    # --- often zero, so default "0" ---------------------------------------
    tax: Optional[str] = Field(
        default="0",
        alias="tax",
        description="Total taxes (positive) or sum of withholdings (negative rows included)",
    )
    discount: Optional[str] = Field(
        default="0",
        alias="discount",
        description="Header-level commercial discounts / allowances",
    )
    withholding: Optional[str] = Field(
        default="0",
        alias="withholding",
        description="Total retained taxes that reduce cash out (positive string even though accounting sign is negative)",
    )
    prepaid: Optional[str] = Field(
        default="0",
        alias="prepaid",
        description="Deposits or advances already applied to this document",
    )
    payable: Optional[str] = Field(
        default="0",
        alias="payable",
        description="Cash to be paid now = gross − discount − withholding − prepaid",
    )

    # --- functional-currency helpers --------------------------------------
    fx_rate: Optional[str] = Field(
        default="0",
        alias="fxRate",
        description="Exchange rate to functional currency; '0' if not applicable",
    )

    # --- granular rows -----------------------------------------------------
    tax_breakdown: List[TaxBreakdown] = Field(
        default_factory=list,
        alias="taxBreakdown",
        description="Detailed list of each tax / withholding with base and amount",
    )

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True
