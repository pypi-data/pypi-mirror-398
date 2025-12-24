"""
application entry point
"""

import sys
from importlib.metadata import entry_points, PackageNotFoundError
from .. import eps_dict


def load_plugins():
    """ Loads all plugins and registers all classes in globals"""
    try:
        if sys.version_info >= (3, 10):
            plugin_eps = entry_points(group=__name__)
        else:
            plugin_eps = entry_points().get(__name__, [])

        plugin_modules_dict = {
            ep.name: ep.load()
            for ep in plugin_eps
        }

        for module_name, module in plugin_modules_dict.items():
            for attribute, value in module.__dict__.items():
                if not attribute.startswith('_'):
                    if hasattr(value, "_get_name"):
                        eps_dict[value._get_name()] = value
    except PackageNotFoundError as e:
        log.print(e)


load_plugins()
