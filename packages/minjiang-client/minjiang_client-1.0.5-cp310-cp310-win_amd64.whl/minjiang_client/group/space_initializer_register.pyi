from minjiang_client.group.space_initializer import SpaceInitializer as SpaceInitializer
from minjiang_client.languages import lang as lang
from minjiang_client.plugin.plugin_register import plugin_register as plugin_register
from minjiang_client.utils import single_decorator as single_decorator
from minjiang_client.utils.config_manager import ConfigManager as ConfigManager
from typing import Any

class SpaceInitializerRegister:
    def __init__(self) -> None: ...
    def reg_initializer(self, initializer_name: str, initializer_detail: dict[str, Any]): ...
    def get_initializer(self, initializer_name: str, **kwargs) -> SpaceInitializer: ...
    def list_initializers(self) -> Any: ...

space_initializer_register: SpaceInitializerRegister
