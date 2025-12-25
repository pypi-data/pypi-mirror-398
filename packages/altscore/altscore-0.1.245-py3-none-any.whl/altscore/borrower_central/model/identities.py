import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class IdentityAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: str = Field(alias="borrowerId")
    key: str = Field(alias="key")
    label: Optional[str] = Field(alias="label")
    value: Optional[str] = Field(alias="value")
    priority: Optional[int] = Field(alias="priority")
    tags: List[str] = Field(alias="tags")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")
    has_attachments: bool = Field(alias="hasAttachments", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateIdentityDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    key: str = Field(alias="key")
    value: Optional[str] = Field(alias="value")
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateIdentityDTO(BaseModel):
    value: Optional[str] = Field(alias="value", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class IdentitySync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "identities", header_builder, renew_token, IdentityAPIDTO.parse_obj(data))


class IdentityAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "identities", header_builder, renew_token, IdentityAPIDTO.parse_obj(data))


class IdentitiesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=IdentitySync,
                         retrieve_data_model=IdentityAPIDTO,
                         create_data_model=CreateIdentityDTO,
                         update_data_model=UpdateIdentityDTO,
                         resource="identities")

    @retry_on_401
    def find_by_key(self, key: str, borrower_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            identities_found_req = client.get(
                f"/v1/identities",
                params={
                    "key": key,
                    "borrower-id": borrower_id,
                    "per-page": 1,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(identities_found_req)
            identities_found_data = identities_found_req.json()
            if len(identities_found_data) == 0:
                return None
            else:
                return self.retrieve(identities_found_data[0]["id"])


class IdentitiesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=IdentityAsync,
                         retrieve_data_model=IdentityAPIDTO,
                         create_data_model=CreateIdentityDTO,
                         update_data_model=UpdateIdentityDTO,
                         resource="identities")

    @retry_on_401_async
    async def find_by_key(self, key: str, borrower_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            identities_found_req = await client.get(
                f"/v1/identities",
                params={
                    "key": key,
                    "borrower-id": borrower_id,
                    "per-page": 1,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(identities_found_req)
            identities_found_data = identities_found_req.json()
            if len(identities_found_data) == 0:
                return None
            else:
                return await self.retrieve(identities_found_data[0]["id"])
