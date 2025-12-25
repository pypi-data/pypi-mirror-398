import os.path

import httpx
import json
from altscore.borrower_central.helpers import build_headers
from altscore.borrower_central.model.attachments import AttachmentAPIDTO, AttachmentInput
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from typing import Dict
from altscore.borrower_central.utils import convert_to_dash_case
import mimetypes
import aiofiles
import urllib.parse
from loguru import logger
import asyncio

class GenericBase:

    def __init__(self, base_url, resource: str):
        self.base_url = base_url.strip("/")
        self.resource = resource.strip("/")

    def _get_attachments(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/attachments"

    def _delete_attachment(self, resource_id, attachment_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/attachments/{attachment_id}"

    def _get_signatures(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/signatures"

    def _get_content(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/content"

    def _get_output(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}/output"

    def _query(self, resource_id):
        return f"{self.base_url}/v1/{self.resource}/{resource_id}"


class GenericSyncResource(GenericBase):

    def __init__(self, base_url, resource, header_builder, renew_token, data):
        super().__init__(base_url, resource)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data
        self.attachments = None
        self.signatures = None
        self.content = None

    @property
    def created_at(self):
        return self.data.created_at

    @retry_on_401
    def get_attachments(self):
        if self.data.has_attachments:
            with httpx.Client() as client:
                response = client.get(
                    self._get_attachments(self.data.id),
                    headers=self._header_builder(),
                    timeout=300
                )
                raise_for_status_improved(response)
                self.attachments = [AttachmentAPIDTO.parse_obj(e) for e in response.json()]
        return self.attachments

    @retry_on_401
    def post_attachment(self, attachment: Dict):
        with httpx.Client() as client:
            response = client.post(
                self._get_attachments(self.data.id),
                headers=self._header_builder(),
                timeout=300,
                json=AttachmentInput.parse_obj(attachment).dict(by_alias=True, exclude_none=True)
            )
            raise_for_status_improved(response)

    @retry_on_401
    def upload_attachment(self, file_path: str, label: str = None, metadata: Dict = None):
        file_name = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        upload_url = urllib.parse.urljoin(self._get_attachments(self.data.id), "attachments/upload")
        data = {}
        if label:
            data["label"] = label
        if metadata:
            data["metadata"] = metadata
        with open(file_path, 'rb') as file:
            with httpx.Client() as client:
                response = client.post(
                    url=upload_url,
                    data=data if isinstance(data,dict) else None,
                    files={'file': (file_name, file, content_type)},
                    headers=self._header_builder(),
                    timeout=300,
                )
                raise_for_status_improved(response)

    @retry_on_401
    def delete_attachment(self, attachment_id):
        with httpx.Client() as client:
            response = client.delete(
                self._delete_attachment(self.data.id, attachment_id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)

    @retry_on_401
    def get_content(self):
        if self.resource in ["stores/packages"]:
            with httpx.Client() as client:
                response = client.get(
                    self._get_content(self.data.id),
                    headers=self._header_builder(),
                    timeout=300
                )
                raise_for_status_improved(response)
                self.content = response.text

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class GenericAsyncResource(GenericBase):

    def __init__(self, base_url, resource, header_builder, renew_token, data):
        super().__init__(base_url, resource)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data
        self.attachments = None
        self.signatures = None
        self.content = None

    @property
    def created_at(self):
        return self.data.created_at

    @retry_on_401_async
    async def get_attachments(self):
        if self.data.has_attachments:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._get_attachments(self.data.id),
                    headers=self._header_builder(),
                    timeout=300
                )
                raise_for_status_improved(response)
                self.attachments = [AttachmentAPIDTO.parse_obj(e) for e in response.json()]
        return self.attachments

    @retry_on_401_async
    async def post_attachment(self, attachment: Dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_attachments(self.data.id),
                headers=self._header_builder(),
                timeout=300,
                json=AttachmentInput.parse_obj(attachment).dict(by_alias=True, exclude_none=True)
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def upload_attachment(self, file_path: str, label: str = None, metadata: Dict = None):
        file_name = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        upload_url = urllib.parse.urljoin(self._get_attachments(self.data.id), "attachments/upload")
        data = {}
        if label:
            data["label"] = label
        if metadata:
            data["metadata"] = metadata

        async with aiofiles.open(file_path, 'rb') as file:
            file_content = await file.read()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=upload_url,
                    data=data,
                    files={'file': (file_name, file_content, content_type)},
                    headers=self._header_builder(),
                    timeout=300,
                )
                raise_for_status_improved(response)

    @retry_on_401_async
    async def delete_attachment(self, attachment_id):
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                self._delete_attachment(self.data.id, attachment_id),
                headers=self._header_builder(),
                timeout=300
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def get_content(self):
        if self.resource in ["stores/packages"]:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._get_content(self.data.id),
                    headers=self._header_builder(),
                    timeout=300
                )
                raise_for_status_improved(response)
                self.content = response.text

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class GenericSyncModule:

    def __init__(self, altscore_client, sync_resource, retrieve_data_model, create_data_model,
                 update_data_model, resource: str):
        self.altscore_client = altscore_client
        self.sync_resource = sync_resource
        self.retrieve_data_model = retrieve_data_model
        self.create_data_model = create_data_model
        self.update_data_model = update_data_model
        self.resource = resource.strip("/")

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def retrieve(self, resource_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return self.sync_resource(
                    base_url=self.altscore_client._borrower_central_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=self.retrieve_data_model.parse_obj(response.json())
                )
            elif response.status_code in [404]:
                return None

            raise_for_status_improved(response)

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
                f"/v1/{self.resource}",
                params=query_params,
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            total_count = int(response.headers["x-total-count"])
        resources = []
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
    def create(self, new_entity_data: Dict, update_if_exists: bool = False) -> str:
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            if response.status_code == 409 and update_if_exists:
                data = response.json()
                if data.get("code") == "DuplicateError":
                    duplicate_id = data.get("details", {}).get("duplicateId", None)
                    if duplicate_id:
                        return self.patch(duplicate_id, new_entity_data)

            raise_for_status_improved(response)
            return response.json()["id"]

    @retry_on_401
    def patch(self, resource_id: str, patch_data: Dict) -> str:
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.patch(
                f"/v1/{self.resource}/{resource_id}",
                headers=self.build_headers(),
                json=self.update_data_model.parse_obj(patch_data).dict(by_alias=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return resource_id

    @retry_on_401
    def delete(self, resource_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.delete(
                f"/v1/{self.resource}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def query(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            return [self.sync_resource(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]


class GenericAsyncModule:

    def __init__(self, altscore_client, async_resource, retrieve_data_model, create_data_model,
                 update_data_model, resource: str):
        self.altscore_client = altscore_client
        self.async_resource = async_resource
        self.retrieve_data_model = retrieve_data_model
        self.create_data_model = create_data_model
        self.update_data_model = update_data_model
        self.resource = resource.strip("/")

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    def print_create_schema(self):
        print(json.dumps(self.create_data_model.schema(), indent=2, ensure_ascii=False))

    def print_update_schema(self):
        if self.update_data_model is None:
            print("No update schema")
            return
        print(json.dumps(self.update_data_model.schema(), indent=2, ensure_ascii=False))

    def print_retrieve_schema(self):
        print(json.dumps(self.retrieve_data_model.schema(), indent=2, ensure_ascii=False))

    @retry_on_401_async
    async def retrieve(self, resource_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/{self.resource}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return self.async_resource(
                    base_url=self.altscore_client._borrower_central_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=self.retrieve_data_model.parse_obj(response.json())
                )
            elif response.status_code in [404]:
                return None

            raise_for_status_improved(response)

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
                f"/v1/{self.resource}",
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
    async def create(self, new_entity_data: Dict, update_if_exists: bool = False) -> str:
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(by_alias=True),
                timeout=30
            )
            if response.status_code == 409 and update_if_exists:
                if response.status_code == 409 and update_if_exists:
                    data = response.json()
                    if data.get("code") == "DuplicateError":
                        duplicate_id = data.get("details", {}).get("duplicateId", None)
                        if duplicate_id:
                            return await self.patch(duplicate_id, new_entity_data)
            raise_for_status_improved(response)
            return response.json()["id"]

    @retry_on_401_async
    async def patch(self, resource_id: str, patch_data: Dict) -> str:
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.patch(
                f"/v1/{self.resource}/{resource_id}",
                headers=self.build_headers(),
                json=self.update_data_model.parse_obj(patch_data).dict(by_alias=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return resource_id

    @retry_on_401_async
    async def delete(self, resource_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.delete(
                f"/v1/{self.resource}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
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
                f"/v1/{self.resource}",
                headers=self.build_headers(),
                params=query_params,
                timeout=timeout
            )
            raise_for_status_improved(response)
            return [self.async_resource(
                base_url=self.altscore_client._borrower_central_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]
