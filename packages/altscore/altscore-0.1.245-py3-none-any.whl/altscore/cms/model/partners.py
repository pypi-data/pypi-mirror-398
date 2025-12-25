import asyncio

from pydantic import BaseModel, Field
from typing import Optional, List
import httpx
from altscore.cms.model.calendars import CreateCalendarAPIDTO, DPACalendarAPIDTO
from altscore.cms.model.dpa_segmentation import DPASegmentationAPIDTO, CreateDPASegmentationDTO, \
    UpdateDPASegmentationDTO
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.cms.model.generics import GenericSyncModule, GenericAsyncModule
from altscore.cms.helpers import build_headers
from altscore.cms.model.dpa_products import DPAProductAPIDTO, CreateDPAProductAPIDTO, UpdateDPAProductAPIDTO
from altscore.borrower_central.utils import clean_dict, convert_to_dash_case
from altscore.cms.model.disbursement_accounts import  BankAccount, DisbursementAccountBaseModel, CreateDisbursementPartnerAccountDTO
from altscore.cms.model.credit_accounts import CreditAccountSync, CreditAccountAPIDTO


class PartnerAPIDTO(BaseModel):
    id: str = Field(alias="partnerId")
    avatar: Optional[str] = Field(alias="avatar", default="")
    name: str = Field(alias="name")
    short_name: str = Field(alias="shortName")
    partner_id: str = Field(alias="partnerId")
    status: str = Field(alias="status")
    tax_id: str = Field(alias="taxId")
    is_aggregator: bool = Field(alias="isAggregator")
    email: str = Field(alias="email")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class CreatePartnerDTO(BaseModel):
    name: str = Field(alias="name")
    short_name: str = Field(alias="shortName")
    email: str = Field(alias="email")
    tax_id: str = Field(alias="taxId")
    is_aggregator: Optional[bool] = Field(alias="isAggregator", default=False)
    avatar: Optional[str] = Field(alias="avatar", default="")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class DPASettingsDefaults(BaseModel):
    currency: Optional[str] = Field(alias="currency", default=None)
    flow_expiration_minutes: Optional[int] = Field(alias="flowExpirationMinutes", default=None)
    closing_balance_threshold: Optional[str] = Field(alias="closingBalanceThreshold", default=None)
    product_id: Optional[str] = Field(alias="productId", default=None)
    segmentation_id: Optional[str] = Field(alias="segmentationId", default=None)
    calendar_type: Optional[str] = Field(alias="calendarType", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class DPASettingsAPIDTO(BaseModel):
    partner_id: Optional[str] = Field(alias="partnerId")
    defaults: Optional[DPASettingsDefaults] = Field(alias="defaults", default=None)
    timezone: Optional[str] = Field(alias="timezone", default=None)
    on_approve_flow_reserve_all_assigned_amount: Optional[bool] = \
        Field(alias="onApproveFlowReserveAllAssignedAmount", default=None)
    invoice_over_limit: Optional[float] = Field(alias="invoiceOverLimit", default=None)
    reserve_on_start: Optional[bool] = Field(alias="reserveOnStart", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class PartnerBase:

    def __init__(self, base_url):
        self.base_url = base_url

    def _get_partner_dpa_products( self, partner_id:str, status: Optional[str]= None, sort_by: Optional[str] = None,
                per_page: Optional[int] = None, page: Optional[int] = None, sort_direction: Optional[str] = None
        ) -> (str, dict):
            query = {
                "status": status,
                "sort-by": sort_by,
                "per-page": per_page,
                "page": page,
                "sort-direction": sort_direction
            }
            return f"{self.base_url}/v2/partners/{partner_id}/products/dpa", clean_dict(query)

    def _get_partner_dpa_segmentations(self,
                                       partner_id:str,
                                       product_ids: Optional[List[str]]= None,
                                       status: Optional[str]= None,
                                       sort_by: Optional[str] = None,
                                        per_page: Optional[int] = None,
                                       page: Optional[int] = None,
                                       sort_direction: Optional[str] = None
        ) -> (str, dict):
        query = {
            "product-ids": ",".join(product_ids) if product_ids else None,
            "status": status,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v2/partners/{partner_id}/segmentations/dpa", clean_dict(query)

    def _get_partner_dpa_calendar (self, partner_id:str) -> (str, dict):
        return f"{self.base_url}/v2/partners/{partner_id}/calendar/dpa", {}
    
    @staticmethod
    def _create_disbursement_account(country: str):
        return f"/v1/disbursements/accounts/{country}/disbursement"

class PartnerAsync(PartnerBase):
    data: PartnerAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: PartnerAPIDTO):
        super().__init__(base_url)
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__})"

    @retry_on_401_async
    async def get_dpa_products(self, **kwargs) -> List[DPAProductAPIDTO]:
        url, query = self._get_partner_dpa_products(self.data.partner_id, **kwargs)
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query,
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPAProductAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401_async
    async def get_dpa_product(self, product_id: str) -> Optional[DPAProductAPIDTO]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}",
                headers=self._header_builder(),
                timeout=30
            )
            if response.status_code == 404:
                return None
            elif response.status_code == 200:
                return DPAProductAPIDTO.parse_obj(response.json())
            raise_for_status_improved(response)

    @retry_on_401_async
    async def create_dpa_product(self, new_entity_data:dict) -> str:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                f"/v2/partners/{self.data.partner_id}/products/dpa",
                json=CreateDPAProductAPIDTO.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json()["productId"]

    @retry_on_401_async
    async def delete_dpa_product(self, product_id: str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.delete(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def update_dpa_product(self, product_id: str, patch_data:dict) -> DPAProductAPIDTO:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.patch(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}",
                json=UpdateDPAProductAPIDTO.parse_obj(patch_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPAProductAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def put_dpa_product_status(self, product_id: str, status: str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}/status",
                headers=self._header_builder(),
                json={"status": status},
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def get_dpa_segmentations(self, **kwargs) -> List[DPASegmentationAPIDTO]:
        url, query = self._get_partner_dpa_segmentations(self.data.partner_id, **kwargs)
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query,
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPASegmentationAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401_async
    async def get_dpa_segmentation(self, segmentation_id: str) -> Optional[DPASegmentationAPIDTO]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}",
                headers=self._header_builder(),
                timeout=30
            )
            if response.status_code == 404:
                return None
            elif response.status_code == 200:
                return DPASegmentationAPIDTO.parse_obj(response.json())
            raise_for_status_improved(response)

    @retry_on_401_async
    async def create_dpa_segmentation(self, new_entity_data:dict) -> str:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa",
                json=CreateDPASegmentationDTO.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json()["segmentationId"]

    @retry_on_401_async
    async def update_dpa_segmentation(self, segmentation_id: str, patch_data:dict) -> DPASegmentationAPIDTO:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.patch(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}",
                json=UpdateDPASegmentationDTO.parse_obj(patch_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPASegmentationAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def put_dpa_segmentation_status(self, segmentation_id: str, status: str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}/status",
                headers=self._header_builder(),
                json={"status": status},
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def delete_dpa_segmentation(self, segmentation_id: str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.delete(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def get_dpa_calendars(self) -> List[DPACalendarAPIDTO]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"{self.base_url}/v2/partners/{self.data.partner_id}/calendars/dpa",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPACalendarAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401_async
    async def get_dpa_calendar(self, calendar_id: str) -> Optional[DPACalendarAPIDTO]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"/v2/partners/{self.data.partner_id}/calendars/dpa/{calendar_id}",
                headers=self._header_builder(),
                timeout=30
            )
            if response.status_code == 404:
                return None
            elif response.status_code == 200:
                return DPACalendarAPIDTO.parse_obj(response.json())
            raise_for_status_improved(response)

    @retry_on_401_async
    async def create_dpa_calendar(self, new_entity_data:dict) -> str:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                f"/v2/partners/{self.data.partner_id}/calendars/dpa",
                json=CreateCalendarAPIDTO.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json()["calendarId"]


    @retry_on_401_async
    async def delete_dpa_calendar(self, calendar_id:str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.delete(
                f"/v2/partners/{self.data.partner_id}/calendars/dpa/{calendar_id}",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def create_disbursement_account(self, country: str, bank_account: dict) -> DisbursementAccountBaseModel:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                self._create_disbursement_account(country),
                headers=self._header_builder(partner_id=self.data.partner_id),
                json=CreateDisbursementPartnerAccountDTO.parse_obj({
                    "id": self.data.partner_id,
                    "partnerId": self.data.partner_id,
                    "bankAccount": BankAccount.parse_obj(bank_account).dict(by_alias=True, exclude_none=True),
                    "taxId": self.data.tax_id,
                    "name": self.data.name,
                }).dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return DisbursementAccountBaseModel.parse_obj(response.json())


class PartnerSync(PartnerBase):
    data: PartnerAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: PartnerAPIDTO):
        super().__init__(base_url)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.partner_id})"

    @retry_on_401
    def get_dpa_products(self, **kwargs) -> List[DPAProductAPIDTO]:
        url, query = self._get_partner_dpa_products(self.data.partner_id, **kwargs)
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query,
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPAProductAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401
    def get_dpa_product(self, product_id: str) -> Optional[DPAProductAPIDTO]:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}",
                headers=self._header_builder(),
                timeout=30
            )
            if response.status_code == 404:
                return None
            elif response.status_code == 200:
                return DPAProductAPIDTO.parse_obj(response.json())
            raise_for_status_improved(response)

    @retry_on_401
    def create_dpa_product(self, new_entity_data:dict):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                f"/v2/partners/{self.data.partner_id}/products/dpa",
                json=CreateDPAProductAPIDTO.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json()["productId"]

    @retry_on_401
    def delete_dpa_product(self, product_id: str) -> None:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.delete(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401
    def update_dpa_product(self, product_id: str, patch_data:dict) -> DPAProductAPIDTO:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.patch(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}",
                json=UpdateDPAProductAPIDTO.parse_obj(patch_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPAProductAPIDTO.parse_obj(response.json())

    @retry_on_401
    def put_dpa_product_status(self, product_id: str, status: str) -> None:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"/v2/partners/{self.data.partner_id}/products/dpa/{product_id}/status",
                headers=self._header_builder(),
                json={"status": status},
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401
    def get_dpa_segmentations(self, **kwargs) -> List[DPASegmentationAPIDTO]:
        url, query = self._get_partner_dpa_segmentations(self.data.partner_id, **kwargs)
        with httpx.Client(base_url=self.base_url) as client:
            response =  client.get(
                url,
                headers=self._header_builder(),
                params=query,
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPASegmentationAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401
    def get_dpa_segmentation(self, segmentation_id: str) -> Optional[DPASegmentationAPIDTO]:
         with httpx.Client(base_url=self.base_url) as client:
            response =  client.get(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}",
                headers=self._header_builder(),
                timeout=30
            )
            if response.status_code == 404:
                return None
            elif response.status_code == 200:
                return DPASegmentationAPIDTO.parse_obj(response.json())
            raise_for_status_improved(response)

    @retry_on_401
    def create_dpa_segmentation(self, new_entity_data: dict) -> str:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa",
                json=CreateDPASegmentationDTO.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json()["segmentationId"]

    @retry_on_401
    def update_dpa_segmentation(self, segmentation_id: str, patch_data: dict) -> DPASegmentationAPIDTO:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.patch(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}",
                json=UpdateDPASegmentationDTO.parse_obj(patch_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPASegmentationAPIDTO.parse_obj(response.json())

    @retry_on_401
    def put_dpa_segmentation_status(self, segmentation_id: str, status: str) -> None:
        with httpx.Client(base_url=self.base_url) as client:
            response =  client.put(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}/status",
                headers=self._header_builder(),
                json={"status": status},
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401
    def delete_dpa_segmentation(self, segmentation_id: str) -> None:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.delete(
                f"/v2/partners/{self.data.partner_id}/segmentations/dpa/{segmentation_id}",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401
    def get_dpa_calendars(self) -> List[DPACalendarAPIDTO]:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"{self.base_url}/v2/partners/{self.data.partner_id}/calendars/dpa",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [DPACalendarAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401
    def get_dpa_calendar(self, calendar_id: str) -> Optional[DPACalendarAPIDTO]:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"/v2/partners/{self.data.partner_id}/calendars/dpa/{calendar_id}",
                headers=self._header_builder(),
                timeout=30
            )
            if response.status_code == 404:
                return None
            elif response.status_code == 200:
                return DPACalendarAPIDTO.parse_obj(response.json())
            raise_for_status_improved(response)

    @retry_on_401
    def create_dpa_calendar(self, new_entity_data: dict) -> str:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                f"/v2/partners/{self.data.partner_id}/calendars/dpa",
                json=CreateCalendarAPIDTO.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json()["calendarId"]

    @retry_on_401
    def delete_dpa_calendar(self, calendar_id: str) -> None:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.delete(
                f"/v2/partners/{self.data.partner_id}/calendars/dpa/{calendar_id}",
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
    
    @retry_on_401
    def create_disbursement_account(self, country: str, bank_account: dict) -> DisbursementAccountBaseModel:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                self._create_disbursement_account(country),
                headers=self._header_builder(partner_id=self.data.partner_id),
                json=CreateDisbursementPartnerAccountDTO.parse_obj({
                    "id": self.data.partner_id,
                    "partnerId": self.data.partner_id,
                    "bankAccount": BankAccount.parse_obj(bank_account).dict(by_alias=True, exclude_none=True),
                    "taxId": self.data.tax_id,
                    "name": self.data.name,
                }).dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return DisbursementAccountBaseModel.parse_obj(response.json())


class PartnersAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            async_resource=PartnerAsync,
            retrieve_data_model=PartnerAPIDTO,
            create_data_model=CreatePartnerDTO,
            update_data_model=None,
            resource="partners",
            resource_version="v2"
        )

    @retry_on_401_async
    async def me(self) -> PartnerAsync:
        async with httpx.AsyncClient(base_url=self.altscore_client._cms_base_url) as client:
            response = await client.get(
                "/v2/partners/me",
                # This is important to avoid infinite recursion
                headers=build_headers(self, partner_id=None),
                timeout=30
            )
            raise_for_status_improved(response)
            return PartnerAsync(
                base_url=self.altscore_client._cms_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=PartnerAPIDTO.parse_obj(response.json())
            )

    @retry_on_401_async
    async def get_dpa_settings(self, partner_id:str) -> DPASettingsAPIDTO:
        async with httpx.AsyncClient(base_url=self.altscore_client._cms_base_url) as client:
            response = await client.get(
                f"/v2/partners/{partner_id}/settings/dpa",
                headers=build_headers(self),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPASettingsAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def update_dpa_settings(self, partner_id: str, settings: dict) -> DPASettingsAPIDTO:
        async with httpx.AsyncClient(base_url=self.altscore_client._cms_base_url) as client:
            settings = DPASettingsAPIDTO.parse_obj(settings)
            response = await client.patch(
                f"/v2/partners/{partner_id}/settings/dpa",
                json=settings.dict(by_alias=True, exclude_none=True),
                headers=build_headers(self),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPASettingsAPIDTO.parse_obj(response.json())
    
    @retry_on_401
    async def get_credit_accounts(self, product_family: str, **kwargs) -> CreditAccountSync:
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        async with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = await client.get(
                f"/v2/clients/credit-accounts/{product_family}",
                params=query_params,
                headers=build_headers(self),
                timeout=30
            )
            raise_for_status_improved(response)
            return [CreditAccountAPIDTO.parse_obj(item) for item in response.json()]



class PartnersSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            sync_resource=PartnerSync,
            retrieve_data_model=PartnerAPIDTO,
            create_data_model=CreatePartnerDTO,
            update_data_model=None,
            resource="partners",
            resource_version="v2"
        )

    @retry_on_401
    def me(self) -> PartnerSync:
        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.get(
                "/v2/partners/me",
                # This is important to avoid infinite recursion
                headers=build_headers(self, partner_id="init"),
                timeout=30
            )
            raise_for_status_improved(response)
            return PartnerSync(
                base_url=self.altscore_client._cms_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=PartnerAPIDTO.parse_obj(response.json())
            )

    @retry_on_401
    def get_dpa_settings(self, partner_id:str) -> DPASettingsAPIDTO:
        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.get(
                f"/v2/partners/{partner_id}/settings/dpa",
                headers=build_headers(self),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPASettingsAPIDTO.parse_obj(response.json())

    @retry_on_401
    def update_dpa_settings(self, partner_id: str, settings: dict) -> DPASettingsAPIDTO:
        settings = DPASettingsAPIDTO.parse_obj(settings)
        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.patch(
                f"/v2/partners/{partner_id}/settings/dpa",
                json=settings.dict(by_alias=True, exclude_none=True),
                headers=build_headers(self),
                timeout=30
            )
            raise_for_status_improved(response)
            return DPASettingsAPIDTO.parse_obj(response.json())

    @retry_on_401
    def get_credit_accounts(self, product_family: str, **kwargs) -> CreditAccountSync:
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.get(
                f"/v2/clients/credit-accounts/{product_family}",
                params=query_params,
                headers=build_headers(self),
                timeout=30
            )
            raise_for_status_improved(response)
            return [CreditAccountAPIDTO.parse_obj(item) for item in response.json()]
