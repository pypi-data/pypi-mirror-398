"""
Implemets redlite web server.

To start server, one can do this:

```bash
python -m redlite.server
```

or, more conveniently:

```bash
redlite server
```
"""

import os

__all__: list[str] = []


def res(*av: str) -> str:
    return os.path.join(os.path.dirname(__file__), "resources", *av)
