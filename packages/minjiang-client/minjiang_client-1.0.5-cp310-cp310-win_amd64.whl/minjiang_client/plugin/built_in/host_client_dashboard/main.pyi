from _typeshed import Incomplete
from minjiang_client.plugin.plugin_object import PluginObject as PluginObject

__MJ_PLUGIN_NAME__: str
__MJ_PLUGIN_HOOKS__: Incomplete

class Main(PluginObject):
    plugin_name: Incomplete
    hooks: Incomplete
    def __init__(self) -> None: ...
    def utility_server_register(self, *args, **kwargs): ...
