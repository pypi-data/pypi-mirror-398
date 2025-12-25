# Usage

To use powerfx in a project:

```python
from powerfx import Engine  # type: ignore
engine = Engine()
result = engine.eval("With({x:1}, x + 1)") # should return 2
```
