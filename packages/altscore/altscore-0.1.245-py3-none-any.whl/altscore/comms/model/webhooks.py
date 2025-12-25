from pydantic import BaseModel, Field
from typing import Optional, List
import httpx

from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.comms.model.generics import GenericSyncModule, GenericAsyncModule


class WebhookEventAPIDTO(BaseModel):
    key: str = Field(alias="key")
    name: str = Field(alias="name")
    description: dict = Field(alias="description")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class WebhookAuthorizationDTO(BaseModel):
    header_name: str = Field(alias="headerName")
    secret_key: str = Field(alias="secret")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class WebhookConfigurationAPIDTO(BaseModel):
    id: str = Field(alias="id")
    name: str = Field(alias="name")
    status: str = Field(alias="status")
    url: str = Field(alias="url")
    events: list[str] = Field(alias="events")
    ssl_skip_verification: bool = Field(alias="skipCertVerification")
    partner_id: str = Field(alias="partnerId")
    authorization: Optional[WebhookAuthorizationDTO] = Field(alias="authorization", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class CreateWebhookConfigurationDTO(BaseModel):
    name: str = Field(alias="name")
    url: str = Field(alias="url")
    events: list[str] = Field(alias="events")
    ssl_skip_verification: bool = Field(alias="skipCertVerification")
    authorization: Optional[WebhookAuthorizationDTO] = Field(alias="authorization", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class UpdateWebhookConfigurationDTO(BaseModel):
    name: str = Field(alias="name")
    url: str = Field(alias="url")
    events: list[str] = Field(alias="events")
    ssl_skip_verification: bool = Field(alias="skipCertVerification")
    authorization: Optional[WebhookAuthorizationDTO] = Field(alias="authorization", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class WebhookBase:
    @staticmethod
    def _get_events(
    ) -> (str, Optional[dict]):
        return f"/v1/webhooks/events"

    @staticmethod
    def _get_webhook(partner_id: str, webhook_id: str):
        return f"/v1/webhooks/{partner_id}/{webhook_id}"

    @staticmethod
    def _get_webhooks(partner_id: str):
        return f"/v1/webhooks/{partner_id}/"

    @staticmethod
    def _webhook_status(partner_id: str, webhook_id: str):
        return f"/v1/webhooks/{partner_id}/{webhook_id}/status"

class WebhookSync(WebhookBase):
    data: WebhookConfigurationAPIDTO
    def __init__(self, base_url, header_builder, renew_token, data):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401
    def enable(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                self._webhook_status(self.data.partner_id,self.data.id),
                headers=self._header_builder(),
                timeout=30,
                json={
                    "status": "enabled"
                },
            )
            raise_for_status_improved(response)

    @retry_on_401
    def disable(self):
        with httpx.Client(base_url=self.base_url) as client:
            response = client.put(
                self._webhook_status(self.data.partner_id, self.data.id),
                headers=self._header_builder(),
                timeout=30,
                json={
                    "status": "disabled"
                },
            )
            raise_for_status_improved(response)

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"

class WebhookAsync(WebhookBase):
    data: WebhookConfigurationAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401_async
    async def enable(self):
       async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                self._webhook_status(self.data.partner_id, self.data.id),
                headers=self._header_builder(),
                timeout=30,
                json={
                    "status": "enabled"
                },
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def disable(self):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(
                self._webhook_status(self.data.partner_id, self.data.id),
                headers=self._header_builder(),
                timeout=30,
                json={
                    "status": "disabled"
                },
            )
            raise_for_status_improved(response)

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class WebhookSyncModule(GenericSyncModule):
    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            sync_resource=WebhookSync,
            retrieve_data_model=WebhookConfigurationAPIDTO,
            create_data_model=CreateWebhookConfigurationDTO,
            update_data_model=UpdateWebhookConfigurationDTO,
            resource="webhooks",
            resource_version="v1"
        )

    def renew_token(self):
        self.altscore_client.renew_token()

    @retry_on_401
    def get_events_available(self) -> List[WebhookEventAPIDTO]:
        with httpx.Client(base_url=self.altscore_client._webhooks_base_url) as client:
            response = client.get(
                f"/{self.resource_version}/{self.resource}/events",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [WebhookEventAPIDTO.parse_obj(e) for e in response.json()]


class WebhookAsyncModule(GenericAsyncModule):
    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            async_resource=WebhookAsync,
            retrieve_data_model=WebhookConfigurationAPIDTO,
            create_data_model=CreateWebhookConfigurationDTO,
            update_data_model=UpdateWebhookConfigurationDTO,
            resource="webhooks",
            resource_version="v1"
        )

    def renew_token(self):
        self.altscore_client.renew_token()

    @retry_on_401_async
    async def get_events_available(self) -> List[WebhookEventAPIDTO]:
        async with httpx.AsyncClient(base_url=self.altscore_client._webhooks_base_url) as client:
            response = await client.get(
                f"/{self.resource_version}/{self.resource}/events",
                headers=self.build_headers(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [WebhookEventAPIDTO.parse_obj(e) for e in response.json()]