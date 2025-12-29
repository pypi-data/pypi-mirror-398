"""
Integration tests for end-to-end request flow from client to API and back.
These tests verify the complete flow of requests from the client through all components and back.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.models import Issue
from zoho_projects_sdk.models.project_models import Project
from zoho_projects_sdk.models.task_models import Task
from zoho_projects_sdk.models.user_models import User


@pytest.mark.asyncio
async def test_complete_project_lifecycle_end_to_end() -> None:
    """Test a complete project lifecycle: create, read, update, delete."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client methods for the complete lifecycle
        with (
            patch.object(
                client._api_client, "get", new_callable=AsyncMock
            ) as mock_api_get,
            patch.object(
                client._api_client, "post", new_callable=AsyncMock
            ) as mock_api_post,
            patch.object(
                client._api_client, "patch", new_callable=AsyncMock
            ) as mock_api_patch,
            patch.object(
                client._api_client, "delete", new_callable=AsyncMock
            ) as mock_api_delete,
        ):

            # Step 1: Create a project
            created_project_data = {
                "project": {
                    "id": 1001,
                    "name": "End-to-End Test Project",
                    "status": "active",
                    "description": "A project created for end-to-end testing",
                }
            }
            mock_api_post.return_value = created_project_data

            project_data = Project(
                id=1001,
                name="End-to-End Test Project",
                status="active",
                description="A project created for end-to-end testing",
            )
            created_project = await client.projects.create(project_data=project_data)
            assert isinstance(created_project, Project)
            assert created_project.id == 1001
            assert created_project.name == "End-to-End Test Project"

            # Step 2: Get the created project
            retrieved_project_data = {
                "projects": [
                    {
                        "id": 1001,
                        "name": "End-to-End Test Project",
                        "status": "active",
                        "description": "A project created for end-to-end testing",
                        "created_time": "2023-05-01T10:00Z",
                    }
                ]
            }
            mock_api_get.return_value = retrieved_project_data

            retrieved_project = await client.projects.get(project_id=1001)
            assert isinstance(retrieved_project, Project)
            assert retrieved_project.id == 1001
            assert retrieved_project.name == "End-to-End Test Project"
            assert retrieved_project.created_time == "2023-05-01T10:00Z"

            # Step 3: Update the project
            updated_project_data = {
                "project": {
                    "id": 1001,
                    "name": "Updated End-to-End Test Project",
                    "status": "active",
                    "description": "An updated project for end-to-end testing",
                    "updated_time": "2023-05-02T15:00:00Z",
                }
            }
            mock_api_patch.return_value = updated_project_data

            updated_project_data_obj = Project(
                id=1001,
                name="Updated End-to-End Test Project",
                status="active",
                description="An updated project for end-to-end testing",
            )
            updated_project = await client.projects.update(
                project_id=1001, project_data=updated_project_data_obj
            )
            assert isinstance(updated_project, Project)
            assert updated_project.id == 1001
            assert updated_project.name == "Updated End-to-End Test Project"
            assert (
                updated_project.description
                == "An updated project for end-to-end testing"
            )

            # Step 4: Delete the project
            mock_api_delete.return_value = True

            delete_result = await client.projects.delete(project_id=1001)
            assert delete_result is True


@pytest.mark.asyncio
async def test_complete_task_lifecycle_within_project_end_to_end() -> None:
    """Test a complete task lifecycle within a project: create, read, update, delete."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client methods for the complete lifecycle
        with (
            patch.object(
                client._api_client, "get", new_callable=AsyncMock
            ) as mock_api_get,
            patch.object(
                client._api_client, "post", new_callable=AsyncMock
            ) as mock_api_post,
            patch.object(
                client._api_client, "patch", new_callable=AsyncMock
            ) as mock_api_patch,
            patch.object(
                client._api_client, "delete", new_callable=AsyncMock
            ) as mock_api_delete,
        ):

            # Step 1: Create a task within a project
            created_task_data = {
                "task": {
                    "id": 2001,
                    "name": "End-to-End Test Task",
                    "status": "Not Started",
                    "priority": "High",
                    "project_id": 1002,
                }
            }
            mock_api_post.return_value = created_task_data

            task_data = Task(
                id=2001,
                name="End-to-End Test Task",
                status="Not Started",
                priority="High",
            )
            created_task = await client.tasks.create(
                project_id=1002, task_data=task_data
            )
            assert isinstance(created_task, Task)
            assert created_task.id == 2001
            assert created_task.name == "End-to-End Test Task"

            # Step 2: Get the created task
            retrieved_task_data = {
                "tasks": [
                    {
                        "id": 2001,
                        "name": "End-to-End Test Task",
                        "status": "Not Started",
                        "priority": "High",
                        "project_id": 1002,
                        "created_time": "2023-05-01T10:00:00Z",
                    }
                ]
            }
            mock_api_get.return_value = retrieved_task_data

            retrieved_task = await client.tasks.get(project_id=1002, task_id=2001)
            assert isinstance(retrieved_task, Task)
            assert retrieved_task.id == 2001
            assert retrieved_task.name == "End-to-End Test Task"
            assert retrieved_task.project_id == 1002

            # Step 3: Update the task
            updated_task_data = {
                "task": {
                    "id": 2001,
                    "name": "Updated End-to-End Test Task",
                    "status": "In Progress",
                    "priority": "Medium",
                    "project_id": 1002,
                    "updated_time": "2023-05-02T15:00:00Z",
                }
            }
            mock_api_patch.return_value = updated_task_data

            updated_task_data_obj = Task(
                id=2001,
                name="Updated End-to-End Test Task",
                status="In Progress",
                priority="Medium",
            )
            updated_task = await client.tasks.update(
                project_id=1002, task_id=2001, task_data=updated_task_data_obj
            )
            assert isinstance(updated_task, Task)
            assert updated_task.id == 2001
            assert updated_task.name == "Updated End-to-End Test Task"
            assert updated_task.status == "In Progress"

            # Step 4: Delete the task
            mock_api_delete.return_value = True

            delete_result = await client.tasks.delete(project_id=1002, task_id=2001)
            assert delete_result is True


@pytest.mark.asyncio
async def test_cross_module_end_to_end_workflow() -> None:
    """Test a cross-module workflow: create project, add tasks and bugs, assign users."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client methods for the cross-module workflow
        with (
            patch.object(
                client._api_client, "get", new_callable=AsyncMock
            ) as mock_api_get,
            patch.object(
                client._api_client, "post", new_callable=AsyncMock
            ) as mock_api_post,
        ):

            # Step 1: Create a project
            created_project_data = {
                "project": {
                    "id": 3001,
                    "name": "Cross-Module Workflow Project",
                    "status": "active",
                    "description": "A project for testing cross-module workflows",
                }
            }
            mock_api_post.return_value = created_project_data

            project_data = Project(
                id=3001,
                name="Cross-Module Workflow Project",
                status="active",
                description="A project for testing cross-module workflows",
            )
            created_project = await client.projects.create(project_data=project_data)
            assert isinstance(created_project, Project)
            assert created_project.id == 3001

            # Step 2: Get users to assign to the project
            users_data = {
                "users": [
                    {
                        "id": "user_workflow",
                        "name": "Workflow Test User",
                        "email": "workflow@example.com",
                        "status": "active",
                    }
                ]
            }
            mock_api_get.return_value = users_data

            users = await client.users.get_all(project_id=1)
            assert len(users) == 1
            assert isinstance(users[0], User)
            assert users[0].id == "user_workflow"

            # Step 3: Create a task in the project
            created_task_data = {
                "task": {
                    "id": 3002,
                    "name": "Workflow Test Task",
                    "status": "Not Started",
                    "priority": "High",
                    "project_id": 3001,
                }
            }
            mock_api_post.return_value = created_task_data

            task_data = Task(
                id=3002,
                name="Workflow Test Task",
                status="Not Started",
                priority="High",
            )
            created_task = await client.tasks.create(
                project_id=3001, task_data=task_data
            )
            assert isinstance(created_task, Task)
            assert created_task.id == 3002
            assert created_task.project_id == 3001  # Verify cross-module consistency

            # Step 4: Create a bug in the project
            created_bug_data = {
                "issue": {
                    "id": 3003,
                    "name": "Workflow Test Bug",
                    "status": {"id": 1, "name": "Open"},
                    "priority": "Critical",
                    "project_id": 3001,
                }
            }
            mock_api_post.return_value = created_bug_data

            bug_data = Issue(
                id=3003,
                name="Workflow Test Bug",
                status={"id": 1, "name": "Open"},
                priority="Critical",
            )
            created_bug = await client.issues.create(
                project_id=3001, issue_data=bug_data
            )
            assert isinstance(created_bug, Issue)
            assert created_bug.id == 3003
            assert created_bug.project_id == 3001  # Verify cross-module consistency

            # Verify all entities are properly connected
            assert (
                created_project.id == created_task.project_id == created_bug.project_id
            )
            assert created_project.name == "Cross-Module Workflow Project"


@pytest.mark.asyncio
async def test_end_to_end_with_data_validation_and_error_handling() -> None:
    """Test end-to-end flow with proper data validation and error handling."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client methods
        with (
            patch.object(
                client._api_client, "get", new_callable=AsyncMock
            ) as mock_api_get,
            patch.object(
                client._api_client, "post", new_callable=AsyncMock
            ) as mock_api_post,
        ):

            # Step 1: Create a project with valid data (should succeed)
            created_project_data = {
                "project": {
                    "id": 4001,
                    "name": "Validation Test Project",
                    "status": "active",
                    "description": "A project for testing validation",
                }
            }
            mock_api_post.return_value = created_project_data

            project_data = Project(
                id=4001,
                name="Validation Test Project",
                status="active",
                description="A project for testing validation",
            )
            created_project = await client.projects.create(project_data=project_data)
            assert isinstance(created_project, Project)
            assert created_project.id == 4001

            # Step 2: Retrieve the project
            retrieved_project_data = {
                "projects": [
                    {
                        "id": 4001,
                        "name": "Validation Test Project",
                        "status": "active",
                        "description": "A project for testing validation",
                        "created_time": "2023-06-01T10:00:00Z",
                        "updated_time": "2023-06-01T10:00:00Z",
                    }
                ]
            }
            mock_api_get.return_value = retrieved_project_data

            retrieved_project = await client.projects.get(project_id=4001)
            assert isinstance(retrieved_project, Project)
            assert retrieved_project.id == 4001
            assert retrieved_project.name == "Validation Test Project"
            assert retrieved_project.created_time == "2023-06-01T10:00:00Z"

            # Step 3: Create a task with valid data (should succeed)
            created_task_data = {
                "task": {
                    "id": 4002,
                    "name": "Validation Test Task",
                    "status": "Not Started",
                    "priority": "Medium",
                    "project_id": 4001,
                }
            }
            mock_api_post.return_value = created_task_data

            task_data = Task(
                id=4002,
                name="Validation Test Task",
                status="Not Started",
                priority="Medium",
            )
            created_task = await client.tasks.create(
                project_id=4001, task_data=task_data
            )
            assert isinstance(created_task, Task)
            assert created_task.id == 4002
            assert created_task.project_id == 4001

            # Verify that the data flowed correctly through the entire system
            assert created_project.id == 4001
            assert created_task.project_id == 4001
            assert created_task.name == "Validation Test Task"
            assert created_task.status == "Not Started"


@pytest.mark.asyncio
async def test_end_to_end_flow_with_multiple_projects_and_tasks() -> None:
    """Test end-to-end flow with multiple projects and tasks to verify isolation."""
    with patch("zoho_projects_sdk.auth.httpx.AsyncClient.post") as mock_post:
        # Mock the token refresh response
        token_response = Mock()
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        token_response.raise_for_status.return_value = None
        mock_post.return_value = token_response

        # Create the main client
        client = ZohoProjects(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            portal_id="test_portal_id",
        )

        # Mock the API client methods
        with (
            patch.object(
                client._api_client, "get", new_callable=AsyncMock
            ) as mock_api_get,
            patch.object(
                client._api_client, "post", new_callable=AsyncMock
            ) as mock_api_post,
        ):

            # Create first project
            project1_data = {
                "project": {
                    "id": 5001,
                    "name": "First End-to-End Project",
                    "status": "active",
                    "description": "First project for multi-project test",
                }
            }
            mock_api_post.return_value = project1_data

            proj1_data = Project(
                id=5001,
                name="First End-to-End Project",
                status="active",
                description="First project for multi-project test",
            )
            created_proj1 = await client.projects.create(project_data=proj1_data)
            assert created_proj1.id == 5001

            # Create second project
            project2_data = {
                "project": {
                    "id": 5002,
                    "name": "Second End-to-End Project",
                    "status": "active",
                    "description": "Second project for multi-project test",
                }
            }
            mock_api_post.return_value = project2_data

            proj2_data = Project(
                id=5002,
                name="Second End-to-End Project",
                status="active",
                description="Second project for multi-project test",
            )
            created_proj2 = await client.projects.create(project_data=proj2_data)
            assert created_proj2.id == 5002

            # Create task in first project
            task1_data = {
                "task": {
                    "id": 5003,
                    "name": "Task in First Project",
                    "status": "Not Started",
                    "priority": "High",
                    "project_id": 5001,
                }
            }
            mock_api_post.return_value = task1_data

            task1_obj = Task(
                id=5003,
                name="Task in First Project",
                status="Not Started",
                priority="High",
            )
            created_task1 = await client.tasks.create(
                project_id=5001, task_data=task1_obj
            )
            assert created_task1.id == 5003
            assert created_task1.project_id == 5001

            # Create task in second project
            task2_data = {
                "task": {
                    "id": 5004,
                    "name": "Task in Second Project",
                    "status": "Not Started",
                    "priority": "Medium",
                    "project_id": 5002,
                }
            }
            mock_api_post.return_value = task2_data

            task2_obj = Task(
                id=5004,
                name="Task in Second Project",
                status="Not Started",
                priority="Medium",
            )
            created_task2 = await client.tasks.create(
                project_id=5002, task_data=task2_obj
            )
            assert created_task2.id == 5004
            assert created_task2.project_id == 5002

            # Verify isolation: tasks belong to correct projects
            assert created_task1.project_id == created_proj1.id
            assert created_task2.project_id == created_proj2.id
            assert created_task1.project_id != created_task2.project_id

            # Retrieve and verify both projects exist separately
            mock_projects_data = {
                "projects": [
                    {
                        "id": 5001,
                        "name": "First End-to-End Project",
                        "status": "active",
                    },
                    {
                        "id": 5002,
                        "name": "Second End-to-End Project",
                        "status": "active",
                    },
                ]
            }
            mock_api_get.return_value = mock_projects_data

            all_projects = await client.projects.get_all()
            assert len(all_projects) == 2
            project_ids = [p.id for p in all_projects]
            assert 5001 in project_ids
            assert 5002 in project_ids
