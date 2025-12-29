"""Generate a simple timelog report for a project.

This script demonstrates how to:

1. Authenticate with the Zoho Projects SDK.
2. Fetch aggregated timelog report data for a project.
3. Summarize billable vs non-billable hours over a date range.

Environment variables:
    ZOHO_PROJECTS_CLIENT_ID
    ZOHO_PROJECTS_CLIENT_SECRET
    ZOHO_PROJECTS_REFRESH_TOKEN
    ZOHO_PROJECTS_PORTAL_ID
    ZOHO_PROJECTS_SAMPLE_PROJECT_ID    # Project for timelog data
    ZOHO_PROJECTS_TIMELOG_FROM_DATE    # Optional ISO date (YYYY-MM-DD).
    ZOHO_PROJECTS_TIMELOG_TO_DATE      # Optional ISO date (YYYY-MM-DD).

Run with:

.. code-block:: bash

   uv run python examples/timelog_report.py
"""

from __future__ import annotations

import asyncio
import os
from typing import Iterable

from pydantic import BaseModel

from zoho_projects_sdk.client import ZohoProjects
from zoho_projects_sdk.exceptions import APIError, ZohoSDKError
from zoho_projects_sdk.models.timelog_models import TimeLog


class TimelogSummary(BaseModel):
    """Aggregated timelog metrics for a date range."""

    total_entries: int
    billable_minutes: int
    non_billable_minutes: int

    @property
    def total_minutes(self) -> int:
        return self.billable_minutes + self.non_billable_minutes

    @property
    def billable_hours(self) -> float:
        return self.billable_minutes / 60

    @property
    def non_billable_hours(self) -> float:
        return self.non_billable_minutes / 60

    @property
    def total_hours(self) -> float:
        return self.total_minutes / 60


def _minutes_from_hhmm(value: str) -> int:
    hours, minutes = value.split(":", maxsplit=1)
    return int(hours) * 60 + int(minutes)


def summarize_timelogs(entries: Iterable[TimeLog]) -> TimelogSummary:
    billable = 0
    non_billable = 0
    count = 0

    for entry in entries:
        count += 1
        if entry.billable_hours:
            billable += _minutes_from_hhmm(entry.billable_hours)
        if entry.non_billable_hours:
            non_billable += _minutes_from_hhmm(entry.non_billable_hours)

    return TimelogSummary(
        total_entries=count,
        billable_minutes=billable,
        non_billable_minutes=non_billable,
    )


async def main() -> None:
    sample_project = os.getenv("ZOHO_PROJECTS_SAMPLE_PROJECT_ID")
    if not sample_project:
        raise RuntimeError(
            "Set ZOHO_PROJECTS_SAMPLE_PROJECT_ID to the project "
            "you want to report on."
        )

    from_date = os.getenv("ZOHO_PROJECTS_TIMELOG_FROM_DATE")
    to_date = os.getenv("ZOHO_PROJECTS_TIMELOG_TO_DATE")

    try:
        async with ZohoProjects() as client:
            timelogs: list[TimeLog] = await client.timelogs.get_report(
                project_id=int(sample_project),
                start_date=from_date,
                end_date=to_date,
                report_type="user",
                view_type="date",
            )

    except APIError as exc:
        print(
            "Zoho Projects API responded with an error: "
            f"status={exc.status_code}, message={exc.message}"
        )
        return
    except ZohoSDKError as exc:
        print(f"SDK error occurred: {exc}")
        return

    summary = summarize_timelogs(timelogs)

    print("Timelog report")
    print("==============")
    print(f"Project ID: {sample_project}")
    if from_date or to_date:
        print(f"Date range: {from_date or 'start'} -> {to_date or 'today'}")
    print(f"Entries: {summary.total_entries}")
    print(f"Billable hours: {summary.billable_hours:.2f}")
    print(f"Non-billable hours: {summary.non_billable_hours:.2f}")
    print(f"Total hours: {summary.total_hours:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
