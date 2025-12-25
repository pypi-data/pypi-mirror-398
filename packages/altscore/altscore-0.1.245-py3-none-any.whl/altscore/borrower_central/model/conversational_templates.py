from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule



class WhatsAppVariable(BaseModel):
    placeholder: str = Field(alias="placeholder")
    sample_value: str = Field(alias="sampleValue")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class WhatsAppTemplateRequest(BaseModel):
    name: str = Field(alias="name")
    label: str = Field(alias="label")
    description: str = Field(alias="description")
    category: str = Field(alias="category")
    segment: str = Field(alias="segment")
    periodicity: str = Field(alias="periodicity")
    client_id: str = Field(alias="clientId")
    language: Optional[str] = Field(alias="language")
    header_type: Optional[Literal['none', 'text', 'image', 'video', 'document']] = Field(alias="headerType")
    header_text: Optional[str] = Field(alias="headerText")
    header_file: Optional[str] = Field(alias="headerFile")
    body_text: str = Field(alias="bodyText")
    footer_text: Optional[str] = Field(alias="footerText")
    buttons: Optional[List[dict]] = Field(alias="buttons")
    variables: Optional[List[WhatsAppVariable]] = Field(alias="variables")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class WhatsAppTemplateAPIDTO(BaseModel):
    id: str = Field(alias="id")
    template_id: str = Field(alias="template_id")
    name: str = Field(alias="name")
    label: str = Field(alias="label")
    description: str = Field(alias="description")
    alias: Optional[str] = Field(alias="alias", default=None)
    version: Optional[int] = Field(alias="version", default=None)
    category: str = Field(alias="category")
    segment: str = Field(alias="segment")
    periodicity: str = Field(alias="periodicity")
    client_id: str = Field(alias="clientId")
    language: Optional[str] = Field(alias="language", default=None)
    header_type: Optional[str] = Field(alias="headerType", default=None)
    header_text: Optional[str] = Field(alias="headerText", default=None)
    header_file: Optional[str] = Field(alias="headerFile", default=None)
    body_text: str = Field(alias="bodyText")
    footer_text: Optional[str] = Field(alias="footerText", default=None)
    buttons: Optional[List[dict]] = Field(alias="buttons", default=None)
    variables: Optional[List[WhatsAppVariable]] = Field(alias="variables", default=None)
    status: Optional[str] = Field(alias="status", default=None)
    tenant: str = Field(alias="tenant")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class WhatsAppTemplateUpdate(BaseModel):
    name: Optional[str] = Field(alias="name", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    category: Optional[str] = Field(alias="category", default=None)
    segment: Optional[str] = Field(alias="segment", default=None)
    periodicity: Optional[str] = Field(alias="periodicity", default=None)
    client_id: Optional[str] = Field(alias="clientId", default=None)
    language: Optional[str] = Field(alias="language", default=None)
    header_type: Optional[str] = Field(alias="headerType", default=None)
    header_text: Optional[str] = Field(alias="headerText", default=None)
    header_file: Optional[str] = Field(alias="headerFile", default=None)
    body_text: Optional[str] = Field(alias="bodyText", default=None)
    footer_text: Optional[str] = Field(alias="footerText", default=None)
    buttons: Optional[List[dict]] = Field(alias="buttons", default=None)
    variables: Optional[List[WhatsAppVariable]] = Field(alias="variables", default=None)

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class PublishRequest(BaseModel):
    connector_id: str = Field(alias="connectorId")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class SendRequest(BaseModel):
    connector_id: Optional[str] = Field(alias="connectorId")
    country_code: Optional[str] = Field(alias="countryCode", default=None)
    phone_number: str = Field(alias="phoneNumber")
    variables: Dict[str, Any] = Field(alias="variables")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class WhatsAppTemplateSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/conversational/templates", header_builder, renew_token,
                         WhatsAppTemplateAPIDTO.parse_obj(data))


class WhatsAppTemplateAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/conversational/templates", header_builder, renew_token,
                         WhatsAppTemplateAPIDTO.parse_obj(data))


class WhatsAppTemplateSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, sync_resource=WhatsAppTemplateSync,
                         retrieve_data_model=WhatsAppTemplateAPIDTO,
                         create_data_model=WhatsAppTemplateRequest,
                         update_data_model=WhatsAppTemplateUpdate,
                         resource="/conversational/templates")

    @retry_on_401
    def publish_template(self, template_id: str, request_body: Dict[str, Any]):
        request_data = PublishRequest(
            **request_body
        )
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            request = client.post(
                f"/v1/conversational/templates/{template_id}/publish",
                json=request_data.dict(by_alias=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(request)
            return request.json()

    @retry_on_401
    def send_template(self, template_id: str, request_body: Dict[str, Any]):
        request_data = SendRequest(
            **request_body
        )
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            request = client.post(
                f"/v1/conversational/templates/{template_id}/send",
                json=request_data.dict(by_alias=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(request)


class WhatsAppTemplateAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, async_resource=WhatsAppTemplateAsync,
                         retrieve_data_model=WhatsAppTemplateAPIDTO,
                         create_data_model=WhatsAppTemplateRequest,
                         update_data_model=WhatsAppTemplateUpdate,
                         resource="/conversational/templates")

    @retry_on_401_async
    async def publish_template(self, template_id: str, request_body: Dict[str, Any]):
        request_data = PublishRequest(
            **request_body
        )
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/conversational/templates/{template_id}/publish",
                json=request_data.dict(by_alias=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return response.json()

    @retry_on_401_async
    async def send_template(self, template_id: str, request_body: Dict[str, Any]):
        request_data = SendRequest(
            **request_body
        )
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/conversational/templates/{template_id}/send",
                json=request_data.dict(by_alias=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)

