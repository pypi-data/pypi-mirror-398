from __future__ import annotations

from collections.abc import Sequence as ABCSequence
from datetime import date, datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel, ValidationError


def _sample_scalar(field_name: str, annotation: Any) -> Any:
    if annotation in {str, Optional[str]}:
        return f"{field_name}_value"
    if annotation in {int, Optional[int]}:
        return 1
    if annotation in {float, Optional[float]}:
        return 1.0
    if annotation in {bool, Optional[bool]}:
        return True
    if annotation in {datetime, Optional[datetime]}:
        return datetime(2024, 1, 1, 0, 0, 0)
    if annotation in {date, Optional[date]}:
        return date(2024, 1, 1)
    if annotation in {dict, Dict, Optional[dict], Optional[Dict]}:
        return {"key": f"{field_name}_value"}
    if annotation in {list, List, Optional[list], Optional[List]}:
        return [f"{field_name}_value"]
    if annotation in {Sequence, Optional[Sequence], ABCSequence, Optional[ABCSequence]}:
        return [f"{field_name}_value"]
    if annotation is Any:
        return f"{field_name}_value"
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return build_payload(annotation)
    return f"{field_name}_value"


def _sample_value(field_name: str, annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is None:
        return _sample_scalar(field_name, annotation)

    if origin in (list, List, Sequence, ABCSequence):
        (inner_annotation,) = get_args(annotation) or (Any,)
        inner_value = _sample_value(field_name, inner_annotation)
        return [] if inner_value is None else [inner_value]

    if origin in (dict, Dict):
        key_annotation, value_annotation = get_args(annotation) or (str, Any)
        key = _sample_value(f"{field_name}_key", key_annotation)
        value = _sample_value(f"{field_name}_value", value_annotation)
        return {key: value}

    if origin is tuple:
        values = [
            _sample_value(f"{field_name}_{index}", arg)
            for index, arg in enumerate(get_args(annotation))
        ]
        return tuple(values)

    if origin is Union:
        options = [
            option for option in get_args(annotation) if option is not type(None)
        ]
        for preferred in (int, float, datetime, date):
            for option in options:
                if option is preferred:
                    return _sample_value(field_name, option)
        for option in options:
            if isinstance(option, type) and issubclass(option, BaseModel):
                try:
                    return _sample_value(field_name, option)
                except ValidationError:
                    continue
        for option in options:
            candidate = _sample_value(field_name, option)
            if candidate is not None:
                return candidate
        return None

    return _sample_scalar(field_name, annotation)


def build_payload(
    model: Type[BaseModel], overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    overrides = overrides or {}

    for field_name, field_info in model.model_fields.items():
        alias = field_info.alias or field_name
        if alias in overrides:
            data[alias] = overrides[alias]
            continue

        value = _sample_value(alias, field_info.annotation)
        if value is None:
            value = f"{alias}_value"
        data[alias] = value

    return data


def build_model(
    model: Type[BaseModel], overrides: Optional[Dict[str, Any]] = None
) -> BaseModel:
    payload = build_payload(model, overrides=overrides)
    return model.model_validate(payload)
