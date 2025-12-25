from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    source_id: str = Field(alias="sourceId")
    version: str = Field(alias="version")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True
