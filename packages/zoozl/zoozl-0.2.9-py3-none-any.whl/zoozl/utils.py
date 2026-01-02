"""Utilities for zoozl package."""

import types


def load_from_module(module: types.ModuleType, parent: type):
    """Generate objects inheriting parent from a module."""
    for item in dir(module):
        i = getattr(module, item)
        if isinstance(i, type) and issubclass(i, parent) and i is not parent:
            yield i
