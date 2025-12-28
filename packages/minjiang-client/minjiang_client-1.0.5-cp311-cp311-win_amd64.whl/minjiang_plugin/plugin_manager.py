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
from typing import List, Optional

from minjiang_client.com.plugin import (create_plugin, list_plugins, upload_plugin_version,
                                        get_plugin_detail, list_plugin_versions, modify_plugin,
                                        set_plugin_global_visibility, get_plugin_config)
from minjiang_client.utils.local import get_cache_dir, get_plugin_dir, get_default_config_dir
from minjiang_client.com.oss import add_plugin_resource, get_plugin_resource_info
from minjiang_client.com.minio import get_minio_client
import os
import sys
import json
import zipfile
import importlib
import shutil
from pathlib import Path


def zip_directory(root_dir, to_file):
    root_dir = Path(root_dir).expanduser().resolve()
    output_zip = Path(to_file).expanduser().resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    exclude_dirs = ['__pycache__']

    with zipfile.ZipFile(to_file + ".zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            for excluded_dir in exclude_dirs:
                if excluded_dir in dirs:
                    dirs.remove(excluded_dir)
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(root_dir)
                zipf.write(file_path, arcname)

    with open(to_file + ".zip", 'rb') as f:
        return f.read()


class PluginManager(object):

    @staticmethod
    def list_local_plugins():
        plugin_dir = get_plugin_dir()
        sys.path.append(str(plugin_dir))
        root_path = Path(plugin_dir)
        json_data = dict()
        for f in root_path.iterdir():
            plugin_name = f.name
            current_dir = str(plugin_dir) + "/" + plugin_name
            try:
                if not os.path.isdir(current_dir):
                    continue
                module = importlib.import_module(plugin_name + ".main")
                if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
                if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
                if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
                plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
                plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
                plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
                if '__MJ_PLUGIN_DESC__' in module.__dict__.keys():
                    plugin_desc = module.__dict__['__MJ_PLUGIN_DESC__']
                else:
                    plugin_desc = "No description."
                json_data[plugin_name] = {
                    "full_path": current_dir,
                    "path": current_dir,
                    "plugin_version": plugin_version,
                    "plugin_hook": plugin_hook,
                    "desc": plugin_desc,
                    "uninstall_enable": True,
                    "update_enable": True
                }
            except Exception as e:
                print(f"Cannot import plugin in {current_dir}: {e}")

        if os.path.isfile(get_default_config_dir() + "/plugin_includes.txt"):
            with open(get_default_config_dir() + "/plugin_includes.txt", "r") as file:
                line = file.readline()
                while line:
                    line = line.strip()
                    normalized_path = os.path.normpath(line)
                    parent_dir = os.path.dirname(normalized_path)
                    current_dir = os.path.basename(normalized_path)
                    main_file = os.path.join(normalized_path, 'main.py')
                    if os.path.isfile(main_file):
                        sys.path.append(parent_dir)
                        module = importlib.import_module(f"{current_dir}.main")
                        importlib.reload(module)
                        if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                            raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
                        if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                            raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
                        if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                            raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
                        plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
                        plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
                        plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
                        if '__MJ_PLUGIN_DESC__' in module.__dict__.keys():
                            plugin_desc = module.__dict__['__MJ_PLUGIN_DESC__']
                        else:
                            plugin_desc = "No description."
                        json_data[plugin_name] = {
                            "full_path": f"{parent_dir}/{current_dir}",
                            "path": current_dir,
                            "plugin_version": plugin_version,
                            "plugin_hook": plugin_hook,
                            "desc": plugin_desc,
                            "uninstall_enable": False,
                            "update_enable": False
                        }

                    line = file.readline()
        else:
            with open(get_default_config_dir() + "/plugin_includes.txt", "w") as file:
                file.write("")

        return json_data

    @staticmethod
    def list_remote_plugins(page, per_page):
        data = list_plugins(page, per_page)
        for item in data['list']:
            if item['latest_version_hook'] is not None:
                item['latest_version_hook'] = json.loads(item['latest_version_hook'])
            else:
                item['latest_version_hook'] = []
        return data

    @staticmethod
    def list_plugin_versions(plugin_id: int, page: int = 1, per_page: int = 10):
        data, count = list_plugin_versions(plugin_id, page, per_page)
        for item in data:
            item['hook'] = json.loads(item['hook'])
        return {"list": data, "total": count}

    @staticmethod
    def get_plugin_detail(plugin_id: int):
        return get_plugin_detail(plugin_id)

    @staticmethod
    def download_plugin(plugin_id: int):
        # Get plugin detail
        plugin_detail = PluginManager.get_plugin_detail(plugin_id)
        plugin_name = plugin_detail['plugin_name']
        # Get versions
        data = PluginManager.list_plugin_versions(plugin_id, page=1, per_page=1)
        if data['total'] == 0:
            raise RuntimeError("Cannot find plugin with plugin ID {}".format(plugin_id))
        version = data['list'][0]
        resource_id = version['resource_id']
        uri_dict = get_plugin_resource_info(plugin_id)
        if not uri_dict:
            raise RuntimeError("Cannot find resource with resource ID {}".format(resource_id))
        uri = uri_dict['uri']
        minio = get_minio_client(is_global=True)
        raw_data = minio.download(uri)
        plugin_version = version['full_version_code']
        plugin_indicator = plugin_name + "_" + plugin_version.replace(".", "_") + ".zip"
        os.makedirs(get_cache_dir() + "/plugin_download/", exist_ok=True)
        filename = get_cache_dir() + "/plugin_download/" + plugin_indicator
        with open(filename, "wb") as fd:
            fd.write(raw_data)
        return filename

    @staticmethod
    def install_plugin(plugin_file: str, replace: bool = None):
        plugin_dir = get_plugin_dir()
        install_cache_dir = plugin_dir + "/plugin_install_cache"
        try:
            if not os.path.exists(plugin_file):
                raise FileNotFoundError(f"Cannot find the plugin package file {plugin_file}.")

            if os.path.exists(install_cache_dir):
                raise RuntimeError(f"Another plugin is installing now, please wait or "
                                   f"remove the cache dir {install_cache_dir} manually.")

            with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
                if 'main.py' not in [f.filename for f in zip_ref.filelist]:
                    filenames = [f.filename.lower() for f in zip_ref.filelist]
                    if 'main.py' not in filenames:
                        raise ValueError(f"main.py cannot be found in {plugin_file}, "
                                         f"it is not a valid plugin package.")
                print("Unpacking plugin...")
                os.makedirs(install_cache_dir, exist_ok=True)
                zip_ref.extractall(install_cache_dir)
                # Analyzing package
                print("Analysing plugin directory...")
                sys.path.append(plugin_dir)
                module = importlib.import_module(f"plugin_install_cache.main")
                module = importlib.reload(module)
                if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
                if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
                if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                    raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
                plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
                plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
                plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
                v1 = plugin_version[0]
                v2 = plugin_version[1]
                v3 = plugin_version[2]
                v_postfix = plugin_version[3] if len(plugin_version) == 4 else ""
                full_version = f"{v1}.{v2}.{v3}{v_postfix}"
                print(" - Plugin name:", plugin_name)
                print(" - Plugin version:", full_version)
                print(" - Plugin hook:", ", ".join(plugin_hook))
                # Check existing
                if os.path.exists(plugin_dir + "/" + plugin_name):
                    if replace is None:
                        yes_or_no = input(f"Plugin {plugin_name} is already installed, "
                                          f"do you want to replace it? [Y/n]")
                        replace = True if yes_or_no.lower() in ["yes", "y"] else False
                    if replace is True:
                        shutil.rmtree(plugin_dir + "/" + plugin_name)

                # Clear Cache
                print("Clearing cache...")
                os.rename(install_cache_dir, plugin_dir + "/" + plugin_name)
                print(f"Plugin {plugin_name} is installed.")

                try:
                    del sys.modules[module.__name__]
                except Exception as e:
                    pass

                return True

        except Exception as e:
            print("Clearing cache...")
            try:
                shutil.rmtree(install_cache_dir)
            except Exception as e:
                pass
            raise RuntimeError(f"Install plugin failed: {e}")

    @staticmethod
    def uninstall_plugin(plugin_name):
        plugin_dir = get_plugin_dir()
        if os.path.exists(plugin_dir + "/" + plugin_name):
            shutil.rmtree(plugin_dir + "/" + plugin_name)
        if f"{plugin_name}.main" in sys.modules:
            try:
                del sys.modules[f"{plugin_name}.main"]
            except Exception as e:
                print(f"Cannot delete module: {plugin_name}.main")

    @staticmethod
    def package_plugin_release(root_dir: str):
        # Check
        log_text = ""
        if root_dir.endswith("main.py"):
            if not os.path.exists(root_dir):
                raise RuntimeError("File main.py is not found in the root directory.")

            plugin_name = os.path.basename(os.path.dirname(root_dir))
            plugin_dir = os.path.dirname(root_dir)

            # 指定模块的绝对路径
            module_path = Path(plugin_dir + "/main.py").resolve()
            module_name = plugin_name  # 自定义模块名（避免冲突）

            # 使用 importlib 加载模块
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        else:
            if not os.path.exists(root_dir + "/main.py"):
                raise RuntimeError("File main.py is not found in the root directory.")

            plugin_dir = root_dir
            plugin_name = os.path.basename(root_dir)

            # 指定模块的绝对路径
            module_path = Path(root_dir + "/main.py").resolve()
            module_name = plugin_name  # 自定义模块名（避免冲突）

            # 使用 importlib 加载模块
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
            raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
        if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
            raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
        if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
            raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
        plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
        plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
        plugin_hooks = module.__dict__['__MJ_PLUGIN_HOOKS__']

        # Package
        plugin_indicator = plugin_name + "_" + "_".join([str(_i) for _i in plugin_version])
        zip_file = get_cache_dir() + "/plugin_release/" + plugin_indicator
        zip_directory(plugin_dir, to_file=zip_file)
        log_text += "Plugin name: " + plugin_name + "\n"
        log_text += "Plugin version: " + '.'.join(map(str, plugin_version)) + "\n"
        log_text += "Plugin hooks: " + ','.join(plugin_hooks) + "\n"
        log_text += "==================================\n"
        log_text += "Save to file: " + zip_file + ".zip\n"
        return log_text

    @staticmethod
    async def submit_plugin_release(plugin_id: int, plugin_file: str):
        plugin_dir = get_plugin_dir()
        if not os.path.exists(plugin_file):
            raise FileNotFoundError(f"Cannot find the plugin package file {plugin_file}.")

        upload_cache_dir = plugin_dir + "/plugin_upload_cache"
        if os.path.exists(upload_cache_dir):
            raise RuntimeError(f"Another plugin is uploading now, please wait or "
                               f"remove the cache dir {upload_cache_dir} manually.")

        with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
            if 'main.py' not in [f.filename for f in zip_ref.filelist]:
                filenames = [f.filename.lower() for f in zip_ref.filelist]
                if 'main.py' not in filenames:
                    raise ValueError(f"main.py cannot be found in {plugin_file}, "
                                     f"it is not a valid plugin package.")
            os.makedirs(upload_cache_dir, exist_ok=True)
            zip_ref.extractall(upload_cache_dir)
            # Analyzing package
            sys.path.append(upload_cache_dir)
            module = importlib.import_module("plugin_upload_cache.main")
            importlib.reload(module)
            if '__MJ_PLUGIN_NAME__' not in module.__dict__.keys():
                raise RuntimeError("__MJ_PLUGIN_NAME__ not found in the main module.")
            if '__MJ_PLUGIN_VERSION__' not in module.__dict__.keys():
                raise RuntimeError("__MJ_PLUGIN_VERSION__ not found in the main module.")
            if '__MJ_PLUGIN_HOOKS__' not in module.__dict__.keys():
                raise RuntimeError("__MJ_PLUGIN_HOOKS__ not found in the main module.")
            plugin_name = module.__dict__['__MJ_PLUGIN_NAME__']
            plugin_version = module.__dict__['__MJ_PLUGIN_VERSION__']
            plugin_hook = module.__dict__['__MJ_PLUGIN_HOOKS__']
            v1 = plugin_version[0]
            v2 = plugin_version[1]
            v3 = plugin_version[2]
            v_postfix = plugin_version[3] if len(plugin_version) == 4 else ""
            full_version = f"{v1}.{v2}.{v3}{v_postfix}"
            if os.path.exists(upload_cache_dir + "/update.txt"):
                with open(upload_cache_dir + "/update.txt", "r", encoding="utf-8") as f:
                    version_desc = f.read()
            else:
                version_desc = "No description."

        try:
            del module
            shutil.rmtree(upload_cache_dir)
        except Exception as e:
            print("Failed to remove the cache dir:", e)

        # Check plugin
        plugin_detail = PluginManager.get_plugin_detail(plugin_id)
        if plugin_detail['plugin_name'] != plugin_name:
            raise RuntimeError(f"Plugin name of plugin ID {plugin_id} is {plugin_detail['plugin_name']}, "
                               f"however, the submitting plugin is named by {plugin_name}.")
        # Upload
        minio = get_minio_client(is_global=True)
        with open(plugin_file, 'rb') as file:
            zip_data = file.read()
        plugin_indicator = plugin_name + "_" + "_".join([str(_i) for _i in plugin_version])
        uri = minio.upload(str(plugin_indicator), zip_data, "plugin", "zip")
        rid = add_plugin_resource("", "zip", json.dumps(uri), "")["resource_id"]
        print("Plugin uploaded.")
        # Submit
        upload = upload_plugin_version(plugin_id, v1, v2, v3, v_postfix, full_version, version_desc,
                                       json.dumps(plugin_hook), rid)
        print("Plugin submitted.")
        return upload

    @staticmethod
    def create_plugin(plugin_name: str, description: str, org_ids: List[int], manager_user_ids: List[int],
                      must_be_installed: bool, auto_upgrade: bool):
        return create_plugin(plugin_name, description, org_ids, manager_user_ids, must_be_installed, auto_upgrade)

    @staticmethod
    def modify_plugin(plugin_id: int, description: Optional[str], org_ids: List[int], manager_user_ids: List[int]):
        return modify_plugin(plugin_id, description, org_ids, manager_user_ids)

    @staticmethod
    def set_plugin_global_visibility(plugin_id: int, visible: bool):
        return set_plugin_global_visibility(plugin_id, visible)

    @staticmethod
    def get_plugin_config(plugin_id: int):
        return get_plugin_config(plugin_id)
