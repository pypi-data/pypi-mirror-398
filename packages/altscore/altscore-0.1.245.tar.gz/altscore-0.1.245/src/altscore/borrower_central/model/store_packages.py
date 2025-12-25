import os
from typing import Optional, List, Dict, Any
import httpx
from altscore.altdata.model.data_request import RequestResult
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from pydantic import BaseModel, Field
import datetime as dt
from dateutil.parser import parse as parse_date
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async


class PackageAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: Optional[str] = Field(alias="borrowerId")
    deal_id: Optional[str] = Field(alias="dealId", default = None)
    source_id: Optional[str] = Field(alias="sourceId", default=None)
    alias: Optional[str] = Field(alias="alias", default=None)
    workflow_id: Optional[str] = Field(alias="workflowId", default=None)
    label: Optional[str] = Field(alias="label")
    content_type: Optional[str] = Field(alias="contentType", default=None)
    tags: List[str] = Field(alias="tags")
    created_at: str = Field(alias="createdAt")
    ttl: Optional[str] = Field(alias="ttl", default=None)
    has_attachments: bool = Field(alias="hasAttachments")
    forced_stale: Optional[bool] = Field(alias="forcedStale", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True



class CreatePackageDTO(BaseModel):
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    source_id: Optional[str] = Field(alias="sourceId", default=None)
    workflow_id: Optional[str] = Field(alias="workflowId", default=None)
    alias: Optional[str] = Field(alias="alias", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    tags: List[str] = Field(alias="tags", default=[])
    content: Any = Field(alias="content")
    content_type: Optional[str] = Field(alias="contentType", default=None)
    ttl_minutes: Optional[int] = Field(alias="ttlMinutes", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class GenerateAttachmentUploadSignedURL(BaseModel):
    file_name: str = Field(alias="fileName")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CommitAttachmentSignedURUpload(BaseModel):
    package_id: str = Field(alias="packageId")
    attachment_file_name: str = Field(alias="attachmentFileName")
    metadata: Optional[dict] = Field(alias="metadata", default=None)
    label: Optional[str] = Field(alias="label", default=None)


    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UploadSignedURLAPIDTO(BaseModel):
    signed_url: str = Field(alias="signedUrl")
    file_name: str = Field(alias="fileName")
    content_type: str = Field(alias="contentType")
    attachment_id: str = Field(alias="attachmentId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class PackageSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/stores/packages", header_builder, renew_token, PackageAPIDTO.parse_obj(data))


    @retry_on_401
    def upload_attachment_with_signed_url(self, file_path: str,  label: str = None, metadata: Dict = None):
        file_name = file_path.split("/")[-1]

        with httpx.Client(base_url=self.base_url) as client:
            headers = self._header_builder()
            response = client.post(
                f"/v1/stores/packages/commands/attachments/generate-upload-signed-url",
                json=GenerateAttachmentUploadSignedURL(file_name=file_name).dict(),
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)
            signed_url = UploadSignedURLAPIDTO.parse_obj(response.json())

        with open(file_path, "rb") as f:
            content = f.read()

            with httpx.Client() as client:
                response = client.put(
                    url=signed_url.signed_url,
                    headers={
                        "Content-Type": signed_url.content_type
                    },
                    content=content,
                    timeout=900
                )

                raise_for_status_improved(response)

        with httpx.Client(base_url=self.base_url) as client:
            headers = self._header_builder()
            response = client.post(
                f"/v1/stores/packages/commands/attachments/commit-signed-url-upload",
                json=CommitAttachmentSignedURUpload(
                    package_id=self.data.id, attachment_file_name=signed_url.file_name, metadata=metadata, label=label
                ).dict(),
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)

    def upload_package_attachment(self, file_path: str, label: str = None, metadata: Dict = None):
        max_cloud_run_allowed_size = 32 * 1024 * 1024

        file_size = os.path.getsize(file_path)

        if file_size < max_cloud_run_allowed_size:
            self.upload_attachment(
                file_path=file_path,
                label=label,
                metadata=metadata
            )
        else:
            self.upload_attachment_with_signed_url(
                file_path = file_path,
                label = label,
                metadata = metadata
            )


class PackageAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "/stores/packages", header_builder, renew_token, PackageAPIDTO.parse_obj(data))


    @retry_on_401_async
    async def upload_attachment_with_signed_url(self, file_path: str, label: str = None, metadata: Dict = None):
        file_name = file_path.split("/")[-1]

        async with httpx.AsyncClient(base_url=self.base_url) as client:
            headers = self._header_builder()
            response = await client.post(
                f"/v1/stores/packages/commands/attachments/generate-upload-signed-url",
                json=GenerateAttachmentUploadSignedURL(file_name=file_name).dict(),
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)

            signed_url = UploadSignedURLAPIDTO.parse_obj(response.json())

        with open(file_path, "rb") as f:
            content = f.read()

        with httpx.Client() as client:
            response = client.put(
                url=signed_url.signed_url,
                headers={
                    "Content-Type": signed_url.content_type
                },
                content=content,
                timeout=900
            )

            raise_for_status_improved(response)

        async with httpx.AsyncClient(base_url=self.base_url) as client:
            headers = self._header_builder()
            response = await client.post(
                f"/v1/stores/packages/commands/attachments/commit-signed-url-upload",
                json=CommitAttachmentSignedURUpload(
                    package_id=self.data.id, attachment_file_name=signed_url.file_name, metadata=metadata, label=label
                ).dict(),
                headers=headers,
                timeout=900
            )
            raise_for_status_improved(response)

    async def upload_package_attachment(self, file_path: str, label: str = None, metadata: Dict = None):
        max_cloud_run_allowed_size = 32 * 1024 * 1024

        file_size = os.path.getsize(file_path)

        if file_size < max_cloud_run_allowed_size:
            await self.upload_attachment(
                file_path=file_path,
                label=label,
                metadata=metadata
            )
        else:
            await self.upload_attachment_with_signed_url(
                file_path = file_path,
                label = label,
                metadata = metadata
            )


class PackagesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=PackageSync,
                         retrieve_data_model=PackageAPIDTO,
                         create_data_model=CreatePackageDTO,
                         update_data_model=None,
                         resource="stores/packages")

    def retrieve_package_by_alias(self, alias: str, data_age: Optional[dt.timedelta] = None) -> Optional[PackageSync]:
        packages = self.query(alias=alias, sort_by="createdAt", sort_order="desc")
        if len(packages) > 0:
            package = packages[0]
            if data_age is None:
                return package
            else:
                if parse_date(package.created_at) + data_age > dt.datetime.utcnow():
                    return package
        return None

    def retrieve_source_package(
            self, source_id: str, borrower_id: Optional[str] = None, data_age: Optional[dt.timedelta] = None,
            package_alias: Optional[str] = None
    ) -> Optional[PackageSync]:
        if borrower_id:
            packages = self.query(
                borrower_id=borrower_id,
                source_id=source_id,
                alias=package_alias,
                sort_by="createdAt",
                sort_order="desc"
            )
        else:
            packages = self.query(
                source_id=source_id,
                alias=package_alias,
                sort_by="createdAt",
                sort_order="desc"
            )
        if len(packages) > 0:
            package = packages[0]
            if data_age is None:
                return package
            else:
                if parse_date(package.created_at) + data_age > dt.datetime.utcnow():
                    return package
        return None

    def retrieve_workflow_package(
            self, workflow_id: str, alias: str, data_age: Optional[dt.timedelta] = None
    ) -> Optional[PackageSync]:
        packages = self.query(workflow_id=workflow_id, alias=alias, sort_by="createdAt", sort_order="desc")
        if len(packages) > 0:
            package = packages[0]
            if data_age is None:
                return package
            else:
                if parse_date(package.created_at) + data_age > dt.datetime.utcnow():
                    return package
        return None

    def force_stale(self, package_id: Optional[str] = None, borrower_id: Optional[str] = None, deal_id: Optional[str] = None,
                    workflow_id: Optional[str] = None, alias: Optional[str] = None):
        if package_id is None and borrower_id is None and deal_id is None and workflow_id is None and alias is None:
            raise ValueError("At least one of package_id, borrower_id, deal_id, workflow_id or alias must be provided")
        body = {
            "packageId": package_id,
            "borrowerId": borrower_id,
            "dealId": deal_id,
            "workflowId": workflow_id,
            "alias": alias,
            "forcedStale": True
        }
        body = {k: v for k, v in body.items() if v is not None}
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            client.put(
                "/stores/packages/stale",
                json=body,
                headers=self.build_headers()
            )

    def create_from_altdata_request_result(
            self, borrower_id: str, source_id: str, altdata_request_result: RequestResult,
            attachments: Optional[List[Dict[str, Any]]] = None,
            content_type: str = "json", package_alias: Optional[str] = None
    ):
        package = altdata_request_result.to_package(source_id)
        bc_source_id = "AD_{}_{}".format(source_id, package["version"])
        package_data = {
            "borrower_id": borrower_id,
            "source_id": bc_source_id,
            "content": package,
            "content_type": content_type,
            "alias": package_alias
        }
        created_package_id = self.create(package_data)
        if attachments is not None:
            package_obj: PackageSync = self.retrieve(created_package_id)
            if package_obj is not None:
                for attachment in attachments:
                    package_obj.post_attachment(
                        attachment
                    )
        return created_package_id

    def create_all_from_altdata_request_result(
            self, borrower_id: str, altdata_request_result: RequestResult,
    ) -> Dict[str, str]:
        packages = {}
        for source_call_summary in altdata_request_result.call_summary:
            if source_call_summary.is_success:
                package_id = self.create_from_altdata_request_result(borrower_id=borrower_id,
                                                                     source_id=source_call_summary.source_id,
                                                                     altdata_request_result=altdata_request_result)
                packages[f"{source_call_summary.source_id}_{source_call_summary.version}"] = package_id
        return packages


class PackagesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=PackageAsync,
                         retrieve_data_model=PackageAPIDTO,
                         create_data_model=CreatePackageDTO,
                         update_data_model=None,
                         resource="/stores/packages")

    async def retrieve_package_by_alias(
            self, alias: str, data_age: Optional[dt.timedelta] = None
    ) -> Optional[PackageAsync]:
        packages = await self.query(alias=alias, sort_by="createdAt", sort_order="desc")
        if len(packages) > 0:
            package = packages[0]
            if data_age is None:
                return package
            else:
                if parse_date(package.created_at) + data_age > dt.datetime.utcnow():
                    return package
        return None

    async def retrieve_source_package(
            self, source_id: str, borrower_id: Optional[str] = None, data_age: Optional[dt.timedelta] = None,
            package_alias: Optional[str] = None
    ) -> Optional[PackageAsync]:
        if borrower_id:
            packages = await self.query(borrower_id=borrower_id,
                                        source_id=source_id,
                                        sort_by="createdAt",
                                        sort_order="desc",
                                        alias=package_alias
                                        )
        else:
            packages = await self.query(
                source_id=source_id,
                sort_by="createdAt",
                sort_order="desc",
                alias=package_alias
            )
        if len(packages) > 0:
            package = packages[0]
            if data_age is None:
                return package
            else:
                if parse_date(package.created_at) + data_age > dt.datetime.utcnow():
                    return package
        return None

    async def retrieve_workflow_package(
            self, workflow_id: str, alias: str, data_age: Optional[dt.timedelta] = None
    ) -> Optional[PackageAsync]:
        packages = await self.query(workflow_id=workflow_id, alias=alias, sort_by="createdAt", sort_order="desc")
        if len(packages) > 0:
            package = packages[0]
            if data_age is None:
                return package
            else:
                if parse_date(package.created_at) + data_age > dt.datetime.utcnow():
                    return package
        return None

    async def create_from_altdata_request_result(
            self, borrower_id: str, source_id: str, altdata_request_result: RequestResult,
            attachments: Optional[List[Dict[str, Any]]] = None, content_type: str = "json",
            package_alias: Optional[str] = None
    ):
        package = altdata_request_result.to_package(source_id)
        bc_source_id = "AD_{}_{}".format(source_id, package["version"])
        package_data = {
            "borrower_id": borrower_id,
            "source_id": bc_source_id,
            "content": package,
            "content_type": content_type,
            "alias": package_alias
        }
        created_package_id = await self.create(package_data)
        if attachments is not None:
            package_obj: PackageSync = await self.retrieve(created_package_id)
            if package_obj is not None:
                for attachment in attachments:
                    await package_obj.post_attachment(
                        attachment
                    )
        return created_package_id

    async def create_all_from_altdata_request_result(
            self, borrower_id: str, altdata_request_result: RequestResult,
    ) -> Dict[str, str]:
        packages = {}
        for source_call_summary in altdata_request_result.call_summary:
            if source_call_summary.is_success:
                package_id = await self.create_from_altdata_request_result(
                    borrower_id=borrower_id,
                    source_id=source_call_summary.source_id,
                    altdata_request_result=altdata_request_result)
                packages[f"{source_call_summary.source_id}_{source_call_summary.version}"] = package_id
        return packages
