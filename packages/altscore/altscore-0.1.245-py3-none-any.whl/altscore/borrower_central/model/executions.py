from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule, convert_to_dash_case
from altscore.borrower_central.model.attachments import AttachmentInput, AttachmentAPIDTO
from altscore.borrower_central.model.workflows import WorkflowExecutionResponseAPIDTO
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
import httpx
import datetime as dt
from altscore.borrower_central.model.decisions import CurrentDecisionInExecution, PostDecisionToExecution
from dateutil.parser import parse

EXECUTION_NOTICE_SEVERITY_INFO = "info"
EXECUTION_NOTICE_SEVERITY_ERROR = "error"
EXECUTION_NOTICE_SEVERITY_DEBUG = "debug"

class ExecutionNotice(BaseModel):
    message: str = Field(alias="message")
    severity: str = Field(alias="severity")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class CreateExecutionDTO(BaseModel):
    workflow_id: Optional[str] = Field(alias="workflowId", default=None)
    workflow_alias: Optional[str] = Field(alias="workflowAlias", default=None)
    workflow_version: Optional[str] = Field(alias="workflowVersion", default=None)
    workflow_type: Optional[str] = Field(alias="workflowType", default=None)
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    billable_id: Optional[str] = Field(alias="billableId", default=None)
    batch_id: Optional[str] = Field(alias="batchId", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateExecutionDTO(BaseModel):
    unsuccessful_sources: Optional[bool] = Field(alias="unsuccessfulSources", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchMeta(BaseModel):
    id: str = Field(alias="id")
    item_index: int = Field(alias="itemIndex")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class ExecutionAPIDTO(BaseModel):
    id: Optional[str] = Field(alias="id")
    principal_id: Optional[str] = Field(alias="principalId", default=None)
    workflow_id: str = Field(alias="workflowId")
    workflow_alias: str = Field(alias="workflowAlias")
    workflow_version: str = Field(alias="workflowVersion")
    workflow_type: Optional[str] = Field(alias="workflowType")
    batch_id: Optional[str] = Field(alias="batchId")
    execution_batch: Optional[ExecutionBatchMeta] = Field(alias="executionBatch", default=None)
    billable_id: Optional[str] = Field(alias="billableId")
    borrower_id: Optional[str] = Field(alias="borrowerId")
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    current_decision: Optional[CurrentDecisionInExecution] = Field(alias="currentDecision", default=None)
    status: Optional[str] = Field(alias="status", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=[])
    unsuccessful_sources: Optional[bool] = Field(alias="unsuccessfulSources", default=None)
    is_success: Optional[bool] = Field(alias="isSuccess", default=None)
    is_billable: Optional[bool] = Field(alias="isBillable", default=None)
    is_re_scoring: Optional[bool] = Field(alias="isReScoring", default=None)
    created_at: str = Field(alias="createdAt")
    execution_time: Optional[int] = Field(alias="executionTime", default=None)
    response_time: Optional[int] = Field(alias="responseTime", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionInputDataAPIDTO(BaseModel):
    id: Optional[str] = Field(alias="id")
    workflow_id: str = Field(alias="workflowId")
    workflow_alias: str = Field(alias="workflowAlias")
    workflow_version: str = Field(alias="workflowVersion")
    input: Dict = Field(alias="input")
    created_at: str = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionOutputDataAPIDTO(BaseModel):
    id: Optional[str] = Field(alias="id")
    billable_id: Optional[str] = Field(alias="billableId")
    borrower_id: Optional[str] = Field(alias="borrowerId")
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    workflow_id: str = Field(alias="workflowId")
    workflow_alias: str = Field(alias="workflowAlias")
    workflow_version: str = Field(alias="workflowVersion")
    workflow_type: Optional[str] = Field(alias="workflowType")
    status: Optional[str] = Field(alias="status", default=None)
    is_success: Optional[bool] = Field(alias="isSuccess")
    output: Any = Field(alias="output")
    custom_output: Any = Field(alias="customOutput")
    has_attachments: bool = Field(alias="hasAttachments")
    created_at: str = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateExecutionOutput(BaseModel):
    is_success: bool = Field(alias="isSuccess")
    status_code: Optional[int] = Field(alias="statusCode", default=None)
    attachments: Optional[List[AttachmentInput]] = Field(alias="attachments", default=[])
    output: Dict = Field(alias="output")
    custom_output: Optional[Any] = Field(alias="customOutput", default=None)
    error_message: Optional[str] = Field(alias="errorMessage", default=None)
    billable_id: Optional[str] = Field(alias="billableId", default=None)
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    execution_time: Optional[int] = Field(alias="executionTime", default=None)
    notices: Optional[List[ExecutionNotice]] = Field(alias="notices", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


EXECUTION_STATUS_PENDING = "pending"
EXECUTION_STATUS_SCHEDULED = "scheduled"
EXECUTION_STATUS_ON_CALLBACK = "on_callback"
EXECUTION_STATUS_COMPLETE = "complete"


class ExecutionState(BaseModel):
    status: str = Field(alias="status")
    execution_batch_id: Optional[str] = Field(alias="executionBatchId", default=None)
    callback_at: dt.datetime = Field(alias="callbackAt")
    state: Dict = Field(alias="state")
    updated_at: Optional[dt.datetime] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

    @classmethod
    def from_api_dto(cls, data: Dict):
        return cls(
            status=data["status"],
            execution_batch_id=data["executionBatchId"],
            callback_at=parse(data["callbackAt"]),
            state=data["state"],
            updated_at=parse(data["updatedAt"]) if data["updatedAt"] else None
        )

    def to_api_dto(self):
        return {
            "status": self.status,
            "executionBatchId": self.execution_batch_id,
            "callbackAt": self.callback_at.isoformat(),
            "state": self.state
        }

    def is_complete(self):
        return self.status == EXECUTION_STATUS_COMPLETE

    def is_scheduled(self):
        return self.status == EXECUTION_STATUS_SCHEDULED

    def is_pending(self):
        return self.status == EXECUTION_STATUS_PENDING

    def is_on_callback(self):
        return self.status == EXECUTION_STATUS_ON_CALLBACK

    def set_as_complete(self):
        self.status = EXECUTION_STATUS_COMPLETE

    def set_as_scheduled(self):
        self.status = EXECUTION_STATUS_SCHEDULED

    def set_as_pending(self):
        self.status = EXECUTION_STATUS_PENDING

    def set_as_on_callback(self):
        self.status = EXECUTION_STATUS_ON_CALLBACK

    @validator("status")
    def status_must_be_valid(cls, v):
        valid_status = [EXECUTION_STATUS_PENDING, EXECUTION_STATUS_SCHEDULED,
                        EXECUTION_STATUS_ON_CALLBACK, EXECUTION_STATUS_COMPLETE]
        if v not in valid_status:
            raise ValueError(f"Invalid status, must be one of {valid_status}")
        return v


class ExecutionSync(GenericSyncResource):
    input: ExecutionInputDataAPIDTO
    output: ExecutionOutputDataAPIDTO
    state: ExecutionState

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "executions", header_builder, renew_token, ExecutionAPIDTO.parse_obj(data))

    def _state(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/state"

    def _input(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/input"

    def _output(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/output"

    def _output_attachments(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/output/attachments"

    @retry_on_401
    def get_input(self):
        with httpx.Client() as client:
            response = client.get(
                self._input(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.input = ExecutionInputDataAPIDTO.parse_obj(response.json())
        return self.input


    @retry_on_401
    def get_output(self):
        with httpx.Client() as client:
            response = client.get(
                self._output(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.output = ExecutionOutputDataAPIDTO.parse_obj(response.json())
        return self.output

    @retry_on_401
    def get_output_attachments(self):
        with httpx.Client() as client:
            response = client.get(
                self._output_attachments(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            return [AttachmentAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401
    def get_state(self):
        with httpx.Client() as client:
            response = client.get(
                self._state(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.state = ExecutionState.parse_obj(response.json())
        return self.state

    @retry_on_401
    def put_state(self, state: Dict):
        state_obj = ExecutionState.parse_obj(state)
        with httpx.Client() as client:
            response = client.put(
                self._state(self.data.id),
                headers=self._header_builder(),
                json=state_obj.to_api_dto(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.state = state_obj

    @retry_on_401
    def put_output(self, output: Dict):
        output_obj = CreateExecutionOutput.parse_obj(output)
        with httpx.Client() as client:
            response = client.put(
                self._output(self.data.id),
                headers=self._header_builder(),
                json=output_obj.dict(by_alias=True),
                timeout=300
            )
            raise_for_status_improved(response)
            self.get_output()

    @retry_on_401
    def post_decision(self, decision_data: PostDecisionToExecution):
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/v1/{self.resource}/{self.data.id}/decisions",
                headers=self._header_builder(),
                json=PostDecisionToExecution.parse_obj(decision_data).dict(by_alias=True, exclude_none=True),
                timeout=300
            )
            raise_for_status_improved(response)

    @retry_on_401
    def delete_decision(self):
        with httpx.Client() as client:
            response = client.delete(
                f"{self.base_url}/v1/{self.resource}/{self.data.id}/decisions",
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)


    @retry_on_401
    def retry(self, execution_mode: Optional[str] = None):
        headers = self._header_builder()
        if execution_mode is not None:
            headers["X-Execution-Mode"] = execution_mode
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/v1/{self.resource}/{self.data.id}/retry",
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)
            return WorkflowExecutionResponseAPIDTO.parse_obj(response.json())


class ExecutionAsync(GenericAsyncResource):
    input: ExecutionInputDataAPIDTO
    output: ExecutionOutputDataAPIDTO
    state: ExecutionState

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "executions", header_builder, renew_token, ExecutionAPIDTO.parse_obj(data))

    def _state(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/state"

    def _input(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/input"

    def _output(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/output"

    def _output_attachments(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/output/attachments"


    @retry_on_401_async
    async def get_input(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._input(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.input = ExecutionInputDataAPIDTO.parse_obj(response.json())
        return self.input


    @retry_on_401_async
    async def get_output(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._output(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.output = ExecutionOutputDataAPIDTO.parse_obj(response.json())
        return self.output

    @retry_on_401_async
    async def get_output_attachments(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._output_attachments(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            return [AttachmentAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401_async
    async def get_state(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._state(self.data.id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.state = ExecutionState.parse_obj(response.json())
        return self.state

    @retry_on_401_async
    async def put_state(self, state: Dict):
        state_obj = ExecutionState.parse_obj(state)
        async with httpx.AsyncClient() as client:
            response = await client.put(
                self._state(self.data.id),
                headers=self._header_builder(),
                json=state_obj.to_api_dto(),
                timeout=300
            )
            raise_for_status_improved(response)
            self.state = state_obj

    @retry_on_401_async
    async def put_output(self, output: Dict):
        output_obj = CreateExecutionOutput.parse_obj(output)
        async with httpx.AsyncClient() as client:
            response = await client.put(
                self._output(self.data.id),
                headers=self._header_builder(),
                json=output_obj.dict(by_alias=True),
                timeout=300
            )
            raise_for_status_improved(response)
            await self.get_output()

    @retry_on_401_async
    async def post_decision(self, decision_data: Dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/{self.resource}/{self.data.id}/decisions",
                headers=self._header_builder(),
                json=PostDecisionToExecution.parse_obj(decision_data).dict(by_alias=True, exclude_none=True),
                timeout=300
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def delete_decision(self):
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/v1/{self.resource}/{self.data.id}/decisions",
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def retry(self, execution_mode: Optional[str] = None):
        headers = self._header_builder()
        if execution_mode is not None:
            headers["X-Execution-Mode"] = execution_mode
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/{self.resource}/{self.data.id}/retry",
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)
            return WorkflowExecutionResponseAPIDTO.parse_obj(response.json())


class ExecutionSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, sync_resource=ExecutionSync, retrieve_data_model=ExecutionAPIDTO,
                         create_data_model=CreateExecutionDTO, update_data_model=UpdateExecutionDTO, resource="executions")

    @retry_on_401
    def query_outputs(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}/outputs",
                headers=self.build_headers(),
                params=query_params,
                timeout=120
            )
            raise_for_status_improved(response)
            return [ExecutionOutputDataAPIDTO.parse_obj(x) for x in response.json()]

    @retry_on_401
    def overwrite_principal(self, old_principal_id: str, new_principal_id: str, from_date: Optional[str] = None,
                             to_date: Optional[str] = None):
        payload = {
            "oldPrincipalId": old_principal_id,
            "newPrincipalId": new_principal_id
        }
        if from_date is not None:
            payload["fromDate"] = from_date
        if to_date is not None:
            payload["toDate"] = to_date

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/{self.resource}/commands/overwrite-principal",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def set_billable_id(self, execution_id:str, billable_id:str):
        payload = {
            "billableId": billable_id
        }

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.put(
                f"/v1/{self.resource}/{execution_id}/billable-id",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None


class ExecutionAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client, async_resource=ExecutionAsync, retrieve_data_model=ExecutionAPIDTO,
                         create_data_model=CreateExecutionDTO, update_data_model=UpdateExecutionDTO, resource="executions")

    @retry_on_401_async
    async def query_outputs(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        async with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/{self.resource}/outputs",
                headers=self.build_headers(),
                params=query_params,
                timeout=120
            )
            raise_for_status_improved(response)
            return [ExecutionOutputDataAPIDTO.parse_obj(x) for x in response.json()]

    @retry_on_401_async
    async def overwrite_principal(self, old_principal_id: str, new_principal_id: str, from_date: Optional[str] = None,
                                 to_date: Optional[str] = None):
        payload = {
            "oldPrincipalId": old_principal_id,
            "newPrincipalId": new_principal_id
        }

        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/{self.resource}/commands/overwrite-principal",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def set_billable_id(self, execution_id:str, billable_id:str):
        payload = {
            "billableId": billable_id
        }

        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.put(
                f"/v1/{self.resource}/{execution_id}/billable-id",
                json=payload,
                headers=self.build_headers()
            )
            raise_for_status_improved(response)
            return None