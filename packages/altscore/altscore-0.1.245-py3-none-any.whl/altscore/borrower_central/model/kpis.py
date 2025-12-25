import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class KpiValue(BaseModel):
    target: Optional[float] = Field(alias="target", default=None)
    red_range: Optional[List[float]] = Field(alias="redRange", default=None)
    yellow_range: Optional[List[float]] = Field(alias="yellowRange", default=None)
    green_range: Optional[List[float]] = Field(alias="greenRange", default=None)


class HistoricValue(BaseModel):
    execution_id: Optional[str] = Field(alias="executionId", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    value: KpiValue = Field(alias="value")
    updated_at: str = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class KpiAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    key: str = Field(alias="key")
    persona: str = Field(alias="persona")
    label: str = Field(alias="label")
    description: str = Field(alias="description")
    value: KpiValue = Field(alias="value")
    history: List[Dict] = Field(alias="history")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateKpi(BaseModel):
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    execution_id: Optional[str] = Field(alias="executionId", default=None)
    label: str = Field(alias="label")
    description: str = Field(alias="description")
    key: str = Field(alias="key")
    persona: Optional[str] = Field(alias="persona")
    value: KpiValue = Field(alias="value")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateKpi(BaseModel):
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    execution_id: Optional[str] = Field(alias="executionId", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    value: Optional[KpiValue] = Field(alias="value")
    date: Optional[str] = Field(alias="date", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class KpiSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "kpis", header_builder, renew_token, KpiAPIDTO.parse_obj(data))


class KpiAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "kpis", header_builder, renew_token, KpiAPIDTO.parse_obj(data))


class KpisSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=KpiSync,
                         retrieve_data_model=KpiAPIDTO,
                         create_data_model=CreateKpi,
                         update_data_model=UpdateKpi,
                         resource="kpis")

    @retry_on_401
    def find_by_key(self, key: str, persona: str = "tenant"):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            metrics_found_request = client.get(
                f"/v1/kpis",
                params={
                    "key": key,
                    "persona": persona,
                    "per-page": 1,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            if metrics_found_request.status_code == 200:
                metrics_found_data = metrics_found_request.json()
                if len(metrics_found_data) == 0:
                    return None
                else:
                    return self.retrieve(metrics_found_data[0]["id"])
            return None


class KpisAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=KpiAsync,
                         retrieve_data_model=KpiAPIDTO,
                         create_data_model=CreateKpi,
                         update_data_model=UpdateKpi,
                         resource="kpis")

    @retry_on_401_async
    async def find_by_key(self, key: str, persona: str = "tenant"):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            metrics_found_request = await client.get(
                f"/v1/kpis",
                params={
                    "key": key,
                    "persona": persona,
                    "per-page": 1,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(metrics_found_request)
            metrics_found_data = metrics_found_request.json()
            if len(metrics_found_data) == 0:
                return None
            else:
                return await self.retrieve(metrics_found_data[0]["id"])
