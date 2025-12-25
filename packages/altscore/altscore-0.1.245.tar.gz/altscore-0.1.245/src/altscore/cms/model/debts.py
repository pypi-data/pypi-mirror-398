from pydantic import BaseModel, Field
from typing import Optional, List
import httpx
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.cms.model.generics import GenericSyncModule, GenericAsyncModule
from altscore.cms.model.common import Money, Schedule, Terms

import datetime as dt


class Balance(BaseModel):
    fees: Optional[Money] = Field(alias="fees")
    interest: Optional[Money] = Field(alias="interest")
    principal: Optional[Money] = Field(alias="principal")
    taxes: Optional[Money] = Field(alias="taxes")
    penalties: Optional[Money] = Field(alias="penalties")
    total: Optional[Money] = Field(alias="total")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Client(BaseModel):
    id: str = Field(alias="clientId")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    partner_id: str = Field(alias="partnerId")
    external_id: str = Field(alias="externalId")
    email: str = Field(alias="email")
    legal_name: str = Field(alias="legalName")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Transaction(BaseModel):
    id: str = Field(alias="transactionId")
    breakdown: Optional[List[Balance]] = Field(alias="breakdown")
    amount: Money = Field(alias="amount")
    type: str = Field(alias="type")
    date: str = Field(alias="date")
    reference_id: str = Field(alias="referenceId", default=None)
    notes: Optional[str] = Field(alias="notes", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class DebtAPIDTO(BaseModel):
    id: str = Field(alias="debtId")
    flow_id: str = Field(alias="flowId")
    tenant: str = Field(alias="tenant")
    reference_id: str = Field(alias="referenceId")
    status: str = Field(alias="status")
    sub_status: str = Field(alias="subStatus")
    client: Client = Field(alias="client")
    balance: Balance = Field(alias="balance")
    closing_balance: Money = Field(alias="closingBalance")
    schedule: List[Schedule] = Field(alias="schedule")
    terms: Terms = Field(alias="terms")
    transactions: List[Transaction] = Field(alias="transactions")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    version: int = Field(alias="version")
    days_past_due: Optional[int] = Field(alias="daysPastDue", default=None)
    max_days_past_due: Optional[int] = Field(alias="maxDaysPastDue", default=None)
    source: Optional[str] = Field(alias="source", default="simple_credit")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Payment(BaseModel):
    debt_id: str = Field(alias="debtId")
    amount: Money = Field(alias="amount")
    payment_date: str = Field(alias="paymentDate")
    reference_id: str = Field(alias="referenceId")
    notes: Optional[str] = Field(alias="notes")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class PenaltyBalance(BaseModel):
    fees: Money = Field(alias="fees")
    interest: Money = Field(alias="interest")
    principal: Money = Field(alias="principal")
    taxes: Money = Field(alias="taxes")
    penalties: Money = Field(alias="penalties")
    total: Money = Field(alias="total")
    installment: int = Field(alias="installment")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class Penalty(BaseModel):
    amount: Money = Field(alias="amount")
    breakdown: List[PenaltyBalance] = Field(alias="breakdown")
    date: str = Field(alias="date")
    notes: Optional[str] = Field(alias="notes")
    reference_id: str = Field(alias="referenceId")
    transaction_id: str = Field(alias="transactionId")
    type: str = Field(alias="type")


class CreateDebt(BaseModel):
    flow_id: str = Field(alias="flowId")
    disbursed_at: Optional[str] = Field(alias="disbursedAt", default=None)
    amount: Optional[Money] = Field(alias="amount", default=None)

    class Config:
        allow_population_by_field_name = True
        populate_by_alias = True
        populate_by_name = True


class Waiver(BaseModel):
    amount: Money = Field(alias="amount") # This amount should be the sum of the breakdown amounts
    breakdown: Optional[Balance] = Field(alias="breakdown", default=None) # These amount should be negative floats
    notes: Optional[str] = Field(alias="notes", default=None)
    reference_id: str = Field(alias="referenceId")
    waiver_date: str = Field(alias="waiverDate")

    class Config:
        allow_population_by_field_name = True
        populate_by_alias = True
        populate_by_name = True


class DebtBase:

    @staticmethod
    def _payments(debt_id: str):
        return f"/v1/debts/{debt_id}/payments"

    @staticmethod
    def _penalties(debt_id: str):
        return f"/v1/debts/{debt_id}/penalties"

    @staticmethod
    def _waivers(debt_id: str):
        return f"/v1/debts/{debt_id}/waivers"


class DebtAsync(DebtBase):
    data: DebtAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DebtAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401_async
    async def get_payments(self) -> List[Payment]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                self._payments(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [Payment.parse_obj(e) for e in response.json()]

    @retry_on_401_async
    async def submit_payment(self, amount: str, currency: str, reference_id: str, notes: Optional[str] = None,
                             payment_date: Optional[dt.date] = None) -> None:
        if payment_date is None:
            payment_date = dt.date.today()
        if notes is None:
            notes = ""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                self._payments(self.data.id),
                json={
                    "amount": {
                        "amount": amount,
                        "currency": currency
                    },
                    "referenceId": reference_id,
                    "notes": notes,
                    "paymentDate": payment_date.strftime("%Y-%m-%d")
                },
                timeout=30,
                headers=self._header_builder()
            )
            raise_for_status_improved(response)

    @retry_on_401_async
    async def get_penalties(self) -> List[Penalty]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(
                self._waivers(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [Penalty.parse_obj(e) for e in response.json()]

    @retry_on_401_async
    async def apply_waiver(self, waiver: dict) -> None:
        waiver = Waiver.parse_obj(waiver)
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                self._waivers(self.data.id),
                headers=self._header_builder(),
                json=waiver.dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class DebtSync(DebtBase):
    data: DebtAPIDTO

    def __init__(self, base_url, header_builder, renew_token, data: DebtAPIDTO):
        super().__init__()
        self.base_url = base_url
        self._header_builder = header_builder
        self.renew_token = renew_token
        self.data = data

    @retry_on_401
    def get_payments(self) -> List[Payment]:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                self._payments(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [Payment.parse_obj(e) for e in response.json()]

    @retry_on_401
    def submit_payment(self, amount: str, currency: str, reference_id: str, notes: Optional[str] = None,
                       payment_date: Optional[dt.date] = None) -> None:
        if payment_date is None:
            payment_date = dt.date.today()
        if notes is None:
            notes = ""
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                self._payments(self.data.id),
                json={
                    "amount": {
                        "amount": amount,
                        "currency": currency
                    },
                    "referenceId": reference_id,
                    "notes": notes,
                    "paymentDate": payment_date.strftime("%Y-%m-%d")
                },
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)

    @retry_on_401
    def get_penalties(self) -> List[Penalty]:
        with httpx.Client(base_url=self.base_url) as client:
            response = client.get(
                self._penalties(self.data.id),
                headers=self._header_builder(),
                timeout=30
            )
            raise_for_status_improved(response)
            return [Penalty.parse_obj(e) for e in response.json()]

    @retry_on_401
    def apply_waiver(self, waiver: dict) -> None:
        waiver = Waiver.parse_obj(waiver)
        with httpx.Client(base_url=self.base_url) as client:
            response = client.post(
                self._waivers(self.data.id),
                headers=self._header_builder(),
                json=waiver.dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            return None

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.id})"


class DebtsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            async_resource=DebtAsync,
            retrieve_data_model=DebtAPIDTO,
            create_data_model=None,
            update_data_model=None,
            resource="debts"
        )

    @retry_on_401_async
    async def create(self, flow_id: str, disbursement_date: Optional[str] = None, amount: Optional[dict] = None) -> str:
        if disbursement_date is not None:
            try:
                disbursement_date = dt.datetime.strptime(disbursement_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid disbursement date, must be in the format YYYY-MM-DD")
        if amount is not None:
            amount = Money.parse_obj(amount)

        create_debt = CreateDebt.parse_obj({
            "amount": amount.dict(by_alias=True) if amount else None,
            "disbursed_at": disbursement_date.strftime("%Y-%m-%d") if disbursement_date else None,
            "flow_id": flow_id,
        })
        async with httpx.AsyncClient(base_url=self.altscore_client._cms_base_url) as client:
            response = await client.post(
                f"/{self.resource_version}/{self.resource}",
                headers=self.build_headers(),
                json=create_debt.dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            response_json = response.json()
            return response_json.get("debtId")


class DebtsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(
            altscore_client=altscore_client,
            sync_resource=DebtSync,
            retrieve_data_model=DebtAPIDTO,
            create_data_model=None,
            update_data_model=None,
            resource="debts"
        )

    @retry_on_401
    def create(self, flow_id: str, disbursement_date: Optional[str] = None, amount: Optional[dict] = None) -> str:
        if disbursement_date is not None:
            try:
                disbursement_date = dt.datetime.strptime(disbursement_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid disbursement date, must be in the format YYYY-MM-DD")
        if amount is not None:
            amount = Money.parse_obj(amount)
        create_debt = CreateDebt.parse_obj({
            "amount": amount.dict(by_alias=True) if amount else None,
            "disbursed_at": disbursement_date.strftime("%Y-%m-%d") if disbursement_date else None,
            "flow_id": flow_id,
        })
        with httpx.Client(base_url=self.altscore_client._cms_base_url) as client:
            response = client.post(
                f"/{self.resource_version}/{self.resource}",
                headers=self.build_headers(),
                json=create_debt.dict(by_alias=True, exclude_none=True),
                timeout=30
            )
            raise_for_status_improved(response)
            response_json = response.json()
            return response_json.get("debtId")
