from _typeshed import Incomplete
from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.utils.request import request as request
from minjiang_host_client.utils.terminate import upload_cancel_status as upload_cancel_status, write_terminate_signal as write_terminate_signal
from minjiang_host_client.utils.worker_registrar import register_worker as register_worker, unregister_worker as unregister_worker
from multiprocessing import Process
from typing import Any

class Worker:
    name: str
    group_name: str
    input_channel: Channel
    output_channel: Channel
    running: Incomplete
    exp_id: int | None
    direct_link: bool
    direct_exp_id: int | None
    priority: str
    direct_link_server: Incomplete
    direct_link_port: Incomplete
    monitor: Incomplete
    def __init__(self, name: str, group_name: str, input_channel: Channel = None, output_channel: Channel = None, direct_link_server: str = 'localhost', direct_link_port: int = 6887) -> None: ...
    def process_data(self, data: Any = None) -> bytes: ...
    def print(self, *args, sep: str = ' ', end: str = '\n', file=None) -> None: ...
    def run(self) -> None: ...
    def write_data(self, data: bytes): ...
    def make_process(self) -> Process: ...
