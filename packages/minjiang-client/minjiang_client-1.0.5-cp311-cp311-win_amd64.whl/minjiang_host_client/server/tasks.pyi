from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.base.server import Server as Server

class TasksServer(Server):
    def __init__(self, name: str, group_name: str, in_chl: Channel = None, out_chl: Channel = None) -> None: ...
