from pydantic import BaseModel, Field
from typing import Optional
from altscore.cms.model.generics import GenericSyncModule, GenericAsyncModule


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

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class PaymentOrderAPIDTO(BaseModel):
    id: str = Field(alias="payOrderId")
    amount: AmountInfo = Field(alias="amount")
    amount_transferred: AmountInfo = Field(alias="amountTransferred")
    client: ClientInfo = Field(alias="client")
    created_at: str = Field(alias="createdAt")
    debt_id: str = Field(alias="debtId")
    disbursement_date: str = Field(alias="disbursementDate")
    gateway: str = Field(alias="gateway")
    notes: Optional[str] = Field(alias="notes")
    partner: PartnerInfo = Field(alias="partner")
    payer: Optional[PayerInfo] = Field(alias="payer", default=None)
    payment_date: Optional[str] = Field(alias="paymentDate", default=None)
    reference_id: str = Field(alias="referenceId")
    reference_number: int = Field(alias="referenceNumber")
    status: str = Field(alias="status")
    tracking_key: str = Field(alias="trackingKey")
    updated_at: str = Field(alias="updatedAt")
    version: int = Field(alias="version")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class PaymentOrdersBase:

    @staticmethod
    def _payment_orders():
        return f"/v1/payment-orders"


class PaymentOrdersAsync(PaymentOrdersBase):
    data: PaymentOrderAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: PaymentOrderAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class PaymentOrdersSync(PaymentOrdersBase):
    data: PaymentOrderAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: PaymentOrderAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class PaymentOrdersAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            async_resource=PaymentOrdersAsync,
            retrieve_data_model=PaymentOrderAPIDTO,
            create_data_model=None,
            update_data_model=None,
            resource="payment-orders"
        )


class PaymentOrdersSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            sync_resource=PaymentOrdersSync,
            retrieve_data_model=PaymentOrderAPIDTO,
            create_data_model=None,
            update_data_model=None,
            resource="payment-orders"
        )
