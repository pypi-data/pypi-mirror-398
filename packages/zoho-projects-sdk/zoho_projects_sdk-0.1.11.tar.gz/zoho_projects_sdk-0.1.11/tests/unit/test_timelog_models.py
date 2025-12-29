"""Unit tests for TimeLog Pydantic model behaviour."""

from zoho_projects_sdk.models.timelog_models import TimeLog


def test_timelog_normalizes_numeric_log_hour() -> None:
    timelog = TimeLog.model_construct(id=1, date="2024-01-01", log_hour="02:30")

    assert timelog.log_hour == "02:30"
    assert timelog.model_dump(by_alias=True)["log_hour"] == "02:30"


def test_timelog_accepts_alias_fields() -> None:
    payload = {
        "id": 2,
        "log_date": "2024-05-10",
        "log_time": 45,
        "description": "Worked on integration.",
    }

    timelog = TimeLog.model_validate(payload)

    assert timelog.date == "2024-05-10"
    assert timelog.log_hour == "00:45"
    assert timelog.notes == "Worked on integration."


def test_timelog_preserves_string_log_hour() -> None:
    timelog = TimeLog.model_construct(id=3, date="2024-06-15", log_hour="03:15")

    assert timelog.log_hour == "03:15"
