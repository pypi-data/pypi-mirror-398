from pydantic import BaseModel, Field
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from typing import Optional, Dict
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async


class AddressAPIDTO(BaseModel):
    id: str = Field(alias="id")
    borrower_id: str = Field(alias="borrowerId")
    label: Optional[str] = Field(alias="label")
    street1: Optional[str] = Field(alias="street1", default=None)
    street2: Optional[str] = Field(alias="street2", default=None)
    external_number: Optional[str] = Field(alias="externalNumber", default=None)
    internal_number: Optional[str] = Field(alias="internalNumber", default=None)
    neighborhood: Optional[str] = Field(alias="neighborhood", default=None)
    city: Optional[str] = Field(alias="city", default=None)
    state: Optional[str] = Field(alias="state", default=None)
    zip_code: Optional[str] = Field(alias="zipCode", default=None)
    reference: Optional[str] = Field(alias="reference", default=None)
    country: Optional[str] = Field(alias="country", default=None)
    province: Optional[str] = Field(alias="province", default=None)
    lat: Optional[float] = Field(alias="lat", default=None)
    lon: Optional[float] = Field(alias="lon", default=None)
    priority: Optional[int] = Field(alias="priority", default=None)
    is_home: bool = Field(alias="isHome", default=False)
    is_work: bool = Field(alias="isWork", default=False)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")
    has_attachments: bool = Field(alias="hasAttachments")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

    def get_location(self):
        if self.lat is None or self.lon is None:
            return None
        return {
            "lat": self.lat,
            "lon": self.lon
        }

    def get_address(self):
        return {
            "street1": self.street1,
            "street2": self.street2,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "province": self.province,
            "state": self.state,
            "zipCode": self.zip_code,
            "country": self.country,
        }

    def get_address_str(self):
        str = ""
        if self.street1 is not None:
            str += self.street1
            if self.external_number is not None:
                str += " " + self.external_number
        if self.street2 is not None:
            str += " " + self.street2
        if self.neighborhood is not None:
            str += " " + self.neighborhood
        if self.city is not None:
            str += " " + self.city
        if self.province is not None:
            str += " " + self.province
        if self.state is not None:
            str += " " + self.state
        if self.zip_code is not None:
            str += " " + self.zip_code
        if self.country is not None:
            str += " " + self.country
        return str


class CreateAddressDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    label: Optional[str] = Field(alias="label")
    street1: Optional[str] = Field(alias="street1", default=None)
    street2: Optional[str] = Field(alias="street2", default=None)
    external_number: Optional[str] = Field(alias="externalNumber", default=None)
    internal_number: Optional[str] = Field(alias="internalNumber", default=None)
    neighborhood: Optional[str] = Field(alias="neighborhood", default=None)
    city: Optional[str] = Field(alias="city", default=None)
    state: Optional[str] = Field(alias="state", default=None)
    zip_code: Optional[str] = Field(alias="zipCode", default=None)
    reference: Optional[str] = Field(alias="reference", default=None)
    country: Optional[str] = Field(alias="country", default=None)
    province: Optional[str] = Field(alias="province", default=None)
    lat: Optional[float] = Field(alias="lat", default=None)
    lon: Optional[float] = Field(alias="lon", default=None)
    priority: Optional[int] = Field(alias="priority", default=None)
    is_home: bool = Field(alias="isHome", default=False)
    is_work: bool = Field(alias="isWork", default=False)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateAddressDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    label: Optional[str] = Field(alias="label", default=None)
    street1: Optional[str] = Field(alias="street1", default=None)
    street2: Optional[str] = Field(alias="street2", default=None)
    external_number: Optional[str] = Field(alias="externalNumber", default=None)
    internal_number: Optional[str] = Field(alias="internalNumber", default=None)
    neighborhood: Optional[str] = Field(alias="neighborhood", default=None)
    city: Optional[str] = Field(alias="city", default=None)
    state: Optional[str] = Field(alias="state", default=None)
    zip_code: Optional[str] = Field(alias="zipCode", default=None)
    reference: Optional[str] = Field(alias="reference", default=None)
    country: Optional[str] = Field(alias="country", default=None)
    lat: Optional[float] = Field(alias="lat", default=None)
    lon: Optional[float] = Field(alias="lon", default=None)
    priority: Optional[int] = Field(alias="priority", default=None)
    is_home: Optional[bool] = Field(alias="isHome", default=None)
    is_work: Optional[bool] = Field(alias="isWork", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class GeocodingAPIDTO(BaseModel):
    id: str = Field(alias="id")
    not_found: Optional[bool] = Field(alias="notFound", default=None)
    is_success: bool = Field(alias="isSuccess")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class NewAddressFromAddressStrDTO(BaseModel):
    borrower_id: str = Field(alias="borrowerId")
    address_str: str = Field(alias="addressStr")
    country: Optional[str] = Field(alias="country", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    priority: Optional[int] = Field(alias="priority", default=None)
    is_home: Optional[bool] = Field(alias="isHome", default=None)
    is_work: Optional[bool] = Field(alias="isWork", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class AddressSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "addresses", header_builder, renew_token, AddressAPIDTO.parse_obj(data))


class AddressAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "addresses", header_builder, renew_token, AddressAPIDTO.parse_obj(data))


class AddressesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=AddressSync,
                         retrieve_data_model=AddressAPIDTO,
                         create_data_model=CreateAddressDTO,
                         update_data_model=UpdateAddressDTO,
                         resource="addresses")


    @retry_on_401
    def geocode(self, address_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/addresses/commands/geocode",
                headers=self.build_headers(),
                json={
                    "id": address_id
                }
            )
            raise_for_status_improved(response)
            return GeocodingAPIDTO.parse_obj(response.json())

    @retry_on_401
    def reverse_geocode(self, address_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/addresses/commands/reverse-geocode",
                headers=self.build_headers(),
                json={
                    "id": address_id
                }
            )
            raise_for_status_improved(response)
            return GeocodingAPIDTO.parse_obj(response.json())

    @retry_on_401
    def new_address_from_address_str(self, new_address_data: dict):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/addresses/commands/new-address-from-address-str",
                headers=self.build_headers(),
                json=NewAddressFromAddressStrDTO.parse_obj(new_address_data).dict(by_alias=True),
            )
            raise_for_status_improved(response)
            return response.json()["id"]

    @retry_on_401
    def add_picture_by_url(self, address_id: str, url: str, label: Optional[str] = None):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/addresses/commands/add-picture-by-url",
                headers=self.build_headers(),
                json={
                    "addressId": address_id,
                    "url": url,
                    "label": label
                }
            )
            raise_for_status_improved(response)
            return response.json()["attachmentId"]

    @retry_on_401
    def set_main_picture(self, address_id: str, attachment_id: str):
        with httpx.Client(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = client.post(
                f"/v1/addresses/commands/set-main-picture",
                headers=self.build_headers(),
                json={
                    "addressId": address_id,
                    "attachmentId": attachment_id
                }
            )
            raise_for_status_improved(response)


class AddressesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=AddressAsync,
                         retrieve_data_model=AddressAPIDTO,
                         create_data_model=CreateAddressDTO,
                         update_data_model=UpdateAddressDTO,
                         resource="addresses")


    @retry_on_401_async
    async def geocode(self, address_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/addresses/commands/geocode",
                headers=self.build_headers(),
                json={
                    "id": address_id
                }
            )
            raise_for_status_improved(response)
            return GeocodingAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def reverse_geocode(self, address_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/addresses/commands/reverse-geocode",
                headers=self.build_headers(),
                json={
                    "id": address_id
                }
            )
            raise_for_status_improved(response)
            return GeocodingAPIDTO.parse_obj(response.json())

    @retry_on_401_async
    async def new_address_from_address_str(self, new_address_data: dict):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/addresses/commands/new-address-from-address-str",
                headers=self.build_headers(),
                json=NewAddressFromAddressStrDTO.parse_obj(new_address_data).dict(by_alias=True),
            )
            raise_for_status_improved(response)
            return response.json()["id"]

    @retry_on_401_async
    async def add_picture_by_url(self, address_id: str, url: str, label: Optional[str] = None):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/addresses/commands/add-picture-by-url",
                headers=self.build_headers(),
                json={
                    "addressId": address_id,
                    "url": url,
                    "label": label
                }
            )
            raise_for_status_improved(response)
            return response.json()["attachmentId"]

    @retry_on_401_async
    async def set_main_picture(self, address_id: str, attachment_id: str):
        async with httpx.AsyncClient(base_url=self.altscore_client._borrower_central_base_url) as client:
            response = await client.post(
                f"/v1/addresses/commands/set-main-picture",
                headers=self.build_headers(),
                json={
                    "addressId": address_id,
                    "attachmentId": attachment_id
                }
            )
            raise_for_status_improved(response)
