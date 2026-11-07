# API guide

`kindof` exposes one function and three immutable result types:

```python
from kindof import FieldInfo, InspectionResult, MethodInfo, inspect
```

## `inspect(obj)`

`inspect` accepts either an object instance or a class and returns an
`InspectionResult`. Class inspection describes declared and inherited metadata;
instance inspection also includes public values found in `__dict__`.

The result has these attributes:

| Attribute | Type | Description |
| --- | --- | --- |
| `type` | `str` | Fully qualified name of the inspected class. |
| `fields` | `dict[str, FieldInfo]` | Public data fields and properties. |
| `methods` | `dict[str, MethodInfo]` | Public methods with safe signatures. |
| `signatures` | `dict[str, str]` | A convenient name-to-signature view. |
| `annotations` | `dict[str, str]` | Class annotations rendered as readable strings. |
| `schema` | `dict[str, Any]` | JSON Schema-like object metadata. |

Use `result.to_dict()` when a recursively JSON-compatible mapping is needed:

```python
import json

payload = inspect(obj).to_dict()
json.dumps(payload)
```

### Fields

`FieldInfo` contains `name`, `type`, `default`, `required`, and `kind`.
`kind` is `"field"` for regular fields and `"property"` for properties.
Inherited fields are included. A field is required when it has an annotation
but no class or instance default.

### Methods

`MethodInfo` contains `name`, `signature`, `annotations`, and `kind`.
Inherited public methods are included. Methods whose signatures cannot be
safely read are omitted rather than raising. `kind` distinguishes ordinary
methods from class methods.

### Schema mapping

The schema is an object with the inspected class name as `title` and one
property per discovered field. The supported annotation mappings are:

| Python annotation | Schema |
| --- | --- |
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `list[T]`, `tuple[T]`, `set[T]`, `frozenset[T]` | `{"type": "array", "items": ...}` |
| `dict[...]` | `{"type": "object"}` |
| `Optional[T]` | The schema for `T` |
| `Union[A, B]` | `{"anyOf": [...]}` |
| `Any` or an unknown type | `{}` or `{"type": "object"}` |

Nested containers are represented recursively. The `required` list is present
only when one or more fields are required.
