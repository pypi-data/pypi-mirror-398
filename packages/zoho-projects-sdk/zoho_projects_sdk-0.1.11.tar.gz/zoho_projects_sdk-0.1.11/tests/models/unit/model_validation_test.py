import importlib
import inspect
import pkgutil
from typing import List, Type

import pytest
from pydantic import BaseModel, ValidationError

from tests.shared.payload_factory import build_payload
from zoho_projects_sdk import models as models_pkg


def _discover_models() -> List[Type[BaseModel]]:
    discovered: List[Type[BaseModel]] = []
    for _, module_name, _ in pkgutil.iter_modules(models_pkg.__path__):
        module = importlib.import_module(f"{models_pkg.__name__}.{module_name}")
        for attr in vars(module).values():
            if (
                inspect.isclass(attr)
                and issubclass(attr, BaseModel)
                and attr.__module__ == module.__name__
                and not attr.__name__.startswith("BaseModel")
            ):
                discovered.append(attr)
    return discovered


MODEL_CLASSES = _discover_models()


@pytest.mark.parametrize("model_cls", MODEL_CLASSES)
def test_model_accepts_payload(model_cls: Type[BaseModel]) -> None:
    payload = build_payload(model_cls)
    instance = model_cls.model_validate(payload)
    dumped = instance.model_dump(by_alias=True)
    for key in payload:
        assert key in dumped


@pytest.mark.parametrize(
    "model_cls",
    [
        model
        for model in MODEL_CLASSES
        if any(field.is_required() for field in model.model_fields.values())
    ],
)
def test_required_fields_raise_when_missing(model_cls: Type[BaseModel]) -> None:
    with pytest.raises(ValidationError):
        model_cls.model_validate({})
