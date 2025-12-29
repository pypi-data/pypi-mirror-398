"""
Pydantic models for Zoho Projects Business Hours API entities.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class BusinessHour(BaseModel):
    """
    A Pydantic model representing a business hour in Zoho Projects.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    timezone: Optional[str] = Field(None, alias="timezone")
    work_days: Optional[List[str]] = Field(None, alias="work_days")
    work_hours: Optional[Dict[str, Any]] = Field(None, alias="work_hours")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class BusinessHourUser(BaseModel):
    """
    A Pydantic model representing a user associated with a business hour.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    email: Optional[str] = Field(None, alias="email")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
