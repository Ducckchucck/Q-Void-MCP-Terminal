from .korada_plugin import get_plugin

registered_plugins = [
    get_plugin()  # Returns KoradaModulePlugin instance
]
