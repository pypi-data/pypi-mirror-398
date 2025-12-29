import importlib
import sys
from typing import NoReturn

import pytest


def test_version_fallback_when__version_import_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in list(sys.modules.keys()):
        if key == "zoho_projects_sdk" or key.startswith("zoho_projects_sdk."):
            monkeypatch.delitem(sys.modules, key, raising=False)

    class BrokenVersionModule:
        def __getattr__(self, name: str) -> NoReturn:
            if name == "version":
                raise ImportError("No module named 'zoho_projects_sdk._version'")
            raise AttributeError(f"module has no attribute '{name}'")

    broken_module = BrokenVersionModule()
    monkeypatch.setitem(sys.modules, "zoho_projects_sdk._version", broken_module)

    pkg = importlib.import_module("zoho_projects_sdk")
    assert getattr(pkg, "__version__", None) == "0.0.0"
