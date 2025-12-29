"""
Comprehensive integration tests covering cross-module interactions and data consistency.
"""

import asyncio
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock

import pytest

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.models import Issue
from zoho_projects_sdk.models.project_models import Project
from zoho_projects_sdk.models.task_models import Task


@pytest.fixture(name="mock_auth_handler")
def _mock_auth_handler() -> Mock:
    """Mock authentication handler for testing."""
    mock = Mock()
    mock.portal_id = "test_portal_id"
    mock.get_access_token = AsyncMock(return_value="test_access_token")
    return mock


class _MockApiClient:
    """Lightweight stub of the ApiClient for testing purposes."""

    def __init__(self, auth_handler: Mock) -> None:
        self._auth_handler = auth_handler
        self.portal_id = getattr(auth_handler, "portal_id", None)
        self.get = AsyncMock()
        self.post = AsyncMock()
        self.patch = AsyncMock()
        self.delete = AsyncMock()
        self.close = AsyncMock()


@pytest.fixture(name="mock_api_client")
def _mock_api_client(mock_auth_handler: Mock) -> _MockApiClient:
    """Mock API client for testing."""
    return _MockApiClient(mock_auth_handler)


@pytest.fixture(name="zoho_client")
def _zoho_client(
    mock_auth_handler: Mock,
    mock_api_client: _MockApiClient,
    monkeypatch: pytest.MonkeyPatch,
) -> ZohoProjects:
    """ZohoProjects client with mocked dependencies."""
    monkeypatch.setattr(
        "zoho_projects_sdk.client.ZohoOAuth2Handler",
        Mock(return_value=mock_auth_handler),
    )
    monkeypatch.setattr(
        "zoho_projects_sdk.client.ApiClient",
        Mock(return_value=mock_api_client),
    )
    return ZohoProjects(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        portal_id="test_portal_id",
    )


@pytest.mark.asyncio
async def test_project_task_integration(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test the integration between projects and tasks modules."""
    # Mock the API responses for both projects and tasks
    project_response = {
        "projects": [
            {
                "id": 123,
                "name": "Integration Test Project",
                "status": "active",
                "description": "A project for testing integration",
            }
        ]
    }
    tasks_response = {
        "tasks": [
            {
                "id": 1,
                "name": "Integration Test Task",
                "status": "open",
                "priority": "high",
                "completed": False,
            },
            {
                "id": 2,
                "name": "Integration Test Task 2",
                "status": "in_progress",
                "priority": "medium",
                "completed": False,
            },
        ]
    }

    # Set up the mock to return different responses for different endpoints
    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = params
        if endpoint.endswith("/projects/123"):
            return project_response
        elif endpoint.endswith("/projects/123/tasks"):
            return tasks_response
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Test fetching a project
    project = await zoho_client.projects.get(123)
    assert isinstance(project, Project)
    assert project.id == 123
    assert project.name == "Integration Test Project"

    # Test fetching tasks for the same project
    tasks = await zoho_client.tasks.get_all(123)
    assert len(tasks) == 2
    assert all(isinstance(task, Task) for task in tasks)
    assert tasks[0].id == 1
    assert tasks[1].id == 2

    # Verify the API calls were made correctly
    assert mock_api_client.get.call_count == 2
    mock_api_client.get.assert_any_call("/portal/test_portal_id/projects/123")
    mock_api_client.get.assert_any_call(
        "/portal/test_portal_id/projects/123/tasks", params={"page": 1, "per_page": 20}
    )


@pytest.mark.asyncio
async def test_project_issue_integration(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test the integration between projects and issues modules."""
    # Mock the API responses for both projects and issues
    project_response = {
        "projects": [
            {
                "id": 456,
                "name": "Issue Integration Test Project",
                "status": "active",
                "description": "A project for testing issue integration",
            }
        ]
    }
    issues_response = {
        "issues": [
            {
                "id": 1,
                "name": "Integration Test Issue",
                "status": "open",
                "priority": "high",
                "description": "An issue for integration testing",
            }
        ]
    }

    # Set up the mock to return different responses for different endpoints
    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = params
        if endpoint.endswith("/projects/456"):
            return project_response
        elif endpoint.endswith("/projects/456/issues"):
            return issues_response
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Test fetching a project
    project = await zoho_client.projects.get(456)
    assert isinstance(project, Project)
    assert project.id == 456
    assert project.name == "Issue Integration Test Project"

    # Test fetching issues for the same project
    issues = await zoho_client.issues.get_all(456)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    assert issues[0].id == 1
    assert issues[0].name == "Integration Test Issue"

    # Verify the API calls were made correctly
    assert mock_api_client.get.call_count == 2
    mock_api_client.get.assert_any_call("/portal/test_portal_id/projects/456")
    mock_api_client.get.assert_any_call(
        "/portal/test_portal_id/projects/456/issues",
        params={"page": 1, "per_page": 20},
    )


@pytest.mark.asyncio
async def test_cross_module_data_consistency(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test data consistency across different modules."""
    # Mock responses that should maintain consistency
    project_id = 789
    project_response = {
        "projects": [
            {
                "id": project_id,
                "name": "Consistency Test Project",
                "status": "active",
                "description": "A project for testing consistency",
                "created_time": "2023-01-01T10:00Z",
                "updated_time": "2023-01-01T10:00:00Z",
            }
        ]
    }
    tasks_response = {
        "tasks": [
            {
                "id": 1,
                "name": "Consistency Test Task",
                "status": "open",
                "priority": "high",
                "completed": False,
                "created_time": "2023-01-01T10:00:00Z",
                "updated_time": "2023-01-01T10:00:00Z",
            }
        ]
    }
    issues_response = {
        "issues": [
            {
                "id": 1,
                "name": "Consistency Test Issue",
                "status": "open",
                "priority": "high",
                "description": "An issue for consistency testing",
                "created_time": "2023-01-01T10:00:00Z",
                "updated_time": "2023-01-01T10:00:00Z",
            }
        ]
    }

    # Set up the mock to return different responses for different endpoints
    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = params
        if endpoint.endswith(f"/projects/{project_id}"):
            return project_response
        elif endpoint.endswith(f"/projects/{project_id}/tasks"):
            return tasks_response
        elif endpoint.endswith(f"/projects/{project_id}/issues"):
            return issues_response
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Test fetching project
    project = await zoho_client.projects.get(project_id)
    assert isinstance(project, Project)
    assert project.id == project_id
    assert project.name == "Consistency Test Project"

    # Test fetching tasks for the same project
    tasks = await zoho_client.tasks.get_all(project_id)
    assert len(tasks) == 1
    assert isinstance(tasks[0], Task)
    assert tasks[0].name == "Consistency Test Task"

    # Test fetching issues for the same project
    issues = await zoho_client.issues.get_all(project_id)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    assert issues[0].name == "Consistency Test Issue"

    # Verify that all API calls were made correctly
    assert mock_api_client.get.call_count == 3
    mock_api_client.get.assert_any_call(f"/portal/test_portal_id/projects/{project_id}")
    mock_api_client.get.assert_any_call(
        f"/portal/test_portal_id/projects/{project_id}/tasks",
        params={"page": 1, "per_page": 20},
    )
    mock_api_client.get.assert_any_call(
        f"/portal/test_portal_id/projects/{project_id}/issues",
        params={"page": 1, "per_page": 20},
    )


@pytest.mark.asyncio
async def test_cross_module_error_propagation(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test error propagation across different modules."""

    # Mock an error for one of the API calls
    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = params
        if endpoint.endswith("/projects/999"):
            raise RuntimeError("Project not found")
        elif endpoint.endswith("/projects/99/tasks"):
            return {"tasks": []}  # This shouldn't be reached due to project error
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Test that error in one module doesn't affect another when properly isolated
    with pytest.raises(RuntimeError, match="Project not found"):
        await zoho_client.projects.get(999)


@pytest.mark.asyncio
async def test_cross_module_transaction_like_behavior(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test scenarios that mimic transaction-like behavior across modules."""
    project_id = 101
    new_project_data = Project(
        id=project_id, name="Transaction Test Project", status="active"
    )
    new_task_data = Task(
        id=0,  # New task
        name="Transaction Test Task",
        status="open",
        priority="medium",
        completed=False,
    )

    # Mock responses for create operations
    created_project_response = {
        "project": {
            "id": project_id,
            "name": "Transaction Test Project",
            "status": "active",
        }
    }
    created_task_response = {
        "task": {
            "id": 1,
            "name": "Transaction Test Task",
            "status": "open",
            "priority": "medium",
            "completed": False,
        }
    }

    # Set up the mock to return different responses for different endpoints
    async def mock_post(
        endpoint: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = json
        if endpoint.endswith("/projects"):
            return created_project_response
        elif endpoint.endswith(f"/projects/{project_id}/tasks"):
            return created_task_response
        else:
            return {}

    mock_api_client.post.side_effect = mock_post

    # Create a project
    created_project = await zoho_client.projects.create(new_project_data)
    assert isinstance(created_project, Project)
    assert created_project.id == project_id
    assert created_project.name == "Transaction Test Project"

    # Create a task in the same project
    created_task = await zoho_client.tasks.create(project_id, new_task_data)
    assert isinstance(created_task, Task)
    assert created_task.id == 1
    assert created_task.name == "Transaction Test Task"

    # Verify both API calls were made
    assert mock_api_client.post.call_count == 2
    mock_api_client.post.assert_any_call(
        "/portal/test_portal_id/projects",
        json=new_project_data.model_dump(by_alias=True, exclude_none=True),
    )
    task_payload = new_task_data.model_dump(by_alias=True, exclude_none=True)
    mock_api_client.post.assert_any_call(
        f"/portal/test_portal_id/projects/{project_id}/tasks",
        json=task_payload,
    )


@pytest.mark.asyncio
async def test_multiple_module_concurrent_access(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test concurrent access to multiple modules."""
    project_response = {
        "projects": [{"id": 1, "name": "Concurrent Project", "status": "active"}]
    }
    task_response = {
        "tasks": [
            {
                "id": 1,
                "name": "Concurrent Task",
                "status": "open",
                "priority": "medium",
                "completed": False,
            }
        ]
    }
    issue_response = {
        "issues": [
            {"id": 1, "title": "Concurrent Issue", "status": "open", "priority": "high"}
        ]
    }

    # Set up the mock to return different responses for different endpoints
    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = params
        if endpoint.endswith("/projects/123"):
            await asyncio.sleep(0.01)  # Simulate network delay
            return project_response
        elif endpoint.endswith("/projects/123/tasks"):
            await asyncio.sleep(0.01)  # Simulate network delay
            return task_response
        elif endpoint.endswith("/projects/123/issues"):
            await asyncio.sleep(0.01)  # Simulate network delay
            return issue_response
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Run multiple API calls concurrently
    project_task = asyncio.create_task(zoho_client.projects.get(123))
    task_task = asyncio.create_task(zoho_client.tasks.get_all(123))
    issue_task = asyncio.create_task(zoho_client.issues.get_all(123))

    # Wait for all tasks to complete
    project, tasks, issues = await asyncio.gather(project_task, task_task, issue_task)

    # Verify results
    assert isinstance(project, Project)
    assert project.id == 1
    assert len(tasks) == 1
    assert isinstance(tasks[0], Task)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)

    # Verify that all calls were made
    assert mock_api_client.get.call_count == 3


@pytest.mark.asyncio
async def test_cross_module_pagination_consistency(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test pagination behavior consistency across modules."""
    project_id = 202

    # Create multiple pages of data for both tasks and issues
    tasks_page_1 = {
        "tasks": [
            {
                "id": 1,
                "name": "Task 1",
                "status": "open",
                "priority": "high",
                "completed": False,
            },
            {
                "id": 2,
                "name": "Task 2",
                "status": "in_progress",
                "priority": "medium",
                "completed": False,
            },
        ]
    }
    tasks_page_2 = {
        "tasks": [
            {
                "id": 3,
                "name": "Task 3",
                "status": "completed",
                "priority": "low",
                "completed": True,
            },
            {
                "id": 4,
                "name": "Task 4",
                "status": "open",
                "priority": "high",
                "completed": False,
            },
        ]
    }
    issues_page_1 = {
        "issues": [
            {"id": 1, "title": "Issue 1", "status": "open", "priority": "high"},
            {"id": 2, "title": "Issue 2", "status": "resolved", "priority": "medium"},
        ]
    }
    issues_page_2 = {
        "issues": [
            {"id": 3, "title": "Issue 3", "status": "open", "priority": "critical"},
            {"id": 4, "title": "Issue 4", "status": "closed", "priority": "low"},
        ]
    }

    # Set up the mock to return different responses based on parameters
    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if endpoint.endswith("/projects/202/tasks"):
            if params and params.get("page") == 2:
                return tasks_page_2
            else:
                return tasks_page_1
        elif endpoint.endswith("/projects/202/issues"):
            if params and params.get("page") == 2:
                return issues_page_2
            else:
                return issues_page_1
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Fetch first pages
    tasks_page1 = await zoho_client.tasks.get_all(project_id, page=1, per_page=2)
    issues_page1 = await zoho_client.issues.get_all(project_id, page=1, per_page=2)

    # Fetch second pages
    tasks_page2 = await zoho_client.tasks.get_all(project_id, page=2, per_page=2)
    issues_page2 = await zoho_client.issues.get_all(project_id, page=2, per_page=2)

    # Verify pagination worked correctly for both modules
    assert len(tasks_page1) == 2
    assert len(tasks_page2) == 2
    assert len(issues_page1) == 2
    assert len(issues_page2) == 2

    # Verify content is correct
    assert tasks_page1[0].id == 1
    assert tasks_page1[1].id == 2
    assert tasks_page2[0].id == 3
    assert tasks_page2[1].id == 4

    assert issues_page1[0].id == 1
    assert issues_page1[1].id == 2
    assert issues_page2[0].id == 3
    assert issues_page2[1].id == 4


@pytest.mark.asyncio
async def test_cross_module_data_relationship_validation(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test validation of data relationships across modules."""
    project_id = 303

    # Mock data that should be consistent across modules
    project_response = {
        "projects": [
            {
                "id": project_id,
                "name": "Relationship Validation Project",
                "status": "active",
                "description": "A project for testing relationships",
                "created_time": "2023-01-01T10:00:00Z",
                "updated_time": "2023-01-01T10:00:00Z",
            }
        ]
    }
    # Tasks belonging to the same project
    tasks_response = {
        "tasks": [
            {
                "id": 1,
                "name": "Task for Project 303",
                "status": "open",
                "priority": "high",
                "completed": False,
                "created_time": "2023-01-01T10:00:00Z",
                "updated_time": "2023-01-01T10:00:00Z",
            }
        ]
    }
    # Issues associated with the same project
    issues_response = {
        "issues": [
            {
                "id": 11,
                "name": "Issue for Project 303",
                "status": "open",
                "priority": "high",
                "created_time": "2023-01-01T10:00:00Z",
                "updated_time": "2023-01-01T10:00:00Z",
            }
        ]
    }

    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = params
        if endpoint.endswith(f"/projects/{project_id}"):
            return project_response
        elif endpoint.endswith(f"/projects/{project_id}/tasks"):
            return tasks_response
        elif endpoint.endswith(f"/projects/{project_id}/issues"):
            return issues_response
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Fetch the project
    project = await zoho_client.projects.get(project_id)
    assert project.id == project_id
    assert project.name == "Relationship Validation Project"

    # Fetch tasks for the project
    tasks = await zoho_client.tasks.get_all(project_id)
    assert len(tasks) == 1
    assert tasks[0].name == "Task for Project 303"

    # Fetch issues for the project
    issues = await zoho_client.issues.get_all(project_id)
    assert len(issues) == 1
    assert issues[0].name == "Issue for Project 303"

    # Verify the relationship consistency by checking if the task belongs to the project
    # (This is implicit in the API structure, but we're validating the data flow)
    assert tasks[0].updated_time == "2023-01-01T10:00:00Z"
    assert issues[0].updated_time == "2023-01-01T10:00:00Z"


@pytest.mark.asyncio
async def test_cross_module_error_handling_consistency(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test that error handling is consistent across modules."""
    # Make all API calls raise the same type of error
    mock_api_client.get.side_effect = Exception("API request failed")

    # Test that all modules handle the error in a similar way
    with pytest.raises(Exception, match="API request failed"):
        await zoho_client.projects.get(123)

    with pytest.raises(Exception, match="API request failed"):
        await zoho_client.tasks.get_all(123)

    with pytest.raises(Exception, match="API request failed"):
        await zoho_client.issues.get_all(123)

    # Verify that all three calls were made
    assert mock_api_client.get.call_count == 3


@pytest.mark.asyncio
async def test_cross_module_data_serialization_consistency(
    zoho_client: ZohoProjects, mock_api_client: Mock
) -> None:
    """Test that data serialization is consistent across modules."""
    project_id = 404

    # Create data with special characters and various types to test serialization
    project_response = {
        "projects": [
            {
                "id": project_id,
                "name": "Serialization Test Project: ñáéíóú 中文 🌍",
                "status": "active",
                "description": "Project with special chars: @#$%^&*()",
            }
        ]
    }
    task_response = {
        "tasks": [
            {
                "id": 1,
                "name": "Serialization Test Task: ñáéíóú 中文 🌍",
                "status": "open",
                "priority": "high",
                "completed": False,
                "description": "Task with special chars: @#$%^&*()",
            }
        ]
    }
    issue_response = {
        "issues": [
            {
                "id": 1,
                "name": "Serialization Test Issue: ñáéíóú 中文 🌍",
                "status": "open",
                "priority": "critical",
                "description": "Issue with special chars: @#$%^&*()",
            }
        ]
    }

    async def mock_get(
        endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        _ = params
        if endpoint.endswith(f"/projects/{project_id}"):
            return project_response
        elif endpoint.endswith(f"/projects/{project_id}/tasks"):
            return task_response
        elif endpoint.endswith(f"/projects/{project_id}/issues"):
            return issue_response
        else:
            return {}

    mock_api_client.get.side_effect = mock_get

    # Fetch data from all modules
    project = await zoho_client.projects.get(project_id)
    tasks = await zoho_client.tasks.get_all(project_id)
    issues = await zoho_client.issues.get_all(project_id)

    # Verify that special characters are preserved in all modules
    assert "ñáéíóú" in project.name
    assert "中文" in project.name
    assert "🌍" in project.name

    assert "ñáéíóú" in tasks[0].name
    assert "中文" in tasks[0].name
    assert "🌍" in tasks[0].name

    assert "ñáéíóú" in issues[0].name
    assert "中文" in issues[0].name
    assert "🌍" in issues[0].name
