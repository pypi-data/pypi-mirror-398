from pydantic import BaseModel, Field
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from typing import Optional, Dict, List


class FormTemplateAPIDTO(BaseModel):
    id: str = Field(alias="id")
    tenant: str = Field(alias="tenant")
    template_slug: str = Field(alias="templateSlug")
    label: Optional[str] = Field(alias="templateLabel", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=[])
    template: Dict = Field(alias="template")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateFormTemplateDTO(BaseModel):
    slug: str = Field(alias="slug")
    template: Dict = Field(alias="template")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class FormTemplatesSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "form-templates", header_builder, renew_token, FormTemplateAPIDTO.parse_obj(data))


class FormTemplatesAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "form-templates", header_builder, renew_token, FormTemplateAPIDTO.parse_obj(data))


class FormTemplatesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=FormTemplatesSync,
                         retrieve_data_model=FormTemplateAPIDTO,
                         create_data_model=CreateFormTemplateDTO,
                         update_data_model=CreateFormTemplateDTO,
                         resource="form-templates")


class FormTemplatesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=FormTemplatesAsync,
                         retrieve_data_model=FormTemplateAPIDTO,
                         create_data_model=CreateFormTemplateDTO,
                         update_data_model=CreateFormTemplateDTO,
                         resource="form-templates")
