"""Modules for interacting with Zoho Projects API entities."""

from .attachments import AttachmentsAPI
from .baselines import BaselinesAPI
from .business_hours import BusinessHoursAPI
from .clients import ClientsAPI
from .comments import CommentsAPI
from .contacts import ContactsAPI
from .events import EventsAPI
from .issues import IssuesAPI
from .milestones import MilestonesAPI
from .phases import PhasesAPI
from .portals import PortalsAPI
from .projects import ProjectsAPI
from .roles import RolesAPI
from .tags import TagsAPI
from .tasklists import TasklistsAPI
from .tasks import TasksAPI
from .timelogs import TimelogsAPI
from .users import UsersAPI

__all__ = [
    "ProjectsAPI",
    "PortalsAPI",
    "TasksAPI",
    "TasklistsAPI",
    "IssuesAPI",
    "UsersAPI",
    "TimelogsAPI",
    "CommentsAPI",
    "EventsAPI",
    "MilestonesAPI",
    "PhasesAPI",
    "BusinessHoursAPI",
    "BaselinesAPI",
    "AttachmentsAPI",
    "TagsAPI",
    "ClientsAPI",
    "ContactsAPI",
    "RolesAPI",
]
