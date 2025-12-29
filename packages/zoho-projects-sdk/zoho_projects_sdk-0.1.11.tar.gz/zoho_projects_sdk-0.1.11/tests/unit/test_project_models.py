"""Unit tests for project models."""

from zoho_projects_sdk.models.project_models import Project, ProjectStatus


def test_project_status_model() -> None:
    """Test ProjectStatus model validation."""
    # Test with all fields
    status = ProjectStatus(
        id="status-1",
        name="Active",
        color="green",
        color_hexcode="#00FF00",
        is_closed_type=False,
    )
    assert status.id == "status-1"
    assert status.name == "Active"
    assert status.color == "green"
    assert status.color_hexcode == "#00FF00"
    assert status.is_closed_type is False


def test_project_model_with_string_status() -> None:
    """Test Project model with string status (backward compatibility)."""
    # Use model_validate to ensure field validators run
    project = Project.model_validate(
        {
            "id": 1,
            "name": "Test Project",
            "status": "active",
            "description": "Test description",
        }
    )
    assert project.id == 1
    assert project.name == "Test Project"
    assert project.status_name == "active"
    # After field validation, status should be a ProjectStatus object
    status_obj = project.status
    assert isinstance(status_obj, ProjectStatus)
    assert status_obj.id == "active"
    assert status_obj.name == "active"


def test_project_model_with_object_status() -> None:
    """Test Project model with ProjectStatus object."""
    status_obj = ProjectStatus(
        id="status-2",
        name="Completed",
        color="blue",
        color_hexcode="#0000FF",
        is_closed_type=True,
    )
    project = Project.model_construct(id=2, name="Test Project 2", status=status_obj)
    assert project.id == 2
    assert project.name == "Test Project 2"
    assert project.status_name == "Completed"
    assert project.status == status_obj


def test_project_status_name_property_with_string() -> None:
    """Test status_name property when status is a string."""
    project = Project.model_construct(id=1, name="Test Project", status="active")
    # Manually set status to a string after creation to bypass field validator
    setattr(project, "status", "active")
    # This covers line 74
    assert project.status_name == "active"


def test_project_status_name_property_with_object() -> None:
    """Test status_name property when status is an object."""
    status_obj = ProjectStatus(id="status-1", name="Active", color="green")
    project = Project.model_construct(id=1, name="Test Project", status=status_obj)
    # This covers line 76-77
    assert project.status_name == "Active"


def test_project_status_name_property_fallback() -> None:
    """Test status_name property fallback case."""
    # Create a project with a status that doesn't have a name attribute
    project = Project.model_construct(id=1, name="Test Project", status="active")
    # Manually set status to an object without name attribute to test fallback
    setattr(project, "status", object())
    # This covers line 79
    assert project.status_name == str(project.status)


def test_project_str_representation() -> None:
    """Test string representation of Project."""
    project = Project.model_construct(id=123, name="Test Project", status="active")
    # This covers line 83
    str_repr = str(project)
    assert "Project(id=123" in str_repr
    assert "name=Test Project" in str_repr
    assert "status=active" in str_repr
