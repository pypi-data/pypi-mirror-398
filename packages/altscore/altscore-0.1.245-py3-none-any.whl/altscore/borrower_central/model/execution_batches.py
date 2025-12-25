import json

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, cast

from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
import httpx


EXECUTION_BATCH_STATUS_PENDING = "pending"
EXECUTION_BATCH_STATUS_PRE_PROCESSING = "pre_processing"
EXECUTION_BATCH_STATUS_PRE_PROCESSING_COMPLETE = "pre_processing_complete"
EXECUTION_BATCH_STATUS_PRE_PROCESSING_FAILED = "pre_processing_failed"
EXECUTION_BATCH_STATUS_PROCESSING = "processing"
EXECUTION_BATCH_STATUS_PROCESSING_COMPLETE = "processing_complete"
EXECUTION_BATCH_STATUS_POST_PROCESSING = "post_processing"
EXECUTION_BATCH_STATUS_POST_PROCESSING_FAILED = "post_processing_failed"
EXECUTION_BATCH_STATUS_COMPLETE = "complete"
EXECUTION_BATCH_STATUS_PAUSED = "paused"
EXECUTION_BATCH_STATUS_CANCELLED = "cancelled"
EXECUTION_BATCH_STATUS_FAILED = "failed"

EXECUTION_BATCH_PHASE_RESULT_SUCCESS = "success"
EXECUTION_BATCH_PHASE_RESULT_FATAL_ERROR = "fatal_error"
EXECUTION_BATCH_PHASE_RESULT_UNHANDLED_ERROR = "unhandled_error"


class BatchItemsExecutionSummary(BaseModel):
    expected: Optional[int] = Field(alias="expected", default=0)
    pending: Optional[int] = Field(alias="pending", default=0)
    failed: Optional[int] = Field(alias="failed", default=0)
    success: Optional[int] = Field(alias="success", default=0)
    unsuccessful_sources: Optional[int] = Field(alias="unsuccessfulSources", default=0)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchInputs(BaseModel):
    items: List[Dict] = Field(alias="items", default=[])
    raw_package_ids: List[str] = Field(alias="rawPackageIds", default=[])
    custom_input: Dict = Field(alias="customInput", default={})

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchPreProcessingOutput(BaseModel):
    processed_input_package_id: str = Field(alias="processedInputPackageId")
    item_count: int = Field(alias="itemCount")
    result: str = Field(alias="result")
    notices: List[str] = Field(alias="notices")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchPostProcessingOutput(BaseModel):
    processed_output_package_id: str = Field(alias="processedOutputPackageId")
    item_count: int = Field(alias="itemCount")
    result: str = Field(alias="result")
    notices: List[str] = Field(alias="notices")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchOutputs(BaseModel):
    w_batch_pre_processing_output: Optional[ExecutionBatchPreProcessingOutput] = Field(alias="wBatchPreProcessingOutput", default=None)
    w_batch_post_processing_output: Optional[ExecutionBatchPostProcessingOutput] = Field(alias="wBatchPostProcessingOutput", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchState(BaseModel):
    batch_items_executions_summary: Optional[BatchItemsExecutionSummary] = Field(alias="batchItemsExecutionsSummary", default=None)
    pre_processing_retries: Optional[int] = Field(alias="preProcessingRetries", default=0)
    post_processing_retries: Optional[int] = Field(alias="postProcessingRetries", default=0)
    batch_items_outputs_generating: Optional[bool] = Field(alias="batchItemsOutputsGenerating", default=False)
    batch_items_outputs_package_id: Optional[str] = Field(alias="batchItemsOutputsPackageId", default=None)
    pre_processing_started_at: Optional[str] = Field(alias="preProcessingStartedAt", default=None)
    post_processing_started_at: Optional[str] = Field(alias="postProcessingStartedAt", default=None)
    processing_started_at: Optional[str] = Field(alias="processingStartedAt", default=None)
    batch_items_outputs_generation_started_at: Optional[str] = Field(alias="batchItemsOutputsGenerationStartedAt", default=None)
    preparing_batch_items_retry: Optional[bool] = Field(alias="preparingBatchItemsRetry", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True



class CreateExecutionBatchDTO(BaseModel):
    status: Optional[str] = Field(alias="status", default=None)
    workflow_id: Optional[str] = Field(alias="workflowId", default=None)
    workflow_alias: Optional[str] = Field(alias="workflowAlias", default=None)
    workflow_version: Optional[str] = Field(alias="workflowVersion", default=None)
    callback_at: Optional[str] = Field(alias="callbackAt", default=None)
    principal_id: Optional[str] = Field(alias="principalId", default=None)
    is_billable: Optional[bool] = Field(alias="isBillable", default=None)
    state: Optional[ExecutionBatchState] = Field(alias="state", default=ExecutionBatchState())
    tags: Optional[List[str]] = Field(alias="tags", default=[])
    label: Optional[str] = Field(alias="label", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    inputs: Optional[ExecutionBatchInputs] = Field(alias="inputs", default=None)
    debug: Optional[bool] = Field(alias="debug", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateExecutionBatchDTO(BaseModel):
    status: Optional[str] = Field(alias="status", default=None)
    callback_at: Optional[str] = Field(alias="callbackAt", default=None)
    state: Optional[ExecutionBatchState] = Field(alias="state", default=None)
    inputs: Optional[ExecutionBatchInputs] = Field(alias="inputs", default=None)
    outputs: Optional[ExecutionBatchOutputs] = Field(alias="outputs", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchItemOutputAPIDTO(BaseModel):
    item_index: int = Field(alias="itemIndex")
    input: dict = Field(alias="input")
    output: dict = Field(alias="output")
    is_success: bool = Field(alias="isSuccess")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchAPIDTO(BaseModel):
    id: str = Field(alias="id")
    status: Optional[str] = Field(alias="status", default=None)
    callback_at: Optional[str] = Field(alias="callbackAt", default=None)
    state: ExecutionBatchState = Field(alias="state")
    label: Optional[str] = Field(alias="label", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    workflow_id: Optional[str] = Field(alias="workflowId", default=None)
    workflow_alias: Optional[str] = Field(alias="workflowAlias", default=None)
    workflow_version: Optional[str] = Field(alias="workflowVersion", default=None)
    is_billable: Optional[bool] = Field(alias="isBillable", default=None)
    tags: List[str] = Field(alias="tags")
    principal_id: Optional[str] = Field(alias="principalId", default=None)
    created_at: str = Field(alias="createdAt")
    finished_at: Optional[str] = Field(alias="finishedAt", default=None)
    inputs: Optional[ExecutionBatchInputs] = Field(alias="inputs", default=None)
    outputs: Optional[ExecutionBatchOutputs] = Field(alias="outputs", default=None)
    debug: Optional[bool] = Field(alias="debug", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ExecutionBatchAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "execution-batches", header_builder, renew_token, ExecutionBatchAPIDTO.parse_obj(data))

    def _execution_batch(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}"


    @retry_on_401_async
    async def patch(self,
        inputs: Optional[Dict] = None,
        outputs: Optional[Dict] = None,
        status: Optional[str] = None,
        callback_at: Optional[str] = None,
        state: Optional[Dict] = None
    ):
        payload = {
            "inputs": inputs,
            "outputs": outputs,
            "status": status,
            "callbackAt": callback_at,
            "state": state
        }

        with httpx.AsyncClient() as client:
            response = await client.patch(
                self._execution_batch(self.data.id),
                headers=self._header_builder(),
                json=payload,
                timeout=300
            )

            raise_for_status_improved(response)
            self.data = ExecutionBatchAPIDTO.parse_obj(response.json())


class ExecutionBatchAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client, async_resource=ExecutionBatchAsync, retrieve_data_model=ExecutionBatchAPIDTO,
                         create_data_model=CreateExecutionBatchDTO, update_data_model=UpdateExecutionBatchDTO, resource="execution-batches")


    async def get_batch_items_outputs(self, execution_batch_id):
        execution_batch = cast(ExecutionBatchAsync, await self.retrieve(execution_batch_id))

        batch_items_outputs_package_id = execution_batch.data.state.batch_items_outputs_package_id

        if batch_items_outputs_package_id is None:
            return None

        package = await self.altscore_client.borrower_central.store_packages.retrieve(batch_items_outputs_package_id)
        await package.get_content()

        outputs = json.loads(package.content)
        outputs = [ExecutionBatchItemOutputAPIDTO.parse_obj(result) for result in outputs]

        return outputs


class ExecutionBatchSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "execution-batches", header_builder, renew_token, ExecutionBatchAPIDTO.parse_obj(data))

    def _execution_batch(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}"

    @retry_on_401
    def patch(self,
        inputs: Optional[Dict] = None,
        outputs: Optional[Dict] = None,
        status: Optional[str] = None,
        callback_at: Optional[str] = None,
        state: Optional[Dict] = None
    ):
        payload = {
            "inputs": inputs,
            "outputs": outputs,
            "status": status,
            "callbackAt": callback_at,
            "state": state
        }

        with httpx.Client() as client:
            response = client.patch(
                self._execution_batch(self.data.id),
                headers=self._header_builder(),
                json=payload,
                timeout=300
            )

            raise_for_status_improved(response)
            self.data = ExecutionBatchAPIDTO.parse_obj(response.json())


class ExecutionBatchSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client, sync_resource=ExecutionBatchSync, retrieve_data_model=ExecutionBatchAPIDTO,
                         create_data_model=CreateExecutionBatchDTO, update_data_model=UpdateExecutionBatchDTO, resource="execution-batches")


    def get_batch_items_outputs(self, execution_batch_id):
        execution_batch = cast(ExecutionBatchSync, self.retrieve(execution_batch_id))

        batch_items_outputs_package_id = execution_batch.data.state.batch_items_outputs_package_id

        if batch_items_outputs_package_id is None:
            return None

        package = self.altscore_client.borrower_central.store_packages.retrieve(batch_items_outputs_package_id)
        package.get_content()

        outputs = json.loads(package.content)
        outputs = [ExecutionBatchItemOutputAPIDTO.parse_obj(result) for result in outputs]

        return outputs