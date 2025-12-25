import httpx
from pydantic import BaseModel, Field
from typing import Optional, Dict
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class StepDataAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: str = Field(alias="borrowerId")
    principal_id: Optional[str] = Field(alias="principalId", default=None)
    order: int = Field(alias="order")
    key: str = Field(alias="key")
    label: str = Field(alias="label")
    created_at: str = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateStepDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    key: str = Field(alias="key")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BorrowerStepSummaryAPIDTO(BaseModel):
    order: int = Field(alias="order")
    step: str = Field(alias="step")
    count: int = Field(alias="count")
    label: str = Field(alias="label")


class StepSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "steps", header_builder, renew_token, StepDataAPIDTO.parse_obj(data))


class StepAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "steps", header_builder, renew_token, StepDataAPIDTO.parse_obj(data))


class StepsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=StepSync,
                         retrieve_data_model=StepDataAPIDTO,
                         create_data_model=CreateStepDTO,
                         update_data_model=None,
                         resource="steps")

    @retry_on_401
    def get_borrower_summary(self):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}/borrower-summary",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
        return [BorrowerStepSummaryAPIDTO.parse_obj(data) for data in response.json()]


class StepsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=StepAsync,
                         retrieve_data_model=StepDataAPIDTO,
                         create_data_model=CreateStepDTO,
                         update_data_model=None,
                         resource="steps")

    @retry_on_401_async
    async def get_borrower_summary(self):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/{self.resource}/borrower-summary",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
        return [BorrowerStepSummaryAPIDTO.parse_obj(data) for data in response.json()]
