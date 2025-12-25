from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async


class PolicyVersion(BaseModel):
    version: int = Field(alias="version")
    short_text: Optional[str] = Field(alias="shortText")
    long_text: Optional[str] = Field(alias="longText")
    policy_url: Optional[str] = Field(alias="policyUrl", default=None)
    updated_at: str = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class PolicyAPIDTO(BaseModel):
    id: str = Field(alias="id")
    label: Optional[str] = Field(alias="label", default=None)
    language: Optional[str] = Field(alias="language", default=None)
    key: str = Field(alias="key", default=None)
    version: int = Field(alias="version")
    short_text: Optional[str] = Field(alias="shortText", default=None)
    long_text: Optional[str] = Field(alias="longText", default=None)
    policy_url: Optional[str] = Field(alias="policyUrl", default=None)
    version_history: List[PolicyVersion] = Field(alias="versionHistory", default=[])
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreatePolicyDTO(BaseModel):
    key: str = Field(alias="key")
    label: Optional[str] = Field(alias="label", default=None)
    short_text: Optional[str] = Field(alias="shortText")
    long_text: Optional[str] = Field(alias="longText")
    policy_url: Optional[str] = Field(alias="policyUrl")
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdatePolicyDTO(BaseModel):
    label: Optional[str] = Field(alias="label", default=None)
    short_text: Optional[str] = Field(alias="shortText", default=None)
    long_text: Optional[str] = Field(alias="longText", default=None)
    policy_url: Optional[str] = Field(alias="policyUrl", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class PolicySync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "policies", header_builder, renew_token, PolicyAPIDTO.parse_obj(data))


class PolicyAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "policies", header_builder, renew_token, PolicyAPIDTO.parse_obj(data))


class PolicySyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=PolicySync,
                         retrieve_data_model=PolicyAPIDTO,
                         create_data_model=CreatePolicyDTO,
                         update_data_model=UpdatePolicyDTO,
                         resource="policies")

    @retry_on_401
    def retrieve_by_key(self, key: str):
        query_params = {
            "key": key
        }
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            res = [self.sync_resource(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]

            if len(res) == 0:
                return None
            return res[0]


class PolicyAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=PolicyAsync,
                         retrieve_data_model=PolicyAPIDTO,
                         create_data_model=CreatePolicyDTO,
                         update_data_model=UpdatePolicyDTO,
                         resource="policies")

    @retry_on_401_async
    async def retrieve_by_key(self, key: str):
        query_params = {
            "key": key
        }
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            res = [self.async_resource(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]

            if len(res) == 0:
                return None
            return res[0]
