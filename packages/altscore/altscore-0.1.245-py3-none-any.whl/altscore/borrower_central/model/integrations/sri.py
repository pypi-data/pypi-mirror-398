import datetime as dt
import httpx
from pydantic import BaseModel, Field
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.helpers import build_headers
from typing import Optional


class ExtractionCoverageInfo(BaseModel):
    ruc: str
    date_from: str = Field(alias="dateFrom")
    date_to: str = Field(alias="dateTo")
    has_coverage: bool = Field(alias="hasCoverage")
    has_running_extractions: bool = Field(alias="hasRunningExtractions")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class SriIntegrationAsyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client
        self.base_url = self.altscore_client._borrower_central_base_url

    def build_headers(self):
        return build_headers(self)

    async def check_extractions(
            self, ruc: str, date_to_analyze: Optional[dt.datetime] = None,
            days_of_tolerance: Optional[int] = None
    ) -> ExtractionCoverageInfo:
        payload = {
            "ruc": ruc
        }
        if date_to_analyze is not None:
            payload["dateToAnalyze"] = date_to_analyze.isoformat()
        if days_of_tolerance is not None:
            payload["daysOfTolerance"] = days_of_tolerance
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                "/v1/integrations/sri/extractions/check",
                json=payload,
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return ExtractionCoverageInfo.parse_obj(response.json())

    async def start_extractions(
            self, ruc: str, date_to_analyze: Optional[dt.datetime] = None
    ) -> None:
        payload = {
            "ruc": ruc
        }
        if date_to_analyze is not None:
            payload["dateToAnalyze"] = date_to_analyze.isoformat()

        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                "/v1/integrations/sri/extractions/start",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None

    async def check_credentials(self, ruc: str, password: str, additional_identification=None):
        payload = {
            "ruc": ruc,
            "password": password
        }
        if additional_identification is not None:
            payload["additionalIdentification"] = additional_identification

        async with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                "/v1/integrations/sri/credentials",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None


class SriIntegrationSyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client
        self.base_url = self.altscore_client._borrower_central_base_url

    def build_headers(self):
        return build_headers(self)

    def check_extractions(
            self, ruc: str, date_to_analyze: Optional[dt.datetime] = None,
            days_of_tolerance: Optional[int] = None
    ) -> ExtractionCoverageInfo:
        payload = {
            "ruc": ruc
        }
        if date_to_analyze is not None:
            payload["dateToAnalyze"] = date_to_analyze.isoformat()
        if days_of_tolerance is not None:
            payload["daysOfTolerance"] = days_of_tolerance

        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                "/v1/integrations/sri/extractions/check",
                json=payload,
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return ExtractionCoverageInfo.parse_obj(response.json())

    def start_extractions(
            self, ruc: str, date_to_analyze: Optional[dt.datetime] = None
    ) -> None:
        payload = {
            "ruc": ruc
        }
        if date_to_analyze is not None:
            payload["dateToAnalyze"] = date_to_analyze.isoformat()
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                "/v1/integrations/sri/extractions/start",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None

    def check_credentials(self, ruc: str, password: str, additional_identification=None):
        payload = {
            "ruc": ruc,
            "password": password
        }
        if additional_identification is not None:
            payload["additionalIdentification"] = additional_identification
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                "/v1/integrations/sri/credentials",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None
