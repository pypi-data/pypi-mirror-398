from typing import List, Optional, Union
from pydantic import BaseModel, Field
from altscore.cms.model.common import Money, DisbursementSettings


class InterestRate(BaseModel):
    type: str
    period: int
    period_time: int = Field(alias="periodTime")
    tier: dict

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class PenaltyRate(BaseModel):
    rate: str
    period: int

class Penalty(BaseModel):
    charge_code: str = Field(alias="chargeCode")
    grace_period: int = Field(alias="gracePeriod")
    rate: PenaltyRate
    compute_every: int = Field(alias="computeEvery")
    times_to_compute: int = Field(alias="timesToCompute")
    enabled: bool

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class ProductTier(BaseModel):
    minimum: Money
    maximum: Money

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True



class DPAProductAPIDTO(BaseModel):
    id: str = Field(alias="productId")
    name: str
    description: Optional[str]
    partner_id: str = Field(alias="partnerId")
    amortization_type: str = Field(alias="amortizationType")
    repay_every: int = Field(alias="repayEvery")
    installments: int
    interest_rate: InterestRate = Field(alias="interestRate")
    interest_tax: float = Field(alias="interestTax")
    penalties: List[Union[Penalty,None]] = Field(alias="penalties", default=[])
    product_tier: Optional[ProductTier] = Field(alias="productTier", default=None)
    disbursement_settings: DisbursementSettings = Field(alias="disbursementSettings")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)
    status: str
    tenant: str

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True



class CreateDPAProductAPIDTO(BaseModel):
    name: str = Field(alias="name")
    description: Optional[str] = Field(alias="description")
    amortization_type: str = Field(alias="amortizationType")
    disbursement_settings: DisbursementSettings = Field(alias="disbursementSettings")
    installments: int = Field(alias="installments")
    interest_calculate_type: str = Field(alias="interestCalculateType")
    interest_rate: InterestRate = Field(alias="interestRate")
    penalties: List[Union[Penalty, None]] = Field(alias="penalties", default=[])
    product_tier: Optional[ProductTier] = Field(alias="productTier", default=None)
    repay_every: int = Field(alias="repayEvery")
    interest_tax: float = Field(alias="interestTax")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class UpdateDPAProductAPIDTO(BaseModel):
    name: Optional[str] = Field(alias="name", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    amortization_type: Optional[str] = Field(alias="amortizationType", default=None)
    disbursement: Optional[DisbursementSettings] = Field(alias="disbursementSettings", default=None)
    installments: Optional[int] = Field(alias="installments", default=None)
    interest_calculate_type: Optional[str] = Field(alias="interestCalculateType", default=None)
    interest_rate: Optional[InterestRate] = Field(alias="interestRate", default=None)
    penalties: Optional[List[Penalty]] = Field(alias="penalties", default=None)
    product_tier: Optional[ProductTier] = Field(alias="productTier", default=None)
    repay_every: Optional[int] = Field(alias="repayEvery", default=None)
    interest_tax: float = Field(alias="interestTax")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True



class ProductBase:

    def __init__(self, base_url):
        self.base_url = base_url


class ProductAsync(ProductBase):
    data: DPAProductAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DPAProductAPIDTO):
        super().__init__(base_url)
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.partner_id})"


class ProductSync(ProductBase):
    data: DPAProductAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DPAProductAPIDTO):
        super().__init__(base_url)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.partner_id})"

