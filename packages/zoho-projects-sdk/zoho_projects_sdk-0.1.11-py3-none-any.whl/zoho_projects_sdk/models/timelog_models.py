"""
Pydantic models for Zoho Projects API entities, such as timelogs.
"""

from typing import Any, Dict, Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class TimeLog(BaseModel):
    """
    A Pydantic model representing a timelog in Zoho Projects.
    """

    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, extra="allow"
    )

    id: int = Field(..., alias="id")
    date: str = Field(
        ..., alias="date", validation_alias=AliasChoices("date", "log_date")
    )
    log_hour: str = Field(
        ...,
        alias="log_hour",
        validation_alias=AliasChoices("log_hour", "log_time"),
    )
    non_billable_hours: Optional[str] = Field(None, alias="non_billable_hours")
    billable_hours: Optional[str] = Field(None, alias="billable_hours")
    total_hours: Optional[str] = Field(None, alias="total_hours")
    notes: Optional[str] = Field(
        None, alias="notes", validation_alias=AliasChoices("notes", "description")
    )
    created_time: Optional[str] = Field(None, alias="created_time")
    last_modified_time: Optional[str] = Field(None, alias="last_modified_time")
    billing_status: Optional[str] = Field(
        None, alias="billing_status"
    )  # e.g., "Billable", "Non-Billable"
    project: Optional[Dict[str, Any]] = Field(
        None, alias="project"
    )  # Project object with name, id
    module_detail: Optional[Dict[str, Any]] = Field(
        None, alias="module_detail"
    )  # Task/Module object
    owner: Optional[Dict[str, Any]] = Field(None, alias="owner")  # User object
    added_by: Optional[Dict[str, Any]] = Field(
        None, alias="added_by"
    )  # User object who added the log
    approval: Optional[Dict[str, Any]] = Field(
        None, alias="approval"
    )  # Approval details

    @field_validator("log_hour", mode="before")
    @classmethod
    def _normalise_log_hour(cls, value: Any) -> str:
        if isinstance(value, (int, float)):
            minutes = int(value)
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours:02d}:{remaining_minutes:02d}"
        return str(value)
