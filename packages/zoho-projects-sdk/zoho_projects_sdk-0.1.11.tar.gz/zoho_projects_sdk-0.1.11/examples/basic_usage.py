"""Quick-start example demonstrating how to work with the Zoho Projects SDK.

This script shows how to:

1. Instantiate the async ``ZohoProjects`` client using environment-driven
   credentials (see README for required variables).
2. Fetch projects from the authenticated portal.
3. Optionally fetch tasks for a specific project when the
   ``ZOHO_PROJECTS_SAMPLE_PROJECT_ID`` environment variable is present.

Run with:

.. code-block:: bash

   uv run python examples/basic_usage.py
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional, Union

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.exceptions import APIError, ZohoSDKError
from zoho_projects_sdk.models.project_models import Project
from zoho_projects_sdk.models.task_models import Task


def _ensure_int_id(value: Union[int, str]) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Expected project identifier convertible to int") from exc


async def _print_projects(client: ZohoProjects) -> Optional[int]:
    projects: list[Project] = await client.projects.get_all()
    if not projects:
        print("No projects available for the authenticated portal.")
        return None

    print(f"Found {len(projects)} project(s):")
    for project in projects:
        print(f"  • [{project.id}] {project.name} (status={project.status})")

    # Return the first project ID as a convenience for follow-up calls.
    first_project = projects[0]
    project_id_candidate = first_project.id
    if project_id_candidate is None:
        raise ValueError("Project returned by Zoho Projects API is missing an ID")

    if not isinstance(project_id_candidate, (int, str)):
        raise ValueError("Project identifier must be an int or string value")

    project_id: Union[int, str] = project_id_candidate
    return _ensure_int_id(project_id)


async def _print_tasks(client: ZohoProjects, project_id: int) -> None:
    tasks: list[Task] = await client.tasks.list_by_project(
        project_id=project_id, per_page=10
    )
    if not tasks:
        print(f"No tasks available for project {project_id}.")
        return

    print(f"Showing up to {len(tasks)} task(s) for project {project_id}:")
    for task in tasks:
        title = task.name or getattr(task, "title", "<unnamed task>")
        print(f"  • [{task.id}] {title}")


async def main() -> None:
    sample_project_env = os.getenv("ZOHO_PROJECTS_SAMPLE_PROJECT_ID")
    sample_project_id = int(sample_project_env) if sample_project_env else None

    try:
        async with ZohoProjects() as client:
            first_project_id = await _print_projects(client)

            # Pick the project from the environment or fall back to the first result.
            target_project_id = sample_project_id or first_project_id
            if target_project_id is not None:
                await _print_tasks(client, target_project_id)
            else:
                print(
                    "Set ZOHO_PROJECTS_SAMPLE_PROJECT_ID to fetch tasks from a "
                    "specific project."
                )

    except ValueError as exc:
        print(f"Configuration error: {exc}")
    except APIError as exc:
        print(
            "Zoho Projects API responded with an error: "
            f"status={exc.status_code}, message={exc.message}"
        )
    except ZohoSDKError as exc:
        print(f"SDK error occurred: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
