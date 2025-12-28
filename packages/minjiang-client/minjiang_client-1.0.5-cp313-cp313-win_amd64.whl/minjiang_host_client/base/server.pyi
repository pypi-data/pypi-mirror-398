from _typeshed import Incomplete
from minjiang_host_client.base.channel import Channel as Channel
from multiprocessing import Process

class Server:
    name: Incomplete
    group_name: Incomplete
    input_channel: Incomplete
    output_channel: Incomplete
    cache: Incomplete
    running: Incomplete
    interval: Incomplete
    def __init__(self, name: str, group_name: str, input_channel: Channel = None, output_channel: Channel = None, interval: float = 0.01) -> None: ...
    def finished_starting(self) -> None: ...
    def run(self) -> None: ...
    def process(self, data): ...
    def make_process(self) -> Process: ...
