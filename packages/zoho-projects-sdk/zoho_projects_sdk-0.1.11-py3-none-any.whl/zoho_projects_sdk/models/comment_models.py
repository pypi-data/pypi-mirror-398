"""
Pydantic models for Zoho Projects API entities, such as comments.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Comment(BaseModel):
    """
    A Pydantic model representing a comment in Zoho Projects.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: int = Field(..., alias="id")
    title: Optional[str] = Field(None, alias="title")  # Title of the comment
    content: Optional[str] = Field(
        None, alias="content"
    )  # Content may be in 'extra_data' or description
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    created_by: Optional[Dict[str, Any]] = Field(
        None, alias="created_by"
    )  # User object
    extra_data: Optional[Dict[str, Any]] = Field(
        None, alias="extra_data"
    )  # Additional data like content
    project: Optional[Dict[str, Any]] = Field(None, alias="project")  # Project object
    entity_id: Optional[str] = Field(
        None, alias="entity_id"
    )  # ID of the entity this comment is on
    tags: Optional[List[Dict[str, Any]]] = Field(
        None, alias="tags"
    )  # Tags associated with the comment
