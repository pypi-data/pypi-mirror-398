from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule


class Money(BaseModel):
    """
    Simple monetary object with string amount for precision
    """
    amount: str = Field(alias="amount", description="Amount as string to preserve precision")
    currency: str = Field(alias="currency", description="ISO-4217 currency code")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BankAccountAPIDTO(BaseModel):
    """
    Bank account information for tenant-level financial operations
    """
    id: str = Field(alias="id", description="Unique bank account identifier")
    account_number: str = Field(alias="accountNumber", description="Bank account number")
    account_name: str = Field(alias="accountName", description="Display name for the account")
    bank_name: str = Field(alias="bankName", description="Financial institution name")
    bank_code: Optional[str] = Field(alias="bankCode", default=None, description="Bank routing or swift code")
    currency: str = Field(alias="currency", description="Account's primary currency")
    account_type: Optional[str] = Field(alias="accountType", default=None, description="Account type: checking, savings, etc.")
    is_active: bool = Field(alias="isActive", default=True, description="Whether the account is active")
    account_status: Optional[str] = Field(alias="accountStatus", default=None, description="Current account status")
    tags: List[str] = Field(alias="tags", default_factory=list, description="Classification tags")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None, description="Additional custom data")
    created_at: str = Field(alias="createdAt", description="Account creation timestamp")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None, description="Last update timestamp")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateBankAccountDTO(BaseModel):
    """
    Request payload for creating a new bank account
    """
    account_number: str = Field(alias="accountNumber")
    account_name: str = Field(alias="accountName")
    bank_name: str = Field(alias="bankName")
    bank_code: Optional[str] = Field(alias="bankCode", default=None)
    currency: str = Field(alias="currency")
    account_type: Optional[str] = Field(alias="accountType", default=None)
    is_active: bool = Field(alias="isActive", default=True)
    account_status: Optional[str] = Field(alias="accountStatus", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateBankAccountDTO(BaseModel):
    """
    Request payload for updating an existing bank account
    """
    account_name: Optional[str] = Field(alias="accountName", default=None)
    bank_name: Optional[str] = Field(alias="bankName", default=None)
    bank_code: Optional[str] = Field(alias="bankCode", default=None)
    account_type: Optional[str] = Field(alias="accountType", default=None)
    is_active: Optional[bool] = Field(alias="isActive", default=None)
    account_status: Optional[str] = Field(alias="accountStatus", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BankAccountSync(GenericSyncResource):
    """
    Synchronous resource for bank account operations
    """
    
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "banking/accounts", header_builder,
                         renew_token, BankAccountAPIDTO.parse_obj(data))


class BankAccountAsync(GenericAsyncResource):
    """
    Asynchronous resource for bank account operations
    """
    
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "banking/accounts", header_builder,
                         renew_token, BankAccountAPIDTO.parse_obj(data))


class BankAccountsSyncModule(GenericSyncModule):
    """
    Synchronous module for bank account management
    """
    
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=BankAccountSync,
                         retrieve_data_model=BankAccountAPIDTO,
                         create_data_model=CreateBankAccountDTO,
                         update_data_model=UpdateBankAccountDTO,
                         resource="banking/accounts")

class BankAccountsAsyncModule(GenericAsyncModule):
    """
    Asynchronous module for bank account management
    """
    
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=BankAccountAsync,
                         retrieve_data_model=BankAccountAPIDTO,
                         create_data_model=CreateBankAccountDTO,
                         update_data_model=UpdateBankAccountDTO,
                         resource="banking/accounts")