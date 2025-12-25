from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class ChannelConnectorAPIDTO(BaseModel):
    id: str = Field(alias="id")
    channel: str = Field(alias="channel")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ChannelConnectorCreate(BaseModel):
    channel: str = Field(alias="channel")
    url: str = Field(alias="url")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ChannelConnectorUpdate(BaseModel):
    url: str = Field(alias="url")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ChannelConnectorSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/conversational/channel-connectors", header_builder, renew_token,
                         ChannelConnectorAPIDTO.parse_obj(data))


class ChannelConnectorAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/conversational/channel-connectors", header_builder, renew_token,
                         ChannelConnectorAPIDTO.parse_obj(data))


class ChannelConnectorSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, sync_resource=ChannelConnectorSync, retrieve_data_model=ChannelConnectorAPIDTO,
                         create_data_model=ChannelConnectorCreate, update_data_model=ChannelConnectorUpdate,
                         resource="/conversational/channel-connectors")


class ChannelConnectorAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, async_resource=ChannelConnectorAsync, retrieve_data_model=ChannelConnectorAPIDTO,
                         create_data_model=ChannelConnectorCreate, update_data_model=ChannelConnectorUpdate,
                         resource="/conversational/channel-connectors")