import datetime as dt
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
import httpx
from altscore.altdata.helpers import build_headers
from pydantic import BaseModel, validator, Field
from altscore.altdata.model.common_schemas import SourceConfig
from altscore.altdata.utils.dataframes import df_to_base64
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from dateutil.parser import parse
import json


class BatchFileRequest(BaseModel):
    name: str
    base64: str


class BatchDataRequest(BaseModel):
    label: str = Field(alias="label")
    sources_config: List[SourceConfig] = Field(alias="sourcesConfig")
    requests: List[Dict] = Field(alias="requests", default=[])
    file: Optional[BatchFileRequest] = Field(alias="file", default=None)


class BatchSourceSuccessStats(BaseModel):
    source_id: str = Field(alias="sourceId")
    total_count: int = Field(alias="totalCount")
    success_count: int = Field(alias="successCount")
    failed_count: int = Field(alias="failedCount")
    processing_count: int = Field(alias="processingCount")
    non_retryable_count: int = Field(alias="nonRetryableCount")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BatchStatus(BaseModel):
    batch_id: str = Field(alias="batchId")
    requested_at: Union[dt.datetime, str] = Field(alias="requestedAt")
    request_count: int = Field(alias="requestCount")
    status: str = Field(alias="status")
    progress_pct: float = Field(alias="progressPct")
    success_pct: float = Field(alias="successPct")
    failed_pct: float = Field(alias="failedPct")
    non_retryable_pct: float = Field(alias="nonRetryablePct")
    source_stats: List[BatchSourceSuccessStats] = Field(alias="sourceStats")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

    @validator("requested_at")
    def parse_requested_at(cls, v):
        if isinstance(v, str):
            return parse(v, yearfirst=True)
        return v

    def __str__(self):
        r = self.dict(by_alias=True)
        if isinstance(r.get("requestedAt"), dt.datetime):
            r["requestedAt"] = r["requestedAt"].isoformat()
        return json.dumps(r, indent=4, ensure_ascii=False)

    def print_source_stats(self):
        import pandas as pd
        df = pd.DataFrame([e.dict() for e in self.source_stats])
        print(df.to_markdown())


class BatchSyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    def new_batch_from_dataframe(self, df, label: str,
                                 sources_config: List[SourceConfig]):
        with httpx.Client(base_url=self.altscore_client._altdata_base_url) as client:
            payload = df_to_batch_payload(df=df, label=label, sources_config=sources_config)
            batch_response = client.post(
                "/v1/batches",
                json=payload,
                headers=self.build_headers(),
                timeout=500
            )
            raise_for_status_improved(batch_response)
            batch_id = batch_response.json()["batchId"]
            return BatchSync(
                base_url=self.altscore_client._altdata_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=BatchData(batch_id=batch_id, label=label, sources_config=sources_config)
            )

    def retrieve(self, batch_id: str):
        with httpx.Client(base_url=self.altscore_client._altdata_base_url) as client:
            response = client.get(
                f"/v1/batches/{batch_id}",
                headers=self.build_headers(),
                timeout=500
            )
            raise_for_status_improved(response)
            return BatchSync(
                base_url=self.altscore_client._altdata_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=BatchData(
                    batch_id=batch_id,
                    label=response.json()["label"],
                    sources_config=response.json()["sourcesConfig"]
                )
            )


class BatchAsyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    async def new_batch_from_dataframe(self, df, label: str, sources_config: List[SourceConfig]):
        async with httpx.AsyncClient(base_url=self.altscore_client._altdata_base_url) as client:
            payload = df_to_batch_payload(df=df, label=label, sources_config=sources_config)
            batch_response = await client.post(
                "/v1/batches",
                json=payload,
                headers=self.build_headers(),
                timeout=500
            )
            raise_for_status_improved(batch_response)
            batch_id = batch_response.json()["batchId"]
            return BatchSync(
                base_url=self.altscore_client._altdata_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=BatchData(batch_id=batch_id, label=label, sources_config=sources_config)
            )

    async def retrieve(self, batch_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._altdata_base_url) as client:
            response = await client.get(
                f"/v1/batches/{batch_id}",
                headers=self.build_headers(),
                timeout=500
            )
            raise_for_status_improved(response)
            return BatchSync(
                base_url=self.altscore_client._altdata_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=BatchData(
                    batch_id=batch_id,
                    label=response.json()["label"],
                    sources_config=response.json()["sourcesConfig"]
                )
            )


class BatchBase:

    def __init__(self, base_url):
        self.base_url = base_url

    def _status(self, batch_id: str):
        return f"{self.base_url}/v1/batches/{batch_id}/status"

    def _retry(self, batch_id: str):
        return f"{self.base_url}/v1/batches/{batch_id}/retry"

    def _export(self, batch_id: str):
        return f"{self.base_url}/v1/batches/{batch_id}/export"


class BatchData:

    def __init__(self, batch_id, label, sources_config):
        self.batch_id = batch_id
        self.label = label
        self.sources_config = sources_config
        self.status: Optional[BatchStatus] = None
        self.export_urls: Optional[Dict[str, str]] = None


class BatchSync(BatchBase):

    def __init__(self, base_url, header_builder, renew_token, data: BatchData):
        super().__init__(base_url)
        self.header_builder = header_builder
        self.renew_token = renew_token
        self.data: BatchData = data

    @property
    def batch_id(self):
        return self.data.batch_id

    @property
    def label(self):
        return self.data.label

    @property
    def status(self):
        return self.data.status

    @property
    def export_urls(self):
        return self.data.export_urls

    @retry_on_401
    def get_status(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(self._status(batch_id=self.data.batch_id),
                                  headers=self.header_builder())
            raise_for_status_improved(response)
            self.data.status = BatchStatus.parse_obj(response.json())

    @retry_on_401
    def retry(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(self._retry(batch_id=self.data.batch_id),
                                   headers=self.header_builder())
            raise_for_status_improved(response)

    @retry_on_401
    def _get_export_urls(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                self._export(batch_id=self.data.batch_id),
                headers=self.header_builder(),
                timeout=500
            )
            raise_for_status_improved(response)
            data = response.json()
            assert data.get("dataExportUrl") is not None and data.get(
                "dataExportUrl") != "", "Failed to parse response, contact support or update SDK"
            assert data.get("sourceDataExportUrl") is not None and data.get(
                "sourceDataExportUrl") != "", "Failed to parse response, contact support or update SDK"
            self.data.export_urls = data

    def export_to_dataframe(self):
        import pandas as pd
        if self.export_urls is None:
            self._get_export_urls()
        return pd.read_csv(
            self.export_urls["dataExportUrl"], encoding="utf-8",
            dtype={"personId": str, "taxId": str, "foreignKey": str, "email": str, "phone": str}
        )

    def export_source_data_to_dict(self):
        if self.export_urls is None:
            self._get_export_urls()
        with httpx.Client() as client:
            req = client.get(self.export_urls["sourceDataExportUrl"], timeout=500)
            data = [json.loads(e) for e in req.content.decode("utf8").split("\n") if len(e) > 0]
            return data


class BatchAsync(BatchBase):

    def __init__(self, base_url, header_builder, renew_token, data: BatchData):
        super().__init__(base_url)
        self.header_builder = header_builder
        self.renew_token = renew_token
        self.data: BatchData = data

    @property
    def batch_id(self):
        return self.data.batch_id

    @property
    def label(self):
        return self.data.label

    @property
    def status(self):
        return self.data.status

    @property
    def export_urls(self):
        return self.data.export_urls

    @retry_on_401_async
    async def get_status(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(self._status(batch_id=self.data.batch_id),
                                        headers=self.header_builder())
            raise_for_status_improved(response)
            self.data.status = BatchStatus.parse_obj(response.json())

    @retry_on_401_async
    async def retry(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(self._retry(batch_id=self.data.batch_id),
                                         headers=self.header_builder())
            raise_for_status_improved(response)

    async def _get_export_urls(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                self._export(batch_id=self.data.batch_id),
                headers=self.header_builder(),
                timeout=500
            )
            raise_for_status_improved(response)
            data = response.json()
            assert data.get("dataExportUrl") is not None and data.get(
                "dataExportUrl") != "", "Failed to parse response, contact support or update SDK"
            assert data.get("sourceDataExportUrl") is not None and data.get(
                "sourceDataExportUrl") != "", "Failed to parse response, contact support or update SDK"
            self.data.export_urls = data

    async def export_to_dataframe(self):
        import pandas as pd
        if self.export_urls is None:
            await self._get_export_urls()
        return pd.read_csv(
            self.export_urls["dataExportUrl"], encoding="utf-8",
            dtype={"personId": str, "taxId": str, "foreignKey": str, "email": str, "phone": str}
        )

    async def export_source_data_to_dict(self):
        if self.export_urls is None:
            await self._get_export_urls()

        async with httpx.AsyncClient() as client:
            req = await client.get(self.export_urls["sourceDataExportUrl"], timeout=500)
            data = [json.loads(e) for e in req.content.decode("utf8").split("\n") if len(e) > 0]
            return data


def df_to_batch_payload(df, label, sources_config):
    import numpy as np
    data = df.replace({np.nan: None})
    base_64 = df_to_base64(data)
    sources_config_obj = [SourceConfig.parse_obj(x) for x in sources_config]
    payload = BatchDataRequest(
        label=label,
        sourcesConfig=sources_config_obj,
        file=BatchFileRequest(name="df_from_sdk.csv", base64=base_64),
    ).dict(by_alias=True)
    return payload
