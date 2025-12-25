from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from altscore.borrower_central.model.generics import GenericSyncResource, GenericAsyncResource, \
    GenericSyncModule, GenericAsyncModule
from altscore.borrower_central.model.accounting_amount import Amount


class LineItemAPIDTO(BaseModel):
    id: str = Field(alias="id")
    item_id: str = Field(alias="itemId")
    line_number_in_source: Optional[int] = Field(default=None, alias="lineNumberInSource")
    accounting_document_id: str = Field(alias="accountingDocumentId")
    item_code: Optional[str] = Field(default=None, alias="itemCode",
                                     description="Item code, if the item is not an stockable with sku")
    sku: Optional[str] = Field(default=None, alias="sku", description="Product / material code")
    description: Optional[str] = Field(default=None, alias="description")
    qty_raw: Optional[str] = Field(default=None, alias="qtyRaw", description="Quantity involved")
    qty_normalized: Optional[float] = Field(default=None, alias="qtyNormalized", description="Quantity involved")
    qty_unit: Optional[str] = Field(default=None, alias="qtyUnit", description="Unit of measure for quantity")
    unit_price: Optional[str] = Field(default=None, alias="unitPrice")
    unit_price_currency: Optional[str] = Field(default=None, alias="unitPriceCurrency")
    amount: Optional[Amount] = Field(default=None, alias="amount", description="amount")
    parsed_raw: Optional[Dict[str, Any]] = Field(default=None, alias="parsedRaw")
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    # Variance
    is_variance: Optional[bool] = Field(default=None, alias="isVariance")
    variance_kind: Optional[str] = Field(
        default=None,
        alias="varianceKind",
        description="PRICE, QUANTITY, BOTH"
    )
    variance_reason: Optional[str] = Field(
        default=None, alias="varianceReason",
        description="Reason for variance"
    )
    reference_unit_price: Optional[str] = Field(
        default=None, alias="referenceUnitPrice",
        description="Price from PO / contract (for PRICE variance)"
    )
    reference_amount: Optional[Amount] = Field(
        default=None, alias="referenceAmount",
        description="Reference amount from PO or internal"
    )
    reference_qty_raw: Optional[str] = Field(
        default=None, alias="referenceQtyRaw",
        description="Expected quantity (for QUANTITY variance)"
    )
    reference_qty_normalized: Optional[float] = Field(
        default=None, alias="referenceQtyNormalized",
        description="Expected quantity (for QUANTITY variance)"
    )
    # Return
    is_return: Optional[bool] = Field(default=None, alias="isReturn")
    reason_code: Optional[str] = Field(
        default=None, alias="reasonCode",
        description="Damaged, expired, decomiso, etc."
    )
    # Rebate
    is_rebate: Optional[bool] = Field(default=None, alias="isRebate")
    agreement_id: Optional[str] = Field(
        default=None, alias="agreementId",
        description="ID of trade-promotion / rebate contract"
    )
    period_start: Optional[str] = Field(
        default=None, alias="periodStart",
        description="Start of accrual period (yyyy-mm-dd)"
    )
    period_end: Optional[str] = Field(
        default=None, alias="periodEnd",
        description="End of accrual period (yyyy-mm-dd)"
    )
    # Parsing confidence
    confidence_score: Optional[float] = Field(
        default=None, alias="confidenceScore",
        description="Confidence score for parsing"
    )
    # Created and updated at
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class CreateLineItemDTO(BaseModel):
    accounting_document_id: str = Field(alias="accountingDocumentId")
    line_number_in_source: Optional[int] = Field(default=None, alias="lineNumberInSource")
    description: Optional[str] = Field(default=None, alias="description")
    qty_raw: Optional[str] = Field(default=None, alias="qtyRaw")
    qty_normalized: Optional[float] = Field(default=None, alias="qtyNormalized")
    qty_unit: Optional[str] = Field(default=None, alias="qtyUnit")
    unit_price: Optional[str] = Field(default=None, alias="unitPrice")
    unit_price_currency: Optional[str] = Field(default=None, alias="unitPriceCurrency")
    amount: Optional[Amount] = Field(default=None, alias="amount")
    sku: Optional[str] = Field(default=None, alias="sku")
    item_code: Optional[str] = Field(default=None, alias="itemCode")
    parsed_raw: Optional[Dict[str, Any]] = Field(default=None, alias="parsedRaw")
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    # Variance fields
    is_variance: Optional[bool] = Field(default=None, alias="isVariance")
    variance_kind: Optional[str] = Field(default=None, alias="varianceKind")
    variance_reason: Optional[str] = Field(default=None, alias="varianceReason")
    reference_unit_price: Optional[str] = Field(default=None, alias="referenceUnitPrice")
    reference_amount: Optional[Amount] = Field(default=None, alias="referenceAmount")
    reference_qty_raw: Optional[str] = Field(default=None, alias="referenceQtyRaw")
    reference_qty_normalized: Optional[float] = Field(default=None, alias="referenceQtyNormalized")
    # Return fields
    is_return: Optional[bool] = Field(default=None, alias="isReturn")
    reason_code: Optional[str] = Field(default=None, alias="reasonCode")
    # Rebate fields
    is_rebate: Optional[bool] = Field(default=None, alias="isRebate")
    agreement_id: Optional[str] = Field(default=None, alias="agreementId")
    period_start: Optional[str] = Field(default=None, alias="periodStart")
    period_end: Optional[str] = Field(default=None, alias="periodEnd")
    # Parsing confidence
    confidence_score: Optional[float] = Field(default=None, alias="confidenceScore")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True

class UpdateLineItemDTO(BaseModel):
    line_number_in_source: Optional[int] = Field(default=None, alias="lineNumberInSource")
    description: Optional[str] = Field(default=None, alias="description")
    qty_raw: Optional[str] = Field(default=None, alias="qtyRaw")
    qty_normalized: Optional[float] = Field(default=None, alias="qtyNormalized")
    qty_unit: Optional[str] = Field(default=None, alias="qtyUnit")
    unit_price: Optional[str] = Field(default=None, alias="unitPrice")
    unit_price_currency: Optional[str] = Field(default=None, alias="unitPriceCurrency")
    amount: Optional[Amount] = Field(default=None, alias="amount")
    sku: Optional[str] = Field(default=None, alias="sku")
    item_code: Optional[str] = Field(default=None, alias="itemCode")
    parsed_raw: Optional[Dict[str, Any]] = Field(default=None, alias="parsedRaw")
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    # Variance fields
    is_variance: Optional[bool] = Field(default=None, alias="isVariance")
    variance_kind: Optional[str] = Field(default=None, alias="varianceKind")
    variance_reason: Optional[str] = Field(default=None, alias="varianceReason")
    reference_unit_price: Optional[str] = Field(default=None, alias="referenceUnitPrice")
    reference_amount: Optional[Amount] = Field(default=None, alias="referenceAmount")
    reference_qty_raw: Optional[str] = Field(default=None, alias="referenceQtyRaw")
    reference_qty_normalized: Optional[float] = Field(default=None, alias="referenceQtyNormalized")
    # Return fields
    is_return: Optional[bool] = Field(default=None, alias="isReturn")
    reason_code: Optional[str] = Field(default=None, alias="reasonCode")
    # Rebate fields
    is_rebate: Optional[bool] = Field(default=None, alias="isRebate")
    agreement_id: Optional[str] = Field(default=None, alias="agreementId")
    period_start: Optional[str] = Field(default=None, alias="periodStart")
    period_end: Optional[str] = Field(default=None, alias="periodEnd")
    # Parsing confidence
    confidence_score: Optional[float] = Field(default=None, alias="confidenceScore")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True



class LineItemSync(GenericSyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "accounting/line-items", header_builder,
                         renew_token, LineItemAPIDTO.parse_obj(data))


class LineItemAsync(GenericAsyncResource):

    def __init__(self, base_url, header_builder, renew_token, data: Dict):
        super().__init__(base_url, "accounting/line-items", header_builder,
                         renew_token, LineItemAPIDTO.parse_obj(data))


class LineItemsSyncModule(GenericSyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         sync_resource=LineItemSync,
                         retrieve_data_model=LineItemAPIDTO,
                         create_data_model=CreateLineItemDTO,
                         update_data_model=UpdateLineItemDTO,
                         resource="accounting/line-items")


class LineItemsAsyncModule(GenericAsyncModule):

    def __init__(self, altscore_client):
        super().__init__(altscore_client,
                         async_resource=LineItemAsync,
                         retrieve_data_model=LineItemAPIDTO,
                         create_data_model=CreateLineItemDTO,
                         update_data_model=UpdateLineItemDTO,
                         resource="accounting/line-items")

