from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Phase(BaseModel):
    """
    Represents a phase in Zoho Projects.
    """

    id: Optional[str] = Field(
        None, alias="phase_id", description="Unique identifier for the phase"
    )
    name: str = Field(..., description="Name of the phase")
    description: Optional[str] = Field(None, description="Description of the phase")
    start_date: Optional[datetime] = Field(None, description="Start date of the phase")
    end_date: Optional[datetime] = Field(None, description="End date of the phase")
    status: Optional[str] = Field(
        None,
        description="Status of the phase (e.g., Not Started, In Progress, Completed)",
    )
    owner: Optional[str] = Field(None, description="Owner of the phase")
    created_time: Optional[datetime] = Field(
        None, description="Time when the phase was created"
    )
    modified_time: Optional[datetime] = Field(
        None, description="Time when the phase was last modified"
    )
    percent_complete: Optional[int] = Field(
        0, description="Percentage of completion for the phase"
    )
    sequence_number: Optional[int] = Field(
        None, description="Sequence number of the phase"
    )

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class PhaseCreateRequest(BaseModel):
    """
    Request model for creating a new phase.
    """

    name: str = Field(..., description="Name of the phase")
    description: Optional[str] = Field(None, description="Description of the phase")
    start_date: Optional[datetime] = Field(None, description="Start date of the phase")
    end_date: Optional[datetime] = Field(None, description="End date of the phase")
    owner: Optional[str] = Field(None, description="Owner of the phase")
    status: Optional[str] = Field("Not Started", description="Status of the phase")
    sequence_number: Optional[int] = Field(
        None, description="Sequence number of the phase"
    )

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class PhaseUpdateRequest(BaseModel):
    """
    Request model for updating an existing phase.
    """

    name: Optional[str] = Field(None, description="Name of the phase")
    description: Optional[str] = Field(None, description="Description of the phase")
    start_date: Optional[datetime] = Field(None, description="Start date of the phase")
    end_date: Optional[datetime] = Field(None, description="End date of the phase")
    owner: Optional[str] = Field(None, description="Owner of the phase")
    status: Optional[str] = Field(None, description="Status of the phase")
    percent_complete: Optional[int] = Field(
        None, description="Percentage of completion for the phase"
    )
    sequence_number: Optional[int] = Field(
        None, description="Sequence number of the phase"
    )

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
