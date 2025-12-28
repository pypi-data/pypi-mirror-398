from _typeshed import Incomplete
from minjiang_client.group.cloud_group import CloudGroup
from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.base.worker import Worker as Worker
from minjiang_host_client.base.worker_monitors import PostProcessMonitor as PostProcessMonitor
from minjiang_host_client.utils.terminate import check_terminate_signal as check_terminate_signal
from typing import Any

class PostProcessWorker(Worker):
    space_name: str | None
    local_space_timestamp: int | None
    pos: list[int] | None
    steps: int | None
    total_steps: int | None
    compiled_sweep_len: list[int] | None
    exp_json: dict | None
    exp_options: dict[str, Any] | None
    temporary_parameters: dict[str, Any] | None
    post_process_space_cache_timestamp: int | None
    raw_result: dict | None
    final_result: dict | None
    direct_link_server: str
    direct_link_port: int
    monitor: Incomplete
    def __init__(self, name: str, group_name: str, in_chl: Channel = None, out_chl: Channel = None, dl_server: str = 'localhost', dl_port: int = 6887) -> None: ...
    @property
    def group(self) -> CloudGroup: ...
    @group.setter
    def group(self, value: CloudGroup): ...
    def post_process(self) -> None: ...
    exp_id: Incomplete
    priority: Incomplete
    direct_link: Incomplete
    direct_exp_id: Incomplete
    def process_data(self, data: Any = None): ...
