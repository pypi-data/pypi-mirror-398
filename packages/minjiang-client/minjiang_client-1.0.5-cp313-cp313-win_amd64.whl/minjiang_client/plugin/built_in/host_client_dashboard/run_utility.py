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

import argparse
import json

import uvicorn

from host_client_dashboard import create_utility_app


def main():
    """主函数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--group-name", required=True)  # 可选参数，根据require_group_name决定
    parser.add_argument("--utility-name", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--config", required=False)
    parser.add_argument("--lang", required=False, help="语言设置（cn, en）")
    parser.add_argument("--studio-url", required=False, help="Studio URL地址")
    parser.add_argument("--persistent", action="store_true", help="是否持久化运行（不随客户端停止而停止）")

    args = parser.parse_args()

    config = json.loads(args.config) if args.config else {}
    # 如果提供了group_name参数，添加到config中
    if args.group_name:
        config["group_name"] = args.group_name

    # 将persistent标志传递给create_utility_app
    config["_persistent"] = args.persistent

    # 将lang参数传递给create_utility_app
    if args.lang:
        config["_lang"] = args.lang

    # 将studio_url参数传递给create_utility_app
    if args.studio_url:
        config["_studio_url"] = args.studio_url

    app = create_utility_app(args.utility_name, config)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()

# python host_client_dashboard.py --server-id 123123 --group-name ZWDX_sim_2q --utility-name host_client_dashboard --port 9999 --config {}
