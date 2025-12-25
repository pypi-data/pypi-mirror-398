from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class FlagAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: str = Field(alias="borrowerId")
    value: str = Field(alias="value")
    history: List[Dict] = Field(alias="history")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateFlag(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    value: str = Field(alias="value")
    principal_id: Optional[str] = Field(alias="principalId", hidden=True, default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class FlagSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "flags", header_builder, renew_token,
                         FlagAPIDTO.parse_obj(data))


class FlagAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "flags", header_builder, renew_token,
                         FlagAPIDTO.parse_obj(data))


class RiskRatingsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=FlagSync,
                         retrieve_data_model=FlagAPIDTO,
                         create_data_model=CreateFlag,
                         update_data_model=None,
                         resource="flags")


class RiskRatingsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=FlagAsync,
                         retrieve_data_model=FlagAPIDTO,
                         create_data_model=CreateFlag,
                         update_data_model=None,
                         resource="flags")
