import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


# DTO for assets
class AssetDTO(BaseModel):
    """Data transfer object for assets"""
    id: str = Field(alias="id")
    deal_id: str = Field(alias="dealId")
    external_id: Optional[str] = Field(alias="externalId", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    group: Optional[str] = Field(alias="group", default=None)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)
    has_attachments: bool = Field(alias="hasAttachments")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateAssetRequest(BaseModel):
    """Model for creating a new asset"""
    deal_id: str = Field(alias="dealId")
    label: str = Field(alias="label")
    description: Optional[str] = Field(alias="description", default=None)
    external_id: Optional[str] = Field(alias="externalId", default=None)
    group: Optional[str] = Field(alias="group", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateAssetRequest(BaseModel):
    """Model for updating an asset"""
    label: Optional[str] = Field(alias="label", default=None)
    description: Optional[str] = Field(alias="description", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExternalIdRequest(BaseModel):
    """Model for setting an external ID"""
    external_id: str = Field(alias="externalId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Resource classes for assets
class AssetSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "assets", header_builder, renew_token, AssetDTO.parse_obj(data))


class AssetAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "assets", header_builder, renew_token, AssetDTO.parse_obj(data))


# Module for assets - synchronous
class AssetsSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=AssetSync,
                         retrieve_data_model=AssetDTO,
                         create_data_model=CreateAssetRequest,
                         update_data_model=UpdateAssetRequest,
                         resource="assets")

    @retry_on_401
    def set_external_id(self, asset_id: str, external_id: str):
        """
        Set an external ID for an asset
        
        Args:
            asset_id: The ID of the asset
            external_id: The external ID to set
            
        Returns:
            None
        """
        request_data = ExternalIdRequest(externalId=external_id)

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.put(
                f"/v1/assets/{asset_id}/external-id",
                json=request_data.dict(by_alias=True, exclude_none=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def query_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 10):
        """
        Find assets by deal ID
        
        Args:
            deal_id: The ID of the deal to filter by
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            Dict with assets and pagination info
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/assets",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return response.json()

    @retry_on_401
    def retrieve_by_external_id(self, external_id: str) -> Optional[AssetSync]:
        """
        Retrieve an asset by its external ID
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/assets",
                params={"external-id": external_id},
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            assets = response.json()
            if assets and len(assets) > 0:
                return AssetSync(
                    base_url=self.altscore_client._borrower_central_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=assets[0]
                )
            return None

    @retry_on_401
    def query_by_group(self, group: str, page: int = 1, per_page: int = 10):
        """
        Find assets by group

        Args:
            group: The group key to filter by
            page: Page number for pagination
            per_page: Number of results per page

        Returns:
            Dict with assets and pagination info
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/assets",
                params={
                    "group": group,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return response.json()


# Module for assets - asynchronous
class AssetsAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=AssetAsync,
                         retrieve_data_model=AssetDTO,
                         create_data_model=CreateAssetRequest,
                         update_data_model=UpdateAssetRequest,
                         resource="assets")

    @retry_on_401_async
    async def set_external_id(self, asset_id: str, external_id: str):
        """
        Set an external ID for an asset
        
        Args:
            asset_id: The ID of the asset
            external_id: The external ID to set
            
        Returns:
            None
        """
        request_data = ExternalIdRequest(externalId=external_id)

        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.put(
                f"/v1/assets/{asset_id}/external-id",
                json=request_data.dict(by_alias=True, exclude_none=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def query_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 10):
        """
        Find assets by deal ID
        
        Args:
            deal_id: The ID of the deal to filter by
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            Dict with assets and pagination info
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/assets",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return response.json()

    @retry_on_401_async
    async def retrieve_by_external_id(self, external_id: str) -> Optional[AssetAsync]:
        """
        Retrieve an asset by its external ID
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/assets",
                params={"external-id": external_id},
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            assets = response.json()
            if assets and len(assets) > 0:
                return AssetAsync(
                    base_url=self.altscore_client._borrower_central_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=assets[0]
                )
            return None

    @retry_on_401_async
    async def query_by_group(self, group: str, page: int = 1, per_page: int = 10):
        """
        Find assets by group

        Args:
            group: The group key to filter by
            page: Page number for pagination
            per_page: Number of results per page

        Returns:
            Dict with assets and pagination info
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/assets",
                params={
                    "group": group,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return response.json()
