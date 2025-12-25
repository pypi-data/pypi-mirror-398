from pydantic import BaseModel, Field
from typing import Optional, List


class DisbursementSettings(BaseModel):
    disburse_to: str = Field(alias="disburseTo")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Money(BaseModel):
    amount: str
    currency: str
    display: Optional[str] = Field(None, alias="display")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class ScheduleOriginalAmounts(BaseModel):
    fees: Money = Field(alias="fees")
    interest: Money = Field(alias="interest")
    principal: Money = Field(alias="principal")
    taxes: Money = Field(alias="taxes")
    total: Money = Field(alias="total")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Schedule(BaseModel):
    due_date: str = Field(alias="dueDate")
    number: int = Field(alias="number")
    original_amounts: ScheduleOriginalAmounts = Field(alias="originalAmounts")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class InterestRate(BaseModel):
    period: int = Field(alias="period")
    rate: str = Field(alias="rate")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class TermsPenalties(BaseModel):
    charge_code: str = Field(alias="chargeCode")
    compute_every: int = Field(alias="computeEvery")
    enabled: Optional[bool] = Field(None, alias="enabled")
    grace_period: int = Field(alias="gracePeriod")
    rate: InterestRate = Field(alias="rate")
    times_to_compute: int = Field(alias="timesToCompute")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class TermsFees(BaseModel):
    amount: Optional[Money] = Field(alias="amount")
    amount_rate: Optional[str] = Field(alias="amountRate")
    calculation_type: Optional[str] = Field(alias="calculationType")
    description: Optional[str] = Field(alias="description")
    name: Optional[str] = Field(alias="name")
    tax: Optional[int] = Field(alias="tax")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Terms(BaseModel):
    amortization_type: str = Field(alias="amortizationType")
    disbursement_date: Optional[str] = Field(alias="disbursementDate")
    installments: int = Field(alias="installments")
    fees: Optional[List[Optional[TermsFees]]] = Field(alias="fees", default=None)
    interest: Money = Field(alias="interest")
    interest_calculate_type: str = Field(alias="interestCalculateType")
    interest_rate: InterestRate = Field(alias="interestRate")
    interest_tax: float = Field(alias="interestTax")
    principal: Optional[Money] = Field(alias="principal")
    repayEvery: int = Field(alias="repayEvery")
    sub_total_amount: Optional[Money] = Field(alias="subTotalAmount", default=None)
    penalties: Optional[List[TermsPenalties]] = Field(alias="penalties", default=None)
    name: Optional[str] = Field(alias="name", default=None)
    calendar_type: Optional[str] = Field(alias="calendarType", default=None)
    loan_term_duration: Optional[int] = Field(alias="loanTermDuration", default=None)
    disbursement_settings: Optional[DisbursementSettings] = Field(alias="disbursementSettings", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True
