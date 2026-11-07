import json
from typing import Any, Optional, Union

from kindof import inspect


class Parent:
    inherited: str = "parent"

    def inherited_method(self, value: int) -> str:
        return str(value)


class User(Parent):
    name: str
    age: int = 0

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def display_name(self) -> str:
        return self.name.upper()

    def greet(self, punctuation: Optional[str] = None) -> str:
        return self.name + (punctuation or "!")


class Complex:
    text: str
    values: list[int]
    mapping: dict[str, int]
    maybe: Optional[str]
    choice: Union[int, str]
    unknown: Any

    @classmethod
    def make(cls, value: int) -> "Complex":
        return cls()


class WithSlots:
    __slots__ = ("value",)
    value: int


def test_inspect_collects_fields_methods_and_inheritance() -> None:
    result = inspect(User("Ada"))

    assert result.type.endswith(".User")
    assert set(result.fields) >= {"name", "age", "inherited", "display_name"}
    assert set(result.methods) >= {"greet", "inherited_method"}
    assert (
        result.signatures["greet"]
        == "(self, punctuation: Optional[str] = None) -> str"
    )
    assert result.fields["display_name"].kind == "property"
    assert result.annotations["name"] == "str"
    assert result.fields["name"].required is False
    assert result.fields["inherited"].default == "parent"


def test_inspecting_a_class_does_not_read_instance_values() -> None:
    result = inspect(User)

    assert result.fields["name"].required is True
    assert result.fields["name"].default is None
    assert result.fields["age"].default == 0


def test_schema_and_to_dict_are_json_compatible() -> None:
    payload = inspect(User).to_dict()

    assert payload["schema"]["type"] == "object"
    assert payload["schema"]["properties"]["name"] == {"type": "string"}
    assert payload["schema"]["properties"]["age"] == {"type": "integer"}
    assert payload["schema"]["properties"]["display_name"] == {}
    json.dumps(payload)


def test_schema_handles_recursive_containers_unions_and_any() -> None:
    schema = inspect(Complex).schema

    assert schema["properties"]["values"] == {
        "type": "array",
        "items": {"type": "integer"},
    }
    assert schema["properties"]["mapping"] == {"type": "object"}
    assert schema["properties"]["maybe"] == {"type": "string"}
    assert schema["properties"]["choice"] == {
        "anyOf": [{"type": "integer"}, {"type": "string"}]
    }
    assert schema["properties"]["unknown"] == {}
    assert set(schema["required"]) >= {
        "text",
        "values",
        "mapping",
        "maybe",
        "choice",
        "unknown",
    }


def test_method_metadata_includes_annotations_and_classmethod_kind() -> None:
    result = inspect(Complex)

    assert result.methods["make"].kind == "classmethod"
    assert result.methods["make"].signature == "(value: int) -> 'Complex'"
    assert result.methods["make"].annotations == {"value": "int", "return": "Complex"}
    assert result.signatures["make"] == result.methods["make"].signature


def test_slots_only_objects_are_safe_to_inspect() -> None:
    result = inspect(WithSlots())

    assert result.fields["value"].required is True
    assert result.schema["properties"]["value"] == {"type": "integer"}


def test_private_and_callable_instance_values_are_omitted() -> None:
    class Dynamic:
        visible: int = 1

        def __init__(self) -> None:
            self.extra = object()
            self._private = "hidden"
            self.callback = lambda: None

    result = inspect(Dynamic())

    assert "extra" in result.fields
    assert "_private" not in result.fields
    assert "callback" not in result.fields
    assert isinstance(result.to_dict()["fields"]["extra"]["default"], str)
