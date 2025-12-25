import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Dict, Any, Literal
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


# DTO for deal fields
class DealFieldDTO(BaseModel):
    """Data transfer object for deal fields"""
    id: str = Field(alias="id")
    deal_id: str = Field(alias="dealId")
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
    def parse_money_values(cls, values):
        """Parse money values based on the field's data_type"""
        data_type = values.get("data_type")
        history = values.get("history", [])

        # Parse current value based on data_type
        current_value = values.get("value")
        if data_type == "money" and isinstance(current_value, dict):
            values["value"] = Money.parse_obj(current_value)

        # Parse history values based on data_type
        for hist_item in history:
            if data_type == "money" and isinstance(hist_item.value, dict):
                hist_item.value = Money.parse_obj(hist_item.value)

        return values


class CreateDealFieldRequest(BaseModel):
    """Model for creating a new deal field"""
    deal_id: str = Field(alias="dealId")
    key: str = Field(alias="key")
    value: Any = Field(alias="value")
    data_type: Optional[Literal["string", "number", "date", "boolean", "money"]] = Field(alias="dataType", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateDealFieldRequest(BaseModel):
    """Model for updating a deal field"""
    deal_id: str = Field(alias="dealId")
    value: Any = Field(alias="value")
    data_type: Optional[Literal["string", "number", "date", "boolean", "money"]] = Field(alias="dataType", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)  # Source of the value for history tracking
    tags: Optional[List[str]] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ValueCounterDTO(BaseModel):
    """DTO for count of field values"""
    count: int = Field(alias="count")
    value: str = Field(alias="value")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Resource classes for deal fields
class DealFieldSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "deal-fields", header_builder, renew_token, DealFieldDTO.parse_obj(data))


class DealFieldAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "deal-fields", header_builder, renew_token, DealFieldDTO.parse_obj(data))


# Module for deal fields - synchronous
class DealFieldsSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=DealFieldSync,
                         retrieve_data_model=DealFieldDTO,
                         create_data_model=CreateDealFieldRequest,
                         update_data_model=UpdateDealFieldRequest,
                         resource="deal-fields")

    @retry_on_401
    def get_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 100):
        """
        Get deal fields by deal ID
        
        Args:
            deal_id: The ID of the deal
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealFieldDTO]: List of deal fields
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/deal-fields",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealFieldDTO.parse_obj(data) for data in response.json()]

    @retry_on_401
    def get_by_key(self, deal_id: str, key: str):
        """
        Get a deal field by its key

        Args:
            deal_id: The ID of the deal
            key: The field key

        Returns:
            List[DealFieldDTO]: List of deal fields matching the key
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/deal-fields",
                params={
                    "key": key,
                    "deal-id": deal_id,
                    "per-page": 100,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealFieldDTO.parse_obj(data) for data in response.json()]

    @retry_on_401
    def get_unique_values(self, key: str):
        """
        Get unique values for a specific field key
        
        Args:
            key: The field key
            
        Returns:
            List[ValueCounterDTO]: List of unique values with counts
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/deal-fields/unique-values/{key}",
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [ValueCounterDTO.parse_obj(item) for item in response.json()]

    @retry_on_401
    def bulk_update_by_value(self, key: str, current_value: str, new_value: str):
        """
        Update all fields with a specific key and value to a new value
        
        Args:
            key: The field key
            current_value: The current value to match
            new_value: The new value to set
            
        Returns:
            None
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.put(
                f"/v1/deal-fields/bulk-update/{key}",
                params={
                    "currentValue": current_value,
                    "newValue": new_value
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return None


# Module for deal fields - asynchronous
class DealFieldsAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=DealFieldAsync,
                         retrieve_data_model=DealFieldDTO,
                         create_data_model=CreateDealFieldRequest,
                         update_data_model=UpdateDealFieldRequest,
                         resource="deal-fields")

    @retry_on_401_async
    async def get_by_deal_id(self, deal_id: str, page: int = 1, per_page: int = 100):
        """
        Get deal fields by deal ID
        
        Args:
            deal_id: The ID of the deal
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List[DealFieldDTO]: List of deal fields
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/deal-fields",
                params={
                    "deal-id": deal_id,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealFieldDTO.parse_obj(data) for data in response.json()]

    @retry_on_401_async
    async def get_by_key(self, deal_id: str, key: str):
        """
        Get a deal field by its key
        
        Args:
            deal_id: The ID of the deal
            key: The field key
            
        Returns:
            List[DealFieldDTO]: List of deal fields matching the key
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/deal-fields",
                params={
                    "key": key,
                    "deal-id": deal_id,
                    "per-page": 100,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [DealFieldDTO.parse_obj(data) for data in response.json()]

    @retry_on_401_async
    async def get_unique_values(self, key: str):
        """
        Get unique values for a specific field key
        
        Args:
            key: The field key
            
        Returns:
            List[ValueCounterDTO]: List of unique values with counts
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/deal-fields/unique-values/{key}",
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return [ValueCounterDTO.parse_obj(item) for item in response.json()]

    @retry_on_401_async
    async def bulk_update_by_value(self, key: str, current_value: str, new_value: str):
        """
        Update all fields with a specific key and value to a new value
        
        Args:
            key: The field key
            current_value: The current value to match
            new_value: The new value to set
            
        Returns:
            None
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.put(
                f"/v1/deal-fields/bulk-update/{key}",
                params={
                    "currentValue": current_value,
                    "newValue": new_value
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return None
