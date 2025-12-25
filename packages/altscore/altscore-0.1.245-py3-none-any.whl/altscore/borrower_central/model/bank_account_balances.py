from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from altscore.borrower_central.model.bank_accounts import Money


class BankAccountBalanceAPIDTO(BaseModel):
    """
    Bank account balance information at a specific point in time
    """
    id: str = Field(alias="id", description="Unique balance record identifier")
    bank_account_id: str = Field(alias="bankAccountId", description="Associated bank account ID")
    current_balance: Money = Field(alias="currentBalance", description="Current available balance")
    available_balance: Optional[Money] = Field(alias="availableBalance", default=None, description="Available for transactions")
    ledger_balance: Optional[Money] = Field(alias="ledgerBalance", default=None, description="Book balance including pending")
    balance_date: str = Field(alias="balanceDate", description="Date this balance is effective")
    effective_date: Optional[str] = Field(alias="effectiveDate", default=None, description="When balance becomes effective")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None, description="Additional custom data")
    created_at: str = Field(alias="createdAt", description="Balance record creation timestamp")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None, description="Last update timestamp")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateBankAccountBalanceDTO(BaseModel):
    """
    Request payload for creating a new bank account balance record
    """
    bank_account_id: str = Field(alias="bankAccountId")
    current_balance: Money = Field(alias="currentBalance")
    available_balance: Optional[Money] = Field(alias="availableBalance", default=None)
    ledger_balance: Optional[Money] = Field(alias="ledgerBalance", default=None)
    balance_date: str = Field(alias="balanceDate", description="Date in YYYY-MM-DD format")
    effective_date: Optional[str] = Field(alias="effectiveDate", default=None, description="Date in YYYY-MM-DD format")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateBankAccountBalanceDTO(BaseModel):
    """
    Request payload for updating an existing bank account balance record
    """
    current_balance: Optional[Money] = Field(alias="currentBalance", default=None)
    available_balance: Optional[Money] = Field(alias="availableBalance", default=None)
    ledger_balance: Optional[Money] = Field(alias="ledgerBalance", default=None)
    balance_date: Optional[str] = Field(alias="balanceDate", default=None, description="Date in YYYY-MM-DD format")
    effective_date: Optional[str] = Field(alias="effectiveDate", default=None, description="Date in YYYY-MM-DD format")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BankAccountBalanceSync(GenericSyncResource):
    """
    Synchronous resource for bank account balance operations
    """
    
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "banking/account-balances", header_builder,
                         renew_token, BankAccountBalanceAPIDTO.parse_obj(data))


class BankAccountBalanceAsync(GenericAsyncResource):
    """
    Asynchronous resource for bank account balance operations
    """
    
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "banking/account-balances", header_builder,
                         renew_token, BankAccountBalanceAPIDTO.parse_obj(data))


class BankAccountBalancesSyncModule(GenericSyncModule):
    """
    Synchronous module for bank account balance management
    """
    
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=BankAccountBalanceSync,
                         retrieve_data_model=BankAccountBalanceAPIDTO,
                         create_data_model=CreateBankAccountBalanceDTO,
                         update_data_model=UpdateBankAccountBalanceDTO,
                         resource="banking/account-balances")

class BankAccountBalancesAsyncModule(GenericAsyncModule):
    """
    Asynchronous module for bank account balance management
    """
    
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=BankAccountBalanceAsync,
                         retrieve_data_model=BankAccountBalanceAPIDTO,
                         create_data_model=CreateBankAccountBalanceDTO,
                         update_data_model=UpdateBankAccountBalanceDTO,
                         resource="banking/account-balances")