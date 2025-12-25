from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class DataModelAPIDTO(BaseModel):
    id: str = Field(alias="id")
    path: str = Field(alias="path")
    key: str = Field(alias="key")
    label: str = Field(alias="label")
    entity_type: str = Field(alias="entityType")
    priority: Optional[int] = Field(alias="priority", default=None)
    order: Optional[int] = Field(alias="order", default=None)
    allowed_values: Optional[List[Any]] = Field(alias="allowedValues", default=None)
    data_type: Optional[str] = Field(alias="dataType", default=None)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata")
    is_segmentation_field: Optional[bool] = Field(alias="isSegmentationField", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class DataModelCreate(BaseModel):
    path: Optional[str] = Field(alias="path", default="")
    key: str = Field(alias="key")
    label: str = Field(alias="label")
    entity_type: str = Field(alias="entityType")
    priority: Optional[int] = Field(alias="priority", default=None)
    allowed_values: Optional[List[Any]] = Field(alias="allowedValues", default=None)
    order: Optional[int] = Field(alias="order", default=None)
    data_type: Optional[str] = Field(alias="dataType", default=None)
    metadata: Optional[dict] = Field(alias="metadata", default={})
    is_segmentation_field: Optional[bool] = Field(alias="isSegmentationField", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class DataModelUpdate(BaseModel):
    path: Optional[str] = Field(alias="path", default="")
    key: Optional[str] = Field(alias="key")
    label: Optional[str] = Field(alias="label")
    priority: Optional[int] = Field(alias="priority", default=None)
    order: Optional[int] = Field(alias="order", default=None)
    allowed_values: Optional[List[Any]] = Field(alias="allowedValues", default=None)
    data_type: Optional[str] = Field(alias="dataType", default=None)
    metadata: Optional[dict] = Field(alias="metadata", default={})
    is_segmentation_field: Optional[bool] = Field(alias="isSegmentationField", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class DataModelSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "data-models", header_builder, renew_token, DataModelAPIDTO.parse_obj(data))


class DataModelAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "data-models", header_builder, renew_token, DataModelAPIDTO.parse_obj(data))


class DataModelSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, sync_resource=DataModelSync, retrieve_data_model=DataModelAPIDTO,
                         create_data_model=DataModelCreate, update_data_model=DataModelUpdate, resource="data-models")


class DataModelAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, async_resource=DataModelSync, retrieve_data_model=DataModelAPIDTO,
                         create_data_model=DataModelCreate, update_data_model=DataModelUpdate, resource="data-models")
