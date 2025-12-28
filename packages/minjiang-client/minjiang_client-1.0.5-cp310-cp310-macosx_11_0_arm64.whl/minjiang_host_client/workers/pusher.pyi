from _typeshed import Incomplete
from minjiang_client.com.minio import MinIOAPI
from minjiang_client.experiment.result import Result
from minjiang_client.group.cloud_group import CloudGroup
from minjiang_client.utils.task_status import ERROR as ERROR, TIMEOUT as TIMEOUT
from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.base.worker import Worker as Worker
from minjiang_host_client.base.worker_monitors import PusherMonitor as PusherMonitor
from minjiang_host_client.direct_group import DirectLinkWorkerClient as DirectLinkWorkerClient
from minjiang_host_client.utils.local import get_cache_dir as get_cache_dir, set_cache_dir as set_cache_dir
from minjiang_host_client.utils.terminate import check_terminate_signal as check_terminate_signal
from typing import Any

__MAX_UPLOAD_DURATION__: int
__MAX_UPLOAD_STEPS__: int

class ExpAgent:
    worker_name: Incomplete
    group_name: Incomplete
    exp_id: Incomplete
    direct_exp_id: Incomplete
    direct_link: Incomplete
    space_name: str | None
    organization_id: int | None
    priority: Incomplete
    last_touch_time: Incomplete
    group: CloudGroup | None
    pos: list[int] | None
    steps: int | None
    total_steps: int | None
    exp_json: dict | None
    exp_options: dict[str, Any] | None
    exp_obj: Any | None
    minio: Incomplete
    result: Incomplete
    result_cache: Incomplete
    result_obj: Result | None
    accumulated_result_obj: Result | None
    cache_dir: Incomplete
    direct_link_client: DirectLinkWorkerClient | None
    compiled_sweep_len: Incomplete
    last_upload_time: int
    last_upload_step: int
    chunk_id: int
    image_uploaded: bool
    def __init__(self, worker_name: str, group_name: str, organization_id: int, cache_dir: str, direct_link_client: DirectLinkWorkerClient, minio_client: MinIOAPI, received: dict) -> None: ...
    def print(self, *args, sep: str = ' ', end: str = '\n', file=None) -> None: ...
    def save_data(self, received: Any = None) -> bool: ...
    def upload_to_direct(self, final) -> None: ...
    def upload_to_cloud(self, final) -> None: ...
    def generate_and_upload_plot_image(self) -> None: ...

class PusherWorker(Worker):
    space_name: str | None
    organization_id: int | None
    minio: Incomplete
    cache_dir: Incomplete
    direct_link_client: DirectLinkWorkerClient | None
    history: Incomplete
    cleanup_thread: Incomplete
    cleanup_running: bool
    direct_link_server: str
    direct_link_port: int
    monitor: Incomplete
    def __init__(self, name: str, group_name: str, in_chl: Channel = None, out_chl: Channel = None, dl_server: str = 'localhost', dl_port: int = 6887) -> None: ...
    def run(self) -> None: ...
    def start_cleanup_thread(self) -> None: ...
    def stop_cleanup_thread(self) -> None: ...
    def process_data(self, data: Any = None): ...
