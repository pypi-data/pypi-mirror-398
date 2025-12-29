"""
Pydantic models for Zoho Projects Baseline API entities.
"""

from typing import Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Baseline(BaseModel):
    """
    A Pydantic model representing a baseline in Zoho Projects.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    project_id: Optional[int] = Field(None, alias="project_id")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
