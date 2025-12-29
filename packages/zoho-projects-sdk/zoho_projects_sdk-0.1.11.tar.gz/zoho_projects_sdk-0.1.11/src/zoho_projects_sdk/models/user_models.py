"""
Pydantic models for Zoho Projects API entities, such as users.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class User(BaseModel):
    """
    A Pydantic model representing a user in Zoho Projects.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Union[str, int] = Field(..., alias="id")
    zuid: Optional[str] = Field(None, alias="zuid")  # Zoho unique ID
    name: str = Field(..., alias="name")
    first_name: Optional[str] = Field(None, alias="first_name")
    last_name: Optional[str] = Field(None, alias="last_name")
    display_name: Optional[str] = Field(None, alias="display_name")
    email: str = Field(..., alias="email")
    status: Optional[str] = Field(None, alias="status")
    user_type: Optional[str] = Field(None, alias="user_type")
    is_active: Optional[bool] = Field(None, alias="is_active")
    is_confirmed: Optional[bool] = Field(None, alias="is_confirmed")
    added_time: Optional[str] = Field(None, alias="added_time")
    updated_time: Optional[str] = Field(None, alias="updated_time")
    profile: Optional[Dict[str, Any]] = Field(
        None, alias="profile"
    )  # Profile object with name, id, type
    full_name: Optional[str] = Field(None, alias="full_name")
    cost_per_hour: Optional[str] = Field(None, alias="cost_per_hour")
    cost_rate: Optional[str] = Field(None, alias="costRate")
    invoice: Optional[str] = Field(None, alias="invoice")
    zohocrm_contact_id: Optional[str] = Field(None, alias="zohocrm_contact_id")
    projects: Optional[List[Dict[str, Any]]] = Field(None, alias="projects")
