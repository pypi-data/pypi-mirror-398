import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from altscore.borrower_central.model.report_templates import ReportFilter, ReportConfig


# DTO for report requests
class ReportRequestDTO(BaseModel):
    """Data transfer object for report requests"""
    id: str = Field(alias="id")
    email: str = Field(alias="email")
    config: Optional[ReportConfig] = Field(alias="config", default=None)
    template_id: Optional[str] = Field(alias="templateId", default=None)
    status: str = Field(alias="status")
    error_message: Optional[str] = Field(alias="errorMessage", default=None)
    file_url: Optional[str] = Field(alias="fileUrl", default=None)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateReportRequest(BaseModel):
    """Model for creating a new report request"""
    email: str = Field(alias="email")
    config: Optional[ReportConfig] = Field(alias="config", default=None)
    template_id: Optional[str] = Field(alias="templateId", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateReportRequest(BaseModel):
    """Model for updating a report request"""
    status: Optional[str] = Field(alias="status", default=None)
    error_message: Optional[str] = Field(alias="errorMessage", default=None)
    file_url: Optional[str] = Field(alias="fileUrl", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Generation result from the high memory endpoint
class CustomReportResult(BaseModel):
    """Result from the generate report endpoint"""
    request_id: str = Field(alias="requestId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class GenerateReportRequest(BaseModel):
    """Model for generating a report"""
    config: Optional[ReportConfig] = Field(alias="config", default=None)
    template_id: Optional[str] = Field(alias="templateId", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Resource classes for report requests
class ReportRequestSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "custom-reports", header_builder, renew_token, ReportRequestDTO.parse_obj(data))


class ReportRequestAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "custom-reports", header_builder, renew_token, ReportRequestDTO.parse_obj(data))


# Module for report requests - synchronous
class CustomReportsSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=ReportRequestSync,
                         retrieve_data_model=ReportRequestDTO,
                         create_data_model=CreateReportRequest,
                         update_data_model=UpdateReportRequest,
                         resource="custom-reports")

    @retry_on_401
    def generate_report(self, config: Optional[ReportConfig] = None,
                        template_id: Optional[str] = None):
        """
        Generate a custom report based on the specified configuration or template.
        Returns immediately with a request ID that can be used to check the status.
        The report will be generated asynchronously and an email will be sent when it's ready.
        
        Args:
            config: Report configuration (optional if template_id is provided)
            template_id: ID of a report template to use (optional if config is provided)
            
        Returns:
            CustomReportResult object containing the request ID
        """
        if not config and not template_id:
            raise ValueError("Either config or template_id must be provided")

        request_data = GenerateReportRequest(
            config=config,
            templateId=template_id
        )

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/custom-reports/commands/generate",
                json=request_data.dict(by_alias=True, exclude_none=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def get_reports_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """Get report requests filtered by status"""
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/custom-reports",
                params={
                    "status": status,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return response.json()


# Module for report requests - asynchronous
class CustomReportsAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=ReportRequestAsync,
                         retrieve_data_model=ReportRequestDTO,
                         create_data_model=CreateReportRequest,
                         update_data_model=UpdateReportRequest,
                         resource="custom-reports")

    @retry_on_401_async
    async def generate_report(self, config: Optional[ReportConfig] = None,
                              template_id: Optional[str] = None) -> CustomReportResult:
        """
        Generate a custom report based on the specified configuration or template.
        Returns immediately with a request ID that can be used to check the status.
        The report will be generated asynchronously and an email will be sent when it's ready.
        
        Args:
            config: Report configuration (optional if template_id is provided)
            template_id: ID of a report template to use (optional if config is provided)
            
        Returns:
            CustomReportResult object containing the request ID
        """
        if not config and not template_id:
            raise ValueError("Either config or template_id must be provided")

        request_data = GenerateReportRequest(
            config=config,
            templateId=template_id
        )

        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/custom-reports/commands/generate",
                json=request_data.dict(by_alias=True, exclude_none=True),
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def get_reports_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """Get report requests filtered by status"""
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/custom-reports",
                params={
                    "status": status,
                    "page": page,
                    "per-page": per_page
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(response)
            return response.json()
