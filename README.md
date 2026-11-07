# kindof

`kindof` provides a small, typed API for describing Python objects at runtime.
It is useful when an application needs stable metadata or a JSON-compatible
description without serializing an object's values directly.

```python
from kindof import inspect

description = inspect(instance)
print(description.schema)
```

The result exposes `type`, `fields`, `methods`, `signatures`, `annotations`, and
a recursive JSON-compatible `schema`. Instance fields, class fields,
properties, inherited members, and safely introspectable method signatures are
included. Unsupported or dynamic members are omitted.

## Installation

```shell
python -m pip install kindof
```

## Quick example

```python
from kindof import inspect


class User:
    name: str
    active: bool = True

    def greet(self, punctuation: str = "!") -> str:
        return f"{self.name}{punctuation}"


user = User()
user.name = "Ada"
result = inspect(user)

assert result.fields["name"].required is False
assert result.methods["greet"].signature == "(self, punctuation: str = '!') -> str"
assert result.schema["properties"]["name"] == {"type": "string"}
```

See [the API guide](docs/api.md) for the complete result model and schema
mapping, and [the examples](docs/examples.md) for more usage patterns.
