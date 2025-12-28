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

from minjiang_client import __VERSION__

built_in_plugin_list = {
    "builtin_waveforms": {
        "file_name": "builtin_waveforms",
        "hook": ["waveform_extension", "plot_waveform", "plot_wave_package", "plot_wave_circuit",
                 "waveform_compiler_setup"],
        "desc": "Built-in waveforms.",
        "version": ".".join(map(str, __VERSION__)),
    },
    "builtin_script_extension": {
        "file_name": "builtin_script_extension",
        "hook": ["script_evaluator_function_extension"],
        "desc": "Built-in script extension.",
        "version": ".".join(map(str, __VERSION__)),
    },
    "builtin_gate_compiler": {
        "file_name": "builtin_gate_compiler",
        "hook": ['gate_compiler_register', 'gate_name_register'],
        "desc": "Built-in gate compiler.",
        "version": ".".join(map(str, __VERSION__)),
    },
    "builtin_experiment_template": {
        "file_name": "builtin_experiment_template",
        "hook": ['experiment_template_extension', 'fitter_extension'],
        "desc": "Built-in Experiment template.",
        "version": ".".join(map(str, __VERSION__)),
    },
    "builtin_cloud_support": {
        "file_name": "builtin_cloud_support",
        "hook": ['experiment_options', 'space_initializer_extension'],
        "desc": "Built-in cloud supporting utils.",
        "version": ".".join(map(str, __VERSION__)),
    },
    "zwdx_device_manager": {
        "file_name": "zwdx_device_manager",
        "hook": ['utility_server_register'],
        "desc": "ZWDX Device Manager.",
        "version": ".".join(map(str, __VERSION__)),
    },
    "zwdx_devices": {
        "file_name": "zwdx_devices",
        "hook": ['device_service_manager'],
        "desc": "中微达信超导量子计算电子学设备基础支持程序",
        "version": ".".join(map(str, __VERSION__)),
    },
    "host_client_dashboard": {
        "file_name": "host_client_dashboard",
        "hook": ['utility_server_register'],
        "desc": "Minjiang Host Client Dashboard.",
        "version": ".".join(map(str, __VERSION__)),
    }
}
