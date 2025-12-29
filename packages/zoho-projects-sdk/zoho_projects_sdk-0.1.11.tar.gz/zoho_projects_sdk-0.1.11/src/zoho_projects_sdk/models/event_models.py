from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Event(BaseModel):
    """
    Represents an event in Zoho Projects.
    """

    id: Optional[str] = Field(
        None, alias="event_id", description="Unique identifier for the event"
    )
    subject: str = Field(..., description="Subject or title of the event")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    start_date: Optional[datetime] = Field(
        None, description="Start date and time of the event"
    )
    end_date: Optional[datetime] = Field(
        None, description="End date and time of the event"
    )
    all_day: Optional[bool] = Field(
        False, description="Indicates if the event is an all-day event"
    )
    created_time: Optional[datetime] = Field(
        None, description="Time when the event was created"
    )
    modified_time: Optional[datetime] = Field(
        None, description="Time when the event was last modified"
    )
    owner: Optional[str] = Field(None, description="Owner of the event")
    attendees: Optional[List[Any]] = Field(
        default_factory=lambda: [], description="List of attendees for the event"
    )
    status: Optional[str] = Field(None, description="Status of the event")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class EventCreateRequest(BaseModel):
    """
    Request model for creating a new event.
    """

    subject: str = Field(..., description="Subject or title of the event")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    start_date: Optional[datetime] = Field(
        None, description="Start date and time of the event"
    )
    end_date: Optional[datetime] = Field(
        None, description="End date and time of the event"
    )
    all_day: Optional[bool] = Field(
        False, description="Indicates if the event is an all-day event"
    )
    attendees: Optional[List[Any]] = Field(
        default_factory=list, description="List of attendees for the event"
    )
    status: Optional[str] = Field(None, description="Status of the event")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class EventUpdateRequest(BaseModel):
    """
    Request model for updating an existing event.
    """

    subject: Optional[str] = Field(None, description="Subject or title of the event")
    description: Optional[str] = Field(None, description="Description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    start_date: Optional[datetime] = Field(
        None, description="Start date and time of the event"
    )
    end_date: Optional[datetime] = Field(
        None, description="End date and time of the event"
    )
    all_day: Optional[bool] = Field(
        None, description="Indicates if the event is an all-day event"
    )
    attendees: Optional[List[Any]] = Field(
        None, description="List of attendees for the event"
    )
    status: Optional[str] = Field(None, description="Status of the event")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
