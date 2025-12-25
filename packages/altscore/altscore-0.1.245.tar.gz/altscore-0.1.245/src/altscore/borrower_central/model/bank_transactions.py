from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from altscore.borrower_central.model.bank_accounts import Money


class TransactionDates(BaseModel):
    """
    Date information for bank transactions
    """
    transaction_date: str = Field(
        alias="transactionDate",
        description="Date when the transaction occurred"
    )
    posting_date: Optional[str] = Field(
        default=None,
        alias="postingDate", 
        description="Date when transaction was posted to account"
    )


    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BankTransactionAPIDTO(BaseModel):
    """
    Bank transaction record with comprehensive transaction details
    """
    id: str = Field(alias="id", description="Unique transaction identifier")
    bank_account_id: str = Field(alias="bankAccountId", description="Associated bank account ID")
    transaction_type: str = Field(alias="transactionType", description="Type of transaction: debit, credit, transfer, etc.")
    amount: Money = Field(alias="amount", description="Transaction amount")
    running_balance: Optional[Money] = Field(alias="runningBalance", default=None, description="Account balance after transaction")
    description: Optional[str] = Field(alias="description", default=None, description="Transaction description")
    reference_number: Optional[str] = Field(alias="referenceNumber", default=None, description="Bank reference number")
    counterparty_name: Optional[str] = Field(alias="counterpartyName", default=None, description="Other party in transaction")
    counterparty_account: Optional[str] = Field(alias="counterpartyAccount", default=None, description="Other party's account")
    transaction_dates: TransactionDates = Field(alias="transactionDates", description="Transaction date information")
    parsed_raw: Optional[Dict[str, Any]] = Field(alias="parsedRaw", default=None, description="Parsed raw transaction data")
    confidence_score: Optional[float] = Field(alias="confidenceScore", default=None, description="Parsing confidence score")
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None, description="Additional custom data")
    created_at: str = Field(alias="createdAt", description="Transaction record creation timestamp")
    updated_at: Optional[str] = Field(alias="updatedAt", default=None, description="Last update timestamp")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateBankTransactionDTO(BaseModel):
    """
    Request payload for creating a new bank transaction record
    """
    bank_account_id: str = Field(alias="bankAccountId")
    transaction_type: str = Field(alias="transactionType")
    amount: Money = Field(alias="amount")
    running_balance: Optional[Money] = Field(alias="runningBalance", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    reference_number: Optional[str] = Field(alias="referenceNumber", default=None)
    counterparty_name: Optional[str] = Field(alias="counterpartyName", default=None)
    counterparty_account: Optional[str] = Field(alias="counterpartyAccount", default=None)
    transaction_dates: TransactionDates = Field(alias="transactionDates")
    parsed_raw: Optional[Dict[str, Any]] = Field(alias="parsedRaw", default=None)
    confidence_score: Optional[float] = Field(alias="confidenceScore", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateBankTransactionDTO(BaseModel):
    """
    Request payload for updating an existing bank transaction record
    """
    transaction_type: Optional[str] = Field(alias="transactionType", default=None)
    amount: Optional[Money] = Field(alias="amount", default=None)
    running_balance: Optional[Money] = Field(alias="runningBalance", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    counterparty_name: Optional[str] = Field(alias="counterpartyName", default=None)
    counterparty_account: Optional[str] = Field(alias="counterpartyAccount", default=None)
    transaction_dates: Optional[TransactionDates] = Field(alias="transactionDates", default=None)
    parsed_raw: Optional[Dict[str, Any]] = Field(alias="parsedRaw", default=None)
    confidence_score: Optional[float] = Field(alias="confidenceScore", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class BankTransactionSync(GenericSyncResource):
    """
    Synchronous resource for bank transaction operations
    """
    
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "banking/transactions", header_builder,
                         renew_token, BankTransactionAPIDTO.parse_obj(data))


class BankTransactionAsync(GenericAsyncResource):
    """
    Asynchronous resource for bank transaction operations
    """
    
    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "banking/transactions", header_builder,
                         renew_token, BankTransactionAPIDTO.parse_obj(data))


class BankTransactionsSyncModule(GenericSyncModule):
    """
    Synchronous module for bank transaction management
    """
    
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=BankTransactionSync,
                         retrieve_data_model=BankTransactionAPIDTO,
                         create_data_model=CreateBankTransactionDTO,
                         update_data_model=UpdateBankTransactionDTO,
                         resource="banking/transactions")

class BankTransactionsAsyncModule(GenericAsyncModule):
    """
    Asynchronous module for bank transaction management
    """
    
    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=BankTransactionAsync,
                         retrieve_data_model=BankTransactionAPIDTO,
                         create_data_model=CreateBankTransactionDTO,
                         update_data_model=UpdateBankTransactionDTO,
                         resource="banking/transactions")