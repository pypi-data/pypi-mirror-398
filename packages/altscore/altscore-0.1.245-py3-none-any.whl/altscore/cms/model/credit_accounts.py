from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.cms.model.common import Money


class Reservation(BaseModel):
    id: Optional[str] = Field(alias="id", default=None)
    type: Optional[str] = Field(alias="type", default=None)
    amount: Money
    status: str
    created_at: str = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

class Percentages(BaseModel):
    available: float
    consumed: float

class CreditLine(BaseModel):
    assigned: Money
    available: Money
    consumed: Money
    reservations: Optional[List[Reservation]] = Field(alias="reservations", default=None)
    percentages: Optional[Percentages] = Field(alias="percentages", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class HistoryItem(BaseModel):
    createdAt: str
    amount: Money
    reason: Optional[str] = Field(alias="reason", default=None)
    userId: str

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class CreditAccountAPIDTO(BaseModel):
    client_id: str = Field(alias="clientId")
    partner_id: str = Field(alias="partnerId")
    borrower_id: str = Field(alias="borrowerId")
    external_id: str = Field(alias="externalId")
    product_family: str = Field(alias="productFamily")
    status: str = Field(alias="status")
    credit_line: CreditLine = Field(alias="creditLine")
    history: Optional[List[HistoryItem]] = Field(alias="history", default=None)
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True

    def is_enabled(self):
        return self.status == "enabled"


class CreditAccountAsync:
    data: CreditAccountAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: CreditAccountAPIDTO):
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401_async
    async def update(self, amount: str, currency: str, reason: str) -> None:
        """
        Updates credit account with the given amount and currency, and the reason for the update.
        It will replace the data in the object with the response from the API.
        """
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.patch(
                f"/v2/clients/{self.data.client_id}/credit-accounts/{self.data.product_family}",
                json={
                    "assigned": {
                        "amount": amount,
                        "currency": currency,
                    },
                    "reason": reason,
                },
                headers=self._header_builder(partner_id=self.data.partner_id),
                timeout=30
            )
            raise_for_status_improved(response)
            self.data = CreditAccountAPIDTO.parse_obj(response.json())

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}"


class CreditAccountSync:
    data: CreditAccountAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: CreditAccountAPIDTO):
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401
    def update(self, amount: str, currency: str, reason: str) -> None:
        """
        Updates credit account with the given amount and currency, and the reason for the update.
        It will replace the data in the object with the response from the API.
        """
        with httpx.Client(base_url=self.base_url) as client:
            response = client.patch(
                f"/v2/clients/{self.data.client_id}/credit-accounts/{self.data.product_family}",
                json={
                    "assigned": {
                        "amount": amount,
                        "currency": currency,
                    },
                    "reason": reason,
                },
                headers=self._header_builder(partner_id=self.data.partner_id),
                timeout=30
            )
            raise_for_status_improved(response)
            self.data = CreditAccountAPIDTO.parse_obj(response.json())

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}"
