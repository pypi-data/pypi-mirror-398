#!/usr/bin/env python
# Copyright 2020 H2O.ai; Proprietary License;  -*- encoding: utf-8 -*-
import importlib.resources

__all__ = ["__version__", "__build_info__"]

# Build defaults
build_info = {
    'suffix': '+local',
    'build': 'dev',
    'commit': '',
    'describe': '',
    'build_os': '',
    'build_machine': '',
    'build_date': '',
    'build_user': '',
    'base_version': '0.0.0'
}

# Load build definition from BUILD_INFO.txt
if importlib.resources.is_resource("_h2oai_client_2_2_0", "BUILD_INFO.txt"):
    exec(importlib.resources.read_text("_h2oai_client_2_2_0", "BUILD_INFO.txt"), build_info)

# Exported properties to make them available in __init__.py
__version__ = build_info['version']
__build_info__ = build_info
