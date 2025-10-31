from .korada_plugin import get_plugin
from qvoid_fusion.plugins.geolocate_plugin import get_plugin as geo_plugin


registered_plugins = [
    get_plugin(),
    geo_plugin()  # Returns KoradaModulePlugin instance
]
