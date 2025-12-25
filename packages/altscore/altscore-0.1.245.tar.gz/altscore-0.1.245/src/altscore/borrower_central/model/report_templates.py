import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class ReportFilter(BaseModel):
    """Filter configuration for custom reports"""
    metric_keys: Optional[List[str]] = Field(alias="metricKeys", default=None)
    step_keys: Optional[List[str]] = Field(alias="stepKeys", default=None)
    field_keys: Optional[List[str]] = Field(alias="fieldKeys", default=None)
    identity_keys: Optional[List[str]] = Field(alias="identityKeys", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ReportConfig(BaseModel):
    """Configuration for custom reports"""
    include_borrowers: bool = Field(alias="includeBorrowers", default=True)
    include_identities: bool = Field(alias="includeIdentities", default=True)
    include_fields: bool = Field(alias="includeFields", default=True)
    include_points_of_contact: bool = Field(alias="includePointsOfContact", default=True)
    include_metrics: bool = Field(alias="includeMetrics", default=False)
    include_steps: bool = Field(alias="includeSteps", default=False)
    include_credit_lines: bool = Field(alias="includeCreditLines", default=False)
    include_debts: bool = Field(alias="includeDebts", default=False)
    include_debt_schedules: bool = Field(alias="includeDebtSchedules", default=False)
    include_debt_transactions: bool = Field(alias="includeDebtTransactions", default=False)
    include_partner_clients: bool = Field(alias="includePartnerClients", default=False)
    filters: Optional[ReportFilter] = Field(alias="filters", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# DTO for report templates
class ReportTemplateDTO(BaseModel):
    """Data transfer object for report templates"""
    id: str = Field(alias="id")
    key: str = Field(alias="key")
    label: str = Field(alias='label')
    description: Optional[str] = Field(alias="description", default=None)
    config: ReportConfig = Field(alias="config")
    created_by: str = Field(alias="createdBy")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateReportTemplate(BaseModel):
    """Model for creating a new report template"""
    key: str = Field(alias="key")
    label: str = Field(alias='label')
    description: Optional[str] = Field(alias="description", default=None)
    config: ReportConfig = Field(alias="config")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateReportTemplate(BaseModel):
    """Model for updating a report template"""
    key: Optional[str] = Field(alias="key")
    label: Optional[str] = Field(alias='label')
    description: Optional[str] = Field(alias="description", default=None)
    config: Optional[ReportConfig] = Field(alias="config", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Resource classes for report templates
class ReportTemplateSync(GenericSyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "report-templates", header_builder, renew_token, ReportTemplateDTO.parse_obj(data))


class ReportTemplateAsync(GenericAsyncResource):
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "report-templates", header_builder, renew_token, ReportTemplateDTO.parse_obj(data))


# Module for report templates - synchronous
class ReportTemplateSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=ReportTemplateSync,
                         retrieve_data_model=ReportTemplateDTO,
                         create_data_model=CreateReportTemplate,
                         update_data_model=UpdateReportTemplate,
                         resource="report-templates")

    @retry_on_401
    def find_by_key(self, key: str):
        """Find a report template by its key"""
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            request = client.get(
                f"/v1/report-templates",
                params={
                    "search": key,
                    "per-page": 10,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            if request.status_code == 200:
                data = request.json()
                if len(data) == 0:
                    return None

                # Filter exact key match
                for item in data:
                    if item["key"].lower() == key.lower():
                        return self.retrieve(item["id"])

                return None
            return None


# Module for report templates - asynchronous
class ReportTemplateAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=ReportTemplateAsync,
                         retrieve_data_model=ReportTemplateDTO,
                         create_data_model=CreateReportTemplate,
                         update_data_model=UpdateReportTemplate,
                         resource="report-templates")

    @retry_on_401_async
    async def find_by_key(self, key: str):
        """Find a report template by its key"""
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            request = await client.get(
                f"/v1/report-templates",
                params={
                    "search": key,
                    "per-page": 10,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            raise_for_status_improved(request)
            data = request.json()
            if len(data) == 0:
                return None

            # Filter exact key match
            for item in data:
                if item["key"].lower() == key.lower():
                    return await self.retrieve(item["id"])

            return None
