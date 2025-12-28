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

import platform
import sys
import threading
import time

import uvicorn

from minjiang_client.com.user import check_user_status, login
from minjiang_client.utils.local import get_default_language
from minjiang_client.utils.local import get_user_token, get_gui_addr, set_gui_addr


def run_uvicorn(host, port):
    """运行uvicorn服务器的函数"""
    try:
        uvicorn.run(
            "minjiang_studio.app:app",
            host=host,
            port=int(port),
            log_level="warning",
            timeout_keep_alive=60,
            access_log=False,  # 禁用访问日志以提高性能
        )
    except OSError as e:
        # 端口被占用等系统错误
        if get_default_language() == "en":
            print(f"Failed to start server: {e}")
            print(f"Please check if port {port} is already in use.")
        else:
            print(f"启动服务器失败: {e}")
            print(f"请检查端口 {port} 是否已被占用。")
        sys.exit(1)
    except Exception as e:
        import traceback
        if get_default_language() == "en":
            print(f"Uvicorn server error: {e}")
        else:
            print(f"Uvicorn服务器错误: {e}")
        traceback.print_exc()
        sys.exit(1)


def run_system_tray(web_gui_url):
    """运行系统托盘应用的函数（仅支持 macOS 和 Windows）"""
    try:
        from minjiang_studio.utils.status_bar import SystemTrayApp
        app = SystemTrayApp(web_gui_url=web_gui_url)
        if app.os_type != "Darwin":
            app.root.mainloop()
    except ImportError as e:
        # 系统托盘依赖缺失，但不影响主程序运行
        if get_default_language() == "en":
            print(f"Warning: System tray unavailable: {e}")
        else:
            print(f"警告: 系统托盘不可用: {e}")
    except Exception as e:
        # 系统托盘启动失败，但不影响主程序运行
        if get_default_language() == "en":
            print(f"Warning: System tray error: {e}")
        else:
            print(f"警告: 系统托盘错误: {e}")


if __name__ == "__main__":
    try:
        # 初始化GUI地址
        gui_addr = get_gui_addr()
        if gui_addr is None:
            set_gui_addr("127.0.0.1", 6886)
            gui_addr = get_gui_addr()

        host = gui_addr["server_addr"]
        port = gui_addr["port"]
        login_page = ""

        # 登录逻辑
        if get_user_token() is not None:
            try:
                user_status = check_user_status()
                if user_status is None:
                    if get_default_language() == "en":
                        print("Login ...")
                    else:
                        print("正在尝试登录 ...")
                    user_name = login(get_user_token())
                else:
                    user_name = user_status['user_name']
                if get_default_language() == "en":
                    print(f"Login successfully as user {user_name}.")
                else:
                    print(f"用户 {user_name} 登录成功。")
            except Exception as e:
                login_page = "/login"
                if get_default_language() == "en":
                    print(f"Login failed: {e}")
                else:
                    print(f"登录失败: {e}")
        else:
            login_page = "/login"

        # Print running information
        web_gui_url = f"http://{host}:{port}{login_page}"
        if get_default_language() == "en":
            print(f'Minjiang Studio is starting, please wait...')
        else:
            print(f'岷江测控软件Studio正在启动, 请等待...')

        # Start uvicorn in a separate thread
        uvicorn_thread = threading.Thread(
            target=run_uvicorn,
            args=(host, port),
            daemon=True
        )
        uvicorn_thread.start()

        time.sleep(2.0)
        if get_default_language() == "en":
            print(f'Minjiang Studio starts successfully, please visit via {web_gui_url}.')
        else:
            print(f'岷江测控软件Studio启动成功, 请通过 {web_gui_url} 链接进行访问。')

        # Run system tray - only for macOS and Windows, not for Linux
        current_platform = platform.system()
        if current_platform == "Darwin":
            # macOS: run on main thread
            run_system_tray(web_gui_url)
        elif current_platform == "Windows":
            # Windows: run in separate thread
            tray_thread = threading.Thread(
                target=run_system_tray,
                daemon=True,
                args=(web_gui_url,)
            )
            tray_thread.start()
        else:
            # Linux: skip system tray
            pass

        # Keep the main thread alive
        try:
            while uvicorn_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            if get_default_language() == "en":
                print("\nShutting down...")
            else:
                print("\n正在关闭...")
            from minjiang_client.utility_manager import utility_manager

            try:
                utility_manager.cleanup_all_servers()
            except Exception as cleanup_error:
                if get_default_language() == "en":
                    print(f"Warning: Error during cleanup: {cleanup_error}")
                else:
                    print(f"警告: 清理过程中出现错误: {cleanup_error}")
            sys.exit(0)
    except KeyboardInterrupt:
        # 处理启动过程中的中断
        if get_default_language() == "en":
            print("\nStartup interrupted by user.")
        else:
            print("\n用户中断了启动过程。")
        sys.exit(0)
    except Exception as e:
        import traceback
        if get_default_language() == "en":
            print(f"Fatal error during startup: {e}")
            print("Traceback:")
        else:
            print(f"启动过程中发生致命错误: {e}")
            print("错误堆栈:")
        traceback.print_exc()
        sys.exit(1)
