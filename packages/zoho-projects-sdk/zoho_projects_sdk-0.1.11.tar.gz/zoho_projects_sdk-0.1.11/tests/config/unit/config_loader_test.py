"""Tests for the configuration loader and Settings class."""

import sys
from types import SimpleNamespace
from typing import Optional

import pytest


def test_load_sdk_config_invokes_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that load_sdk_config calls load_dotenv."""
    invoked = SimpleNamespace(count=0)

    def _fake_load() -> None:
        invoked.count += 1

    monkeypatch.setattr("dotenv.load_dotenv", _fake_load)
    monkeypatch.delitem(sys.modules, "zoho_projects_sdk.config", raising=False)

    # Import the module to trigger load_dotenv call
    import importlib

    importlib.import_module("zoho_projects_sdk.config")

    assert invoked.count == 1


def test_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Settings class reads from environment variables."""
    env = {
        "ZOHO_PROJECTS_CLIENT_ID": "id",
        "ZOHO_PROJECTS_CLIENT_SECRET": "secret",
        "ZOHO_PROJECTS_REFRESH_TOKEN": "refresh",
        "ZOHO_PROJECTS_PORTAL_ID": "portal",
    }

    def _fake_getenv(key: str, default: Optional[str] = None) -> Optional[str]:
        return env.get(key, default)

    monkeypatch.setattr("zoho_projects_sdk.config.os.getenv", _fake_getenv)
    import importlib

    config_module = importlib.import_module("zoho_projects_sdk.config")
    importlib.reload(config_module)
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_ID == "id"
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_SECRET == "secret"
    assert config_module.settings.ZOHO_PROJECTS_REFRESH_TOKEN == "refresh"
    assert config_module.settings.ZOHO_PROJECTS_PORTAL_ID == "portal"


def test_settings_handles_missing_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that Settings handles missing environment variables gracefully."""

    def _fake_getenv(key: str, default: Optional[str] = None) -> Optional[str]:
        return default  # Always return default, simulating missing env vars

    monkeypatch.setattr("zoho_projects_sdk.config.os.getenv", _fake_getenv)
    import importlib

    config_module = importlib.import_module("zoho_projects_sdk.config")
    importlib.reload(config_module)

    # All should be None when environment variables are missing
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_ID is None
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_SECRET is None
    assert config_module.settings.ZOHO_PROJECTS_REFRESH_TOKEN is None
    assert config_module.settings.ZOHO_PROJECTS_PORTAL_ID is None


def test_settings_handles_partial_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Settings handles partially set environment variables."""
    env = {
        "ZOHO_PROJECTS_CLIENT_ID": "test-id",
        "ZOHO_PROJECTS_PORTAL_ID": "test-portal",
        # Missing CLIENT_SECRET and REFRESH_TOKEN
    }

    def _fake_getenv(key: str, default: Optional[str] = None) -> Optional[str]:
        return env.get(key, default)

    monkeypatch.setattr("zoho_projects_sdk.config.os.getenv", _fake_getenv)
    import importlib

    config_module = importlib.import_module("zoho_projects_sdk.config")
    importlib.reload(config_module)

    # Set variables should have values
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_ID == "test-id"
    assert config_module.settings.ZOHO_PROJECTS_PORTAL_ID == "test-portal"

    # Missing variables should be None
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_SECRET is None
    assert config_module.settings.ZOHO_PROJECTS_REFRESH_TOKEN is None


def test_settings_class_instantiation() -> None:
    """Test that Settings class can be instantiated directly."""
    from zoho_projects_sdk.config import Settings

    settings = Settings()

    # Should have all expected attributes
    assert hasattr(settings, "ZOHO_PROJECTS_CLIENT_ID")
    assert hasattr(settings, "ZOHO_PROJECTS_CLIENT_SECRET")
    assert hasattr(settings, "ZOHO_PROJECTS_REFRESH_TOKEN")
    assert hasattr(settings, "ZOHO_PROJECTS_PORTAL_ID")

    # All should be Optional[str], so can be None
    assert settings.ZOHO_PROJECTS_CLIENT_ID is None or isinstance(
        settings.ZOHO_PROJECTS_CLIENT_ID, str
    )
    assert settings.ZOHO_PROJECTS_CLIENT_SECRET is None or isinstance(
        settings.ZOHO_PROJECTS_CLIENT_SECRET, str
    )
    assert settings.ZOHO_PROJECTS_REFRESH_TOKEN is None or isinstance(
        settings.ZOHO_PROJECTS_REFRESH_TOKEN, str
    )
    assert settings.ZOHO_PROJECTS_PORTAL_ID is None or isinstance(
        settings.ZOHO_PROJECTS_PORTAL_ID, str
    )


def test_settings_instance_created_at_module_level() -> None:
    """Test that settings instance is created at module level."""
    import zoho_projects_sdk.config as config_module

    # Should have a settings instance
    assert hasattr(config_module, "settings")
    assert isinstance(config_module.settings, config_module.Settings)


def test_load_sdk_config_function_exists() -> None:
    """Test that load_sdk_config function exists and is callable."""
    from zoho_projects_sdk.config import load_sdk_config

    assert callable(load_sdk_config)

    # Should not raise when called
    load_sdk_config()  # Should call load_dotenv again


def test_environment_variable_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables are properly typed as Optional[str]."""
    env = {
        "ZOHO_PROJECTS_CLIENT_ID": "string-value",
        "ZOHO_PROJECTS_CLIENT_SECRET": "",
        "ZOHO_PROJECTS_REFRESH_TOKEN": "another-string",
        "ZOHO_PROJECTS_PORTAL_ID": "123",
    }

    def _fake_getenv(key: str, default: Optional[str] = None) -> Optional[str]:
        return env.get(key, default)

    monkeypatch.setattr("zoho_projects_sdk.config.os.getenv", _fake_getenv)
    import importlib

    config_module = importlib.import_module("zoho_projects_sdk.config")
    importlib.reload(config_module)

    # All should be strings (including empty string)
    assert isinstance(config_module.settings.ZOHO_PROJECTS_CLIENT_ID, str)
    assert isinstance(config_module.settings.ZOHO_PROJECTS_CLIENT_SECRET, str)
    assert isinstance(config_module.settings.ZOHO_PROJECTS_REFRESH_TOKEN, str)
    assert isinstance(config_module.settings.ZOHO_PROJECTS_PORTAL_ID, str)

    # Check specific values
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_ID == "string-value"
    assert config_module.settings.ZOHO_PROJECTS_CLIENT_SECRET == ""
    assert config_module.settings.ZOHO_PROJECTS_REFRESH_TOKEN == "another-string"
    assert config_module.settings.ZOHO_PROJECTS_PORTAL_ID == "123"


def test_config_module_imports() -> None:
    """Test that config module can be imported and has expected attributes."""
    import zoho_projects_sdk.config as config_module

    # Should have expected functions and classes
    assert hasattr(config_module, "load_sdk_config")
    assert hasattr(config_module, "Settings")
    assert hasattr(config_module, "settings")

    # Should be callable/class
    assert callable(config_module.load_sdk_config)
    assert isinstance(config_module.Settings, type)
    assert isinstance(config_module.settings, config_module.Settings)
