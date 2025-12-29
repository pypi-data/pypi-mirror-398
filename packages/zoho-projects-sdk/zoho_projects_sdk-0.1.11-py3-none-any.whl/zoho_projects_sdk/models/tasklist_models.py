"""
Pydantic models for Zoho Projects API entities, such as tasklists.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Tasklist(BaseModel):
    """
    A Pydantic model representing a tasklist in Zoho Projects.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: int = Field(..., alias="id")
    title: str = Field(
        ..., alias="title"
    )  # In API docs, tasklists use 'title' rather than 'name'
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    extra_data: Optional[Dict[str, Any]] = Field(
        None, alias="extra_data"
    )  # Contains flag, milestone, is_completed
    project: Optional[Dict[str, Any]] = Field(
        None, alias="project"
    )  # Project object with name, id, status
    entity_id: Optional[str] = Field(None, alias="entity_id")  # Tasklist ID
    module_info: Optional[Dict[str, Any]] = Field(
        None, alias="module_info"
    )  # Module info object
    created_by: Optional[Dict[str, Any]] = Field(
        None, alias="created_by"
    )  # User object
    tags: Optional[List[Dict[str, Any]]] = Field(None, alias="tags")
