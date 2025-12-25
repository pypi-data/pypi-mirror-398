"""Manipulator model package.

Submodules are imported eagerly so registration decorators run at import time.
"""

import pkgutil
from importlib import import_module

# discover sub-modules so decorators run
for m in pkgutil.walk_packages(__path__, __name__ + "."):
    import_module(m.name)
