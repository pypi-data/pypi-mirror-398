#!/usr/bin/python3
# -*- coding: utf8 -*-
# Copyright (c) 2025 ZWDX, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import traceback

import minjiang_client
from minjiang_client.group.cloud_group import CloudGroup
from minjiang_host_client.server.final import FinalServer
from minjiang_host_client.server.main import MainServer
from minjiang_host_client.server.direct_link import DirectLinkServer
from minjiang_host_client.server.result import ResultServer
from minjiang_host_client.server.tasks import TasksServer
from minjiang_host_client.server.waveform import WaveformServer
from minjiang_host_client.workers.compiler import CompilerWorker
from minjiang_host_client.workers.post_process import PostProcessWorker
from minjiang_host_client.workers.puller import PullerWorker
from minjiang_host_client.workers.pusher import PusherWorker
from minjiang_host_client.workers.qhal import QHALWorker
from minjiang_host_client.base.channel import Channel
from multiprocessing import shared_memory
from typing import Callable, Optional

import sys
import os
import io
import threading
import time
import platform
import subprocess

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

IS_WINDOWS = platform.system() == "Windows"
if sys.version_info >= (3, 7):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)


__VERSION__ = minjiang_client.__VERSION__


class Main(object):

    def __init__(self, group_name: str, manual_compiler: Callable = None, manual_qhal: Callable = None,
                 manual_post_process: Callable = None, direct_link_addr: str = 'localhost',
                 direct_link_port: int = 6887, shared_memory_size_mb: int = 200,
                 enable_device_manager: bool = True):

        self.group_name = group_name
        self.direct_link_port = direct_link_port
        self.direct_link_addr = direct_link_addr
        self.enable_device_manager = enable_device_manager

        # Channel
        mem_size = shared_memory_size_mb * 1024 * 1024
        self.chl_puller_task = Channel("chl_pl_t_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_compiler_task = Channel("chl_cp_t_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_compiler_waveform = Channel("chl_cp_w_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_qhal_waveform = Channel("chl_qh_w_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_qhal_result = Channel("chl_qh_r_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_post_process_result = Channel("chl_pp_r_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_post_process_final = Channel("chl_pp_f_" + group_name, shared_memory_size=mem_size, create=True)
        self.chl_pusher_final = Channel("chl_ps_f_" + group_name, shared_memory_size=mem_size, create=True)

        # Server
        self.main_server = MainServer("main", self.group_name, enable_device_manager=enable_device_manager)
        self.direct_link_server = DirectLinkServer("direct_link", self.group_name, dl_server=self.direct_link_addr,
                                                   dl_port=self.direct_link_port)
        self.tasks_server = TasksServer("tasks", self.group_name,
                                        self.chl_puller_task, self.chl_compiler_task)
        self.waveform_server = WaveformServer("waveform", self.group_name,
                                              self.chl_compiler_waveform, self.chl_qhal_waveform)
        self.result_server = ResultServer("result", self.group_name,
                                          self.chl_qhal_result, self.chl_post_process_result)
        self.final_server = FinalServer("final", self.group_name,
                                        self.chl_post_process_final, self.chl_pusher_final)

        # Worker
        self.pull_worker = PullerWorker("puller", self.group_name, None, self.chl_puller_task,
                                        dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        self.push_worker = PusherWorker("pusher", self.group_name, self.chl_pusher_final, None,
                                        dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        if manual_compiler is None:
            self.compiler_worker = CompilerWorker("compiler", self.group_name, self.chl_compiler_task, self.chl_compiler_waveform,
                                                  dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.compiler_worker = manual_compiler("compiler", self.group_name, self.chl_compiler_task, self.chl_compiler_waveform,
                                                   dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        if manual_qhal is None:
            self.qhal_worker = QHALWorker("qhal", self.group_name, self.chl_qhal_waveform, self.chl_qhal_result,
                                          dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.qhal_worker = manual_qhal("qhal", self.group_name, self.chl_qhal_waveform, self.chl_qhal_result,
                                           dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        if manual_post_process is None:
            self.post_process_worker = PostProcessWorker("post_process", self.group_name,
                                                         self.chl_post_process_result, self.chl_post_process_final,
                                                         dl_server=self.direct_link_addr, dl_port=self.direct_link_port)
        else:
            self.post_process_worker = manual_post_process("post_process", self.group_name,
                                                           self.chl_post_process_result, self.chl_post_process_final,
                                                           dl_server=self.direct_link_addr, dl_port=self.direct_link_port)

        # Process
        self.main_server_process = None
        self.tasks_server_process = None
        self.waveform_server_process = None
        self.result_server_process = None
        self.final_server_process = None
        self.pull_worker_process = None
        self.compiler_worker_process = None
        self.qhal_worker_process = None
        self.post_process_worker_process = None
        self.push_worker_process = None

        self.compiler_worker.group = CloudGroup(group_name)
        self.qhal_worker.group = CloudGroup(group_name)
        self.post_process_worker.group = CloudGroup(group_name)

        # 父进程监控
        self.parent_monitor_thread: Optional[threading.Thread] = None
        self.parent_pid: Optional[int] = None
        self._monitoring = False

    def _get_parent_pid(self) -> Optional[int]:
        """获取父进程ID"""
        try:
            # 优先使用 os.getppid()（跨平台，但Windows上可能不准确）
            parent_pid = os.getppid()
            print("Host Client 父进程 PID (parent_pid):", parent_pid)
            return parent_pid
        except (AttributeError, OSError):
            # 如果 os.getppid() 不可用，尝试使用 psutil
            if PSUTIL_AVAILABLE:
                try:
                    current_process = psutil.Process()
                    parent_process = current_process.parent()
                    if parent_process:
                        print("Host Client 父进程 PID (parent_process.pid):", parent_process.pid)
                        return parent_process.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    pass
            return None

    def _is_process_running(self, pid: int) -> bool:
        """检查进程是否在运行"""
        if pid is None:
            return False

        # 使用 psutil 检查（最可靠）
        try:
            process = psutil.Process(pid)
            # 检查进程状态
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            # 如果没有权限访问，假设进程还在运行
            return True

    def _monitor_parent_process(self):
        """监控父进程的线程函数"""
        check_interval = 2.0  # 每2秒检查一次
        while self._monitoring:
            try:
                if self.parent_pid is None:
                    # 如果无法获取父进程ID，跳过检查
                    time.sleep(check_interval)
                    continue

                # 检查父进程是否还在运行
                is_running = self._is_process_running(self.parent_pid)
                if not is_running:
                    # 父进程已停止，强制终止所有子进程
                    self.terminate_all(timeout=2.0, force=True)
                    # 等待一段时间确保进程已终止，然后退出
                    time.sleep(1)
                    exit(0)

                # 等待检查间隔
                time.sleep(check_interval)

            except Exception as e:
                # 发生异常时，继续监控（避免监控线程崩溃）
                time.sleep(check_interval)

    def _start_parent_monitor(self):
        """启动父进程监控"""
        if self._monitoring:
            return

        # 获取父进程ID
        self.parent_pid = self._get_parent_pid()

        if self.parent_pid is None:
            # 无法获取父进程ID，静默跳过（可能是直接启动的进程）
            return

        # 启动监控线程
        self._monitoring = True
        self.parent_monitor_thread = threading.Thread(target=self._monitor_parent_process, daemon=True)
        self.parent_monitor_thread.start()

    def _stop_parent_monitor(self):
        """停止父进程监控"""
        self._monitoring = False
        if self.parent_monitor_thread and self.parent_monitor_thread.is_alive():
            self.parent_monitor_thread.join(timeout=1.0)

    def run(self):
        try:

            print("Host Client 主进程 PID:", os.getpid())

            # 启动父进程监控
            self._start_parent_monitor()

            # Make server's process
            self.main_server_process = self.main_server.make_process()
            self.direct_link_server_process = self.direct_link_server.make_process()
            self.tasks_server_process = self.tasks_server.make_process()
            self.waveform_server_process = self.waveform_server.make_process()
            self.result_server_process = self.result_server.make_process()
            self.final_server_process = self.final_server.make_process()

            # Make worker's process
            self.pull_worker_process = self.pull_worker.make_process()
            self.compiler_worker_process = self.compiler_worker.make_process()
            self.qhal_worker_process = self.qhal_worker.make_process()
            self.post_process_worker_process = self.post_process_worker.make_process()
            self.push_worker_process = self.push_worker.make_process()

            # Start
            self.main_server_process.start()
            self.direct_link_server_process.start()
            self.tasks_server_process.start()
            self.waveform_server_process.start()
            self.result_server_process.start()
            self.final_server_process.start()
            self.pull_worker_process.start()
            self.compiler_worker_process.start()
            self.qhal_worker_process.start()
            self.post_process_worker_process.start()
            self.push_worker_process.start()

            # Join
            self.main_server_process.join()
            self.direct_link_server_process.join()
            self.tasks_server_process.join()
            self.waveform_server_process.join()
            self.result_server_process.join()
            self.final_server_process.join()
            self.pull_worker_process.join()
            self.compiler_worker_process.join()
            self.qhal_worker_process.join()
            self.post_process_worker_process.join()
            self.push_worker_process.join()
        finally:
            # 清理共享内存
            self.chl_puller_task.close()
            self.chl_compiler_task.close()
            self.chl_compiler_waveform.close()
            self.chl_qhal_waveform.close()
            self.chl_qhal_result.close()
            self.chl_post_process_result.close()
            self.chl_post_process_final.close()
            self.chl_pusher_final.close()

            # 在Unix系统上需要手动取消链接
            if hasattr(shared_memory, 'unlink'):
                try:
                    # 使用正确的Channel名称格式
                    shared_memory.SharedMemory(name="chl_pl_t_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_cp_t_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_cp_w_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_qh_w_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_qh_r_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_pp_r_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_pp_f_" + self.group_name).unlink()
                    shared_memory.SharedMemory(name="chl_ps_f_" + self.group_name).unlink()
                except FileNotFoundError:
                    pass
                except Exception as e:
                    # 捕获其他可能的异常，避免影响清理流程
                    print(f"清理共享内存时发生错误: {e}")

            print("All processes stopped and shared memory cleaned up.")
            # 停止父进程监控
            self._stop_parent_monitor()

    def stop(self):
        """优雅停止所有进程（通过设置running标志）"""
        self.main_server.running.value = False
        self.tasks_server.running.value = False
        self.waveform_server.running.value = False
        self.result_server.running.value = False
        self.final_server.running.value = False
        self.pull_worker.running.value = False
        self.compiler_worker.running.value = False
        self.qhal_worker.running.value = False
        self.post_process_worker.running.value = False
        self.push_worker.running.value = False

    def terminate_all(self, timeout: float = 5.0, force: bool = False):
        """
        主动终止所有进程
        
        Args:
            timeout: 等待进程退出的超时时间（秒），默认5秒
            force: 如果为True，超时后强制kill进程；如果为False，只发送terminate信号
        """
        # 先调用stop()设置停止标志
        self.stop()
        
        # 收集所有进程对象
        processes = []
        if self.main_server_process is not None:
            processes.append(("main_server", self.main_server_process))
        if self.direct_link_server_process is not None:
            processes.append(("direct_link_server", self.direct_link_server_process))
        if self.tasks_server_process is not None:
            processes.append(("tasks_server", self.tasks_server_process))
        if self.waveform_server_process is not None:
            processes.append(("waveform_server", self.waveform_server_process))
        if self.result_server_process is not None:
            processes.append(("result_server", self.result_server_process))
        if self.final_server_process is not None:
            processes.append(("final_server", self.final_server_process))
        if self.pull_worker_process is not None:
            processes.append(("pull_worker", self.pull_worker_process))
        if self.compiler_worker_process is not None:
            processes.append(("compiler_worker", self.compiler_worker_process))
        if self.qhal_worker_process is not None:
            processes.append(("qhal_worker", self.qhal_worker_process))
        if self.post_process_worker_process is not None:
            processes.append(("post_process_worker", self.post_process_worker_process))
        if self.push_worker_process is not None:
            processes.append(("push_worker", self.push_worker_process))
        
        # 对所有进程发送terminate信号
        for name, proc in processes:
            if proc.is_alive():
                try:
                    proc.terminate()
                except Exception as e:
                    print(f"Failed to terminate {name}: {e}")
        
        # 等待进程退出
        if timeout > 0:
            end_time = time.time() + timeout
            for name, proc in processes:
                remaining_time = end_time - time.time()
                if remaining_time <= 0:
                    break
                try:
                    proc.join(timeout=remaining_time)
                except Exception as e:
                    print(f"Error waiting for {name} to exit: {e}")
        
        # 如果force=True，强制kill仍在运行的进程
        if force:
            for name, proc in processes:
                if proc.is_alive():
                    try:
                        proc.kill()
                        print(f"Force killed {name} process")
                    except Exception as e:
                        print(f"Failed to kill {name}: {e}")
        
        # 停止父进程监控
        self._stop_parent_monitor()
