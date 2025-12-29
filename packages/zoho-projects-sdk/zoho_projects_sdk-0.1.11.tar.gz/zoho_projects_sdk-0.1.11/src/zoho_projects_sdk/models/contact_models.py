"""
Pydantic models for Zoho Projects Contact API entities.
"""

from typing import Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Contact(BaseModel):
    """
    A Pydantic model representing a contact in Zoho Projects.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    email: Optional[str] = Field(None, alias="email")
    phone: Optional[str] = Field(None, alias="phone")
    mobile: Optional[str] = Field(None, alias="mobile")
    department: Optional[str] = Field(None, alias="department")
    designation: Optional[str] = Field(None, alias="designation")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    client_id: Optional[int] = Field(None, alias="client_id")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
