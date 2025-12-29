"""Manage issues within a Zoho Projects project.

Workflow illustrated:

1. Locate or create a project (expects project ID via environment variable).
2. List the top issues for that project.
3. Create a new issue (skipped by default—set CREATE_SAMPLE_ISSUE=1 to enable).
4. Update the created issue's status/priority.
5. Clean up by deleting the sample issue if desired.

Environment variables:
    ZOHO_PROJECTS_CLIENT_ID
    ZOHO_PROJECTS_CLIENT_SECRET
    ZOHO_PROJECTS_REFRESH_TOKEN
    ZOHO_PROJECTS_PORTAL_ID
    ZOHO_PROJECTS_SAMPLE_PROJECT_ID
    CREATE_SAMPLE_ISSUE  # Optional, "1" to create/update/delete an issue demo.

Run with:

.. code-block:: bash

   uv run python examples/issue_management.py
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from pydantic import BaseModel

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.exceptions import APIError, ZohoSDKError
from zoho_projects_sdk.models.issue_models import (
    Issue,
    IssueCreateRequest,
    IssueUpdateRequest,
)


class IssueContext(BaseModel):
    project_id: int
    issue_id: Optional[int] = None


async def _list_issues(client: ZohoProjects, project_id: int) -> None:
    issues: list[Issue] = await client.issues.list_by_project(
        project_id=project_id,
        per_page=5,
        sort_by="created_time.desc",
    )

    if not issues:
        print("No issues found for this project.")
        return

    print("Top issues:")
    for issue in issues:
        print(
            f"  • [{issue.id}] {issue.title} "
            f"(status={issue.status}, priority={issue.priority})"
        )


async def _maybe_create_issue(client: ZohoProjects, context: IssueContext) -> None:
    if os.getenv("CREATE_SAMPLE_ISSUE") != "1":
        print("Skipping sample issue creation")
        print("(set CREATE_SAMPLE_ISSUE=1 to enable).")
        return
    create_payload = IssueCreateRequest(
        name="SDK sample issue",
        description="Created via the zoho-projects-sdk examples.",
        priority="High",
    )

    created = await client.issues.create(
        project_id=context.project_id,
        issue_data=create_payload,
    )
    if created.id is None:
        raise RuntimeError("Created issue did not return an ID.")

    context.issue_id = int(created.id)
    print(f"Created sample issue [{context.issue_id}].")


async def _update_issue(client: ZohoProjects, context: IssueContext) -> None:
    if context.issue_id is None:
        return

    update_payload = IssueUpdateRequest(
        priority="Medium",
        flag="Internal",
    )

    updated = await client.issues.update(
        project_id=context.project_id,
        issue_id=context.issue_id,
        issue_data=update_payload,
    )
    print(
        f"Updated issue [{context.issue_id}] -> "
        f"priority={updated.priority}, flag={updated.flag}"
    )


async def _cleanup_issue(client: ZohoProjects, context: IssueContext) -> None:
    if context.issue_id is None:
        return

    await client.issues.delete(
        project_id=context.project_id,
        issue_id=context.issue_id,
    )
    print(f"Deleted sample issue [{context.issue_id}].")


async def main() -> None:
    project_env = os.getenv("ZOHO_PROJECTS_SAMPLE_PROJECT_ID")
    if not project_env:
        raise RuntimeError("Set ZOHO_PROJECTS_SAMPLE_PROJECT_ID to target a project.")

    project_id = int(project_env)

    try:
        async with ZohoProjects() as client:
            context = IssueContext(project_id=project_id)
            await _list_issues(client, project_id)
            await _maybe_create_issue(client, context)
            await _update_issue(client, context)
            await _cleanup_issue(client, context)
    except APIError as exc:
        print(
            "Zoho Projects API responded with an error: "
            f"status={exc.status_code}, message={exc.message}"
        )
    except ZohoSDKError as exc:
        print(f"SDK error occurred: {exc}")
    except (ValueError, TypeError, AttributeError, RuntimeError) as exc:
        print(f"Application error: {exc}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except OSError as exc:
        print(f"System error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
