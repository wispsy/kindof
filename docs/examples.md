# Examples

## Inspecting a class

```python
from kindof import inspect


class Account:
    owner: str
    balance: float = 0.0

    @property
    def label(self) -> str:
        return f"{self.owner}: {self.balance:.2f}"


result = inspect(Account)
print(result.annotations)
print(result.fields["label"].kind)
print(result.schema)
```

Inspecting the class is useful for documentation, forms, and API discovery.
Inspecting an instance additionally captures public attributes assigned at
runtime.

## Recursive annotations

```python
from typing import Optional

from kindof import inspect


class Profile:
    tags: list[str]
    preferences: dict[str, int]
    nickname: Optional[str]


schema = inspect(Profile).schema
assert schema["properties"]["tags"] == {
    "type": "array",
    "items": {"type": "string"},
}
assert schema["properties"]["preferences"] == {"type": "object"}
assert schema["properties"]["nickname"] == {"type": "string"}
```

## Exporting metadata

```python
import json

from kindof import inspect

metadata = inspect(Profile).to_dict()
with open("profile-metadata.json", "w", encoding="utf-8") as output:
    json.dump(metadata, output, indent=2)
```

`to_dict()` converts dataclass records and non-JSON defaults into a stable
mapping suitable for logs, documentation generators, or API responses.
