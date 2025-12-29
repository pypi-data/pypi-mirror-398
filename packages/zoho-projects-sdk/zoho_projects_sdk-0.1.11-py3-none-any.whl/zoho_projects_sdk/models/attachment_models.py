"""
Pydantic models for Zoho Projects Attachment API entities.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Attachment(BaseModel):
    """
    A Pydantic model representing an attachment in Zoho Projects.
    """

    id: Optional[int] = Field(None, alias="id")
    name: Optional[str] = Field(None, alias="name")
    size: Optional[int] = Field(None, alias="size")
    type: Optional[str] = Field(None, alias="type")
    url: Optional[str] = Field(None, alias="url")
    content_type: Optional[str] = Field(None, alias="content_type")
    download_url: Optional[str] = Field(None, alias="download_url")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    project_id: Optional[int] = Field(None, alias="project_id")
    owner_id: Optional[int] = Field(None, alias="owner_id")
    uploaded_by: Optional[Dict[str, Any]] = Field(None, alias="uploaded_by")
    description: Optional[str] = Field(None, alias="description")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
