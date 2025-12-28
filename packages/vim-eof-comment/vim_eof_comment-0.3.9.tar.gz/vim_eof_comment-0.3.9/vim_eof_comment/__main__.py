# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
# PYTHON_ARGCOMPLETE_OK
"""
Main entrypoint for `vim-eof-comment`.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
import sys

from .eof import main

if __name__ == "__main__":
    sys.exit(main())

# vim: set ts=4 sts=4 sw=4 et ai si sta:
