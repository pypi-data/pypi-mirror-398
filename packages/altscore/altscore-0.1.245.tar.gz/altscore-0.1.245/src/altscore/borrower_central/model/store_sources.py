from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class SourceAPIDTO(BaseModel):
    id: str = Field(alias="id")
    label: Optional[str] = Field(alias="label", default=None)
    tags: List[str] = Field(alias="tags", default=[])
    transformer_config: Optional[Dict] = Field(alias="transformerConfig", default=None)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class TransformerConfig(BaseModel):
    url: str = Field(alias="url")
    headers: Dict[str, str] = Field(alias="headers")


class CreateSourceDTO(BaseModel):
    id: str = Field(alias="id")
    label: Optional[str] = Field(alias="label", default=None)
    tags: List[str] = Field(alias="tags", default=[])
    transformer_config: Optional[TransformerConfig] = Field(alias="transformerConfig", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateAltdataSourceDTO(BaseModel):
    label: Optional[str] = Field(alias="label", default=None)
    altdata_source_id: str = Field(alias="altdataSourceId")
    altdata_source_version: str = Field(alias="altdataSourceVersion")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class SourceSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/stores/sources", header_builder, renew_token, SourceAPIDTO.parse_obj(data))


class SourceAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/stores/sources", header_builder, renew_token, SourceAPIDTO.parse_obj(data))


class SourcesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=SourceSync,
                         retrieve_data_model=SourceAPIDTO,
                         create_data_model=CreateSourceDTO,
                         update_data_model=CreateSourceDTO,
                         resource="/stores/sources")

    @retry_on_401
    def create_altdata(self, altdata_source_id: str, altdata_source_version: str) -> str:
        new_entity_data = {
            "altdataSourceId": altdata_source_id,
            "altdataSourceVersion": altdata_source_version
        }
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/stores/sources/altdata",
                headers=self.build_headers(),
                json=CreateAltdataSourceDTO.parse_obj(new_entity_data).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()["id"]


class SourcesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=SourceAsync,
                         retrieve_data_model=SourceAPIDTO,
                         create_data_model=CreateSourceDTO,
                         update_data_model=CreateSourceDTO,
                         resource="/stores/sources")

    @retry_on_401_async
    async def create_altdata(self, altdata_source_id: str, altdata_source_version: str) -> str:
        new_entity_data = {
            "altdataSourceId": altdata_source_id,
            "altdataSourceVersion": altdata_source_version
        }
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/stores/sources/altdata",
                headers=self.build_headers(),
                json=CreateAltdataSourceDTO.parse_obj(new_entity_data).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()["id"]
