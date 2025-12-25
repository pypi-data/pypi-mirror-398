from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class StageAPIDTO(BaseModel):
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


class CreateUpdateStageDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    value: str = Field(alias="value")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class StageSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "stages", header_builder, renew_token, StageAPIDTO.parse_obj(data))


class StageAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "stages", header_builder, renew_token, StageAPIDTO.parse_obj(data))


class StagesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=StageSync,
                         retrieve_data_model=StageAPIDTO,
                         create_data_model=CreateUpdateStageDTO,
                         update_data_model=CreateUpdateStageDTO,
                         resource="stages")


class StagesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=StageAsync,
                         retrieve_data_model=StageAPIDTO,
                         create_data_model=CreateUpdateStageDTO,
                         update_data_model=CreateUpdateStageDTO,
                         resource="stages")
