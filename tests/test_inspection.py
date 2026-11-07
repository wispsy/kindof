import json
from typing import Optional

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


def test_inspect_collects_fields_methods_and_inheritance():
    result = inspect(User("Ada"))

    assert result.type.endswith(".User")
    assert set(result.fields) >= {"name", "age", "inherited", "display_name"}
    assert set(result.methods) >= {"greet", "inherited_method"}
    assert result.signatures["greet"] == "(self, punctuation: Optional[str] = None) -> str"
    assert result.fields["display_name"].kind == "property"
    assert result.annotations["name"] == "str"


def test_schema_and_to_dict_are_json_compatible():
    payload = inspect(User).to_dict()

    assert payload["schema"]["type"] == "object"
    assert payload["schema"]["properties"]["name"] == {"type": "string"}
    assert payload["schema"]["properties"]["age"] == {"type": "integer"}
    assert payload["schema"]["properties"]["display_name"] == {}
    json.dumps(payload)
