from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class ConversationAPIDTO(BaseModel):
    """DTO for conversation API responses"""
    id: str = Field(alias="id")
    borrower_id: str = Field(alias="borrowerId")
    channel: str = Field(alias="channel")
    channel_customer_id: str = Field(alias="channelCustomerId")
    state: str = Field(alias="state")
    current_human_agent_id: Optional[str] = Field(alias="currentHumanAgentId")  # Fixed alias to be consistent
    current_ai_agent_id: Optional[str] = Field(alias="currentAIAgentId")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ConversationCreate(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    channel: str = Field(alias="channel")
    channel_customer_id: str = Field(alias="channelCustomerId")
    state: Optional[str] = Field(alias="state")
    current_human_agent_id: Optional[str] = Field(alias="currentHumanAgentId", default=None)  # Fixed alias to be consistent
    current_ai_agent_id: Optional[str] = Field(alias="currentAIAgentId", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ConversationUpdate(BaseModel):
    state: Optional[str] = Field(alias="state")
    current_human_agent_id: Optional[str] = Field(alias="currentHumanAgentId")  # Fixed alias to be consistent
    current_ai_agent_id: Optional[str] = Field(alias="currentAIAgentId")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ConversationSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/conversational/conversations", header_builder, renew_token,
                         ConversationAPIDTO.parse_obj(data))


class ConversationAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/conversational/conversations", header_builder, renew_token,
                         ConversationAPIDTO.parse_obj(data))


class ConversationSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, sync_resource=ConversationSync, retrieve_data_model=ConversationAPIDTO,
                         create_data_model=ConversationCreate, update_data_model=ConversationUpdate,
                         resource="/conversational/conversations")


class ConversationAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, async_resource=ConversationAsync, retrieve_data_model=ConversationAPIDTO,
                         create_data_model=ConversationCreate, update_data_model=ConversationUpdate,
                         resource="/conversational/conversations")

