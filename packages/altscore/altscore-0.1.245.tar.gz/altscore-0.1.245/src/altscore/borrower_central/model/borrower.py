from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict
import httpx
import asyncio
import datetime as dt

from altscore.borrower_central.helpers import build_headers
from altscore.borrower_central.model.identities import IdentitySync, IdentityAsync
from altscore.borrower_central.model.documents import DocumentSync, DocumentAsync
from altscore.borrower_central.model.addresses import AddressSync, AddressAsync
from altscore.borrower_central.model.points_of_contact import PointOfContactSync, PointOfContactAsync
from altscore.borrower_central.model.borrower_fields import BorrowerFieldSync, BorrowerFieldAsync
from altscore.borrower_central.model.authorizations import AuthorizationSync, AuthorizationAsync
from altscore.borrower_central.model.relationships import RelationshipSync, RelationshipAsync

from altscore.borrower_central.model.stages import StageSync, StageAsync
from altscore.borrower_central.model.steps import StepSync, StepAsync
from altscore.borrower_central.model.risk_ratings import RiskRatingSync, RiskRatingAsync
from altscore.borrower_central.model.repayment_risk_ratings import RepaymentRiskRatingSync, RepaymentRiskRatingAsync
from altscore.borrower_central.model.flags import FlagSync, FlagAsync
from altscore.borrower_central.model.policy_alerts import AlertSync, AlertAsync
from altscore.borrower_central.model.metrics import MetricSync, MetricAsync

from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.model.store_packages import PackageSync, PackageAsync
from altscore.borrower_central.model.executions import ExecutionSync, ExecutionAsync
from altscore.borrower_central.utils import clean_dict, convert_to_dash_case

from loguru import logger


class StepDataInBorrower(BaseModel):
    step_id: str = Field(alias="stepId")
    order: int = Field(alias="order")
    key: str = Field(alias="key")
    created_at: str = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BorrowerAPIDTO(BaseModel):
    id: str = Field(alias="id")
    external_id: Optional[str] = Field(alias="externalId", default=None)
    persona: str = Field(alias="persona")
    avatar_url: Optional[str] = Field(alias="avatarUrl")
    label: Optional[str] = Field(alias="label")
    tags: List[str] = Field(alias="tags", default=[])
    flag: Optional[str] = Field(alias="flag", default=None)
    risk_rating: Optional[str] = Field(alias="riskRating", default=None)
    repayment_risk_rating: Optional[int] = Field(alias="repaymentRiskRating", default=None)
    current_step: Optional[StepDataInBorrower] = Field(alias="currentStep", default=None)
    cms_client_ids: Optional[List[str]] = Field(alias="cmsClientIds", default=[])
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class EntityCategoryValueDTO(BaseModel):
    category_id: str = Field(alias="categoryId")
    category_key: str = Field(alias="categoryKey")
    category_value_id: str = Field(alias="categoryValueId")
    entity_type: str = Field(alias="entityType")
    entity_id: str = Field(alias="entityId")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class SimplifiedIdentity(BaseModel):
    id: str = Field(alias="id")
    key: str = Field(alias="key")
    label: Optional[str] = Field(alias="label")
    value: Optional[str] = Field(alias="value")
    priority: Optional[int] = Field(alias="priority")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class SimplifiedField(BaseModel):
    id: str = Field(alias="id")
    key: str = Field(alias="key")
    label: Optional[str] = Field(alias="label")
    value: Optional[str] = Field(alias="value")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class SimplifiedPointOfContact(BaseModel):
    id: str = Field(alias="id")
    signatures: Optional[List[str]] = Field(alias="signatures")
    priority: int = Field(alias="priority"),
    value: str = Field(alias="value")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CurrentStep(BaseModel):
    order: int = Field(alias="order")
    key: str = Field(alias="key")
    label: str = Field(alias="label")


class BorrowerSummaryAPIDTO(BaseModel):
    id: str = Field(alias="id")
    external_id: Optional[str] = Field(alias="externalId", default=None)
    persona: str = Field(alias="persona")
    label: Optional[str] = Field(alias="label")
    flag: Optional[str] = Field(alias="flag")
    identities: Optional[List[SimplifiedIdentity]] = Field(alias="identities", default=[])
    fields: Optional[List[SimplifiedField]] = Field(alias="fields", default=[])
    points_of_contact: Optional[List[SimplifiedPointOfContact]] = Field(alias="pointsOfContact", default=[])
    tags: List[str] = Field(alias="tags", default=[])
    stage: Optional[str] = Field(alias="stage", default=None)
    risk_rating: Optional[str] = Field(alias="riskRating", default=None)
    repayment_risk_rating: Optional[int] = Field(alias="repaymentRiskRating", default=None)
    current_step: Optional[StepDataInBorrower] = Field(alias="currentStep", default=None)
    cms_client_ids: Optional[List[str]] = Field(alias="cmsClientIds", default=[])
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateBorrowerDTO(BaseModel):
    persona: str = Field(alias="persona")
    external_id: str = Field(alias="externalId", default=None)
    label: Optional[str] = Field(alias="label")
    risk_rating: Optional[str] = Field(alias="riskRating", default=None)
    repayment_risk_rating: Optional[int] = Field(alias="repaymentRiskRating", default=None)
    flag: Optional[str] = Field(alias="flag", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class SetRiskRatingAPIDTO(BaseModel):
    value: str = Field(alias="value")
    reference_id: Optional[str] = Field(alias="referenceId", default=None)
    updated_at: Optional[dt.datetime] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

    def dict(self, *args, **kwargs):
        base_dict = super().dict(*args, **kwargs)
        date_key = 'updatedAt' if kwargs.get("by_alias") else 'updated_at'
        base_dict[date_key] = self.updated_at.isoformat() if self.updated_at else None
        return base_dict

class UpdateBorrowerDTO(BaseModel):
    label: Optional[str] = Field(alias="label", default=None)
    tags: List[str] = Field(alias="tags", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class BorrowerLoginAPIDTO(BaseModel):
    otp_id: str = Field(alias="otpId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BorrowerExportAPIDTO(BaseModel):
    signed_url: str = Field(alias="signedUrl")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BorrowerBase:
    resource = "borrowers"

    def __init__(self, base_url):
        self.base_url = base_url

    def _authorizations(
            self, borrower_id: str, sort_by: Optional[str] = None, key: Optional[str] = None,
            per_page: Optional[int] = None, page: Optional[int] = None, sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "key": key,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/authorizations", clean_dict(query)

    def _addresses(
            self, borrower_id: str, priority: Optional[int] = None, sort_by: Optional[str] = None,
            per_page: Optional[int] = None, page: Optional[int] = None, sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "priority": priority,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/addresses", clean_dict(query)

    def _identities(
            self, borrower_id: str, priority: Optional[int] = None, sort_by: Optional[str] = None,
            key: Optional[str] = None, per_page: Optional[int] = None, page: Optional[int] = None,
            sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "key": key,
            "priority": priority,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/identities", clean_dict(query)

    def _metrics(
            self, borrower_id: str, sort_by: Optional[str] = None,
            key: Optional[str] = None, per_page: Optional[int] = None, page: Optional[int] = None,
            sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "key": key,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/metrics", clean_dict(query)

    def _documents(
            self, borrower_id: str, key: Optional[str] = None, sort_by: Optional[str] = None,
            per_page: Optional[int] = None, page: Optional[int] = None, sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "key": key,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/documents", clean_dict(query)

    def _points_of_contact(
            self, borrower_id: str, contact_method: Optional[str] = None, priority: Optional[int] = None,
            sort_by: Optional[str] = None, per_page: Optional[int] = None, page: Optional[int] = None,
            sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "priority": priority,
            "contact-method": contact_method,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/points-of-contact", clean_dict(query)

    def _relationships(
            self, borrower_id: str, priority: Optional[int] = None, sort_by: Optional[str] = None,
            per_page: Optional[int] = None, page: Optional[int] = None, sort_direction: Optional[str] = None,
            is_legal_representative: Optional[bool] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "priority": priority,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction,
            "is-legal-representative": is_legal_representative
        }
        return f"{self.base_url}/v1/relationships", clean_dict(query)

    def _borrower_fields(
            self, borrower_id: str, key: Optional[str] = None, sort_by: Optional[str] = None,
            per_page: Optional[int] = None, page: Optional[int] = None, sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "key": key,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/borrower-fields", clean_dict(query)

    def _packages(
            self, borrower_id: str, source_id: Optional[str] = None, sort_by: Optional[str] = None,
            per_page: Optional[int] = None, page: Optional[int] = None, sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "source-id": source_id,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/stores/packages", clean_dict(query)

    def _executions(
            self, borrower_id: str, execution_id: Optional[str] = None, workflow_id: Optional[str] = None,
            sort_by: Optional[str] = None, per_page: Optional[int] = None, page: Optional[int] = None,
            sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "billable-id": borrower_id,
            "workflow-id": workflow_id,
            "execution-id": execution_id,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/executions", clean_dict(query)

    def _alerts(
            self, borrower_id: str, alert_id: Optional[str] = None, rule_id: Optional[str] = None,
            rule_code: Optional[str] = None, level: Optional[str] = None, reference_id: Optional[str] = None,
            is_acknowledged: Optional[bool] = None, sort_by: Optional[str] = None, per_page: Optional[int] = None,
            page: Optional[int] = None, sort_direction: Optional[str] = None
    ) -> (str, dict):
        query = {
            "borrower-id": borrower_id,
            "alert-id": alert_id,
            "rule-id": rule_id,
            "rule-code": rule_code,
            "level": level,
            "reference-id": reference_id,
            "is-acknowledged": is_acknowledged,
            "sort-by": sort_by,
            "per-page": per_page,
            "page": page,
            "sort-direction": sort_direction
        }
        return f"{self.base_url}/v1/alerts", clean_dict(query)


class BorrowersAsyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401_async
    async def create(self, new_entity_data: dict):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/borrowers",
                headers=self.build_headers(),
                json=CreateBorrowerDTO.parse_obj(new_entity_data).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()["id"]

    @retry_on_401_async
    async def patch(self, resource_id: str, patch_data: dict):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.patch(
                f"/v1/borrowers/{resource_id}",
                headers=self.build_headers(),
                json=UpdateBorrowerDTO.parse_obj(patch_data).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return await self.retrieve(response.json()["id"])

    @retry_on_401_async
    async def delete(self, resource_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.delete(
                f"/v1/borrowers/{resource_id}",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def retrieve(self, resource_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/borrowers/{resource_id}",
                headers=self.build_headers(),
                timeout=120,
            )
            if response.status_code == 200:
                return BorrowerAsync(
                    base_url=self.altscore_client._borrower_central_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=BorrowerAPIDTO.parse_obj(response.json())
                )
            elif response.status_code in [404]:
                return None
            raise_for_status_improved(response)

    @retry_on_401_async
    async def find_one_by_identity(self, identity_key: str, identity_value: str):
        """
        Exact match by identity
        """
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                "/v1/identities",
                params={
                    "key": identity_key,
                    "value": identity_value,
                    "per-page": 1,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            response.raise_for_status()
            identities = response.json()
            if len(identities) == 0:
                return None

            identity = identities[0]
            if identity["value"] == identity_value:
                return await self.retrieve(identity["borrowerId"])
            return None

    @retry_on_401_async
    async def query(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None and k not in ["timeout", "per_page"]:
                query_params[convert_to_dash_case(k)] = v

        timeout = kwargs.get("timeout", 30)
        per_page = kwargs.get("per_page", 100)
        if per_page > 100:
            logger.warning("per_page is greater than 100, setting it to 100")
            per_page = 100
        query_params["per-page"] = per_page

        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/borrowers",
                headers=self.build_headers(),
                params=query_params,
                timeout=timeout
            )
            raise_for_status_improved(response)
            return [BorrowerAsync(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=BorrowerAPIDTO.parse_obj(e)
            ) for e in response.json()]

    @retry_on_401_async
    async def query_summary(self, by: Optional[Literal["self", "identity"]] = None, search: Optional[str] = None,
                            **kwargs):
        query_params = {
            "by": by,
            "search": search
        }
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v
        query_params = clean_dict(query_params)
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/borrowers-summary",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            return [BorrowerSummaryAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401_async
    async def retrieve_all(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v
        per_page = kwargs.get("per_page", 100)
        timeout = kwargs.get("timeout", 30)
        if per_page > 100:
            logger.warning("per_page is greater than 100, setting it to 100")
            per_page = 100
        query_params["per-page"] = per_page
        clean_kwargs = {k: v for k, v in query_params.items() if v is not None and v not in {"page", "per_page"}}
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/borrowers",
                params=query_params,
                headers=self.build_headers(),
                timeout=timeout
            )
            raise_for_status_improved(response)
            total_count = int(response.headers["x-total-count"])

        total_pages = (total_count // per_page) + 1
        if total_pages > 1:
            pages = list(range(1, total_pages + 1))
        else:
            pages = [1]

        resources = []
        page_chunks = [pages[i:i + 10] for i in range(0, len(pages), 10)]

        for page_chunk in page_chunks:
            tasks = [self.query(page=page, per_page=per_page, **clean_kwargs) for page in page_chunk]
            chunk_results = await asyncio.gather(*tasks)
            resources.extend(chunk_results)

        resources = [item for sublist in resources for item in sublist]
        return resources

    @retry_on_401_async
    async def summary_retrieve_all(self, **kwargs):
        query_params = {}
        kwargs_allowed = {}
        per_page = 50
        for k, v in kwargs.items():
            if k in ["by", "search", "borrower_id"]:
                logger.warning(f"Skipping {k} as it is not allowed in summary retrieve all")
                continue
            if v is not None:
                kwargs_allowed[k] = v
                query_params[convert_to_dash_case(k)] = v
        query_params["per-page"] = per_page
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/borrowers-summary",
                params=query_params,
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            total_count = int(response.headers["x-total-count"])
        total_pages = (total_count // per_page) + 1
        if total_pages > 1:
            pages = range(1, total_pages + 1)
        else:
            pages = [1]

        results = []
        page_chunks = [pages[i:i + 5] for i in range(0, len(pages), 5)]
        for page_chunk in page_chunks:
            calls = []
            for page in page_chunk:
                calls.append(self.query_summary(page=page, per_page=per_page, **kwargs_allowed))
            results += await asyncio.gather(*calls)

        results = [item for sublist in results for item in sublist]
        return results

    @retry_on_401_async
    async def commands_borrower_login(self, borrower_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/{borrower_id}/commands/login",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return BorrowerLoginAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def commands_export(self):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/borrowers/commands/export",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return BorrowerExportAPIDTO.parse_obj(response.json())


class BorrowersSyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def create(self, new_entity_data: dict):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/borrowers",
                headers=self.build_headers(),
                json=CreateBorrowerDTO.parse_obj(new_entity_data).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return response.json()["id"]

    @retry_on_401
    def patch(self, resource_id: str, patch_data: dict):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.patch(
                f"/v1/borrowers/{resource_id}",
                headers=self.build_headers(),
                json=UpdateBorrowerDTO.parse_obj(patch_data).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            return self.retrieve(response.json()["id"])

    @retry_on_401
    def delete(self, resource_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.delete(
                f"/v1/borrowers/{resource_id}",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def retrieve(self, resource_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/borrowers/{resource_id}",
                headers=self.build_headers(),
                timeout=120
            )
            if response.status_code == 200:
                return BorrowerSync(
                    base_url=self.altscore_client._borrower_central_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=BorrowerAPIDTO.parse_obj(response.json())
                )
            elif response.status_code in [404]:
                return None
            raise_for_status_improved(response)

    @retry_on_401
    def find_one_by_identity(self, identity_key: str, identity_value: str):
        """
        Exact match by identity
        """
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                "/v1/identities",
                params={
                    "key": identity_key,
                    "value": identity_value,
                    "per-page": 1,
                    "page": 1
                },
                headers=self.build_headers(),
                timeout=120,
            )
            response.raise_for_status()
            identities = response.json()
            if len(identities) == 0:
                return None

            identity = identities[0]
            if identity["value"] == identity_value:
                return self.retrieve(identity["borrowerId"])
            return None

    @retry_on_401
    def query(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/borrowers",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            return [BorrowerSync(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=BorrowerAPIDTO.parse_obj(e)
            ) for e in response.json()]

    @retry_on_401
    def query_summary(self, by: Optional[Literal["self", "identity"]] = None, search: Optional[str] = None,
                      **kwargs):
        query_params = {
            "by": by,
            "search": search
        }
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v
        query_params = clean_dict(query_params)
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/borrowers-summary",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            return [BorrowerSummaryAPIDTO.parse_obj(e) for e in response.json()]

    @retry_on_401
    def retrieve_all(self, **kwargs):
        query_params = {}
        per_page = 10
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v
        query_params["per-page"] = per_page
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/borrowers",
                params=query_params,
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            total_count = int(response.headers["x-total-count"])
        resources = []
        # TODO: this is not optimal, we should use asyncio.gather and a batch size
        total_pages = (total_count // per_page) + 1
        if total_pages > 1:
            pages = range(1, total_pages + 1)
        else:
            pages = [1]
        for page in pages:
            r = self.query(page=page, per_page=per_page, **kwargs)
            resources.append(r)
        resources = [item for sublist in resources for item in sublist]
        return resources

    @retry_on_401
    def summary_retrieve_all(self, **kwargs):
        query_params = {}
        kwargs_allowed = {}
        per_page = 50
        for k, v in kwargs.items():
            if k in ["by", "search", "borrower_id"]:
                logger.warning(f"Skipping {k} as it is not allowed in summary retrieve all")
                continue
            if v is not None:
                kwargs_allowed[k] = v
                query_params[convert_to_dash_case(k)] = v
        query_params["per-page"] = per_page
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/borrowers-summary",
                params=query_params,
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            total_count = int(response.headers["x-total-count"])
        resources = []
        # TODO: this is not optimal, we should use asyncio.gather and a batch size
        total_pages = (total_count // per_page) + 1
        if total_pages > 1:
            pages = range(1, total_pages + 1)
        else:
            pages = [1]
        for page in pages:
            r = self.query_summary(page=page, per_page=per_page, **kwargs_allowed)
            resources.append(r)
        resources = [item for sublist in resources for item in sublist]
        return resources

    @retry_on_401
    def commands_borrower_login(self, borrower_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/{borrower_id}/commands/login",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return BorrowerLoginAPIDTO.parse_obj(response.json())

    @retry_on_401
    def commands_export(self):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/borrowers/commands/export",
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)
            return BorrowerExportAPIDTO.parse_obj(response.json())


class BorrowerAsync(BorrowerBase):
    data: BorrowerAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: BorrowerAPIDTO):
        super().__init__(base_url)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401_async
    async def set_label(self, label: str):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.patch(
                f"{self.base_url}/v1/borrowers/{self.data.id}",
                headers=self._header_builder(),
                json={
                    "label": label,
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def get_stage(self) -> StageAsync:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/stage",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return StageAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401_async
    async def get_current_step(self) -> StepAsync:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/steps/current",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return StepAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401_async
    async def set_current_step(self, key: str):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/steps/current",
                json={
                    "key": key
                },
                headers=self._header_builder()
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def set_stage(self, stage: str, reference_id: Optional[str] = None):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/stage",
                headers=self._header_builder(),
                json={
                    "value": stage,
                    "referenceId": reference_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def get_risk_rating(self) -> RiskRatingAsync:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/risk-rating",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return RiskRatingAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401_async
    async def get_repayment_risk_rating(self) -> RepaymentRiskRatingAsync:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/repayment-risk-rating",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return RepaymentRiskRatingAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401_async
    async def set_risk_rating(self, risk_rating: str, reference_id: Optional[str] = None, updated_at: Optional[dt.datetime] = None):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/risk-rating",
                headers=self._header_builder(),
                json=SetRiskRatingAPIDTO.parse_obj({
                    "value": risk_rating,
                    "reference_id": reference_id,
                    "updated_at": updated_at
                }).dict(by_alias=True)
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def set_repayment_risk_rating(self, risk_rating: str, reference_id: Optional[str] = None):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/repayment-risk-rating",
                headers=self._header_builder(),
                json={
                    "value": risk_rating,
                    "referenceId": reference_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def set_flag(self, flag: str, reference_id: Optional[str] = None):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/flag",
                headers=self._header_builder(),
                json={
                    "value": flag,
                    "referenceId": reference_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def get_documents(self, **kwargs) -> List[DocumentAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._documents(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [DocumentAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=document_data
            ) for document_data in data]

    @retry_on_401_async
    async def get_identity_by_key(self, key: str) -> Optional[IdentityAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._identities(self.data.id, key=key)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return IdentityAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )

    @retry_on_401_async
    async def get_metric_by_key(self, key: str) -> Optional[MetricAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._metrics(self.data.id, key=key)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return MetricAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )

    @retry_on_401_async
    async def get_borrower_field_by_key(self, key: str) -> Optional[BorrowerFieldAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._borrower_fields(self.data.id, key=key)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return BorrowerFieldAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )

    @retry_on_401_async
    async def get_document_by_key(self, key: str) -> Optional[DocumentAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._documents(self.data.id, key=key)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return DocumentAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )


    @retry_on_401_async
    async def get_identities(self, **kwargs) -> List[IdentityAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._identities(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [IdentityAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=identity_data
            ) for identity_data in data]

    @retry_on_401_async
    async def get_addresses(self, **kwargs) -> List[AddressAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._addresses(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [AddressAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=address_data
            ) for address_data in data]

    @retry_on_401_async
    async def get_points_of_contact(self, **kwargs) -> List[PointOfContactAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._points_of_contact(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [PointOfContactAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=point_of_contact_data
            ) for point_of_contact_data in data]

    @retry_on_401_async
    async def get_borrower_fields(self, **kwargs) -> List[BorrowerFieldAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._borrower_fields(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [BorrowerFieldAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=borrower_field_data
            ) for borrower_field_data in data]

    @retry_on_401_async
    async def get_metrics(self, **kwargs) -> List[MetricAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._metrics(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [MetricAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=borrower_field_data
            ) for borrower_field_data in data]

    @retry_on_401_async
    async def get_authorizations(self, **kwargs) -> List[AuthorizationAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._authorizations(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [AuthorizationAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=authorization_data
            ) for authorization_data in data]

    @retry_on_401_async
    async def get_relationships(self, **kwargs) -> List[RelationshipAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._relationships(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [RelationshipAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=relationship_data
            ) for relationship_data in data]

    @retry_on_401_async
    async def get_executions(self, **kwargs) -> List[ExecutionAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._executions(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [ExecutionAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=execution_data
            ) for execution_data in data]

    @retry_on_401_async
    async def get_packages(self, **kwargs) -> List[PackageAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._packages(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [PackageAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=package_data
            ) for package_data in data]

    @retry_on_401_async
    async def get_alerts(self, **kwargs) -> List[AlertAsync]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            url, query = self._alerts(self.data.id, **kwargs)
            response = await client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            alerts = [AlertAsync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=alert_data
            ) for alert_data in data]
            return alerts

    @retry_on_401_async
    async def associate_cms_client_id(self, cms_client_id: str):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                f"/v1/borrowers/{self.data.id}/cms-client-ids/{cms_client_id}",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def put_cms_client_ids(self, cms_client_ids: List[str]):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"/v1/borrowers/{self.data.id}/cms-client-ids",
                headers=self._header_builder(),
                json={
                    "cmsClientIds": cms_client_ids
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def get_main_address(self) -> Optional[AddressAsync]:
        addresses = await self.get_addresses(sort_by="priority", per_page=1)
        if len(addresses) == 0:
            return None
        else:
            return addresses[0]

    @retry_on_401_async
    async def get_main_point_of_contact(self, contact_method: str) -> Optional[PointOfContactAsync]:
        points_of_contact = await self.get_points_of_contact(
            contact_method=contact_method, sort_by="priority", per_page=1
        )
        if len(points_of_contact) == 0:
            return None
        else:
            return points_of_contact[0]

    @retry_on_401_async
    async def map_identities_and_fields_onto_dict(self, mapping_dict: dict):
        identities_to_query = {k: 1 for k in mapping_dict.values() if k.startswith("identity.")}
        malformed_identities = [k for k in identities_to_query if len(k.split(".")[-1]) == 0]
        borrower_fields_to_query = {k: 1 for k in mapping_dict.values() if k.startswith("borrower_field.")}
        malformed_fields = [k for k in borrower_fields_to_query if len(k.split(".")[-1]) == 0]
        if len(malformed_fields + malformed_identities) > 0:
            raise ValueError(f"Found malformed keys: {malformed_fields + malformed_identities}")
        calls = []
        for identity_key in identities_to_query:
            calls.append(
                self.get_identity_by_key(identity_key.replace("identity.", ""))
            )
        for field_key in borrower_fields_to_query:
            calls.append(
                self.get_borrower_field_by_key(field_key.replace("borrower_field.", ""))
            )
        calls = await asyncio.gather(*calls)
        value_maps = {}
        for element in calls:
            if element is None:
                pass
            elif element.resource == "identities":
                value_maps[f"identity.{element.data.key}"] = element.data.value
            elif element.resource == "borrower-fields":
                value_maps[f"borrower_field.{element.data.key}"] = element.data.value
        mapped_dict = {}
        for k, v_map in mapping_dict.items():
            mapped_dict[k] = value_maps.get(v_map)
        return mapped_dict

    @retry_on_401_async
    async def send_sms(self, message: str, point_of_contact_id: Optional[str] = None, skip_verification_check: Optional[bool] = False):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                f"{self.base_url}/v1/borrowers/{self.data.id}/communications/sms",
                headers=self._header_builder(),
                json={
                    "message": message,
                    "pointOfContactId": point_of_contact_id,
                    "skipVerificationCheck": skip_verification_check
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def set_external_id(self, external_id: str):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/external-id",
                headers=self._header_builder(),
                json={
                    "externalId": external_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def set_category_value(self, category_key: str, category_value_id: str, inherit_value = False):
        resource = self.resource
        if inherit_value:
            resource += "_ds"
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                f"{self.base_url}/v1/category/commands/categorize-entity",
                headers=self._header_builder(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": resource,
                    "entityId": self.data.id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def delete_category_value(self, category_key: str, category_value_id: str):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                f"{self.base_url}/v1/category/commands/delete-entity-category",
                headers=self._header_builder(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": self.resource,
                    "entityId": self.data.id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def get_entity_categories(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                f"{self.base_url}/v1/category/queries/entity/{self.resource}/{self.data.id}",
                headers=self._header_builder(),
            )
            raise_for_status_improved(response)
            return [
                EntityCategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class BorrowerSync(BorrowerBase):
    data: BorrowerAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: BorrowerAPIDTO):
        super().__init__(base_url)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401
    def set_label(self, label: str):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.patch(
                f"{self.base_url}/v1/borrowers/{self.data.id}",
                headers=self._header_builder(),
                json={
                    "label": label,
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def get_stage(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/stage",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return StageSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401
    def get_current_step(self) -> StepSync:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/steps/current",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return StepSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401
    def set_current_step(self, key: str):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/steps/current",
                json={
                    "key": key
                },
                headers=self._header_builder()
            )
            raise_for_status_improved(response)

    @retry_on_401
    def set_stage(self, stage: str, reference_id: Optional[str] = None):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/stage",
                headers=self._header_builder(),
                json={
                    "value": stage,
                    "referenceId": reference_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def get_risk_rating(self) -> RiskRatingSync:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/risk-rating",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return RiskRatingSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401
    def get_repayment_risk_rating(self) -> RepaymentRiskRatingSync:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"{self.base_url}/v1/borrowers/{self.data.id}/repayment-risk-rating",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return RepaymentRiskRatingSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=response.json()
            )

    @retry_on_401
    def set_risk_rating(self, risk_rating: str, reference_id: Optional[str] = None, updated_at: Optional[dt.datetime] = None):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/risk-rating",
                headers=self._header_builder(),
                json=SetRiskRatingAPIDTO.parse_obj({
                    "value": risk_rating,
                    "reference_id": reference_id,
                    "updated_at": updated_at
                }).dict(by_alias=True)
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def set_repayment_risk_rating(self, risk_rating: str, reference_id: Optional[str] = None):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/repayment-risk-rating",
                headers=self._header_builder(),
                json={
                    "value": risk_rating,
                    "referenceId": reference_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def set_flag(self, flag: str, reference_id: Optional[str] = None):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/flag",
                headers=self._header_builder(),
                json={
                    "value": flag,
                    "referenceId": reference_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def get_documents(self, **kwargs) -> List[DocumentSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._documents(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [DocumentSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=document_data
            ) for document_data in data]

    @retry_on_401
    def get_identity_by_key(self, key: str) -> Optional[IdentitySync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._identities(self.data.id, key=key)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return IdentitySync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )

    @retry_on_401
    def get_metric_by_key(self, key: str) -> Optional[MetricSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._metrics(self.data.id, key=key)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return MetricSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )

    @retry_on_401
    def get_borrower_field_by_key(self, key: str) -> Optional[BorrowerFieldSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._borrower_fields(self.data.id, key=key)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return BorrowerFieldSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )

    @retry_on_401
    def get_document_by_key(self, key) -> Optional[DocumentSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._documents(self.data.id, key=key)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            if len(data) == 0:
                return None
            return DocumentSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=data[0]
            )


    @retry_on_401
    def get_identities(self, **kwargs) -> List[IdentitySync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._identities(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [IdentitySync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=identity_data
            ) for identity_data in data]

    @retry_on_401
    def get_addresses(self, **kwargs) -> List[AddressSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._addresses(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [AddressSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=address_data
            ) for address_data in data]

    @retry_on_401
    def get_points_of_contact(self, **kwargs) -> List[PointOfContactSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._points_of_contact(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [PointOfContactSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=point_of_contact_data
            ) for point_of_contact_data in data]

    @retry_on_401
    def get_borrower_fields(self, **kwargs) -> List[BorrowerFieldSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._borrower_fields(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [BorrowerFieldSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=borrower_field_data
            ) for borrower_field_data in data]

    @retry_on_401
    def get_metrics(self, **kwargs) -> List[MetricSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._metrics(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [MetricSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=borrower_field_data
            ) for borrower_field_data in data]

    @retry_on_401
    def get_authorizations(self, **kwargs) -> List[AuthorizationSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._authorizations(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [AuthorizationSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=authorization_data
            ) for authorization_data in data]

    @retry_on_401
    def get_relationships(self, **kwargs) -> List[RelationshipSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._relationships(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [RelationshipSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=relationship_data
            ) for relationship_data in data]

    @retry_on_401
    def get_executions(self, **kwargs) -> List[ExecutionSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._executions(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [ExecutionSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=execution_data
            ) for execution_data in data]

    @retry_on_401
    def get_packages(self, **kwargs) -> List[PackageSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._packages(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            return [PackageSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=package_data
            ) for package_data in data]

    @retry_on_401
    def get_alerts(self, **kwargs) -> List[AlertSync]:
        with httpx.Client(base_url=self.base_url) as client:
            url, query = self._alerts(self.data.id, **kwargs)
            response = client.get(
                url,
                headers=self._header_builder(),
                params=query
            )
            data = response.json()
            alerts = [AlertSync(
                base_url=self.base_url,
                header_builder=self._header_builder,
                renew_token=self.renew_token,
                data=alert_data
            ) for alert_data in data]
            return alerts

    @retry_on_401
    def associate_cms_client_id(self, cms_client_id: str):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                f"/v1/borrowers/{self.data.id}/cms-client-ids/{cms_client_id}",
                headers=self._header_builder()
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def put_cms_client_ids(self, cms_client_ids: List[str]):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"/v1/borrowers/{self.data.id}/cms-client-ids",
                headers=self._header_builder(),
                json={
                    "cmsClientIds": cms_client_ids
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def get_main_address(self) -> Optional[AddressSync]:
        addresses = self.get_addresses(sort_by="priority", per_page=1)
        if len(addresses) == 0:
            return None
        else:
            return addresses[0]

    @retry_on_401
    def get_main_point_of_contact(self, contact_method: str) -> Optional[PointOfContactSync]:
        points_of_contact = self.get_points_of_contact(
            contact_method=contact_method, sort_by="priority", per_page=1
        )
        if len(points_of_contact) == 0:
            return None
        else:
            return points_of_contact[0]

    @retry_on_401
    def map_identities_and_fields_onto_dict(self, mapping_dict: dict):
        identities_to_query = {k: 1 for k in mapping_dict.values() if k.startswith("identity.")}
        malformed_identities = [k for k in identities_to_query if len(k.split(".")[-1]) == 0]
        borrower_fields_to_query = {k: 1 for k in mapping_dict.values() if k.startswith("borrower_field.")}
        malformed_fields = [k for k in borrower_fields_to_query if len(k.split(".")[-1]) == 0]
        if len(malformed_fields + malformed_identities) > 0:
            raise ValueError(f"Found malformed keys: {malformed_fields + malformed_identities}")
        calls = []
        for identity_key in identities_to_query:
            calls.append(
                self.get_identity_by_key(identity_key.replace("identity.", ""))
            )
        for field_key in borrower_fields_to_query:
            calls.append(
                self.get_borrower_field_by_key(field_key.replace("borrower_field.", ""))
            )
        value_maps = {}
        for element in calls:
            if element is None:
                pass
            elif element.resource == "identities":
                value_maps[f"identity.{element.data.key}"] = element.data.value
            elif element.resource == "borrower-fields":
                value_maps[f"borrower_field.{element.data.key}"] = element.data.value
        mapped_dict = {}
        for k, v_map in mapping_dict.items():
            mapped_dict[k] = value_maps.get(v_map)
        return mapped_dict

    @retry_on_401
    def send_sms(self, message: str, point_of_contact_id: Optional[str] = None, skip_verification_check: Optional[bool] = False ):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                f"{self.base_url}/v1/borrowers/{self.data.id}/communications/sms",
                headers=self._header_builder(),
                json={
                    "message": message,
                    "pointOfContactId": point_of_contact_id,
                    "skipVerificationCheck": skip_verification_check
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def set_external_id(self, external_id: str):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                f"{self.base_url}/v1/borrowers/{self.data.id}/external-id",
                headers=self._header_builder(),
                json={
                    "externalId": external_id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def set_category_value(self, category_key: str, category_value_id: str, inherit_value = False):
        resource = self.resource
        if inherit_value:
            resource += "_ds"
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                f"{self.base_url}/v1/category/commands/categorize-entity",
                headers=self._header_builder(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": resource,
                    "entityId": self.data.id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def delete_category_value(self, category_key: str, category_value_id: str):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                f"{self.base_url}/v1/category/commands/delete-entity-category",
                headers=self._header_builder(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": self.resource,
                    "entityId": self.data.id
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def get_entity_categories(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                f"{self.base_url}/v1/category/queries/entity/{self.resource}/{self.data.id}",
                headers=self._header_builder(),
            )
            raise_for_status_improved(response)
            return [
                EntityCategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"
