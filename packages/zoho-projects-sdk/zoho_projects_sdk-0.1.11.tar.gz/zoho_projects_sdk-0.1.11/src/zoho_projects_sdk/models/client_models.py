"""
Pydantic models for Zoho Projects Client API entities.
"""

from typing import Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Client(BaseModel):
    """
    A Pydantic model representing a client in Zoho Projects.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    website: Optional[str] = Field(None, alias="website")
    email: Optional[str] = Field(None, alias="email")
    phone: Optional[str] = Field(None, alias="phone")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class ClientProject(BaseModel):
    """
    A Pydantic model representing a project associated with a client.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
