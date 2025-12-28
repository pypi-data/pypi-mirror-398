# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
Ensure EOF Vim comments.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
__all__ = [
    "args",
    "comments",
    "eof",
    "file",
    "main",
    "regex",
    "types",
    "util",
    "version",
    "version_info",
]

from . import args, comments, eof, file, regex, types, util
from .eof import main
from .version import version_info

version: str = str(version_info)

# vim: set ts=4 sts=4 sw=4 et ai si sta:
