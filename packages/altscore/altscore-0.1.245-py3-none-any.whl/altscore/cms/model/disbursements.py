from typing import Optional
from pydantic import BaseModel, Field
import httpx

from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.cms.model.generics import GenericAsyncModule, GenericSyncModule

class AmountInfo(BaseModel):
    amount: str = Field(alias="amount")
    currency: str = Field(alias="currency")
    display: Optional[str] = Field(None, alias="display")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class ClientInfo(BaseModel):
    client_id: str = Field(alias="clientId")
    external_id: str = Field(alias="externalId")
    legal_name: str = Field(alias="legalName")
    tax_id: str = Field(alias="taxId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class PartnerInfo(BaseModel):
    name: str = Field(alias="name")
    partner_id: str = Field(alias="partnerId")
    tax_id: str = Field(alias="taxId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class PayerInfo(BaseModel):
    account_number: str = Field(alias="accountNumber")
    institution: int = Field(alias="institution")
    institution_name: str = Field(alias="institutionName")
    name: str = Field(alias="name")
    tax_id: Optional[str] = Field(alias="rfcCurp", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class DisbursementAPIDTO(BaseModel):
    id: str = Field(alias="payOrderId")
    amount: AmountInfo = Field(alias="amount")
    amount_transferred: AmountInfo = Field(alias="amountTransferred")
    client: ClientInfo = Field(alias="client")
    created_at: str = Field(alias="createdAt")
    debt_id: str = Field(alias="debtId")
    disbursement_date: str = Field(alias="disbursementDate")
    gateway: str = Field(alias="gateway")
    notes: Optional[str] = Field(alias="notes", default=None)
    partner: PartnerInfo = Field(alias="partner")
    payer: Optional[PayerInfo] = Field(alias="payer", default=None)
    beneficiary: Optional[PayerInfo] = Field(alias="beneficiary", default=None)
    payment_date: Optional[str] = Field(alias="paymentDate", default=None)
    reference_id: str = Field(alias="referenceId")
    reference_number: int = Field(alias="referenceNumber")
    status: str = Field(alias="status")
    tracking_key: str = Field(alias="trackingKey")
    updated_at: str = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class DisbursementBase:
    @staticmethod
    def _conciliate_disbursement(payOrderId: str):
        return f"/v1/disbursements/{payOrderId}/reconcile"
    
    @staticmethod
    def _disbursement_success(payOrderId: str):
        return f"/v1/disbursements/{payOrderId}/success"

class DisbursementAsync(DisbursementBase):
    data: DisbursementAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DisbursementAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"
    
    @retry_on_401_async
    async def conciliate_disbursement(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                self._conciliate_disbursement(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def disbursement_success(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                self._disbursement_success(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

class DisbursementSync(DisbursementBase):
    data: DisbursementAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DisbursementAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"
    
    @retry_on_401
    def conciliate_disbursement(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                self._conciliate_disbursement(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
    
    @retry_on_401
    def disbursement_success(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                self._disbursement_success(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

class DisbursementAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            async_resource=DisbursementAsync,
            retrieve_data_model=DisbursementAPIDTO,
            create_data_model=None,
            update_data_model=None,
            resource="disbursements"
        )

class DisbursementSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            sync_resource=DisbursementSync,
            retrieve_data_model=DisbursementAPIDTO,
            create_data_model=None,
            update_data_model=None,
            resource="disbursements"
        )