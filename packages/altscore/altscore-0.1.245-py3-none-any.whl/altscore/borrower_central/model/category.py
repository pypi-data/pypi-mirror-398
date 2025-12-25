from typing import List, Optional

import httpx
from pydantic import BaseModel, Field

from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.helpers import build_headers

class CategoryDTO(BaseModel):
    id: str = Field(alias="id")
    category_key: str = Field(alias="categoryKey")
    label: str = Field(alias="label")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class CategoryValueDTO(BaseModel):
    id: str = Field(alias="id")
    category_id: str = Field(alias="categoryId")
    category_key: str = Field(alias="categoryKey")
    value: str = Field(alias="value")

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

class NewCategoryDTO(BaseModel):
    category_key: str = Field(alias="categoryKey")
    label: str = Field(alias="label")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class NewCategoryValueDTO(BaseModel):
    id: Optional[str] = Field(alias="id", default=None)
    value: str = Field(alias="value")

class EntityWrapper(BaseModel):
    entity_type: str = Field(alias="entityType")
    entity_id: str = Field(alias="entityId")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CategoryBase:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _get_category_values_url(self, category_id: str) -> str:
        return f"{self.base_url}/v1/category/{category_id}/values"

    def _add_category_value_url(self, category_id: str):
        return f"{self.base_url}/v1/category/{category_id}/value"

    def _delete_category_value_url(self, category_id: str, category_value_id: str):
        return f"{self.base_url}/v1/category/{category_id}/value/{category_value_id}"


class CategoryAsyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401_async
    async def create(self, new_category: dict, values: Optional[List[NewCategoryValueDTO]] = None):
        if values is None:
            values = []
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/category",
                headers=self.build_headers(),
                json=NewCategoryDTO.parse_obj(new_category).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)
            cat_id = response.json()["id"]
            if len(values) > 0:
                category = await self.retrieve(cat_id)
                for value in values:
                    await category.create_category_value(value)

            return cat_id

    @retry_on_401_async
    async def retrieve(self, category_id):
        base_url = self.altscore_client._borrower_central_base_url
        async with httpx.AsyncClient(base_url=base_url) as client:
            response = await client.get(
                "/v1/category/{}".format(category_id),
                headers=self.build_headers(),
                timeout=120
            )
            if response.status_code == 200:
                return CategoryAsync(
                    base_url=base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    category_data=CategoryDTO.parse_obj(response.json())
                )
            if response.status_code == 404:
                return None
            raise_for_status_improved(response)

    @retry_on_401_async
    async def delete(self, category_id):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.delete(
                "/v1/category/{}".format(category_id),
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def set_category_value_to_entity(self, entity: EntityWrapper, category_key: str, category_value_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/category/commands/categorize-entity",
                headers=self.build_headers(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": entity.entity_type,
                    "entityId": entity.entity_id,
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def delete_category_value_from_entity(self, entity: EntityWrapper, category_key: str, category_value_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                "/v1/category/commands/delete-entity-category",
                headers=self.build_headers(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": entity.entity_type,
                    "entityId": entity.entity_id,
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401_async
    async def get_category_values_by_entity(self, entity: EntityWrapper):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/category/queries/entity/{entity.entity_type}/{entity.entity_id}",
                headers=self.build_headers(),
            )
            raise_for_status_improved(response)
            return [
                EntityCategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    @retry_on_401_async
    async def get_category_values_by_entity_type(self, entity_type: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/category/queries/entity/{entity_type}",
                headers=self.build_headers(),
            )
            raise_for_status_improved(response)
            return [
                EntityCategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    @retry_on_401_async
    async def get_category_values_by_key(self, category_key: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.get(
                f"/v1/category/by-key/{category_key}/values",
                headers=self.build_headers(),
            )
            raise_for_status_improved(response)
            return [
                CategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

class CategorySyncModule:
    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def renew_token(self):
        self.altscore_client.renew_token()

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def create(self, new_category: dict, values: Optional[List[NewCategoryValueDTO]] = None):
        if values is None:
            values = []
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/category",
                headers=self.build_headers(),
                json=NewCategoryDTO.parse_obj(new_category).dict(by_alias=True),
                timeout=120
            )
            raise_for_status_improved(response)

            cat_id = response.json()["id"]
            if len(values) > 0:
                category = self.retrieve(cat_id)
                for value in values:
                    category.create_category_value(value)

            return cat_id

    @retry_on_401
    def retrieve(self, category_id):
        base_url = self.altscore_client._borrower_central_base_url
        with httpx.Client(base_url=base_url) as client:
            response = client.get(
                "/v1/category/{}".format(category_id),
                headers=self.build_headers(),
                timeout=120
            )
            if response.status_code == 200:
                return CategorySync(
                    base_url=base_url,
                    header_builder=self.build_headers,
                    renew_token=self.renew_token,
                    category_data=CategoryDTO.parse_obj(response.json())
                )
            if response.status_code == 404:
                return None
            raise_for_status_improved(response)

    @retry_on_401
    def delete(self, category_id):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.delete(
                "/v1/category/{}".format(category_id),
                headers=self.build_headers(),
                timeout=120
            )
            raise_for_status_improved(response)

    @retry_on_401
    def set_category_value_to_entity(self, entity: EntityWrapper, category_key: str, category_value_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/category/commands/categorize-entity",
                headers=self.build_headers(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": entity.entity_type,
                    "entityId": entity.entity_id,
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def delete_category_value_from_entity(self, entity: EntityWrapper, category_key: str, category_value_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                "/v1/category/commands/delete-entity-category",
                headers=self.build_headers(),
                json={
                    "categoryKey": category_key,
                    "categoryValueId": category_value_id,
                    "entityType": entity.entity_type,
                    "entityId": entity.entity_id,
                }
            )
            raise_for_status_improved(response)
            return None

    @retry_on_401
    def get_category_values_by_entity(self, entity: EntityWrapper):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/category/queries/entity/{entity.entity_type}/{entity.entity_id}",
                headers=self.build_headers(),
            )
            raise_for_status_improved(response)
            return [
                EntityCategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    @retry_on_401
    def get_category_values_by_entity_type(self, entity_type: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/category/queries/entity/{entity_type}",
                headers=self.build_headers(),
            )
            raise_for_status_improved(response)
            return [
                EntityCategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    @retry_on_401
    def get_category_values_by_key(self, category_key: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.get(
                f"/v1/category/by-key/{category_key}/values",
                headers=self.build_headers(),
            )
            raise_for_status_improved(response)
            return [
                CategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

class CategoryAsync(CategoryBase):
    data: CategoryDTO

    def __init__(self, base_url, header_builder, renew_token, category_data: CategoryDTO):
        super().__init__(base_url)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = category_data

    @retry_on_401_async
    async def create_category_value(self, value: NewCategoryValueDTO):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                self._add_category_value_url(self.data.id),
                headers=self._header_builder(),
                json=value.dict(by_alias=True),
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def get_category_values(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                self._get_category_values_url(self.data.id),
                headers=self._header_builder(),
            )
            raise_for_status_improved(response)
            return [
                CategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    @retry_on_401_async
    async def delete_category_value(self, category_value_id: str):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.delete(
                self._delete_category_value_url(self.data.id, category_value_id),
                headers=self._header_builder(),
            )
            raise_for_status_improved(response)



class CategorySync(CategoryBase):
    data: CategoryDTO

    def __init__(self, base_url, header_builder, renew_token, category_data: CategoryDTO):
        super().__init__(base_url)
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = category_data

    @retry_on_401
    def create_category_value(self, value: NewCategoryValueDTO):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                self._add_category_value_url(self.data.id),
                headers=self._header_builder(),
                json=value.dict(by_alias=True),
            )
            raise_for_status_improved(response)

    @retry_on_401
    def get_category_values(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                self._get_category_values_url(self.data.id),
                headers=self._header_builder(),
            )
            raise_for_status_improved(response)
            return [
                CategoryValueDTO.parse_obj(data)
                for data in response.json()
            ]

    @retry_on_401
    def delete_category_value(self, category_value_id: str):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.delete(
                self._delete_category_value_url(self.data.id, category_value_id),
                headers=self._header_builder(),
            )
            raise_for_status_improved(response)
