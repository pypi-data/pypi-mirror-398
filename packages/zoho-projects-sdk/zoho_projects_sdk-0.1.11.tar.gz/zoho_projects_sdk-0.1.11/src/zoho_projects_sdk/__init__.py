"""
zoho-projects-sdk: A modern, async, and type-safe SDK for the Zoho Projects API V3.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0"

from .api import (
    AttachmentsAPI,
    BaselinesAPI,
    BusinessHoursAPI,
    ClientsAPI,
    ContactsAPI,
    RolesAPI,
    TagsAPI,
)
from .client import ZohoProjects
from .models import (
    Attachment,
    Baseline,
    BusinessHour,
    BusinessHourUser,
    Client,
    ClientProject,
    Contact,
    Role,
    Tag,
)

__all__ = [
    "ZohoProjects",
    "BusinessHoursAPI",
    "BaselinesAPI",
    "AttachmentsAPI",
    "TagsAPI",
    "ClientsAPI",
    "ContactsAPI",
    "RolesAPI",
    "BusinessHour",
    "BusinessHourUser",
    "Baseline",
    "Attachment",
    "Tag",
    "Client",
    "ClientProject",
    "Contact",
    "Role",
]
