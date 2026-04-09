---
description: "Use when writing or editing Python code. Enforces top-level-only imports — no inline, conditional, or deferred imports inside functions, methods, or classes."
applyTo: "**/*.py"
---
# Python Import Rule

**All imports must be at the top level of the module.** This is a hard rule with no exceptions.

- Place all `import` and `from ... import` statements at the top of the file, after any module docstring and `__future__` imports, and before all other code.
- Never place imports inside functions, methods, classes, `if` blocks, `try` blocks, or any other nested scope.

## Correct

```python
import os
from pathlib import Path

def load_config(path: str) -> dict:
    return Path(path).read_text()
```

## Forbidden

```python
def load_config(path: str) -> dict:
    import os          # ❌ import inside function
    from pathlib import Path  # ❌ import inside function
    ...
```

```python
try:
    import ujson as json   # ❌ import inside try block
except ImportError:
    import json            # ❌ import inside except block
```

```python
if TYPE_CHECKING:
    from typing import Optional  # ❌ import inside if block
```

If an optional dependency may not be installed, handle it at the top level with a guarded import and a clear error at call time, not a deferred import:

```python
try:
    import ujson as json  # ❌ still forbidden — see below
except ImportError:
    json = None  # ❌

# ✅ Instead, declare at top level and fail fast at call time:
import json  # or require the dependency in pyproject.toml
```

The preferred solution for optional dependencies is to declare them as required or provide a stub at module level, never to import lazily.
