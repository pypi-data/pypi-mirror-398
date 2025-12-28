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
import json
from pathlib import Path
import sys
import os
sys.path.append(str(Path(os.path.dirname(__file__)).parent))

from minjiang_plugin.plugin_manager import PluginManager


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] in ["--package", "-p"]:
        if len(sys.argv) < 3:
            raise RuntimeError("Please input the plugin directory.")
        plugin_id = str(sys.argv[2])
        PluginManager.package_plugin_release(root_dir=os.getcwd())
    elif len(sys.argv) >= 2 and sys.argv[1] in ["--submit", "-s"]:
        if len(sys.argv) < 4:
            raise RuntimeError("Please input the plugin ID.")
        plugin_id = int(sys.argv[2])
        plugin_file = str(sys.argv[3])
        PluginManager.submit_plugin_release(plugin_id=plugin_id, plugin_file=plugin_file)
    elif len(sys.argv) >= 2 and sys.argv[1] in ["--download", "-d"]:
        if len(sys.argv) < 3:
            raise RuntimeError("Please input the plugin ID.")
        plugin_id = int(sys.argv[2])
        PluginManager.download_plugin(plugin_id=plugin_id)
    elif len(sys.argv) >= 2 and sys.argv[1] in ["--install", "-i"]:
        if len(sys.argv) < 3:
            raise RuntimeError("Please input the package filename.")
        plugin_file = str(sys.argv[2])
        PluginManager.install_plugin(plugin_file=plugin_file)
    elif len(sys.argv) >= 2 and sys.argv[1] in ["--uninstall", "-u"]:
        if len(sys.argv) < 3:
            raise RuntimeError("Please input the plugin name.")
        plugin_name = str(sys.argv[2])
        PluginManager.uninstall_plugin(plugin_name=plugin_name)
    elif len(sys.argv) >= 2 and sys.argv[1] in ["--list-local", "-ll"]:
        plugin_list = PluginManager.list_local_plugins()
        print(json.dumps(plugin_list, indent=4))
    else:
        print("Unknown option.")
        print("  - Use `python -m minjiang_plugin -p PLUGIN_DIR` for submitting a plugin.")
        print("  - Use `python -m minjiang_plugin -s PLUGIN_ID FILENAME` for submitting a plugin.")
        print("  - Use `python -m minjiang_plugin -d PLUGIN_ID` for downloading a plugin.")
        print("  - Use `python -m minjiang_plugin -i PACKAGE_FILE` for installing a plugin.")
        print("  - Use `python -m minjiang_plugin -u PLUGIN_NAME` for uninstalling a plugin.")
        print("  - Use `python -m minjiang_plugin -ll` for listing all local plugins.")