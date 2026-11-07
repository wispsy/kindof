# kindof

`kindof` provides a small, typed API for describing Python objects:

```python
from kindof import inspect

description = inspect(instance)
print(description.schema)
```

The result exposes `type`, `fields`, `methods`, `signatures`, `annotations`, and
a recursive JSON-compatible `schema`. Instance fields, class fields,
properties, inherited members, and safely introspectable method signatures are
included. Unsupported or dynamic members are omitted.
