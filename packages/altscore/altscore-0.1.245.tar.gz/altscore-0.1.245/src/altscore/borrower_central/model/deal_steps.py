import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


# DTO for deal steps
class DealStepDTO(BaseModel):
    """Data transfer object for deal steps"""
    id: str = Field(alias="id")
    deal_id: str = Field(alias="dealId")
    principal_id: Optional[str] = Field(alias="principalId", default=None)
    order: int = Field(alias="order")
    key: str = Field(alias="key")
    label: str = Field(alias="label")
    created_at: str = Field(alias="createdAt")
    comment: Optional[str] = Field(alias="comment", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateDealStepRequest(BaseModel):
    """Model for creating a new deal step"""
    deal_id: str = Field(alias="dealId")
    order: int = Field(alias="order")
    key: str = Field(alias="key")
    label: str = Field(alias="label")
    comment: Optional[str] = Field(alias="comment", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class SetCurrentStepRequest(BaseModel):
    """Model for setting the current step of a deal"""
    key: str = Field(alias="key")
    comment: Optional[str] = Field(alias="comment", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Resource classes for deal steps
class DealStepSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "deal-steps", header_builder, renew_token, DealStepDTO.parse_obj(data))


class DealStepAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "deal-steps", header_builder, renew_token, DealStepDTO.parse_obj(data))


# Module for deal steps - synchronous
class DealStepsSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=DealStepSync,
                         retrieve_data_model=DealStepDTO,
                         create_data_model=CreateDealStepRequest,
                         update_data_model=None,  # Steps can't be updated, only created
                         resource="deal-steps")

    @retry_on_401
    def get_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 100):
        """
        Get all steps for a specific deal
        
        Args:
            deal_id: The ID of the deal
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealStepDTO]: List of steps for the deal
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/deal-steps",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealStepDTO.parse_obj(data) for data in response.json()]

    @retry_on_401
    def get_latest_by_deal_id(self, deal_id: str):
        """
        Get the latest step for a specific deal
        
        Args:
            deal_id: The ID of the deal
            
        Returns:
            DealStepSync resource instance or None if no steps exist
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/deal-steps/latest/{deal_id}",
                headers=self.build_headers(),
                timeout=120,
            )
            if response.status_code == 404:
                return None
            raise_for_status_improved(response)
            return DealStepSync(
                self.altscore_client._borrower_central_base_url,
                self.build_headers,
                self.altscore_client.renew_token,
                response.json()
            )

    @retry_on_401
    def get_by_key(self, deal_id: str, key: str, page: int = 1, per_page: int = 100):
        """
        Get all steps with a specific key for a deal
        
        Args:
            deal_id: The ID of the deal
            key: The step key
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealStepDTO]: List of steps matching the key
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/deal-steps/by-key/{deal_id}/{key}",
                params={
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealStepDTO.parse_obj(data) for data in response.json()]


# Module for deal steps - asynchronous
class DealStepsAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=DealStepAsync,
                         retrieve_data_model=DealStepDTO,
                         create_data_model=CreateDealStepRequest,
                         update_data_model=None,  # Steps can't be updated, only created
                         resource="deal-steps")

    @retry_on_401_async
    async def get_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 100):
        """
        Get all steps for a specific deal
        
        Args:
            deal_id: The ID of the deal
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealStepDTO]: List of steps for the deal
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/deal-steps",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealStepDTO.parse_obj(data) for data in response.json()]

    @retry_on_401_async
    async def get_latest_by_deal_id(self, deal_id: str):
        """
        Get the latest step for a specific deal
        
        Args:
            deal_id: The ID of the deal
            
        Returns:
            DealStepAsync resource instance or None if no steps exist
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/deal-steps/latest/{deal_id}",
                headers=self.build_headers(),
                timeout=120,
            )
            if response.status_code == 404:
                return None
            raise_for_status_improved(response)
            return DealStepAsync(
                self.altscore_client._borrower_central_base_url,
                self.build_headers,
                self.altscore_client.renew_token,
                response.json()
            )

    @retry_on_401_async
    async def get_by_key(self, deal_id: str, key: str, page: int = 1, per_page: int = 100):
        """
        Get all steps with a specific key for a deal
        
        Args:
            deal_id: The ID of the deal
            key: The step key
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealStepDTO]: List of steps matching the key
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/deal-steps/by-key/{deal_id}/{key}",
                params={
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealStepDTO.parse_obj(data) for data in response.json()]
