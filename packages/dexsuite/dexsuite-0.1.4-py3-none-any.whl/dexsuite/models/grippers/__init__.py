import pkgutil
from importlib import import_module

for m in pkgutil.walk_packages(__path__, __name__ + "."):
    import_module(m.name)
