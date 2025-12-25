from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Any, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class DocumentsAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    key: str = Field(alias="key")
    label: Optional[str] = Field(alias="label", default=None)
    value: Optional[Any] = Field(alias="value")
    tags: List[str] = Field(alias="tags")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")
    has_attachments: bool = Field(alias="hasAttachments")

    @root_validator
    def check_id_requirements(cls, values):
        borrower_id = values.get("borrower_id")
        deal_id = values.get("deal_id")
        if not borrower_id and not deal_id:
            raise ValueError("At least one of borrowerId or dealId must be provided")
        return values

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateDocumentDTO(BaseModel):
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    key: str = Field(alias="key")
    value: Optional[Any] = Field(alias="value", default=None)
    tags: List[str] = Field(alias="tags", default=[])
    
    @root_validator(pre=True)
    def check_id_requirements(cls, values):
        borrower_id = values.get("borrowerId")
        deal_id = values.get("dealId")
        if not borrower_id and not deal_id:
            raise ValueError("At least one of borrowerId or dealId must be provided")
        return values

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateDocumentDTO(BaseModel):
    key: Optional[str] = Field(alias="key", default=None)
    value: Optional[Any] = Field(alias="value", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class DocumentSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "documents", header_builder, renew_token, DocumentsAPIDTO.parse_obj(data))


class DocumentAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "documents", header_builder, renew_token, DocumentsAPIDTO.parse_obj(data))


class DocumentsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=DocumentSync,
                         retrieve_data_model=DocumentsAPIDTO,
                         create_data_model=CreateDocumentDTO,
                         update_data_model=UpdateDocumentDTO,
                         resource="documents")


class DocumentsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=DocumentAsync,
                         retrieve_data_model=DocumentsAPIDTO,
                         create_data_model=CreateDocumentDTO,
                         update_data_model=UpdateDocumentDTO,
                         resource="documents")
