#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI模块初始化
"""

__version__ = "1.1.0"

def __getattr__(name: str):
    if name == "main":
        from .tsdb_manager_main import main
        return main
    raise AttributeError(f"module {__name__} has no attribute {name}")