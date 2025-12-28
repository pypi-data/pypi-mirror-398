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

from typing import Union, get_origin, get_args


def single_decorator(cls):
    _instance = {}
    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton


def parse_type(type_annotation) -> str:
    origin = get_origin(type_annotation)
    args = get_args(type_annotation)

    if origin is Union:
        return "|".join(parse_type(t) for t in args)
    else:
        if isinstance(type_annotation, str):
            return str(type_annotation)
        else:
            return str(type_annotation.__name__)