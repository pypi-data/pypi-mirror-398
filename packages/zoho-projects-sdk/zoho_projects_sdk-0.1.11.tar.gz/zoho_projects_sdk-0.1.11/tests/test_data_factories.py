"""
Test data factories for creating consistent test data in the Zoho Projects SDK tests.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ProjectDataParams(BaseModel):  # noqa: PLR0902
    """Parameters for creating test project data."""

    project_id: Optional[str] = None
    name: Optional[str] = None
    description: str = "Test project description"
    status: str = "active"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class TaskDataParams(BaseModel):  # noqa: PLR0902
    """Parameters for creating test task data."""

    task_id: Optional[str] = None
    name: Optional[str] = None
    description: str = "Test task description"
    status: str = "not_started"
    priority: str = "medium"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None


class IssueDataParams(BaseModel):  # noqa: PLR0902
    """Parameters for creating test issue data."""

    issue_id: Optional[str] = None
    title: Optional[str] = None
    description: str = "Test issue description"
    status: str = "open"
    priority: str = "high"
    severity: str = "medium"
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None


class ContactDataParams(BaseModel):  # noqa: PLR0902
    """Parameters for creating test contact data."""

    contact_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    client_id: Optional[str] = None


class TimelogDataParams(BaseModel):  # noqa: PLR0902
    """Parameters for creating test timelog data."""

    timelog_id: Optional[str] = None
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    hours: float = 1.5
    minutes: int = 30
    log_date: Optional[str] = None
    description: str = "Test timelog description"


class AttachmentDataParams(BaseModel):
    """Parameters for creating test attachment data."""

    attachment_id: Optional[str] = None
    name: Optional[str] = None
    size: int = 1024
    url: str = "https://example.com/test_attachment.pdf"
    entity_id: Optional[str] = None
    entity_type: str = "task"


class BaselineDataParams(BaseModel):
    """Parameters for creating test baseline data."""

    baseline_id: Optional[str] = None
    name: Optional[str] = None
    project_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: str = "Test baseline description"


class EventDataParams(BaseModel):
    """Parameters for creating test event data."""

    event_id: Optional[str] = None
    title: Optional[str] = None
    description: str = "Test event description"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    project_id: Optional[str] = None


class MilestoneDataParams(BaseModel):
    """Parameters for creating test milestone data."""

    milestone_id: Optional[str] = None
    name: Optional[str] = None
    description: str = "Test milestone description"
    project_id: Optional[str] = None
    target_date: Optional[str] = None
    status: str = "not_started"


class PhaseDataParams(BaseModel):
    """Parameters for creating test phase data."""

    phase_id: Optional[str] = None
    name: Optional[str] = None
    description: str = "Test phase description"
    project_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "not_started"


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of specified length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def create_test_project_data(
    params: Optional[ProjectDataParams] = None,
) -> Dict[str, Any]:
    """Create test data for a project."""
    params = params or ProjectDataParams()

    project_id = params.project_id or generate_random_string(12)
    name = params.name or f"Test Project {generate_random_string(8)}"
    start_date = params.start_date or (datetime.now() - timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    end_date = params.end_date or (datetime.now() + timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )

    return {
        "project_id": project_id,
        "name": name,
        "description": params.description,
        "status": params.status,
        "start_date": start_date,
        "end_date": end_date,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_task_data(params: Optional[TaskDataParams] = None) -> Dict[str, Any]:
    """Create test data for a task."""
    params = params or TaskDataParams()

    task_id = params.task_id or generate_random_string(12)
    name = params.name or f"Test Task {generate_random_string(8)}"
    start_date = params.start_date or (datetime.now() - timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    end_date = params.end_date or (datetime.now() + timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    project_id = params.project_id or generate_random_string(12)
    assignee_id = params.assignee_id or generate_random_string(12)

    return {
        "task_id": task_id,
        "name": name,
        "description": params.description,
        "status": params.status,
        "priority": params.priority,
        "start_date": start_date,
        "end_date": end_date,
        "project_id": project_id,
        "assignee_id": assignee_id,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_issue_data(params: Optional[IssueDataParams] = None) -> Dict[str, Any]:
    """Create test data for an issue."""
    params = params or IssueDataParams()

    issue_id = params.issue_id or generate_random_string(12)
    title = params.title or f"Test Issue {generate_random_string(8)}"
    project_id = params.project_id or generate_random_string(12)
    assignee_id = params.assignee_id or generate_random_string(12)

    return {
        "issue_id": issue_id,
        "title": title,
        "description": params.description,
        "status": params.status,
        "priority": params.priority,
        "severity": params.severity,
        "project_id": project_id,
        "assignee_id": assignee_id,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_user_data(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
    role: str = "user",
    status: str = "active",
) -> Dict[str, Any]:
    """Create test data for a user."""
    if user_id is None:
        user_id = generate_random_string(12)
    if email is None:
        email = f"user_{generate_random_string(8)}@example.com"
    if name is None:
        name = f"Test User {generate_random_string(6)}"

    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "role": role,
        "status": status,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_client_data(
    client_id: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    website: Optional[str] = None,
) -> Dict[str, Any]:
    """Create test data for a client."""
    if client_id is None:
        client_id = generate_random_string(12)
    if name is None:
        name = f"Test Client {generate_random_string(8)}"
    if email is None:
        email = f"client_{generate_random_string(8)}@example.com"
    if phone is None:
        phone = (
            f"+1-{random.randint(100, 999)}-"
            f"{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        )
    if website is None:
        website = f"https://www.{generate_random_string(8)}.com"

    return {
        "client_id": client_id,
        "name": name,
        "email": email,
        "phone": phone,
        "website": website,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_contact_data(
    params: Optional[ContactDataParams] = None,
) -> Dict[str, Any]:
    """Create test data for a contact."""
    params = params or ContactDataParams()

    contact_id = params.contact_id or generate_random_string(12)
    first_name = params.first_name or f"TestFirst{generate_random_string(6)}"
    last_name = params.last_name or f"TestLast{generate_random_string(6)}"
    email = params.email or f"contact_{generate_random_string(8)}@example.com"
    phone = params.phone or (
        f"+1-{random.randint(100, 999)}-"
        f"{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    )
    client_id = params.client_id or generate_random_string(12)

    return {
        "contact_id": contact_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "client_id": client_id,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_portal_data(
    portal_id: Optional[str] = None,
    name: Optional[str] = None,
    description: str = "Test portal description",
) -> Dict[str, Any]:
    """Create test data for a portal."""
    if portal_id is None:
        portal_id = generate_random_string(12)
    if name is None:
        name = f"Test Portal {generate_random_string(8)}"

    return {
        "portal_id": portal_id,
        "name": name,
        "description": description,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_role_data(
    role_id: Optional[str] = None,
    name: Optional[str] = None,
    description: str = "Test role description",
) -> Dict[str, Any]:
    """Create test data for a role."""
    if role_id is None:
        role_id = generate_random_string(12)
    if name is None:
        name = f"Test Role {generate_random_string(8)}"

    return {
        "role_id": role_id,
        "name": name,
        "description": description,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_tag_data(
    tag_id: Optional[str] = None,
    name: Optional[str] = None,
    color: str = "#FF0000",
) -> Dict[str, Any]:
    """Create test data for a tag."""
    if tag_id is None:
        tag_id = generate_random_string(12)
    if name is None:
        name = f"Test Tag {generate_random_string(8)}"

    return {
        "tag_id": tag_id,
        "name": name,
        "color": color,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_tasklist_data(
    tasklist_id: Optional[str] = None,
    name: Optional[str] = None,
    description: str = "Test tasklist description",
    project_id: Optional[str] = None,
    status: str = "active",
) -> Dict[str, Any]:
    """Create test data for a tasklist."""
    if tasklist_id is None:
        tasklist_id = generate_random_string(12)
    if name is None:
        name = f"Test Tasklist {generate_random_string(8)}"
    if project_id is None:
        project_id = generate_random_string(12)

    return {
        "tasklist_id": tasklist_id,
        "name": name,
        "description": description,
        "project_id": project_id,
        "status": status,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_timelog_data(
    params: Optional[TimelogDataParams] = None,
) -> Dict[str, Any]:
    """Create test data for a timelog."""
    params = params or TimelogDataParams()

    timelog_id = params.timelog_id or generate_random_string(12)
    task_id = params.task_id or generate_random_string(12)
    user_id = params.user_id or generate_random_string(12)
    log_date = params.log_date or datetime.now().strftime("%Y-%m-%d")

    return {
        "timelog_id": timelog_id,
        "task_id": task_id,
        "user_id": user_id,
        "hours": params.hours,
        "minutes": params.minutes,
        "log_date": log_date,
        "description": params.description,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_comment_data(
    comment_id: Optional[str] = None,
    content: str = "Test comment content",
    author_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    entity_type: str = "task",
) -> Dict[str, Any]:
    """Create test data for a comment."""
    if comment_id is None:
        comment_id = generate_random_string(12)
    if author_id is None:
        author_id = generate_random_string(12)
    if entity_id is None:
        entity_id = generate_random_string(12)

    return {
        "comment_id": comment_id,
        "content": content,
        "author_id": author_id,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_attachment_data(
    params: Optional[AttachmentDataParams] = None,
) -> Dict[str, Any]:
    """Create test data for an attachment."""
    params = params or AttachmentDataParams()

    attachment_id = params.attachment_id or generate_random_string(12)
    name = params.name or f"test_attachment_{generate_random_string(8)}.pdf"
    entity_id = params.entity_id or generate_random_string(12)

    return {
        "attachment_id": attachment_id,
        "name": name,
        "size": params.size,
        "url": params.url,
        "entity_id": entity_id,
        "entity_type": params.entity_type,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_baseline_data(
    params: Optional[BaselineDataParams] = None,
) -> Dict[str, Any]:
    """Create test data for a baseline."""
    params = params or BaselineDataParams()

    baseline_id = params.baseline_id or generate_random_string(12)
    name = params.name or f"Test Baseline {generate_random_string(8)}"
    project_id = params.project_id or generate_random_string(12)
    start_date = params.start_date or (datetime.now() - timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    end_date = params.end_date or (datetime.now() + timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )

    return {
        "baseline_id": baseline_id,
        "name": name,
        "project_id": project_id,
        "start_date": start_date,
        "end_date": end_date,
        "description": params.description,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_business_hours_data(
    business_hours_id: Optional[str] = None,
    name: Optional[str] = None,
    start_time: str = "09:00",
    end_time: str = "17:00",
    timezone: str = "UTC",
) -> Dict[str, Any]:
    """Create test data for business hours."""
    if business_hours_id is None:
        business_hours_id = generate_random_string(12)
    if name is None:
        name = f"Test Business Hours {generate_random_string(8)}"

    return {
        "business_hours_id": business_hours_id,
        "name": name,
        "start_time": start_time,
        "end_time": end_time,
        "timezone": timezone,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_event_data(params: Optional[EventDataParams] = None) -> Dict[str, Any]:
    """Create test data for an event."""
    params = params or EventDataParams()

    event_id = params.event_id or generate_random_string(12)
    title = params.title or f"Test Event {generate_random_string(8)}"
    start_time = params.start_time or (datetime.now() + timedelta(hours=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    end_time = params.end_time or (datetime.now() + timedelta(hours=2)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    project_id = params.project_id or generate_random_string(12)

    return {
        "event_id": event_id,
        "title": title,
        "description": params.description,
        "start_time": start_time,
        "end_time": end_time,
        "project_id": project_id,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_milestone_data(
    params: Optional[MilestoneDataParams] = None,
) -> Dict[str, Any]:
    """Create test data for a milestone."""
    params = params or MilestoneDataParams()

    milestone_id = params.milestone_id or generate_random_string(12)
    name = params.name or f"Test Milestone {generate_random_string(8)}"
    project_id = params.project_id or generate_random_string(12)
    target_date = params.target_date or (datetime.now() + timedelta(days=14)).strftime(
        "%Y-%m-%d"
    )

    return {
        "milestone_id": milestone_id,
        "name": name,
        "description": params.description,
        "project_id": project_id,
        "target_date": target_date,
        "status": params.status,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_phase_data(params: Optional[PhaseDataParams] = None) -> Dict[str, Any]:
    """Create test data for a phase."""
    params = params or PhaseDataParams()

    phase_id = params.phase_id or generate_random_string(12)
    name = params.name or f"Test Phase {generate_random_string(8)}"
    project_id = params.project_id or generate_random_string(12)
    start_date = params.start_date or (datetime.now() - timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    end_date = params.end_date or (datetime.now() + timedelta(days=14)).strftime(
        "%Y-%m-%d"
    )

    return {
        "phase_id": phase_id,
        "name": name,
        "description": params.description,
        "project_id": project_id,
        "start_date": start_date,
        "end_date": end_date,
        "status": params.status,
        "created_time": datetime.now().isoformat(),
        "modified_time": datetime.now().isoformat(),
    }


def create_test_api_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """Create a test API response structure."""
    return {
        "data": data,
        "status_code": status_code,
        "success": status_code < 300,
        "message": "Success" if status_code < 300 else "Error",
    }


def create_test_error_response(
    message: str = "An error occurred",
    status_code: int = 400,
    error_code: str = "GENERAL_ERROR",
) -> Dict[str, Any]:
    """Create a test error response structure."""
    return {
        "message": message,
        "status_code": status_code,
        "error_code": error_code,
        "success": False,
    }
