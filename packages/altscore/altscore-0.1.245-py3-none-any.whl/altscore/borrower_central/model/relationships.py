from pydantic import BaseModel, Field
from typing import Optional, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class RelationshipAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: str = Field(alias="borrowerId")
    contact_id: str = Field(alias="contactId")
    priority: int = Field(alias="priority")
    is_active: bool = Field(alias="isActive")
    is_legal_representative: bool = Field(alias="isLegalRepresentative")
    relationship: str = Field(alias="relationship")
    ownership_pct: Optional[float] = Field(alias="ownershipPct")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateRelationshipDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    contact_id: str = Field(alias="contactId")
    priority: Optional[int] = Field(alias="priority", default=None)
    relationship: str = Field(alias="relationship")
    is_legal_representative: Optional[bool] = Field(alias="isLegalRepresentative")
    is_active: Optional[bool] = Field(alias="isActive")
    ownership_pct: Optional[float] = Field(None, alias="ownershipPct")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateRelationshipDTO(BaseModel):
    priority: Optional[int] = Field(alias="priority", default=None)
    relationship: Optional[str] = Field(alias="relationship")
    is_legal_representative: Optional[bool] = Field(alias="isLegalRepresentative")
    is_active: Optional[bool] = Field(alias="isActive")
    ownership_pct: Optional[float] = Field(None, alias="ownershipPct")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class RelationshipSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "relationships", header_builder, renew_token, RelationshipAPIDTO.parse_obj(data))


class RelationshipAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "relationships", header_builder, renew_token, RelationshipAPIDTO.parse_obj(data))


class RelationshipsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=RelationshipSync,
                         retrieve_data_model=RelationshipAPIDTO,
                         create_data_model=CreateRelationshipDTO,
                         update_data_model=UpdateRelationshipDTO,
                         resource="relationships")


class RelationshipsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=RelationshipAsync,
                         retrieve_data_model=RelationshipAPIDTO,
                         create_data_model=CreateRelationshipDTO,
                         update_data_model=UpdateRelationshipDTO,
                         resource="relationships")
