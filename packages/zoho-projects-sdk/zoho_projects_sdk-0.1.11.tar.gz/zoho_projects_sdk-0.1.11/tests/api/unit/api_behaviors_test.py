import importlib
import inspect
import pkgutil
import re
import sys
from types import SimpleNamespace
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import pytest
from pydantic import BaseModel, ValidationError

from tests.shared.payload_factory import build_model, build_payload
from zoho_projects_sdk import api as api_pkg


def _iter_api_classes() -> List[Type[Any]]:
    classes: List[Type[Any]] = []
    for _, module_name, _ in pkgutil.iter_modules(api_pkg.__path__):
        module = importlib.import_module(f"{api_pkg.__name__}.{module_name}")
        for attr in vars(module).values():
            if (
                inspect.isclass(attr)
                and attr.__module__ == module.__name__
                and attr.__name__.endswith("API")
            ):
                classes.append(attr)
    return classes


API_METHODS = [
    (api_cls, name)
    for api_cls in _iter_api_classes()
    for name, member in inspect.getmembers(api_cls, inspect.iscoroutinefunction)
    if not name.startswith("_")
]


def _get_return_annotation(method: Any) -> Any:
    """Resolve the return annotation, handling forward references."""

    annotation = inspect.signature(method).return_annotation
    if annotation is inspect.Parameter.empty:
        return annotation

    module = sys.modules.get(method.__module__)
    globalns = vars(module) if module is not None else None
    try:
        type_hints = get_type_hints(method, globalns=globalns)
    except (NameError, TypeError, ValueError):  # pragma: no cover - defensive fallback
        return annotation
    return type_hints.get("return", annotation)


def _build_response_payload() -> Dict[str, Dict[str, Any]]:
    type_map: Dict[str, List[Type[BaseModel]]] = {}
    for api_cls, method_name in API_METHODS:
        method = getattr(api_cls, method_name)
        annotation = _get_return_annotation(method)
        model_type: Optional[Type[BaseModel]] = None
        origin = get_origin(annotation)
        if origin in (list, List):
            (model_arg,) = get_args(annotation) or (None,)
            if isinstance(model_arg, type) and issubclass(model_arg, BaseModel):
                model_type = model_arg
        elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
            model_type = annotation
        if model_type is None:
            continue
        source = inspect.getsource(method)
        keys = re.findall(r'get\("([^\"]+)"', source)
        if not keys:
            continue
        key = keys[0]
        bucket = type_map.setdefault(key, [])
        if model_type not in bucket:
            bucket.append(model_type)
    payload: Dict[str, Any] = {}
    for key, models in type_map.items():
        combined: Dict[str, Any] = {}
        entries = []
        for model in models:
            data = build_payload(model)
            entries.append(data)
            combined.update(data)
        if key == "time_logs":
            payload[key] = [{"log_details": entries}]
        elif key == "log_details":
            payload[key] = entries
        elif key.endswith("s"):
            payload[key] = [combined]
        else:
            payload[key] = combined
    return {method: dict(payload) for method in ("get", "post", "patch")}


SUCCESS_PAYLOADS = _build_response_payload()
EMPTY_PAYLOADS: Dict[str, Dict[str, Any]] = {
    method: {} for method in ("get", "post", "patch")
}


class DynamicClient:
    def __init__(
        self, payloads: Dict[str, Dict[str, Any]], error_method: Optional[str] = None
    ):
        self._auth_handler = SimpleNamespace(portal_id="portal-123")
        self.portal_id = "portal-123"
        self._payloads = payloads
        self._error_method = error_method

    async def _maybe_raise(self, method: str) -> None:
        if self._error_method == method:
            raise RuntimeError("simulated failure")

    async def get(  # pylint: disable=unused-argument
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        await self._maybe_raise("get")
        return dict(self._payloads.get("get", {}))

    async def post(  # pylint: disable=unused-argument
        self, endpoint: str, json: Dict[str, Any]
    ) -> Dict[str, Any]:
        await self._maybe_raise("post")
        return dict(self._payloads.get("post", {}))

    async def patch(  # pylint: disable=unused-argument
        self, endpoint: str, json: Dict[str, Any]
    ) -> Dict[str, Any]:
        await self._maybe_raise("patch")
        return dict(self._payloads.get("patch", {}))

    async def delete(  # pylint: disable=unused-argument
        self, endpoint: str
    ) -> Dict[str, Any]:
        await self._maybe_raise("delete")
        return {}


def _sample_argument(name: str, annotation: Any) -> Any:
    if annotation is inspect.Parameter.empty:
        return 1 if name.endswith("_id") else f"{name}_value"
    origin = get_origin(annotation)
    if origin in (list, List):
        (item_type,) = get_args(annotation) or (str,)
        return [] if item_type is Any else [_sample_argument(name, item_type)]
    if origin in (dict, Dict):
        key_type, value_type = get_args(annotation) or (str, Any)
        return {
            _sample_argument(f"{name}_key", key_type): _sample_argument(
                f"{name}_value", value_type
            )
        }
    if origin is Union:
        options = [
            option for option in get_args(annotation) if option is not type(None)
        ]
        # Prefer Pydantic models first so create/update calls receive valid payloads.
        for option in options:
            if isinstance(option, type) and issubclass(option, BaseModel):
                return build_model(option)
        # Special handling for TimelogFilters
        for option in options:
            if hasattr(option, "__name__") and option.__name__ == "TimelogFilters":
                from zoho_projects_sdk.api.timelogs import TimelogFilters

                return TimelogFilters()
        # Handle dataclass types (ListParams, TimelogRequestParams, TimelogOperationParams)
        for option in options:
            if hasattr(option, "__dataclass_fields__"):
                return _create_dataclass_instance(option)
        # Prefer mapping types next to provide structured payloads.
        for option in options:
            option_origin = get_origin(option)
            if option_origin in (dict, Dict):
                key_type, value_type = get_args(option) or (str, Any)
                key = _sample_argument(f"{name}_key", key_type)
                value = _sample_argument(f"{name}_value", value_type)
                return {key: value}
        # Fallback to simple scalar preferences.
        for preferred in (int, float):
            for option in options:
                if option is preferred:
                    return _sample_argument(name, option)
        for option in options:
            return _sample_argument(name, option)
        return None
    # Handle dataclass types directly
    if hasattr(annotation, "__dataclass_fields__"):
        return _create_dataclass_instance(annotation)
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return build_model(annotation)
    if annotation is bool:
        return True
    if annotation in {int, float}:
        return 1
    if annotation is str:
        return f"{name}_value"
    return 1 if name.endswith("_id") else f"{name}_value"


def _create_dataclass_instance(dataclass_type: Any) -> Any:
    """Create an instance of a dataclass with sample values."""
    import dataclasses

    if not hasattr(dataclass_type, "__dataclass_fields__"):
        return f"{dataclass_type.__name__}_value"

    fields = dataclasses.fields(dataclass_type)
    kwargs = {}

    for field in fields:
        field_name = field.name
        field_type = field.type

        # Handle default values
        if field.default is not dataclasses.MISSING:
            kwargs[field_name] = field.default
        elif field.default_factory is not dataclasses.MISSING:
            kwargs[field_name] = field.default_factory()
        else:
            # Create sample value based on field type
            if field_type == int:
                kwargs[field_name] = 1
            elif field_type == str:
                kwargs[field_name] = f"{field_name}_value"
            elif field_type == bool:
                kwargs[field_name] = True
            elif hasattr(field_type, "__dataclass_fields__"):
                kwargs[field_name] = _create_dataclass_instance(field_type)
            elif get_origin(field_type) is Union:
                # Handle Optional types
                args = get_args(field_type)
                if len(args) == 2 and type(None) in args:
                    # Optional type - use the non-None type
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    if non_none_type == int:
                        kwargs[field_name] = 1
                    elif non_none_type == str:
                        kwargs[field_name] = f"{field_name}_value"
                    elif non_none_type == bool:
                        kwargs[field_name] = True
                    else:
                        kwargs[field_name] = None
                else:
                    kwargs[field_name] = None
            else:
                kwargs[field_name] = None

    return dataclass_type(**kwargs)


def _build_arguments(method: Any) -> Dict[str, Any]:
    signature = inspect.signature(method)
    module = sys.modules.get(method.__module__)
    globalns = vars(module) if module is not None else None
    type_hints = get_type_hints(method, globalns=globalns)
    arguments: Dict[str, Any] = {}
    for param in signature.parameters.values():
        if param.name == "self":
            continue
        annotation = type_hints.get(param.name, param.annotation)
        arguments[param.name] = _sample_argument(param.name, annotation)
    return arguments


def _assert_result(method: Any, result: Any) -> None:
    annotation = _get_return_annotation(method)
    origin = get_origin(annotation)
    if annotation is inspect.Parameter.empty:
        return
    if annotation is bool:
        assert isinstance(result, bool)
        return
    if origin in (list, List):
        assert isinstance(result, list)
        (item_type,) = get_args(annotation) or (Any,)
        if isinstance(item_type, type) and issubclass(item_type, BaseModel) and result:
            assert isinstance(result[0], item_type)
        return
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        assert isinstance(result, annotation)
        return
    assert result is not None


def _http_method_for(method_name: str) -> str:
    post_methods = {
        "associate_bugs",
        "associate_with_module",
        "approve_timelog",
        "clone",
        "move",
        "reject_timelog",
    }
    if method_name.startswith("create") or method_name.startswith("bulk_create"):
        return "post"
    if method_name in post_methods:
        return "post"
    if method_name.startswith("update") or method_name.startswith("bulk_update"):
        return "patch"
    if method_name.startswith("delete") or method_name.startswith("bulk_delete"):
        return "delete"
    return "get"


@pytest.mark.asyncio()
@pytest.mark.parametrize("api_cls, method_name", API_METHODS)
async def test_api_methods_produce_expected_types(
    api_cls: Type[Any], method_name: str
) -> None:
    client = DynamicClient(SUCCESS_PAYLOADS)
    instance = api_cls(client)
    method = getattr(instance, method_name)
    result = await method(**_build_arguments(method))
    _assert_result(method, result)


@pytest.mark.asyncio()
@pytest.mark.parametrize("api_cls, method_name", API_METHODS)
async def test_api_methods_handle_empty_payloads(
    api_cls: Type[Any], method_name: str
) -> None:
    client = DynamicClient(EMPTY_PAYLOADS)
    instance = api_cls(client)
    method = getattr(instance, method_name)
    try:
        result = await method(**_build_arguments(method))
    except ValidationError:
        annotation = _get_return_annotation(method)
        assert isinstance(annotation, type) and issubclass(annotation, BaseModel)
        return
    _assert_result(method, result)


@pytest.mark.asyncio()
@pytest.mark.parametrize("api_cls, method_name", API_METHODS)
async def test_api_methods_surface_client_errors(
    api_cls: Type[Any], method_name: str
) -> None:
    client = DynamicClient(SUCCESS_PAYLOADS, error_method=_http_method_for(method_name))
    instance = api_cls(client)
    method = getattr(instance, method_name)
    with pytest.raises(RuntimeError):
        await method(**_build_arguments(method))
