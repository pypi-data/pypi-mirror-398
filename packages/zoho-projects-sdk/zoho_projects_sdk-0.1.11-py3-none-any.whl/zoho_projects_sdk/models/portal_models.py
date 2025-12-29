"""
Pydantic models for Zoho Projects API entities, such as portals.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Portal(BaseModel):
    """
    A Pydantic model representing a portal in Zoho Projects.
    This model is designed to be flexible, accommodating both summary and detailed
    portal information.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    # Required fields that are always present in API responses
    id: int = Field(..., description="Portal ID")
    name: str = Field(..., description="Portal name")

    # Optional fields that may or may not be present depending on the API endpoint
    description: Optional[str] = Field(None, description="Portal description")
    status: Optional[str] = Field(None, description="Portal status")
    created_time: Optional[str] = Field(None, description="Portal creation time")
    updated_time: Optional[str] = Field(None, description="Portal last update time")
    url: Optional[str] = Field(None, description="Portal URL")
    timezone: Optional[str] = Field(None, description="Portal timezone")
    locale: Optional[str] = Field(None, description="Portal locale")
    currency: Optional[str] = Field(None, description="Portal currency")
    company_name: Optional[str] = Field(None, description="Company name")
    company_address: Optional[str] = Field(None, description="Company address")
    company_phone: Optional[str] = Field(None, description="Company phone")
    company_website: Optional[str] = Field(None, description="Company website")

    # Custom attributes for extended functionality
    custom_attributes: Optional[Dict[str, Any]] = Field(
        None, description="Custom attributes"
    )
