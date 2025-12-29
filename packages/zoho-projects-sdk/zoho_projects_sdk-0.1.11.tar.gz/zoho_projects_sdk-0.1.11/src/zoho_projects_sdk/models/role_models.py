"""
Pydantic models for Zoho Projects Role API entities.
"""

from typing import Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Role(BaseModel):
    """
    A Pydantic model representing a role in Zoho Projects.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
