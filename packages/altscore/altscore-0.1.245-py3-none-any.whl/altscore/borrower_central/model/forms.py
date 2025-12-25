from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class FormAPIDTO(BaseModel):
    id: str = Field(alias="id")
    tenant: str = Field(alias="tenant")
    form_id: str = Field(alias="formId")
    template_id: str = Field(alias="templateId")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    is_finished: bool = Field(alias="isFinished", default=False)
    is_notified: bool = Field(alias="isNotified", default=False)
    last_ping_at: Optional[str] = Field(alias="lastPingAt", default=None)
    finished_at: Optional[str] = Field(alias="finishedAt", default=None)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class StartFormRequest(BaseModel):
    template_slug: str = Field(alias="templateSlug")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BorrowerSignUpRequest(BaseModel):
    tenant: str = Field(alias="tenant")
    persona: str = Field(alias="persona")
    form_id: str = Field(alias="formId")
    is_primary: bool = Field(alias="isPrimary", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BorrowerSignUpResponse(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    form_token: str = Field(alias="formToken")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class IdentityLookupResponse(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    points_of_contact: List[Dict] = Field(alias="pointsOfContact")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class FormSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "forms", header_builder, renew_token, FormAPIDTO.parse_obj(data))


class FormAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "forms", header_builder, renew_token, FormAPIDTO.parse_obj(data))


class FormsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, sync_resource=FormSync, retrieve_data_model=FormAPIDTO,
                         create_data_model=StartFormRequest, update_data_model=None, resource="forms")

    @retry_on_401
    def command_borrower_sign_up(self, borrower_sign_up_request: dict):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/{self.resource}/commands/borrower-sign-up",
                json=BorrowerSignUpRequest.parse_obj(borrower_sign_up_request).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return BorrowerSignUpResponse(
                borrower_id=response.json().get("borrowerId"),
                form_token=response.headers.get("Authorization").split(" ")[1]
            )

    @retry_on_401
    def query_identity_lookup(self, tenant: str, key: str, value: str, form_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}/queries/identity-lookup",
                params={
                    "key": key,
                    "value": value,
                    "form-id": form_id,
                    "tenant": tenant
                },
                timeout=120
            )
            raise_for_status_improved(response)
            return IdentityLookupResponse.parse_obj(response.json())

    @retry_on_401
    def query_entity_value(self, borrower_id: str, entity_type: str, key: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}/queries/entity-value",
                params={
                    "borrower-id": borrower_id,
                    "key": key,
                    "entity-type": entity_type,
                },
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json().get("value")


class FormsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, async_resource=FormSync, retrieve_data_model=FormAPIDTO,
                         create_data_model=StartFormRequest, update_data_model=None, resource="forms")

    @retry_on_401_async
    async def command_borrower_sign_up(self, borrower_sign_up_request: dict):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/{self.resource}/commands/borrower-sign-up",
                json=BorrowerSignUpRequest.parse_obj(borrower_sign_up_request).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return BorrowerSignUpResponse(
                borrower_id=response.json().get("borrowerId"),
                form_token=response.headers.get("Authorization").split(" ")[1]
            )

    @retry_on_401_async
    async def query_identity_lookup(self, tenant: str, key: str, value: str, form_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/{self.resource}/queries/identity-lookup",
                params={
                    "key": key,
                    "value": value,
                    "form-id": form_id,
                    "tenant": tenant
                },
                timeout=120
            )
            raise_for_status_improved(response)
            return IdentityLookupResponse.parse_obj(response.json())

    @retry_on_401_async
    async def query_entity_value(self, borrower_id: str, entity_type: str, key: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/{self.resource}/queries/entity-value",
                params={
                    "borrower-id": borrower_id,
                    "key": key,
                    "entity-type": entity_type,
                },
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json().get("value")
