# lia-web has been renamed to cross-web

This package has been renamed to [cross-web](https://pypi.org/project/cross-web/).

Please update your dependencies to use `cross-web` instead:

```bash
uv add cross-web
# or
pip install cross-web
```

And update your imports from:

```python
from lia import Response
```

to:

```python
from cross import Response
```

## Backwards Compatibility

This package (`lia-web`) now depends on `cross-web` and re-exports all its symbols under the `lia` namespace for backwards compatibility. However, we recommend updating your imports to use `cross` directly.
