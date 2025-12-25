import httpx
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class WorkflowSchedule(BaseModel):
    cron: str = Field(alias="cron")
    utc_delta_hours: int = Field(alias="utcDeltaHours", default=0, ge=-12, le=14)
    execution_settings: Optional[dict] = Field(alias="executionSettings", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class WorkflowDataAPIDTO(BaseModel):
    id: str = Field(alias="id")
    execution_mode: Optional[str] = Field(alias="executionMode", default=None)
    alias: str = Field(alias="alias")
    version: str = Field(alias="version")
    label: Optional[str] = Field(alias="label")
    type: Optional[str] = Field(alias="type")
    description: Optional[str] = Field(alias="description")
    context: Optional[str] = Field(alias="context")
    input_schema: Optional[str] = Field(alias="inputSchema", default=None)
    json_schema: Optional[str] = Field(alias="jsonSchema", default=None)
    ui_schema: Optional[str] = Field(alias="uiSchema", default=None)
    initial_data: Optional[str] = Field(alias="initialData", default=None)
    flow_definition: Optional[dict] = Field(alias="flowDefinition")
    batch_flow_definition: Optional[dict] = Field(alias="batchFlowDefinition")
    schedule: Optional[WorkflowSchedule] = Field(alias="schedule", default=None)
    schedule_batch: Optional[WorkflowSchedule] = Field(alias="scheduleBatch", default=None)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")
    use_high_memory: Optional[bool] = Field(alias="useHighMemory", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class Lambda(BaseModel):
    url: str = Field(alias="url")
    headers: Dict[str, str] = Field(alias="headers", default={})


class CreateWorkflowDTO(BaseModel):
    label: Optional[str] = Field(alias="label")
    alias: str = Field(alias="alias")
    version: str = Field(alias="version")
    type: Optional[str] = Field(alias="type", default=None)
    execution_mode: Optional[str] = Field(alias="executionMode", default=None)
    description: Optional[str] = Field(alias="description")
    context: Optional[str] = Field(alias="context", default=None)
    flow_definition: Optional[dict] = Field(alias="flowDefinition", default=None)
    batch_flow_definition: Optional[dict] = Field(alias="batchFlowDefinition", default=None)
    input_schema: Optional[str] = Field(alias="inputSchema", default=None)
    json_schema: Optional[str] = Field(alias="jsonSchema", default=None)
    ui_schema: Optional[str] = Field(alias="uiSchema", default=None)
    initial_data: Optional[str] = Field(alias="initialData", default=None)
    route: Optional[Lambda] = Field(alias="route", default=None)
    schedule: Optional[WorkflowSchedule] = Field(alias="schedule", default=None)
    schedule_batch: Optional[WorkflowSchedule] = Field(alias="scheduleBatch", default=None)
    use_high_memory: Optional[bool] = Field(alias="useHighMemory", default=False)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateWorkflowDTO(BaseModel):
    label: Optional[str] = Field(alias="label")
    description: Optional[str] = Field(alias="description")
    type: Optional[str] = Field(alias="type", default=None)
    route: Optional[Lambda] = Field(alias="route", default=None)
    flow_definition: Optional[dict] = Field(alias="flowDefinition", default=None)
    batch_flow_definition: Optional[dict] = Field(alias="batchFlowDefinition", default=None)
    json_schema: Optional[str] = Field(alias="jsonSchema", default=None)
    ui_schema: Optional[str] = Field(alias="uiSchema", default=None)
    initial_data: Optional[str] = Field(alias="initialData", default=None)
    input_schema: Optional[str] = Field(alias="inputSchema", default=None)
    use_high_memory: Optional[bool] = Field(alias="useHighMemory", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ConfigureSchedulesDTO(BaseModel):
    workflow_id: str = Field(alias="workflowId")
    schedule: Optional[WorkflowSchedule] = Field(alias="schedule", default=None)
    schedule_batch: Optional[WorkflowSchedule] = Field(alias="scheduleBatch", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class WorkflowExecutionResponseAPIDTO(BaseModel):
    execution_id: str = Field(alias="executionId")
    workflow_id: str = Field(alias="workflowId")
    workflow_alias: str = Field(alias="workflowAlias")
    workflow_version: str = Field(alias="workflowVersion")
    is_success: Optional[bool] = Field(alias="isSuccess")
    executed_at: str = Field(alias="executedAt")
    execution_output: Any = Field(alias="executionOutput")
    execution_custom_output: Any = Field(alias="executionCustomOutput")
    error_message: Optional[str] = Field(alias="errorMessage", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class WorkflowSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "workflows", header_builder, renew_token, WorkflowDataAPIDTO.parse_obj(data))

    @retry_on_401
    def configure_schedules(self, schedule: dict = None, schedule_batch: dict = None):
        url = f"{self.base_url}/v1/{self.resource}/commands/configure-schedules"

        with httpx.Client() as client:
            response = client.post(
                url,
                headers=self._header_builder(),
                timeout=300,
                json=ConfigureSchedulesDTO.parse_obj({
                    "workflowId": self.data.id,
                    "schedule": schedule,
                    "scheduleBatch": schedule_batch
                }).dict(by_alias=True)
            )

            raise_for_status_improved(response)

    @retry_on_401
    def delete_schedules(self, schedule: bool = False, schedule_batch: bool = False):
        url = f"{self.base_url}/v1/{self.resource}/commands/delete-schedules"

        with httpx.Client() as client:
            response = client.post(
                url,
                headers=self._header_builder(),
                timeout=300,
                json={
                    "workflowId": self.data.id,
                    "schedule": schedule,
                    "scheduleBatch": schedule_batch
                }
            )

            raise_for_status_improved(response)


class WorkflowAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "workflows", header_builder, renew_token, WorkflowDataAPIDTO.parse_obj(data))

    @retry_on_401_async
    async def configure_schedules(self, schedule: dict = None, schedule_batch: dict = None):
        url = f"{self.base_url}/v1/{self.resource}/commands/configure-schedules"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._header_builder(),
                timeout=300,
                json=ConfigureSchedulesDTO.parse_obj({
                    "workflowId": self.data.id,
                    "schedule": schedule,
                    "scheduleBatch": schedule_batch
                }).dict(by_alias=True)
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def delete_schedules(self, schedule: bool = False, schedule_batch: bool = False):
        url = f"{self.base_url}/v1/{self.resource}/commands/delete-schedules"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._header_builder(),
                timeout=300,
                json={
                    "workflowId": self.data.id,
                    "schedule": schedule,
                    "scheduleBatch": schedule_batch
                }
            )
            raise_for_status_improved(response)


class WorkflowsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=WorkflowSync,
                         retrieve_data_model=WorkflowDataAPIDTO,
                         create_data_model=CreateWorkflowDTO,
                         update_data_model=UpdateWorkflowDTO,
                         resource="workflows")

    @retry_on_401
    def retrieve_by_alias_version(self, alias: str, version: str):
        query_params = {
            "alias": alias,
            "version": version
        }

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            res = [self.sync_resource(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]

            if len(res) == 0:
                return None
            return res[0]

    @retry_on_401
    def execute(self, workflow_input: Dict,
                workflow_id: Optional[str] = None,
                workflow_alias: Optional[str] = None,
                workflow_version: Optional[str] = None,
                execution_mode: Optional[str] = None,
                batch_id: Optional[str] = None,
                tags: Optional[List[str]] = None,
                batch: Optional[bool] = False
                ):
        headers = self.build_headers()
        if execution_mode is not None:
            headers["X-Execution-Mode"] = execution_mode
        if batch_id is not None:
            headers["X-Batch-Id"] = batch_id

        if tags is not None:
            tags = ",".join(tags)
            headers["x-tags"] = tags

        if workflow_id is not None:
            with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
                response = client.post(
                    f"/v1/workflows/{workflow_id}/execute",
                    json=workflow_input,
                    headers=headers,
                    timeout=900
                )
                raise_for_status_improved(response)
                return WorkflowExecutionResponseAPIDTO.parse_obj(response.json())

        elif workflow_alias is not None and workflow_version is not None:
            with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
                response = client.post(
                    f"/v1/workflows/{workflow_alias}/{workflow_version}/execute",
                    json=workflow_input,
                    headers=headers,
                    timeout=900
                )
                raise_for_status_improved(response)
                return WorkflowExecutionResponseAPIDTO.parse_obj(response.json())
        else:
            raise ValueError("You must provide a workflow id or a workflow alias and version")

    @retry_on_401
    def execute_batch(self,
                      workflow_id=None,
                      workflow_alias=None,
                      workflow_version=None,
                      label=None,
                      description=None,
                      max_executions_per_second=1,
                      max_concurrent_dispatches=1,
                      max_item_execution_runs=2,
                      items=None,
                      raw_package_ids=None,
                      custom_input=None,
                      tags=None,
                      debug=False,
                      billable=True):
        """
        Execute a batch workflow with the given parameters.

        Args:
            workflow_id: ID of the workflow to execute
            workflow_alias: Alias of the workflow (required if workflow_id not provided)
            workflow_version: Version of the workflow (required if workflow_id not provided)
            label: Optional label for the batch execution
            description: Optional description for the batch execution
            max_executions_per_second: Rate limit for executions
            max_concurrent_dispatches: Maximum number of concurrent dispatches
            max_item_execution_runs: Maximum number of execution runs per item
            items: List of items to process (max 10)
            raw_package_ids: List of package IDs containing items to process (max 5)
            custom_input: Custom input for the workflow
            tags: List of tags for the execution
            debug: Whether to run in debug mode
            billable: Whether the execution is billable

        Returns:
            Execution response
        """
        # Basic validation
        if workflow_id is None and (workflow_alias is None or workflow_version is None):
            raise ValueError("Either workflow_id or both workflow_alias and workflow_version must be provided")

        # Prepare headers
        headers = self.build_headers()
        if tags:
            headers["x-tags"] = ",".join(tags) if isinstance(tags, list) else tags
        headers["x-debug"] = str(debug).lower()
        headers["x-billable"] = str(billable).lower()

        # Prepare payload
        execute_input = {
            "label": label,
            "description": description,
            "maxExecutionsPerSecond": max_executions_per_second,
            "maxConcurrentDispatches": max_concurrent_dispatches,
            "maxItemExecutionRuns": max_item_execution_runs,
            "workflowInput": {
                "items": items or [],
                "rawPackageIds": raw_package_ids or [],
                "customInput": custom_input or {}
            },
            "attachmentFileNames": []
        }

        # Execute API call
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            if workflow_id:
                url = f"/v1/workflows/{workflow_id}/execute-batch"
            else:
                url = f"/v1/workflows/{workflow_alias}/{workflow_version}/execute-batch"

            response = client.post(
                url,
                json=execute_input,
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)
            return response.json()

    @retry_on_401
    def clear_metadata(self, workflow_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.delete(
                f"/v1/workflows/{workflow_id}/metadata",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401
    def execute_batch_with_dataframe(self,
                                     dataframe,
                                     workflow_id=None,
                                     workflow_alias=None,
                                     workflow_version=None,
                                     alias=None,
                                     label=None,
                                     description=None,
                                     max_executions_per_second=1,
                                     max_concurrent_dispatches=1,
                                     max_item_execution_runs=2,
                                     custom_input=None,
                                     output_format="csv",
                                     export_params=None,
                                     tags=None,
                                     debug=False,
                                     billable=True):
        """
        Execute a batch workflow with data from a pandas DataFrame.

        This method handles converting the dataframe to the specified format (CSV, XLSX, JSON, or Parquet),
        uploading it as a package attachment, and executing the batch workflow with the package.

        Args:
            dataframe: Pandas DataFrame containing the data to process
            workflow_id: ID of the workflow to execute
            workflow_alias: Alias of the workflow (required if workflow_id not provided)
            workflow_version: Version of the workflow (required if workflow_id not provided)
            alias: Optional alias for the created package
            label: Optional label for the batch execution
            description: Optional description for the batch execution
            max_executions_per_second: Rate limit for executions
            max_concurrent_dispatches: Maximum number of concurrent dispatches
            max_item_execution_runs: Maximum number of execution runs per item
            custom_input: Custom input for the workflow
            output_format: Format for the dataframe export ("csv", "xlsx", "json", or "parquet")
            export_params: Additional parameters to pass to the pandas export function
            tags: List of tags for the execution
            debug: Whether to run in debug mode
            billable: Whether the execution is billable

        Returns:
            Execution response
        """
        import os
        import tempfile
        import uuid

        # Validate the output format
        valid_formats = ["csv", "xlsx", "json", "parquet"]
        if output_format not in valid_formats:
            raise ValueError(f"Invalid output_format. Must be one of: {', '.join(valid_formats)}")

        # Set default export parameters
        if export_params is None:
            if output_format == "csv":
                export_params = {"index": False}
            elif output_format == "xlsx":
                export_params = {"index": False}
            elif output_format == "json":
                export_params = {"orient": "records"}
            elif output_format == "parquet":
                export_params = {}

        # Set default file name with appropriate extension
        file_name = f"{uuid.uuid4()}.{output_format}"

        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file_name)

        # Export dataframe to the specified format
        if output_format == "csv":
            dataframe.to_csv(temp_file_path, **export_params)
        elif output_format == "xlsx":
            try:
                dataframe.to_excel(temp_file_path, **export_params)
            except ImportError:
                raise ImportError("Excel export requires openpyxl. Install with 'pip install openpyxl'")
        elif output_format == "json":
            dataframe.to_json(temp_file_path, **export_params)
        elif output_format == "parquet":
            try:
                dataframe.to_parquet(temp_file_path, **export_params)
            except ImportError:
                raise ImportError(
                    "Parquet export requires pyarrow or fastparquet. Install with 'pip install pyarrow' or 'pip install fastparquet'")

        try:
            # Create a package with minimal content
            package_data = {
                "alias": alias or f'batch-{uuid.uuid4()}',
            }

            # Create the package
            package_id = self.altscore_client.borrower_central.store_packages.create(package_data)

            # Retrieve the package to upload attachment
            package = self.altscore_client.borrower_central.store_packages.retrieve(package_id)

            # Upload the file as an attachment
            package.upload_package_attachment(temp_file_path)

            # Execute batch with the package_id
            return self.execute_batch(
                workflow_id=workflow_id,
                workflow_alias=workflow_alias,
                workflow_version=workflow_version,
                label=label,
                description=description,
                max_executions_per_second=max_executions_per_second,
                max_concurrent_dispatches=max_concurrent_dispatches,
                max_item_execution_runs=max_item_execution_runs,
                raw_package_ids=[package_id],
                custom_input=custom_input,
                tags=tags,
                debug=debug,
                billable=billable
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


class WorkflowsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=WorkflowAsync,
                         retrieve_data_model=WorkflowDataAPIDTO,
                         create_data_model=CreateWorkflowDTO,
                         update_data_model=UpdateWorkflowDTO,
                         resource="workflows")

    @retry_on_401_async
    async def retrieve_by_alias_version(self, alias: str, version: str):
        query_params = {
            "alias": alias,
            "version": version
        }

        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            res = [self.async_resource(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]

            if len(res) == 0:
                return None
            return res[0]

    @retry_on_401_async
    async def execute(self,
                      workflow_input: Dict,
                      workflow_id: Optional[str] = None,
                      workflow_alias: Optional[str] = None,
                      workflow_version: Optional[str] = None,
                      execution_mode: Optional[str] = None,
                      batch_id: Optional[str] = None,
                      tags: Optional[List[str]] = None
                      ):
        headers = self.build_headers()
        if execution_mode is not None:
            headers["X-Execution-Mode"] = execution_mode
        if batch_id is not None:
            headers["X-Batch-Id"] = batch_id

        if tags is not None:
            tags = ",".join(tags)
            headers["x-tags"] = tags

        if workflow_id is not None:
            async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
                response = await client.post(
                    f"/v1/workflows/{workflow_id}/execute",
                    json=workflow_input,
                    headers=headers,
                    timeout=900
                )
                raise_for_status_improved(response)
                return WorkflowExecutionResponseAPIDTO.parse_obj(response.json())

        elif workflow_alias is not None and workflow_version is not None:
            async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
                response = await client.post(
                    f"/v1/workflows/{workflow_alias}/{workflow_version}/execute",
                    json=workflow_input,
                    headers=headers,
                    timeout=900
                )
                raise_for_status_improved(response)
                return WorkflowExecutionResponseAPIDTO.parse_obj(response.json())
        else:
            raise ValueError("You must provide a workflow id or a workflow alias and version")

    @retry_on_401_async
    async def execute_batch(self,
                            workflow_id=None,
                            workflow_alias=None,
                            workflow_version=None,
                            label=None,
                            description=None,
                            max_executions_per_second=1,
                            max_concurrent_dispatches=1,
                            max_item_execution_runs=2,
                            items=None,
                            raw_package_ids=None,
                            custom_input=None,
                            tags=None,
                            debug=False,
                            billable=True):
        """
        Execute a batch workflow with the given parameters asynchronously.

        Args:
            workflow_id: ID of the workflow to execute
            workflow_alias: Alias of the workflow (required if workflow_id not provided)
            workflow_version: Version of the workflow (required if workflow_id not provided)
            label: Optional label for the batch execution
            description: Optional description for the batch execution
            max_executions_per_second: Rate limit for executions
            max_concurrent_dispatches: Maximum number of concurrent dispatches
            max_item_execution_runs: Maximum number of execution runs per item
            items: List of items to process (max 10)
            raw_package_ids: List of package IDs containing items to process (max 5)
            custom_input: Custom input for the workflow
            tags: List of tags for the execution
            debug: Whether to run in debug mode
            billable: Whether the execution is billable

        Returns:
            Execution response
        """
        # Basic validation
        if workflow_id is None and (workflow_alias is None or workflow_version is None):
            raise ValueError("Either workflow_id or both workflow_alias and workflow_version must be provided")

        # Prepare headers
        headers = self.build_headers()
        if tags:
            headers["x-tags"] = ",".join(tags) if isinstance(tags, list) else tags
        headers["x-debug"] = str(debug).lower()
        headers["x-billable"] = str(billable).lower()

        # Prepare payload
        execute_input = {
            "label": label,
            "description": description,
            "maxExecutionsPerSecond": max_executions_per_second,
            "maxConcurrentDispatches": max_concurrent_dispatches,
            "maxItemExecutionRuns": max_item_execution_runs,
            "workflowInput": {
                "items": items or [],
                "rawPackageIds": raw_package_ids or [],
                "customInput": custom_input or {}
            },
            "attachmentFileNames": []
        }

        # Execute API call
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            if workflow_id:
                url = f"/v1/workflows/{workflow_id}/execute-batch"
            else:
                url = f"/v1/workflows/{workflow_alias}/{workflow_version}/execute-batch"

            response = await client.post(
                url,
                json=execute_input,
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)
            return response.json()

    @retry_on_401_async
    async def clear_metadata(self, workflow_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.delete(
                f"/v1/workflows/{workflow_id}/metadata",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def execute_batch_with_dataframe(self,
                                           dataframe,
                                           workflow_id=None,
                                           workflow_alias=None,
                                           workflow_version=None,
                                           alias=None,
                                           label=None,
                                           description=None,
                                           max_executions_per_second=1,
                                           max_concurrent_dispatches=1,
                                           max_item_execution_runs=2,
                                           custom_input=None,
                                           output_format="csv",
                                           export_params=None,
                                           tags=None,
                                           debug=False,
                                           billable=True):
        """
        Execute a batch workflow with data from a pandas DataFrame asynchronously.

        This method handles converting the dataframe to the specified format (CSV, XLSX, JSON, or Parquet),
        uploading it as a package attachment, and executing the batch workflow with the package.

        Args:
            dataframe: Pandas DataFrame containing the data to process
            workflow_id: ID of the workflow to execute
            workflow_alias: Alias of the workflow (required if workflow_id not provided)
            workflow_version: Version of the workflow (required if workflow_id not provided)
            alias: Optional alias for the created package
            label: Optional label for the batch execution
            description: Optional description for the batch execution
            max_executions_per_second: Rate limit for executions
            max_concurrent_dispatches: Maximum number of concurrent dispatches
            max_item_execution_runs: Maximum number of execution runs per item
            custom_input: Custom input for the workflow
            output_format: Format for the dataframe export ("csv", "xlsx", "json", or "parquet")
            export_params: Additional parameters to pass to the pandas export function
            tags: List of tags for the execution
            debug: Whether to run in debug mode
            billable: Whether the execution is billable

        Returns:
            Execution response
        """
        import os
        import tempfile
        import uuid

        # Validate the output format
        valid_formats = ["csv", "xlsx", "json", "parquet"]
        if output_format not in valid_formats:
            raise ValueError(f"Invalid output_format. Must be one of: {', '.join(valid_formats)}")

        # Set default export parameters
        if export_params is None:
            if output_format == "csv":
                export_params = {"index": False}
            elif output_format == "xlsx":
                export_params = {"index": False}
            elif output_format == "json":
                export_params = {"orient": "records"}
            elif output_format == "parquet":
                export_params = {}

        # Set default file name with appropriate extension
        file_name = f"{uuid.uuid4()}.{output_format}"

        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file_name)

        # Export dataframe to the specified format
        if output_format == "csv":
            dataframe.to_csv(temp_file_path, **export_params)
        elif output_format == "xlsx":
            try:
                dataframe.to_excel(temp_file_path, **export_params)
            except ImportError:
                raise ImportError("Excel export requires openpyxl. Install with 'pip install openpyxl'")
        elif output_format == "json":
            dataframe.to_json(temp_file_path, **export_params)
        elif output_format == "parquet":
            try:
                dataframe.to_parquet(temp_file_path, **export_params)
            except ImportError:
                raise ImportError(
                    "Parquet export requires pyarrow or fastparquet. Install with 'pip install pyarrow' or 'pip install fastparquet'")

        try:
            # Create a package with minimal content
            package_data = {
                "alias": alias or f'batch-{uuid.uuid4()}',
            }

            # Create the package
            package_id = await self.altscore_client.borrower_central.store_packages.create(package_data)

            # Retrieve the package to upload attachment
            package = await self.altscore_client.borrower_central.store_packages.retrieve(package_id)

            # Upload the file as an attachment
            await package.upload_package_attachment(temp_file_path)

            # Execute batch with the package_id
            return await self.execute_batch(
                workflow_id=workflow_id,
                workflow_alias=workflow_alias,
                workflow_version=workflow_version,
                label=label,
                description=description,
                max_executions_per_second=max_executions_per_second,
                max_concurrent_dispatches=max_concurrent_dispatches,
                max_item_execution_runs=max_item_execution_runs,
                raw_package_ids=[package_id],
                custom_input=custom_input,
                tags=tags,
                debug=debug,
                billable=billable
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
