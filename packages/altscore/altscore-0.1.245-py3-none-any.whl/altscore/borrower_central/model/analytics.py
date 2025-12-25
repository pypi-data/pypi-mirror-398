from typing import List, Dict, Optional, Union

import httpx
from pydantic import BaseModel, Field

from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.helpers import build_headers

class DateInterval(BaseModel):
    from_: Optional[str] = Field(alias="from", default=None)
    to: Optional[str] = Field(alias="to", default=None)

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True
        populate_by_name = True

class Filter(BaseModel):
    key: str = Field(alias="key")
    entity_type: str = Field(alias="entityType")
    operator: str = Field(alias="operator")
    value: Union[str | List[str]] = Field(alias="value")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True
        populate_by_name = True


class QueryMetadataDTO(BaseModel):
    intl: Dict[str, Dict] = Field(alias="intl")
    data_type: str = Field(alias="dataType")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class NewQueryDTO(BaseModel):
    metric_key: str = Field(alias="metricKey")
    columns: List[str] = Field(alias="columns")
    metadata_cols: List[str] = Field(alias="metadataCols")
    query_metadata: QueryMetadataDTO = Field(alias="queryMetadata")
    query_template: str = Field(alias="queryTemplate")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class ExecuteQueryDTO(BaseModel):
    metric_key: str = Field(alias="metricKey")
    filters: Optional[List[Filter]] = Field(alias="filters", default=[])
    cohort_date: DateInterval = Field(alias="cohortDate", default=DateInterval())
    analysis_date: Optional[str] = Field(alias="analysisDate", default=None)

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True
        populate_by_name = True

class AnalyticsAsyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401_async
    async def create_query(self, new_metric: Dict):
        base_url = self.altscore_client._borrower_central_base_url
        async with httpx.AsyncClient(base_url=base_url) as client:
            response = await client.post(
                "/v1/analytics/commands/new-metric",
                headers=self.build_headers(),
                json=NewQueryDTO.parse_obj(new_metric).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def execute_query(self, query: Dict):
        base_url = self.altscore_client._borrower_central_base_url
        async with httpx.AsyncClient(base_url=base_url) as client:
            response = await client.post(
                "/v1/analytics/commands/get-metrics",
                headers=self.build_headers(),
                json=ExecuteQueryDTO.parse_obj(query).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()

    @retry_on_401_async
    async def delete_query(self, query_key: str):
        base_url = self.altscore_client._borrower_central_base_url
        async with httpx.AsyncClient(base_url=base_url) as client:
            response = await client.delete(
                f"/v1/analytics/query/{query_key}",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)

class AnalyticsSyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def create_query(self, new_metric: Dict):
        base_url = self.altscore_client._borrower_central_base_url
        with httpx.Client(base_url=base_url) as client:
            response = client.post(
                "/v1/analytics/commands/new-metric",
                headers=self.build_headers(),
                json=NewQueryDTO.parse_obj(new_metric).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)

    @retry_on_401
    def execute_query(self, query: Dict):
        base_url = self.altscore_client._borrower_central_base_url
        with httpx.Client(base_url=base_url) as client:
            response = client.post(
                "/v1/analytics/commands/get-metrics",
                headers=self.build_headers(),
                json=ExecuteQueryDTO.parse_obj(query).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()

    @retry_on_401
    def delete_query(self, query_key: str):
        base_url = self.altscore_client._borrower_central_base_url
        with httpx.Client(base_url=base_url) as client:
            response = client.delete(
                f"/v1/analytics/query/{query_key}",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)