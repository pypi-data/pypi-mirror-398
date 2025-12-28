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

from minjiang_client.utils.local import get_cache_dir, get_user_token, get_default_config_dir, get_server_addr
from minjiang_client.utils.start import setup_user_token, first_run_setup, setup_server_addr
from minjiang_client.com.user import check_user_status, login


if __name__ == "__main__":

    print("Welcome to Minjiang MC Software")

    # Get default config dir
    mc_dir = get_default_config_dir()
    print(f"Default config directory: {mc_dir}")

    # Check if already configured cache dir
    cache_dir = get_cache_dir()
    if not cache_dir:
        # First-time setup
        cache_dir = first_run_setup()
    else:
        print(f"Using existing cache directory: {cache_dir}")

    # Check if already configured server address
    svr_addr = get_server_addr()
    if not svr_addr:
        setup_server_addr()
    else:
        print(f"Using existing server address: {svr_addr}")

    # Check if already configured token
    token = get_user_token()
    if not token:
        print("No authentication token found")
        setup_user_token()

    token = get_user_token()
    if token:
        print("Authentication token loaded successfully.")

    # Login
    user_status = check_user_status()
    while not user_status:
        login_status = login(token)
        user_status = check_user_status()
    if user_status is not None:
        print(f"User logged in as username: {user_status['user_name']}")
