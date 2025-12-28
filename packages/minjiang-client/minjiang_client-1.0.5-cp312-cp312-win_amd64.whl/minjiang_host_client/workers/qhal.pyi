from _typeshed import Incomplete
from minjiang_client.group.cloud_group import CloudGroup
from minjiang_client.waveform import WavePackage
from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.base.worker import Worker as Worker
from minjiang_host_client.base.worker_monitors import QHALMonitor as QHALMonitor
from minjiang_host_client.utils.terminate import check_terminate_signal as check_terminate_signal
from typing import Any

class QHALWorker(Worker):
    space_name: str | None
    local_space_timestamp: int | None
    pos: list[int] | None
    steps: int | None
    total_steps: int | None
    compiled_sweep_len: list[int] | None
    exp_json: dict | None
    exp_options: dict[str, Any] | None
    temporary_parameters: dict[str, Any] | None
    qhal_space_cache_timestamp: int | None
    wave_package: WavePackage | None
    compiled_data: dict | None
    qhal_full_timing: Incomplete
    direct_link_server: str
    direct_link_port: int
    monitor: Incomplete
    monitor_exp_id: Incomplete
    def __init__(self, name: str, group_name: str, in_chl: Channel = None, out_chl: Channel = None, dl_server: str = 'localhost', dl_port: int = 6887) -> None: ...
    @property
    def group(self) -> CloudGroup: ...
    @group.setter
    def group(self, value: CloudGroup): ...
    def qhal_run(self): ...
    exp_id: Incomplete
    priority: Incomplete
    direct_link: Incomplete
    direct_exp_id: Incomplete
    def process_data(self, data: Any = None): ...
