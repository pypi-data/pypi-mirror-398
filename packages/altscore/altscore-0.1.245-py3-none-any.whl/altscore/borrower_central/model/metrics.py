import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class HistoricValue(BaseModel):
    execution_id: Optional[str] = Field(alias="executionId", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    value: Any = Field(alias="value")
    updated_at: str = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class MetricsAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    key: str = Field(alias="key")
    label: str = Field(alias="label")
    value: Any = Field(alias="value")
    data_type: str = Field(alias="dataType")
    history: List[HistoricValue] = Field(alias="history")
    tags: List[str] = Field(alias="tags", default=[])
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateMetric(BaseModel):
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    execution_id: Optional[str] = Field(alias="executionId", default=None)
    key: str = Field(alias="key")
    value: str = Field(alias="value")
    data_type: Optional[str] = Field(alias="dataType", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateMetric(BaseModel):
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    execution_id: Optional[str] = Field(alias="executionId", default=None)
    value: Optional[str] = Field(alias="value")
    date: Optional[str] = Field(alias="date", default=None)
    data_type: Optional[str] = Field(alias="dataType")
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class MetricSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "metrics", header_builder, renew_token, MetricsAPIDTO.parse_obj(data))


class MetricAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "metrics", header_builder, renew_token, MetricsAPIDTO.parse_obj(data))


class MetricsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=MetricSync,
                         retrieve_data_model=MetricsAPIDTO,
                         create_data_model=CreateMetric,
                         update_data_model=UpdateMetric,
                         resource="metrics")

    @retry_on_401
    def find_tenant_metric_by_key(self, key: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            metrics_found_request = client.get(
                f"/v1/metrics",
                params={
                    "key": key,
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

    @retry_on_401
    def find_borrower_metric_by_key(self, borrower_id: str, key: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            metrics_found_request = client.get(
                f"/v1/metrics",
                params={
                    "borrower-id": borrower_id,
                    "key": key,
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


class MetricsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=MetricAsync,
                         retrieve_data_model=MetricsAPIDTO,
                         create_data_model=CreateMetric,
                         update_data_model=UpdateMetric,
                         resource="metrics")

    @retry_on_401_async
    async def find_tenant_metric_by_key(self, key: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            metrics_found_request = await client.get(
                f"/v1/metrics",
                params={
                    "key": key,
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

    @retry_on_401_async
    async def find_borrower_metric_by_key(self, borrower_id: str, key: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            metrics_found_request = await client.get(
                f"/v1/metrics",
                params={
                    "borrower-id": borrower_id,
                    "key": key,
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
