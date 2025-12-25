import httpx
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from altscore.common.http_errors import raise_for_status_improved, retry_on_401, retry_on_401_async
from altscore.borrower_central.helpers import build_headers


class ValidationErrorLocation(BaseModel):
    row: Optional[int] = Field(alias="row", default=None)
    column: Optional[str] = Field(alias="column", default=None)
    field: Optional[str] = Field(alias="field", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ValidationError(BaseModel):
    location: ValidationErrorLocation = Field(alias="location")
    value: Any = Field(alias="value")
    message: str = Field(alias="message")
    error_type: Optional[str] = Field(alias="errorType", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ValidationResult(BaseModel):
    success: bool = Field(alias="success")
    errors: List[ValidationError] = Field(alias="errors", default=[])

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True


class InputValidationSyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def build_headers(self):
        return build_headers(self)

    @retry_on_401
    def validate_single(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        language: str = "en"
    ) -> ValidationResult:
        """
        Validate a single JSON object against a JSON schema.

        Args:
            data: The JSON object to validate
            schema: JSON Schema definition
            language: Language for error messages (default: "en")

        Returns:
            ValidationResult with success status and any validation errors
        """
        url = f"{self.altscore_client._borrower_central_base_url}/v1/input-validation/"

        payload = {
            "data": data,
            "schema": schema,
            "language": language
        }

        with httpx.Client() as client:
            response = client.post(
                url,
                headers=self.build_headers(),
                json=payload,
                timeout=30
            )
            raise_for_status_improved(response)
            return ValidationResult.parse_obj(response.json())


class InputValidationAsyncModule:

    def __init__(self, altscore_client):
        self.altscore_client = altscore_client

    def build_headers(self):
        return build_headers(self)

    @retry_on_401_async
    async def validate_single(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        language: str = "en"
    ) -> ValidationResult:
        """
        Validate a single JSON object against a JSON schema.

        Args:
            data: The JSON object to validate
            schema: JSON Schema definition
            language: Language for error messages (default: "en")

        Returns:
            ValidationResult with success status and any validation errors
        """
        url = f"{self.altscore_client._borrower_central_base_url}/v1/input-validation/"

        payload = {
            "data": data,
            "schema": schema,
            "language": language
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.build_headers(),
                json=payload,
                timeout=30
            )
            raise_for_status_improved(response)
            return ValidationResult.parse_obj(response.json())
