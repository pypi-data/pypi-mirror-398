from typing import List, Optional
from pydantic import BaseModel, Field


class AccountHolder(BaseModel):
    client_id: str = Field(alias="clientId")
    partner_id: str = Field(alias="partnerId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Reference(BaseModel):
    account_reference_id: str = Field(alias="accountReferenceId")
    gateway_id: str = Field(alias="gatewayId")
    provider: str = Field(alias="provider")
    reference: str = Field(alias="reference")
    status: str = Field(alias="status")
    created_at: str = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class PaymentAccountAPIDTO(BaseModel):
    account_id: str = Field(alias="accountId")
    account_holder: AccountHolder = Field(alias="accountHolder")
    references: Optional[List[Reference]] = Field(alias="references", default=[])
    created_at: str = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

    def get_active_references_by_provider(self, provider: str):
        return [reference for reference in self.references if
                reference.provider == provider and reference.status == "ACTIVE"]


class CreatePaymentAccountDTO(BaseModel):
    partner_id: str = Field(alias="partnerId")
    client_id: str = Field(alias="clientId")
    auto_create_references: bool = Field(alias="autoCreateReferences", default=True)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class CreatePaymentReferenceDTO(BaseModel):
    provider: Optional[str] = Field(alias="provider", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True
