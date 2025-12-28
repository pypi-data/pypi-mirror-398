from _typeshed import Incomplete
from minjiang_client.com.command import upload_print as upload_print
from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.base.server import Server as Server
from minjiang_host_client.utils.device_manager import DeviceManager as DeviceManager

class MainServer(Server):
    SUPPORTED_COMMAND_TYPES: list[str]
    enable_device_manager: Incomplete
    device_manager: DeviceManager | None
    def __init__(self, name: str, group_name: str, in_chl: Channel = None, out_chl: Channel = None, enable_device_manager: bool = True) -> None: ...
    def run(self) -> None: ...
