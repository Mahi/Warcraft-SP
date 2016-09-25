"""Package which imports all hero classes from all modules."""

# Python 3 imports
import sys

# Warcraft imports
from warcraft.utilities import get_classes_from_module
from warcraft.utilities import import_submodules
from warcraft.entities import Hero

__all__ = (
    'get_heroes',
)


def get_heroes():
    """Yield all the heroes to use on the server.

    Automatically goes through every module in the ``heroes`` directory,
    importing every ``Hero`` subclass class from the modules.

    Ignores modules and classes with a leading underscore in their name.
    """
    heroes_package = sys.modules['warcraft.heroes']
    for module in import_submodules(heroes_package):
        for cls in get_classes_from_module(module):
            if issubclass(cls, Hero):
                yield cls
