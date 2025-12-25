from typing import Dict

import httpx

from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.utils import convert_to_dash_case
from altscore.comms.helpers import build_headers



class GenericSyncModule:
    def __init__(self, altscore_client, sync_resource, retrieve_data_model, create_data_model,
                 update_data_model, resource: str, resource_version: str = "v1"):
        self.altscore_client = altscore_client
        self.sync_resource = sync_resource
        self.retrieve_data_model = retrieve_data_model
        self.create_data_model = create_data_model
        self.update_data_model = update_data_model
        self.resource_version = resource_version
        self.resource = resource.strip("/")

    def renew_token(self):
        return self.altscore_client.renew_token()

    def build_headers(self, **kwargs):
        return build_headers(self, **kwargs)

    @retry_on_401
    def create(self, new_entity_data: dict):
        with httpx.Client(base_url=self.altscore_client._webhooks_base_url) as client:
            response = client.post(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(by_alias=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json().get('id')

    @retry_on_401
    def retrieve(self, resource_id: str):
        with httpx.Client(base_url=self.altscore_client._webhooks_base_url) as client:
            response = client.get(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return self.sync_resource(
                    base_url=self.altscore_client._webhooks_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=self.retrieve_data_model.parse_obj(response.json())
                )
            return None

    @retry_on_401
    def patch(self, resource_id: str, patch_data: Dict) -> str:
        with httpx.Client(base_url=self.altscore_client._webhooks_base_url) as client:
            response = client.patch(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}/{resource_id}",
                headers=self.build_headers(),
                json=self.update_data_model.parse_obj(patch_data).dict(by_alias=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return self.retrieve_data_model.parse_obj(response.json())

    @retry_on_401
    def delete(self, resource_id: str):
        with httpx.Client(base_url=self.altscore_client._webhooks_base_url) as client:
            response = client.delete(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def retrieve_all(self, **kwargs):
        query_params = {}
        with httpx.Client(base_url=self.altscore_client._webhooks_base_url) as client:
            response = client.get(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}",
                params=query_params,
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            # If no header then total_count is 0
            total_count = int(response.headers.get("x-total-count", 0))
        resources = []
        for offset in range(0, total_count, 100):
            resources.append(self.query(limit=100, offset=offset, **kwargs))
        resources = [item for sublist in resources for item in sublist]
        return resources

    @retry_on_401
    def query(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        with httpx.Client(base_url=self.altscore_client._webhooks_base_url) as client:
            response = client.get(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            return [self.sync_resource(
                base_url=self.altscore_client._webhooks_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]




class GenericAsyncModule:
    def __init__(self, altscore_client, async_resource, retrieve_data_model, create_data_model,
                 update_data_model, resource: str, resource_version: str = "v1"):
        self.altscore_client = altscore_client
        self.async_resource = async_resource
        self.retrieve_data_model = retrieve_data_model
        self.create_data_model = create_data_model
        self.update_data_model = update_data_model
        self.resource_version = resource_version
        self.resource = resource.strip("/")

    def renew_token(self):
        return self.altscore_client.renew_token()

    def build_headers(self, **kwargs):
        return build_headers(self, **kwargs)

    @retry_on_401_async
    async def create(self, new_entity_data: dict):
        async with httpx.AsyncClient(base_url=self.altscore_client._webhooks_base_url) as client:
            response = await client.post(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}",
                headers=self.build_headers(),
                json=self.create_data_model.parse_obj(new_entity_data).dict(by_alias=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return response.json().get('id')

    @retry_on_401_async
    async def retrieve(self, resource_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._webhooks_base_url) as client:
            response = await client.get(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return self.async_resource(
                    base_url=self.altscore_client._webhooks_base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    data=self.retrieve_data_model.parse_obj(response.json())
                )
            return None

    @retry_on_401_async
    async def patch(self, resource_id: str, patch_data: Dict) -> str:
        async with httpx.AsyncClient(base_url=self.altscore_client._webhooks_base_url) as client:
            response = await client.patch(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}/{resource_id}",
                headers=self.build_headers(),
                json=self.update_data_model.parse_obj(patch_data).dict(by_alias=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return self.retrieve_data_model.parse_obj(response.json())

    @retry_on_401_async
    async def delete(self, resource_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._webhooks_base_url) as client:
            response = await client.delete(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}/{resource_id}",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def retrieve_all(self, **kwargs):
        query_params = {}
        async with httpx.AsyncClient(base_url=self.altscore_client._webhooks_base_url) as client:
            response = await client.get(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}",
                params=query_params,
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            # If no header then total_count is 0
            total_count = int(response.headers.get("x-total-count", 0))
        resources = []
        for offset in range(0, total_count, 100):
            resources.append(await self.query(limit=100, offset=offset, **kwargs))
        resources = [item for sublist in resources for item in sublist]
        return resources

    @retry_on_401_async
    async def query(self, **kwargs):
        query_params = {}
        for k, v in kwargs.items():
            if v is not None:
                query_params[convert_to_dash_case(k)] = v

        async with httpx.AsyncClient(base_url=self.altscore_client._webhooks_base_url) as client:
            response = await client.get(
                f"/{self.resource_version}/{self.resource}/{self.altscore_client.partner_id}",
                headers=self.build_headers(),
                params=query_params,
                timeout=30
            )
            raise_for_status_improved(response)
            return [self.async_resource(
                base_url=self.altscore_client._webhooks_base_url,
                header_builder=self.build_headers,
                renew_token=self.renew_token,
                data=self.retrieve_data_model.parse_obj(e)
            ) for e in response.json()]
