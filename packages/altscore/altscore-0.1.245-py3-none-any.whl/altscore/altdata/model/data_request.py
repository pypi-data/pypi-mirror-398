from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from altscore.altdata.helpers import build_headers
from altscore.altdata.model.common_schemas import SourceConfig
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
import json
import httpx


class Address(BaseModel):
    street1: str = Field(alias="street1")
    street2: Optional[str] = Field(alias="street2", default=None)
    neighborhood: str = Field(alias="neighborhood", default=None)
    district: str = Field(alias="district", default=None)
    city: str = Field(alias="city", default=None)
    state: str = Field(alias="state", default=None)
    province: Optional[str] = Field(alias="province", default=None)
    zip_code: str = Field(alias="zipCode", default=None)
    country: str = Field(alias="country", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Location(BaseModel):
    lat: float = Field(alias="lat")
    lon: float = Field(alias="lon")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class InputKeys(BaseModel):
    foreign_key: Optional[str] = Field(alias="foreignKey", default=None)
    person_id: Optional[str] = Field(alias="personId", default=None)
    person_id_expedition_date: Optional[str] = Field(alias="personIdExpeditionDate", default=None)
    name: Optional[str] = Field(alias="name", default=None)
    first_name: Optional[str] = Field(alias="firstName", default=None)
    middle_name: Optional[str] = Field(alias="middleName", default=None)
    paternal_surname: Optional[str] = Field(alias="paternalSurname", default=None)
    maternal_surname: Optional[str] = Field(alias="maternalSurname", default=None)
    birth_date: Optional[str] = Field(alias="birthDate", default=None)
    nationality: Optional[str] = Field(alias="nationality", default=None)
    phone: Optional[str] = Field(alias="phone", default=None)
    email: Optional[str] = Field(alias="email", default=None)
    vehicle_license_plate: Optional[str] = Field(alias="vehicleLicensePlate", default=None)
    address: Optional[Address] = Field(alias="address", default=None)
    location: Optional[Location] = Field(alias="location", default=None)
    tax_id: Optional[str] = Field(alias="taxId", default=None)
    legal_name: Optional[str] = Field(alias="legalName", default=None)
    dba: Optional[str] = Field(alias="dba", default=None)
    business_id: Optional[str] = Field(alias="businessId", default=None)
    legal_rep_id: Optional[str] = Field(alias="legalRepId", default=None)
    country_code: Optional[str] = Field(alias="countryCode", default=None)
    date_to_analyze: Optional[str] = Field(alias="dateToAnalyze", default=None)
    authorization_reference: Optional[str] = Field(alias="authorizationReference", default=None)
    passport_number: Optional[str] = Field(alias="passportNumber", default=None)
    items: Optional[List] = Field(alias="items", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class SourceCallSummary(BaseModel):
    source_id: str = Field(alias="sourceId")
    version: str = Field(alias="version")
    status: Optional[str] = Field(alias="status", default=None)
    is_success: bool = Field(alias="isSuccess")
    error_message: Optional[str] = Field(alias="errorMessage", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

    def __repr__(self):
        return f"<SourceCallSummary: {self.source_id}_{self.version}, isSuccess:{self.is_success}>"


class StatusAPIDTO(BaseModel):
    request_id: str = Field(alias="requestId")
    status: str = Field(alias="status")
    requested_at: str = Field(alias="requestedAt")
    call_summary: List[SourceCallSummary] = Field(alias="callSummary")


class RequestStatus:
    def __init__(self, data: StatusAPIDTO):
        self.data = data

    @classmethod
    def from_api(cls, response: Dict):
        return cls(data=StatusAPIDTO.parse_obj(response))

    def are_all_source_calls_success(self):
        return all([s.is_success for s in self.data.call_summary])

    @property
    def status(self):
        return self.data.status

    def is_complete(self):
        return self.status == "complete"


class RequestAPIDTO(BaseModel):
    request_id: str = Field(alias="requestId")
    flat_data: Dict = Field(alias="data")
    call_summary: Optional[List[SourceCallSummary]] = Field(alias="callSummary", default=[])
    source_data: Dict = Field(alias="sourceData", default=None)
    inputs: Dict
    requested_at: str = Field(alias="requestedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class RequestResult:
    def __init__(self, data: RequestAPIDTO):
        self.data = data

    def __repr__(self):
        r = self.data.dict(by_alias=True)
        return json.dumps(r, indent=4, ensure_ascii=False)

    @classmethod
    def from_api(cls, response: Dict):
        return cls(data=RequestAPIDTO.parse_obj(response))

    @property
    def call_summary(self):
        return self.data.call_summary

    def are_all_source_calls_success(self):
        return all([s.is_success for s in self.data.call_summary])

    def get_source_call_summary(self, source_id: str):
        return next((s for s in self.data.call_summary if s.source_id == source_id), None)

    def get_data(self, source_id: str):
        return self.data.flat_data.get(source_id, None)

    def get_source_data(self, source_id: str):
        return self.data.source_data.get(source_id, None)

    def to_package(self, source_id: str):
        source_call_summary = self.get_source_call_summary(source_id).dict(by_alias=True)
        return {
            "sourceId": source_id,
            "version": source_call_summary["version"],
            "isSuccess": source_call_summary["isSuccess"],
            "requestId": self.data.request_id,
            "data": self.get_data(source_id),
            "sourceData": self.get_source_data(source_id),
            "inputs": self.data.inputs,
            "requestedAt": self.data.requested_at,
        }


class RequestSyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def new_sync(self, input_keys: Union[InputKeys, Dict], sources_config: List[Union[Dict, SourceConfig]],
                 timeout: Optional[int] = None, execution_id: Optional[str] = None, workflow_id: Optional[str] = None,
                 batch_id: Optional[str] = None):
        if isinstance(input_keys, dict):
            # to validate the input keys
            input_keys = InputKeys.parse_obj(input_keys)
        payload = input_keys.dict(by_alias=True, exclude_none=True)
        # to validate the sources config model
        sources_config = [SourceConfig.parse_obj(s) if isinstance(s, dict) else s for s in sources_config]

        if timeout is not None:
            payload["timeout"] = timeout

        if execution_id is not None:
            payload["executionId"] = execution_id

        if workflow_id is not None:
            payload["workflowId"] = workflow_id

        if batch_id is not None:
            payload["batchId"] = batch_id

        payload["sourcesConfig"] = [s.dict(by_alias=True) for s in sources_config]
        with httpx.Client(base_url=self.altscore_client._altdata_base_url) as client:
            r = client.post(
                url="/v1/requests/sync",
                json=payload,
                headers=self.build_headers(),
                timeout=500
                # dont confuse with the timeout in the payload, this is the timeout for the request, not the sources
            )
            raise_for_status_improved(r)
            sync_data_response = r.json()
            return RequestResult.from_api(sync_data_response)

    @retry_on_401
    def new_async(self, input_keys: Union[InputKeys, Dict], sources_config: List[Union[Dict, SourceConfig]],
                  execution_id: Optional[str] = None, workflow_id: Optional[str] = None,
                  batch_id: Optional[str] = None):
        if isinstance(input_keys, dict):
            # to validate the input keys
            input_keys = InputKeys.parse_obj(input_keys)
        payload = input_keys.dict(by_alias=True, exclude_none=True)
        # to validate the sources config model
        sources_config = [SourceConfig.parse_obj(s) if isinstance(s, dict) else s for s in sources_config]

        if execution_id is not None:
            payload["executionId"] = execution_id

        if workflow_id is not None:
            payload["workflowId"] = workflow_id

        if batch_id is not None:
            payload["batchId"] = batch_id

        payload["sourcesConfig"] = [s.dict(by_alias=True) for s in sources_config]
        with httpx.Client(base_url=self.altscore_client._altdata_base_url) as client:
            r = client.post(
                url="/v1/requests/async",
                json=payload,
                headers=self.build_headers(),
                timeout=500
            )
            raise_for_status_improved(r)
            sync_data_response = r.json()
            return AsyncRequestSync(
                base_url=self.altscore_client._altdata_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                request_id=sync_data_response["requestId"]
            )

    def retrieve(self, request_id: str):
        return AsyncRequestSync(
            base_url=self.altscore_client._altdata_base_url,
            header_builder=self.build_headers,
            renew_token=self.renew_token,
            request_id=request_id
        )


class RequestAsyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401_async
    async def new_sync(self, input_keys: Union[InputKeys, Dict], sources_config: List[Union[Dict, SourceConfig]],
                       timeout: Optional[int] = None, execution_id: Optional[str] = None,
                       workflow_id: Optional[str] = None, batch_id: Optional[str] = None):
        if isinstance(input_keys, dict):
            # to validate the input keys
            input_keys = InputKeys.parse_obj(input_keys)
        payload = input_keys.dict(by_alias=True, exclude_none=True)
        # to validate the sources config model
        sources_config = [SourceConfig.parse_obj(s) if isinstance(s, dict) else s for s in sources_config]
        if timeout is not None:
            payload["timeout"] = timeout

        if execution_id is not None:
            payload["executionId"] = execution_id

        if workflow_id is not None:
            payload["workflowId"] = workflow_id

        if batch_id is not None:
            payload["batchId"] = batch_id

        payload["sourcesConfig"] = [s.dict(by_alias=True) for s in sources_config]
        async with httpx.AsyncClient(base_url=self.altscore_client._altdata_base_url) as client:
            r = await client.post(
                url="/v1/requests/sync",
                json=payload,
                headers=self.build_headers(),
                timeout=500
            )
            raise_for_status_improved(r)
            sync_data_response = r.json()
            return RequestResult.from_api(sync_data_response)

    @retry_on_401_async
    async def new_async(self, input_keys: Union[InputKeys, Dict], sources_config: List[Union[Dict, SourceConfig]],
                        execution_id: Optional[str] = None, workflow_id: Optional[str] = None,
                        batch_id: Optional[str] = None):
        if isinstance(input_keys, dict):
            # to validate the input keys
            input_keys = InputKeys.parse_obj(input_keys)
        payload = input_keys.dict(by_alias=True, exclude_none=True)
        # to validate the sources config model
        sources_config = [SourceConfig.parse_obj(s) if isinstance(s, dict) else s for s in sources_config]

        if execution_id is not None:
            payload["executionId"] = execution_id

        if workflow_id is not None:
            payload["workflowId"] = workflow_id

        if batch_id is not None:
            payload["batchId"] = batch_id

        payload["sourcesConfig"] = [s.dict(by_alias=True) for s in sources_config]
        async with httpx.AsyncClient(base_url=self.altscore_client._altdata_base_url) as client:
            r = await client.post(
                url="/v1/requests/async",
                json=payload,
                headers=self.build_headers(),
                timeout=500
            )
            raise_for_status_improved(r)
            sync_data_response = r.json()
            return AsyncRequestAsync(
                base_url=self.altscore_client._altdata_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                request_id=sync_data_response["requestId"]
            )

    def retrieve(self, request_id: str):
        return AsyncRequestSync(
            base_url=self.altscore_client._altdata_base_url,
            header_builder=self.build_headers,
            renew_token=self.renew_token,
            request_id=request_id
        )


class RequestsBase:

    def __init__(self, base_url):
        self.base_url = base_url

    def _get(self, request_id: str):
        return f"{self.base_url}/v1/requests/{request_id}"

    def _get_status(self, request_id: str):
        return f"{self.base_url}/v1/requests/{request_id}/status"

    def _retry(self, request_id: str):
        return f"{self.base_url}/v1/requests/{request_id}/retry"


class AsyncRequestSync(RequestsBase):

    def __init__(self, base_url, header_builder, renew_token, request_id: str):
        super().__init__(base_url)
        self.base_url = base_url
        self.header_builder = header_builder
        self.renew_token = renew_token
        self.request_id = request_id

    @property
    def id(self):
        return self.request_id

    @retry_on_401
    def pull(self):
        with httpx.Client(base_url=self.base_url) as client:
            r = client.get(
                url=self._get(self.id),
                headers=self.header_builder()
            )
            raise_for_status_improved(r)
            return RequestResult.from_api(r.json())

    @retry_on_401
    def get_status(self):
        with httpx.Client(base_url=self.base_url) as client:
            r = client.get(
                url=self._get_status(self.id),
                headers=self.header_builder()
            )
            raise_for_status_improved(r)
            return RequestStatus.from_api(r.json())


class AsyncRequestAsync(RequestsBase):

    def __init__(self, base_url, header_builder, renew_token, request_id: str):
        super().__init__(base_url)
        self.base_url = base_url
        self.header_builder = header_builder
        self.renew_token = renew_token
        self.request_id = request_id

    @property
    def id(self):
        return self.request_id

    @retry_on_401_async
    async def pull(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            r = await client.get(
                url=self._get(self.id),
                headers=self.header_builder()
            )
            raise_for_status_improved(r)
            return RequestResult.from_api(r.json())

    @retry_on_401_async
    async def get_status(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            r = await client.get(
                url=self._get_status(self.id),
                headers=self.header_builder()
            )
            raise_for_status_improved(r)
            return RequestStatus.from_api(r.json())
