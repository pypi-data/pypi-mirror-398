from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class AttachmentAPIDTO(BaseModel):
    id: str = Field(alias="id")
    url: Optional[str] = Field(alias="url", default=None)
    label: Optional[str] = Field(alias="label", default=None)
    file_extension: Optional[str] = Field(alias="fileExtension", default=None)
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata")
    created_at: str = Field(alias="createdAt", default=str)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class AttachmentInput(BaseModel):
    url: str = Field(alias="url")
    label: Optional[str] = Field(alias="label", default=None)
    file_extension: Optional[str] = Field(alias="fileExtension")
    metadata: Optional[dict] = Field(alias="metadata", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True
