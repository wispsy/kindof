"""Runtime object inspection with a stable, JSON-compatible result."""

from __future__ import annotations

import inspect as _inspect
import json
import types
import typing
from dataclasses import dataclass, field
from typing import Any

_UNION_TYPE = getattr(types, "UnionType", None)


def _type_name(value: Any) -> str:
    if value is Any:
        return "Any"
    if isinstance(value, str):
        return value
    origin = typing.get_origin(value)
    if origin is typing.Union or (
        _UNION_TYPE is not None and origin is _UNION_TYPE
    ):
        return " | ".join(_type_name(item) for item in typing.get_args(value))
    if origin is not None:
        name = getattr(origin, "__name__", str(origin))
        args = ", ".join(_type_name(item) for item in typing.get_args(value))
        return f"{name}[{args}]" if args else name
    return getattr(value, "__qualname__", getattr(value, "__name__", str(value)))


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return repr(value)
    return value


def _safe_annotations(cls: type[Any]) -> dict[str, Any]:
    try:
        return dict(typing.get_type_hints(cls))
    except (NameError, TypeError, ValueError):
        annotations: dict[str, Any] = {}
        for base in reversed(cls.__mro__):
            annotations.update(getattr(base, "__annotations__", {}))
        return annotations


def _safe_signature(member: Any) -> str | None:
    try:
        return str(_inspect.signature(member))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class FieldInfo:
    """Description of an inspectable field."""

    name: str
    type: str
    default: Any = None
    required: bool = False
    kind: str = "field"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "default": _json_value(self.default),
            "required": self.required,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class MethodInfo:
    """Description of an inspectable method."""

    name: str
    signature: str | None
    annotations: dict[str, str] = field(default_factory=dict)
    kind: str = "method"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "signature": self.signature,
            "annotations": dict(self.annotations),
            "kind": self.kind,
        }


@dataclass(frozen=True)
class InspectionResult:
    """Structured inspection data returned by :func:`inspect`."""

    type: str
    fields: dict[str, FieldInfo]
    methods: dict[str, MethodInfo]
    signatures: dict[str, str]
    annotations: dict[str, str]
    schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a recursively JSON-compatible representation."""
        return {
            "type": self.type,
            "fields": {name: value.to_dict() for name, value in self.fields.items()},
            "methods": {name: value.to_dict() for name, value in self.methods.items()},
            "signatures": dict(self.signatures),
            "annotations": dict(self.annotations),
            "schema": self.schema,
        }


def _schema_for(annotation: Any) -> dict[str, Any]:
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if annotation is Any:
        return {}
    if origin is typing.Union or (
        _UNION_TYPE is not None and origin is _UNION_TYPE
    ):
        non_none = [item for item in args if item is not type(None)]
        if len(non_none) != len(args):
            return _schema_for(non_none[0]) if len(non_none) == 1 else {
                "anyOf": [_schema_for(item) for item in non_none]
            }
        return {"anyOf": [_schema_for(item) for item in args]}
    if origin in (list, tuple, set, frozenset):
        return {"type": "array", "items": _schema_for(args[0]) if args else {}}
    if origin is dict:
        return {"type": "object"}
    primitive = {str: "string", int: "integer", float: "number", bool: "boolean"}
    if annotation in primitive:
        return {"type": primitive[annotation]}
    return {"type": "object"}


def inspect(obj: Any) -> InspectionResult:
    """Inspect an object or class and return stable metadata."""
    cls = obj if _inspect.isclass(obj) else type(obj)
    annotations = _safe_annotations(cls)
    values = (
        {}
        if _inspect.isclass(obj)
        else vars(obj)
        if hasattr(obj, "__dict__")
        else {}
    )
    fields: dict[str, FieldInfo] = {}

    for name, annotation in annotations.items():
        class_member = getattr(cls, name, None)
        if callable(class_member):
            continue
        member = getattr(obj, name, class_member)
        has_class_default = (
            name in cls.__dict__
            and not isinstance(class_member, types.MemberDescriptorType)
            and not isinstance(class_member, property)
        )
        has_default = name in values or has_class_default
        fields[name] = FieldInfo(
            name=name,
            type=_type_name(annotation),
            default=values.get(name, member),
            required=not has_default,
            kind="property" if isinstance(class_member, property) else "field",
        )

    for name, value in values.items():
        if name.startswith("_") or name in fields or callable(value):
            continue
        fields[name] = FieldInfo(name, _type_name(type(value)), value)

    for name, member in _inspect.getmembers(cls):
        if name.startswith("_") or name in fields:
            continue
        if isinstance(member, property):
            fields[name] = FieldInfo(
                name,
                _type_name(annotations.get(name, Any)),
                kind="property",
            )

    methods: dict[str, MethodInfo] = {}
    signatures: dict[str, str] = {}
    for name, member in _inspect.getmembers(cls, callable):
        if name.startswith("_"):
            continue
        signature = _safe_signature(member)
        if signature is None:
            continue
        try:
            method_annotations = {
                key: _type_name(value)
                for key, value in typing.get_type_hints(member).items()
            }
        except (NameError, TypeError, ValueError):
            method_annotations = {}
        descriptor = cls.__dict__.get(name)
        kind = "classmethod" if isinstance(descriptor, classmethod) else "method"
        methods[name] = MethodInfo(name, signature, method_annotations, kind)
        signatures[name] = signature

    schema_properties = {
        name: _schema_for(
            annotations.get(name, type(values[name]) if name in values else Any)
        )
        for name in fields
    }
    schema: dict[str, Any] = {
        "type": "object",
        "title": cls.__name__,
        "properties": schema_properties,
    }
    required = [name for name, info in fields.items() if info.required]
    if required:
        schema["required"] = required

    return InspectionResult(
        type=f"{cls.__module__}.{cls.__qualname__}",
        fields=fields,
        methods=methods,
        signatures=signatures,
        annotations={name: _type_name(value) for name, value in annotations.items()},
        schema=schema,
    )
