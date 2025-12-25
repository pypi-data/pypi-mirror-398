#!/usr/bin/env python
# Copyright 2020 H2O.ai; Proprietary License;  -*- encoding: utf-8 -*-
import importlib.resources

__all__ = ["__version__", "__build_info__"]

# Build defaults
build_info = {
    "git_commit": "",
    "build_os": "",
    "build_machine": "",
    "build_date": "",
    "build_user": "",
    "version": "0.0.0",
}

if importlib.resources.is_resource("driverlessai", "BUILD_INFO.txt"):
    exec(importlib.resources.read_text("driverlessai", "BUILD_INFO.txt"), build_info)

# Exported properties
__version__: str = build_info["version"]
"""Returns package version."""

__build_info__ = build_info
