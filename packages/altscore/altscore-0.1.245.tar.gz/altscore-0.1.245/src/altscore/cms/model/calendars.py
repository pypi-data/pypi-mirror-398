from typing import Optional, List
from pydantic import BaseModel, Field


class CalendarHoliday(BaseModel):
    day: int = Field(alias="day")
    month: str = Field(alias="month")


class DPACalendarAPIDTO(BaseModel):
    id: str = Field(alias="calendarId")
    name: str = Field(alias="name")
    description: Optional[str] = Field(alias="description", default=None)
    exclusionDays: Optional[List[str]] = Field(alias="exclusionDays", default=None)
    holidays: Optional[List[CalendarHoliday]] = Field(alias="holidays", default=None)
    type: str = Field(alias="type")
    year: int = Field(alias="year")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True


class CreateCalendarAPIDTO(BaseModel):
    name: str = Field(alias="name")
    description: Optional[str] = Field(alias="description", default=None)
    exclusionDays: Optional[List[str]] = Field(alias="exclusionDays", default=None)
    holidays: Optional[List[str]] = Field(alias="holidays", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        populate_by_alias = True
