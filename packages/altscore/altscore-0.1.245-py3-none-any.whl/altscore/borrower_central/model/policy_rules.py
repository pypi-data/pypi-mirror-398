from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async


class RuleAlert(BaseModel):
    level: int = Field(alias="level")
    message: str = Field(alias="message")


class RuleAPIDTO(BaseModel):
    id: str = Field(alias="id")
    code: str = Field(alias="code")
    label: str = Field(alias="label")
    alerts: List[RuleAlert] = Field(alias="alerts", default=[])
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

    def get_alert_by_level(self, level: int):
        for alert in self.alerts:
            if alert.level == level:
                return alert
        return None


class CreateRuleDTO(BaseModel):
    label: str = Field(alias="label")
    code: str = Field(alias="code")
    alerts: List[RuleAlert] = Field(alias="alerts")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class RulesSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "rules", header_builder, renew_token, RuleAPIDTO.parse_obj(data))


class RulesAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "rules", header_builder, renew_token, RuleAPIDTO.parse_obj(data))


class RulesSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=RulesSync,
                         retrieve_data_model=RuleAPIDTO,
                         create_data_model=CreateRuleDTO,
                         update_data_model=CreateRuleDTO,
                         resource="rules")

    @retry_on_401
    def retrieve_by_code(self, code: str):
        query_params = {
            "code": code
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


class RulesAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=RulesAsync,
                         retrieve_data_model=RuleAPIDTO,
                         create_data_model=CreateRuleDTO,
                         update_data_model=CreateRuleDTO,
                         resource="rules")

    @retry_on_401_async
    async def retrieve_by_code(self, code: str):
        query_params = {
            "code": code
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
