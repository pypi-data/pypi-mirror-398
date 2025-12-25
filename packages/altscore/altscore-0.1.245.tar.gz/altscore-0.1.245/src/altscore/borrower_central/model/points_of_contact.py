from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class PointOfContactAPIDTO(BaseModel):
    id: str = Field(alias="id")
    label: Optional[str] = Field(alias="label")
    contact_method: str = Field(alias="contactMethod")
    value: str = Field(alias="value")
    borrower_id: str = Field(alias="borrowerId")
    is_verified: Optional[bool] = Field(alias="isVerified", default=False)
    priority: Optional[int] = Field(alias="priority", default=None)
    verified_at: Optional[str] = Field(alias="verifiedAt", default=None)
    tags: List[str] = Field(alias="tags", default=[])
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreatePointOfContactDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    label: Optional[str] = Field(alias="label", default=None)
    contact_method: str = Field(alias="contactMethod")
    value: str = Field(alias="value", default=None)
    priority: Optional[int] = Field(alias="priority", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdatePointOfContact(BaseModel):
    label: Optional[str] = Field(alias="label", default=None)
    contact_method: Optional[str] = Field(alias="contactMethod", default=None)
    value: Optional[str] = Field(alias="value", default=None)
    priority: Optional[int] = Field(alias="priority", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class PointOfContactSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "points-of-contact", header_builder, renew_token, PointOfContactAPIDTO.parse_obj(data))


class PointOfContactAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "points-of-contact", header_builder, renew_token, PointOfContactAPIDTO.parse_obj(data))


class PointOfContactSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=PointOfContactSync,
                         retrieve_data_model=PointOfContactAPIDTO,
                         create_data_model=CreatePointOfContactDTO,
                         update_data_model=UpdatePointOfContact,
                         resource="points-of-contact")


class PointOfContactAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=PointOfContactAsync,
                         retrieve_data_model=PointOfContactAPIDTO,
                         create_data_model=CreatePointOfContactDTO,
                         update_data_model=UpdatePointOfContact,
                         resource="points-of-contact")
