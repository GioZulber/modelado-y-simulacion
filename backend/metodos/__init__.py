"""
Auto-discovery of numerical methods from clase*.py files.

Every module in this package whose name starts with "clase" and defines
a ``METODOS`` dict will have its methods merged into the global
``REGISTRY``.  Adding a new file is all that's needed to extend the app.
"""

import importlib
import pkgutil
import pathlib

REGISTRY: dict = {}


def _discover():
    """Scan this package for clase* modules and merge their METODOS dicts."""
    package_dir = pathlib.Path(__file__).parent

    for finder, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if not module_name.startswith("clase"):
            continue
        module = importlib.import_module(f".{module_name}", package=__name__)
        metodos = getattr(module, "METODOS", None)
        if isinstance(metodos, dict):
            REGISTRY.update(metodos)


_discover()
