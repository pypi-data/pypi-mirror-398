"""
Pydantic models for Zoho Projects API entities, such as projects.
"""

from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class ProjectStatus(BaseModel):
    """Model for project status information."""

    id: str = Field(..., alias="id")
    name: str = Field(..., alias="name")
    color: Optional[str] = Field(None, alias="color")
    color_hexcode: Optional[str] = Field(None, alias="color_hexcode")
    is_closed_type: Optional[bool] = Field(None, alias="is_closed_type")


class Project(BaseModel):
    """
    A Pydantic model representing a project in Zoho Projects.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: int = Field(..., alias="id")
    name: str = Field(..., alias="name")
    status: Union[ProjectStatus, str] = Field(..., alias="status")
    description: Optional[str] = Field(None, alias="description")
    created_time: Optional[str] = Field(None, alias="created_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    owner: Optional[Dict[str, Any]] = Field(None, alias="owner")  # Zoho user details
    portal_id: Optional[str] = Field(None, alias="portal_id")
    prefix: Optional[str] = Field(None, alias="prefix")
    is_active: Optional[bool] = Field(None, alias="is_active")

    # Additional fields from the actual API response
    key: Optional[str] = Field(None, alias="key")
    project_type: Optional[str] = Field(None, alias="project_type")
    is_public_project: Optional[bool] = Field(None, alias="is_public_project")
    is_strict_project: Optional[bool] = Field(None, alias="is_strict_project")
    created_by: Optional[Dict[str, Any]] = Field(None, alias="created_by")
    modified_time: Optional[str] = Field(None, alias="modified_time")
    updated_by: Optional[Dict[str, Any]] = Field(None, alias="updated_by")
    layout: Optional[Dict[str, Any]] = Field(None, alias="layout")
    business_hours_id: Optional[str] = Field(None, alias="business_hours_id")
    is_rollup_project: Optional[bool] = Field(None, alias="is_rollup_project")
    budget_info: Optional[Dict[str, Any]] = Field(None, alias="budget_info")
    project_group: Optional[Dict[str, Any]] = Field(None, alias="project_group")
    percent_complete: Optional[int] = Field(None, alias="percent_complete")
    tasks: Optional[Dict[str, Any]] = Field(None, alias="tasks")
    issues: Optional[Dict[str, Any]] = Field(None, alias="issues")
    milestones: Optional[Dict[str, Any]] = Field(None, alias="milestones")
    is_completed: Optional[bool] = Field(None, alias="is_completed")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Union[str, "ProjectStatus"]) -> "ProjectStatus":
        """Validate status field to handle both string and ProjectStatus objects."""
        if isinstance(v, str):
            # Convert string status to ProjectStatus object
            return ProjectStatus(
                id=v, name=v, color=None, color_hexcode=None, is_closed_type=None
            )
        return v

    @property
    def status_name(self) -> str:
        """Get the status name for backward compatibility."""
        if isinstance(self.status, str):
            return self.status
        if hasattr(self.status, "name"):
            return self.status.name
        return str(self.status)

    def __str__(self) -> str:
        """String representation for backward compatibility."""
        return f"Project(id={self.id}, name={self.name}, status={self.status_name})"
