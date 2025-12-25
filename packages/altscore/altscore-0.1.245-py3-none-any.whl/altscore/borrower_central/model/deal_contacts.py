import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


# DTO for deal contacts
class DealContactDTO(BaseModel):
    """Data transfer object for deal contacts"""
    id: str = Field(alias="id")
    deal_id: str = Field(alias="dealId")
    borrower_id: str = Field(alias="borrowerId")
    role_key: str = Field(alias="roleKey")
    is_primary: bool = Field(alias="isPrimary")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateDealContactRequest(BaseModel):
    """Model for creating a new deal contact"""
    deal_id: str = Field(alias="dealId")
    borrower_id: str = Field(alias="borrowerId")
    role_key: str = Field(alias="roleKey")
    is_primary: bool = Field(alias="isPrimary", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateDealContactRequest(BaseModel):
    """Model for updating a deal contact"""
    role_key: Optional[str] = Field(alias="roleKey", default=None)
    is_primary: Optional[bool] = Field(alias="isPrimary", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Resource classes for deal contacts
class DealContactSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "deal-contacts", header_builder, renew_token, DealContactDTO.parse_obj(data))


class DealContactAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "deal-contacts", header_builder, renew_token, DealContactDTO.parse_obj(data))


# Module for deal contacts - synchronous
class DealContactsSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=DealContactSync,
                         retrieve_data_model=DealContactDTO,
                         create_data_model=CreateDealContactRequest,
                         update_data_model=UpdateDealContactRequest,
                         resource="deal-contacts")

    @retry_on_401
    def get_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 100):
        """
        Get all contacts for a specific deal
        
        Args:
            deal_id: The ID of the deal
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of contacts for the deal
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/deal-contacts",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]

    @retry_on_401
    def get_by_borrower_id(self, borrower_id: str, page: int = 1, per_page: int = 100):
        """
        Get all deal contacts for a specific borrower
        
        Args:
            borrower_id: The ID of the borrower
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of deal contacts for the borrower
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/deal-contacts",
                params={
                    "borrower-id": borrower_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]

    @retry_on_401
    def get_by_deal_and_borrower(self, deal_id: str, borrower_id: str, page: int = 1, per_page: int = 100):
        """
        Get all contacts for a specific deal and borrower
        
        Args:
            deal_id: The ID of the deal
            borrower_id: The ID of the borrower
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of contacts for the deal and borrower
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/deal-contacts",
                params={
                    "deal-id": deal_id,
                    "borrower-id": borrower_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]
    
    @retry_on_401
    def get_by_role_key(self, role_key: str, page: int = 1, per_page: int = 100):
        """
        Get all contacts with a specific role
        
        Args:
            role_key: The role key to filter by
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of contacts with the specified role
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/deal-contacts",
                params={
                    "role-key": role_key,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]


# Module for deal contacts - asynchronous
class DealContactsAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=DealContactAsync,
                         retrieve_data_model=DealContactDTO,
                         create_data_model=CreateDealContactRequest,
                         update_data_model=UpdateDealContactRequest,
                         resource="deal-contacts")

    @retry_on_401_async
    async def get_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 100):
        """
        Get all contacts for a specific deal
        
        Args:
            deal_id: The ID of the deal
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of contacts for the deal
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/deal-contacts",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]

    @retry_on_401_async
    async def get_by_borrower_id(self, borrower_id: str, page: int = 1, per_page: int = 100):
        """
        Get all deal contacts for a specific borrower
        
        Args:
            borrower_id: The ID of the borrower
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of deal contacts for the borrower
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/deal-contacts",
                params={
                    "borrower-id": borrower_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]

    @retry_on_401_async
    async def get_by_deal_and_borrower(self, deal_id: str, borrower_id: str, page: int = 1, per_page: int = 100):
        """
        Get all contacts for a specific deal and borrower
        
        Args:
            deal_id: The ID of the deal
            borrower_id: The ID of the borrower
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of contacts for the deal and borrower
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/deal-contacts",
                params={
                    "deal-id": deal_id,
                    "borrower-id": borrower_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]
    
    @retry_on_401_async
    async def get_by_role_key(self, role_key: str, page: int = 1, per_page: int = 100):
        """
        Get all contacts with a specific role
        
        Args:
            role_key: The role key to filter by
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealContactDTO]: List of contacts with the specified role
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/deal-contacts",
                params={
                    "role-key": role_key,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealContactDTO.parse_obj(data) for data in response.json()]
