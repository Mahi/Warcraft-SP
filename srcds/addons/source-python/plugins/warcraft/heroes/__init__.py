"""Package which imports all hero classes from all modules."""

# Python 3 imports
import importlib
import inspect
import pkgutil

# Source.Python imports
from paths import PLUGIN_PATH

# Warcraft imports
from warcraft.entities import Hero

__all__ = (
    'get_heroes',
)

# Path for the 'warcraft/heroes' directory for automatic importing
_PATH = PLUGIN_PATH / 'warcraft' / 'heroes'


def get_heroes():
    """Yield all the heroes to use on the server.

    Automatically goes through every module in the ``heroes`` directory,
    importing every ``Hero`` subclass class from the modules.

    Ignores modules and classes with a leading underscore in their name.
    """
    for finder, module_name, ispkg in pkgutil.iter_modules([_PATH]):
        if module_name.startswith('_'):  # Includes __init__.py
            continue
        module = importlib.import_module('warcraft.heroes.' + module_name)
        
        for obj_name, obj in inspect.getmembers(module):
            if obj_name.startswith('_') or obj_name == 'Hero':
                continue
            if inspect.isclass(obj) and issubclass(obj, Hero):
                yield obj
