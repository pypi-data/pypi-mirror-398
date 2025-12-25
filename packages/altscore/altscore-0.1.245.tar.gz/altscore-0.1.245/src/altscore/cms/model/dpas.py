from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.cms.model.generics import GenericSyncModule, GenericAsyncModule
from altscore.cms.model.common import Money, Schedule, Terms
import datetime as dt
from dateutil.parser import parse as date_parser


class Client(BaseModel):
    id: str = Field(alias="clientId")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    partner_id: str = Field(alias="partnerId")
    external_id: str = Field(alias="externalId")
    email: str = Field(alias="email")
    legal_name: str = Field(alias="legalName")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class DPAFlowAPIDTO(BaseModel):
    id: str = Field(alias="flowId")
    tenant: str = Field(alias="tenant")
    reference_id: str = Field(alias="referenceId")
    status: str = Field(alias="status")
    client: Client = Field(alias="client")
    schedule: List[Schedule] = Field(alias="schedule")
    terms: Terms = Field(alias="terms")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    cancellation_reason: Optional[str] = Field(None, alias="cancellationReason")
    close_reason: Optional[str] = Field(None, alias="closeReason")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class CreateDPAFlowDTO(BaseModel):
    amount: Money = Field(alias="amount")
    disbursement_date: str = Field(alias="disbursementDate")
    client_id: str = Field(alias="clientId", default=None)
    reference_id: str = Field(alias="referenceId", default=None)
    product_id: Optional[str] = Field(alias="productId", default=None)
    external_id: Optional[str] = Field(alias="externalId", default=None)
    terms: Optional[Terms] = Field(alias="terms")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class AdvanceSimulationFlowDTO(BaseModel):
    amount: Money = Field(alias="amount")
    disbursement_date: str = Field(alias="disbursementDate")
    client_id: str = Field(alias="clientId", default=None)
    external_id: Optional[str] = Field(alias="externalId", default=None)
    metadata: Optional[dict] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class InvoiceInstallment(BaseModel):
    due_date: str = Field(alias="dueDate")
    number: int = Field(alias="number")
    interest: Money = Field(alias="interest")
    amount: Money = Field(alias="amount")
    tax: Money = Field(alias="tax")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Invoice(BaseModel):
    amount: Money = Field(alias="amount")
    invoice_date: str = Field(alias="invoiceDate")
    installments: Optional[List[InvoiceInstallment]] = Field(alias="installments", default=None)
    notes: str = Field(alias="notes")
    reference_id: str = Field(alias="referenceId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class ApproveDPAFlowDTO(BaseModel):
    amount: Money = Field(alias="amount")
    disbursement_date: str = Field(alias="disbursementDate")
    client_id: Optional[str] = Field(alias="clientId", default=None)
    external_id: Optional[str] = Field(alias="externalId", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class DPABase:

    @staticmethod
    def _approval(flow_id: str):
        return f"/v1/dpas/{flow_id}/approval"

    @staticmethod
    def _cancellation(flow_id: str):
        return f"/v1/dpas/{flow_id}/cancellation"

    @staticmethod
    def _invoice(flow_id: str):
        return f"/v1/dpas/{flow_id}/invoices"


class DPAFlowAsync(DPABase):
    data: DPAFlowAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DPAFlowAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401_async
    async def approve(self, approve_data: Optional[dict] = None):
        if approve_data is None:
            approve_data = {
                "amount": {
                    "amount": self.data.terms.principal.amount,
                    "currency": self.data.terms.principal.currency
                },
                "clientId": self.data.client.id,
                "disbursementDate": self.data.terms.disbursement_date,
                "referenceId": self.data.reference_id,
            }
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                self._approval(self.data.id),
                headers=self._header_builder(),
                json=ApproveDPAFlowDTO.parse_obj(approve_data).dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            self.data = DPAFlowAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def cancel(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                self._cancellation(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            self.data = DPAFlowAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def submit_invoice(self, invoice_data: dict):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                self._invoice(self.data.id),
                json=Invoice.parse_obj(invoice_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json()

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class DPAFlowSync(DPABase):
    data: DPAFlowAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DPAFlowAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data: DPAFlowAPIDTO = data

    @retry_on_401
    def approve(self, approve_data: Optional[dict] = None):
        if approve_data is None:
            approve_data = {
                "amount": {
                    "amount": self.data.terms.principal.amount,
                    "currency": self.data.terms.principal.currency
                },
                "clientId": self.data.client.id,
                "disbursementDate": self.data.terms.disbursement_date,
                "referenceId": self.data.reference_id,
            }
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                self._approval(self.data.id),
                headers=self._header_builder(),
                json=ApproveDPAFlowDTO.parse_obj(approve_data).dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            self.data = DPAFlowAPIDTO.parse_obj(response.json())

    @retry_on_401
    def cancel(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                self._cancellation(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            self.data = DPAFlowAPIDTO.parse_obj(response.json())

    @retry_on_401
    def submit_invoice(self, invoice_data: dict):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                self._invoice(self.data.id),
                headers=self._header_builder(),
                json=Invoice.parse_obj(invoice_data).dict(by_alias=True, exclude_none=True),
                timeout=300
            )
            raise_for_status_improved(response)
            return response.json()

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class DPAFlowsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            async_resource=DPAFlowAsync,
            retrieve_data_model=DPAFlowAPIDTO,
            create_data_model=CreateDPAFlowDTO,
            update_data_model=None,
            resource="dpas"
        )

    def renew_token(self):
        self.altscore_client.renew_token()

    @retry_on_401_async
    async def create(self, new_entity_data: dict):
        disbursement_date_str = \
            new_entity_data.get("disbursementDate") or new_entity_data.get("disbursement_date")
        if disbursement_date_str is None:
            disbursement_date = dt.date.today().strftime("%Y-%m-%d")
        else:
            disbursement_date = date_parser(disbursement_date_str).strftime("%Y-%m-%d")
        new_entity_data["disbursementDate"] = disbursement_date

        async with httpx.AsyncClient(base_url=self.altscore_client._cms_base_url) as client:
            response = await client.post(
                f"/{self.resource_version}/{self.resource}",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(
                    by_alias=True,
                    exclude_none=True
                ),
                timeout=30
            )
            raise_for_status_improved(response)
            return self.retrieve_data_model.parse_obj(response.json()).id

    @retry_on_401_async
    async def simulate(self, new_entity_data: dict):
        disbursement_date_str = \
            new_entity_data.get("disbursementDate") or new_entity_data.get("disbursement_date")
        if disbursement_date_str is None:
            disbursement_date = dt.date.today().strftime("%Y-%m-%d")
        else:
            disbursement_date = date_parser(disbursement_date_str).strftime("%Y-%m-%d")
        new_entity_data["disbursementDate"] = disbursement_date

        async with httpx.AsyncClient(base_url=self.altscore_client._cms_base_url) as client:
            response = await client.post(
                f"/{self.resource_version}/{self.resource}/simulations",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(
                    by_alias=True,
                    exclude_none=True
                ),
                timeout=30
            )
            raise_for_status_improved(response)
            return self.retrieve_data_model.parse_obj(response.json())

    @retry_on_401_async
    async def simulate_advanced(self, new_entity_data: dict):
        disbursement_date_str = \
            new_entity_data.get("disbursementDate") or new_entity_data.get("disbursement_date")
        if disbursement_date_str is None:
            disbursement_date = dt.date.today().strftime("%Y-%m-%d")
        else:
            disbursement_date = date_parser(disbursement_date_str).strftime("%Y-%m-%d")
        new_entity_data["disbursementDate"] = disbursement_date

        async with httpx.AsyncClient(base_url=self.altscore_client._cms_base_url) as client:
            response = await client.post(
                f"/{self.resource_version}/{self.resource}/advanced/simulations",
                headers=self.build_headers(),
                json=AdvanceSimulationFlowDTO.parse_obj(new_entity_data).dict(
                    by_alias=True,
                    exclude_none=True
                ),
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPAFlowAPIDTO.parse_obj(item) for item in response.json()]


class DPAFlowsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            sync_resource=DPAFlowSync,
            retrieve_data_model=DPAFlowAPIDTO,
            create_data_model=CreateDPAFlowDTO,
            update_data_model=None,
            resource="dpas"
        )

    def renew_token(self):
        self.altscore_client.renew_token()

    @retry_on_401
    def create(self, new_entity_data: dict):
        disbursement_date_str = \
            new_entity_data.get("disbursementDate") or new_entity_data.get("disbursement_date")
        if disbursement_date_str is None:
            disbursement_date = dt.date.today().strftime("%Y-%m-%d")
        else:
            disbursement_date = date_parser(disbursement_date_str).strftime("%Y-%m-%d")
        new_entity_data["disbursementDate"] = disbursement_date
        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.post(
                f"/{self.resource_version}/{self.resource}",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return self.retrieve_data_model.parse_obj(response.json()).id

    @retry_on_401
    def simulate(self, new_entity_data: dict):
        disbursement_date_str = \
            new_entity_data.get("disbursementDate") or new_entity_data.get("disbursement_date")
        if disbursement_date_str is None:
            disbursement_date = dt.date.today().strftime("%Y-%m-%d")
        else:
            disbursement_date = date_parser(disbursement_date_str).strftime("%Y-%m-%d")
        new_entity_data["disbursementDate"] = disbursement_date

        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.post(
                f"/{self.resource_version}/{self.resource}/simulations",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(
                    by_alias=True,
                    exclude_none=True
                ),
                timeout=30
            )
            raise_for_status_improved(response)
            return self.retrieve_data_model.parse_obj(response.json())

    @retry_on_401
    def simulate_advanced(self, new_entity_data: dict):
        disbursement_date_str = \
            new_entity_data.get("disbursementDate") or new_entity_data.get("disbursement_date")
        if disbursement_date_str is None:
            disbursement_date = dt.date.today().strftime("%Y-%m-%d")
        else:
            disbursement_date = date_parser(disbursement_date_str).strftime("%Y-%m-%d")
        new_entity_data["disbursementDate"] = disbursement_date

        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.post(
                f"/{self.resource_version}/{self.resource}/advanced/simulations",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(
                    by_alias=True,
                    exclude_none=True
                ),
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPAFlowAPIDTO.parse_obj(item) for item in response.json()]
