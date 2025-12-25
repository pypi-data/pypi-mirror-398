import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class Money(BaseModel):
    amount: str = Field(alias="amount")
    currency: str = Field(alias="currency")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

# DTO for field value history
class HistoricValueDTO(BaseModel):
    """Data transfer object for a historic field value"""
    reference_id: str = Field(alias="referenceId")
    value: Any = Field(alias="value")
    updated_at: str = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# DTO for priced array items
class MoneyArrayItemDTO(BaseModel):
    """Data transfer object for a money array item"""
    key: str = Field(alias="key")
    label: Optional[str] = Field(alias="label", default=None)
    value: Money = Field(alias="value")

# DTO for asset fields
class AssetFieldDTO(BaseModel):
    """Data transfer object for asset fields"""
    id: str = Field(alias="id")
    asset_id: str = Field(alias="assetId")
    key: str = Field(alias="key")
    label: Optional[str] = Field(alias="label", default=None)
    value: Any = Field(alias="value")
    data_type: str = Field(alias="dataType")
    history: List[HistoricValueDTO] = Field(alias="history", default=[])
    tags: List[str] = Field(alias="tags", default=[])
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

    @root_validator(pre=False)
    def parse_history_values(cls, values):
        """Parse history values based on the field's data_type"""
        data_type = values.get("data_type")
        history = values.get("history", [])
        
        if not history:
            return values
        
        # Parse current value based on data_type
        current_value = values.get("value")
        if data_type == "money" and isinstance(current_value, dict):
            values["value"] = Money.parse_obj(current_value)
        elif data_type == "money_array" and isinstance(current_value, list):
            values["value"] = [MoneyArrayItemDTO.parse_obj(item) for item in current_value]
        
        # Parse history values based on data_type
        for hist_item in history:
            if data_type == "money" and isinstance(hist_item.value, dict):
                hist_item.value = Money.parse_obj(hist_item.value)
            elif data_type == "money_array" and isinstance(hist_item.value, list):
                hist_item.value = [MoneyArrayItemDTO.parse_obj(item) for item in hist_item.value]
        
        return values


class CreateAssetFieldRequest(BaseModel):
    """Model for creating a new asset field"""
    asset_id: str = Field(alias="assetId")
    key: str = Field(alias="key")
    value: Any = Field(alias="value")
    data_type: Optional[str] = Field(alias="dataType", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateAssetFieldRequest(BaseModel):
    """Model for updating an asset field"""
    asset_id: str = Field(alias="assetId")
    value: Any = Field(alias="value")
    data_type: Optional[str] = Field(alias="dataType", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)  # Source of the value for history tracking
    tags: Optional[List[str]] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Resource classes for asset fields
class AssetFieldSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "asset-fields", header_builder, renew_token, AssetFieldDTO.parse_obj(data))


class AssetFieldAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "asset-fields", header_builder, renew_token, AssetFieldDTO.parse_obj(data))


# Module for asset fields - synchronous
class AssetFieldsSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=AssetFieldSync,
                         retrieve_data_model=AssetFieldDTO,
                         create_data_model=CreateAssetFieldRequest,
                         update_data_model=UpdateAssetFieldRequest,
                         resource="asset-fields")

    @retry_on_401
    def get_by_asset_id(self, asset_id: str, page: int = 1, per_page: int = 100):
        """
        Get asset fields by asset ID
        
        Args:
            asset_id: The ID of the asset
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[AssetFieldDTO]: List of asset fields
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/asset-fields",
                params={
                    "asset-id": asset_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [AssetFieldDTO.parse_obj(data) for data in response.json()]

    @retry_on_401
    def get_by_key(self, asset_id: str, key: str):
        """
        Get an asset field by its key

        Args:
            asset_id: The ID of the asset
            key: The field key

        Returns:
            List[AssetFieldDTO]: List of asset fields matching the key
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/asset-fields",
                params={
                    "key": key,
                    "asset-id": asset_id,
                    "per-page": 100,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [AssetFieldDTO.parse_obj(data) for data in response.json()]


# Module for asset fields - asynchronous
class AssetFieldsAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=AssetFieldAsync,
                         retrieve_data_model=AssetFieldDTO,
                         create_data_model=CreateAssetFieldRequest,
                         update_data_model=UpdateAssetFieldRequest,
                         resource="asset-fields")

    @retry_on_401_async
    async def get_by_asset_id(self, asset_id: str, page: int = 1, per_page: int = 100):
        """
        Get asset fields by asset ID
        
        Args:
            asset_id: The ID of the asset
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[AssetFieldDTO]: List of asset fields
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/asset-fields",
                params={
                    "asset-id": asset_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [AssetFieldDTO.parse_obj(data) for data in response.json()]

    @retry_on_401_async
    async def get_by_key(self, asset_id: str, key: str):
        """
        Get an asset field by its key
        
        Args:
            asset_id: The ID of the asset
            key: The field key
            
        Returns:
            List[AssetFieldDTO]: List of asset fields matching the key
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/asset-fields",
                params={
                    "key": key,
                    "asset-id": asset_id,
                    "per-page": 100,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [AssetFieldDTO.parse_obj(data) for data in response.json()]
