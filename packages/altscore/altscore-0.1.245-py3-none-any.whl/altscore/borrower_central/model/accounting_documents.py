from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Union
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from altscore.borrower_central.model.accounting_amount import Amount

class DocumentDates(BaseModel):
    """
    Standardised date set for any accounting-related document.
    """
    issue_date: str = Field(
        alias="issueDate",
        description=(
            "Date the document was created / signed / CAE-stamped. "
            "Used for legal retention and tax‐book period."
        ),
    )
    posting_date: Optional[str] = Field(
        default=None,
        alias="postingDate",
        description=(
            "Date the document hit the general ledger (SAP “contable”). "
            "Controls accounting period close and revaluation runs."
        ),
    )
    due_date: Optional[str] = Field(
        default=None,
        alias="dueDate",
        description="Contractual deadline for payment; drives AP ageing and DSO.",
    )
    payment_date: Optional[str] = Field(
        default=None,
        alias="paymentDate",
        description=(
            "Actual settlement date when cash left or entered the company. "
            "Basis for cash-flow and realised FX gains/losses."
        ),
    )
    clearing_date: Optional[str] = Field(
        default=None,
        alias="clearingDate",
        description=(
            "Date the liability/receivable was cleared inside the ERP. "
            "May differ from payment_date (e.g. cheque deposited two days later)."
        ),
    )
    goods_receipt_date: Optional[str] = Field(
        default=None,
        alias="goodsReceiptDate",
        description="Physical arrival date of goods (GRN) for inventory documents.",
    )
    service_entry_date: Optional[str] = Field(
        default=None,
        alias="serviceEntryDate",
        description="Date a service was accepted (SES); used for accruals.",
    )
    tax_point_date: Optional[str] = Field(
        default=None,
        alias="taxPointDate",
        description=(
            "VAT ‘tax point’ / ‘date of supply’ when different from issue_date; "
            "relevant in UK/EU and some LATAM regimes."
        ),
    )
    value_date: Optional[str] = Field(
        default=None,
        alias="valueDate",
        description=(
            "Bank’s effective date for interest or FX on the payment "
            "(treasury forecasting and bank reconciliation)."
        ),
    )
    period_start: Optional[str] = Field(
        default=None,
        alias="periodStart",
        description="Start of the service/coverage period for periodic billing.",
    )
    period_end: Optional[str] = Field(
        default=None,
        alias="periodEnd",
        description="End of the service/coverage period for periodic billing.",
    )

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class AccountingDocumentAPIDTO(BaseModel):
    id: str = Field(alias="id")
    parent_document_id: Optional[str] = Field(alias="parentAccountingDocumentId", default=None)
    label: Optional[str] = Field(alias="label")
    key: str = Field(alias="key")
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    voucher: Optional[str] = Field(alias="voucher", default=None)
    reference_voucher: Optional[str] = Field(alias="referenceVoucher", default=None)
    producer_document_reference: Optional[str] = Field(alias="producerDocumentReference", default=None)
    receiver_document_reference: Optional[str] = Field(alias="receiverDocumentReference", default=None)
    is_outbound: bool = Field(alias="isOutbound")
    document_dates: Optional[DocumentDates] = Field(alias="documentDates", default=None)
    tags: List[str] = Field(alias="tags", default=[])
    raw_content: Optional[str] = Field(alias="rawContent", default=None)
    content: Optional[Dict[str, Any]] = Field(alias="content", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)
    amount: Optional[Amount] = Field(alias="amount", default=None)
    confidence_score: Optional[float] = Field(alias="confidenceScore", default=None)
    has_attachments: bool = Field(alias="hasAttachments")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateAccountingDocumentDTO(BaseModel):
    key: str = Field(alias="key")
    is_outbound: bool = Field(alias="isOutbound")
    parent_document_id: Optional[str] = Field(alias="parentAccountingDocumentId", default=None)
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    voucher: Optional[str] = Field(alias="voucher", default=None)
    reference_voucher: Optional[str] = Field(alias="referenceVoucher", default=None)
    producer_document_reference: Optional[str] = Field(alias="producerDocumentReference", default=None)
    receiver_document_reference: Optional[str] = Field(alias="receiverDocumentReference", default=None)
    document_dates: Union[Dict, DocumentDates, None] = Field(alias="documentDates", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=None)
    raw_content: Optional[str] = Field(alias="rawContent", default=None)
    content: Optional[Dict[str, Any]] = Field(alias="content", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)
    amount: Optional[Amount] = Field(alias="amount", default=None)
    confidence_score: Optional[float] = Field(alias="confidenceScore", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class UpdateAccountingDocumentDTO(BaseModel):
    is_outbound: Optional[bool] = Field(alias="isOutbound", default=None)
    parent_document_id: Optional[str] = Field(alias="parentAccountingDocumentId", default=None)
    borrower_id: Optional[str] = Field(alias="borrowerId", default=None)
    deal_id: Optional[str] = Field(alias="dealId", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    voucher: Optional[str] = Field(alias="voucher", default=None)
    reference_voucher: Optional[str] = Field(alias="referenceVoucher", default=None)
    producer_document_reference: Optional[str] = Field(alias="producerDocumentReference", default=None)
    receiver_document_reference: Optional[str] = Field(alias="receiverDocumentReference", default=None)
    document_dates: Union[Dict, DocumentDates, None] = Field(alias="documentDates", default=None)
    tags: Optional[List[str]] = Field(alias="tags", default=None)
    raw_content: Optional[str] = Field(alias="rawContent", default=None)
    content: Optional[Dict[str, Any]] = Field(alias="content", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata", default=None)
    amount: Optional[Amount] = Field(alias="amount", default=None)
    confidence_score: Optional[float] = Field(alias="confidenceScore", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class AccountingDocumentSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "accounting/documents", header_builder,
                         renew_token, AccountingDocumentAPIDTO.parse_obj(data))


class AccountingDocumentAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "accounting/documents", header_builder,
                         renew_token, AccountingDocumentAPIDTO.parse_obj(data))


class AccountingDocumentsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=AccountingDocumentSync,
                         retrieve_data_model=AccountingDocumentAPIDTO,
                         create_data_model=CreateAccountingDocumentDTO,
                         update_data_model=UpdateAccountingDocumentDTO,
                         resource="accounting/documents")


class AccountingDocumentsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=AccountingDocumentAsync,
                         retrieve_data_model=AccountingDocumentAPIDTO,
                         create_data_model=CreateAccountingDocumentDTO,
                         update_data_model=UpdateAccountingDocumentDTO,
                         resource="accounting/documents")
