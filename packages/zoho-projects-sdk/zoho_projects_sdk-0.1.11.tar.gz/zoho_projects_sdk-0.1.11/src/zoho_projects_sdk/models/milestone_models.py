from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Milestone(BaseModel):
    """
    Represents a milestone in Zoho Projects.
    """

    id: Optional[str] = Field(
        None, alias="milestone_id", description="Unique identifier for the milestone"
    )
    name: str = Field(..., description="Name of the milestone")
    description: Optional[str] = Field(None, description="Description of the milestone")
    start_date: Optional[datetime] = Field(
        None, description="Start date of the milestone"
    )
    due_date: Optional[datetime] = Field(None, description="Due date of the milestone")
    completed_date: Optional[datetime] = Field(
        None, description="Date when the milestone was completed"
    )
    status: Optional[str] = Field(
        None,
        description="Status of the milestone (e.g., Not Started, In Progress, "
        "Completed)",
    )
    owner: Optional[str] = Field(None, description="Owner of the milestone")
    created_time: Optional[datetime] = Field(
        None, description="Time when the milestone was created"
    )
    modified_time: Optional[datetime] = Field(
        None, description="Time when the milestone was last modified"
    )
    percent_complete: Optional[int] = Field(
        0, description="Percentage of completion for the milestone"
    )

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class MilestoneCreateRequest(BaseModel):
    """
    Request model for creating a new milestone.
    """

    name: str = Field(..., description="Name of the milestone")
    description: Optional[str] = Field(None, description="Description of the milestone")
    start_date: Optional[datetime] = Field(
        None, description="Start date of the milestone"
    )
    due_date: Optional[datetime] = Field(None, description="Due date of the milestone")
    owner: Optional[str] = Field(None, description="Owner of the milestone")
    status: Optional[str] = Field("Not Started", description="Status of the milestone")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class MilestoneUpdateRequest(BaseModel):
    """
    Request model for updating an existing milestone.
    """

    name: Optional[str] = Field(None, description="Name of the milestone")
    description: Optional[str] = Field(None, description="Description of the milestone")
    start_date: Optional[datetime] = Field(
        None, description="Start date of the milestone"
    )
    due_date: Optional[datetime] = Field(None, description="Due date of the milestone")
    completed_date: Optional[datetime] = Field(
        None, description="Date when the milestone was completed"
    )
    owner: Optional[str] = Field(None, description="Owner of the milestone")
    status: Optional[str] = Field(None, description="Status of the milestone")
    percent_complete: Optional[int] = Field(
        None, description="Percentage of completion for the milestone"
    )

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
