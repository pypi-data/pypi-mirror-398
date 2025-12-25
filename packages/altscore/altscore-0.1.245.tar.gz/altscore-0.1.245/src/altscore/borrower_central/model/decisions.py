from pydantic import BaseModel, Field
from typing import Optional
import datetime as dt


class CurrentDecisionInExecution(BaseModel):
    decision_id: str = Field(alias="decisionId")
    key: str = Field(alias="key")
    decision_type: str = Field(alias="decisionType")
    principal_id: str = Field(alias="principalId")
    updated_at: str = Field(alias="updatedAt")


class PostDecisionToExecution(BaseModel):
    key: str = Field(alias="key")
    decision_type: str = Field(alias="decisionType")
    principal_id: Optional[str] = Field(alias="principalId")
    updated_at: Optional[dt.datetime] = Field(alias="updatedAt", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        allow_population_by_alias = True
