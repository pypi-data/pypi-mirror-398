import queue
from _typeshed import Incomplete
from minjiang_host_client.base.channel import Channel as Channel
from minjiang_host_client.base.worker import Worker as Worker
from minjiang_host_client.base.worker_monitors import PullerMonitor as PullerMonitor
from minjiang_host_client.direct_group import DirectLinkWorkerClient as DirectLinkWorkerClient
from minjiang_host_client.utils.terminate import check_terminate_signal as check_terminate_signal, cleanup_old_ts_files as cleanup_old_ts_files, list_terminate_signal as list_terminate_signal, write_terminate_signal as write_terminate_signal
from typing import Any

class PullerWorker(Worker):
    connection_status: Incomplete
    sent_signal_exp_id_list: Incomplete
    dl_worker: DirectLinkWorkerClient | None
    task_queue: queue.Queue | None
    stop_event: Incomplete
    producer_thread1: Incomplete
    producer_thread2: Incomplete
    consumer_thread: Incomplete
    transfer_queue: Incomplete
    direct_link_server: str
    direct_link_port: int
    monitor: PullerMonitor | None
    def __init__(self, name: str, group_name: str, in_chl: Channel = None, out_chl: Channel = None, dl_server: str = 'localhost', dl_port: int = 6887) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def producer1(self) -> None: ...
    def producer2(self) -> None: ...
    def consumer(self) -> None: ...
    def process_task(self, task: dict): ...
    def check_terminate_signal(self) -> None: ...
    def process_data(self, data: Any = None): ...
