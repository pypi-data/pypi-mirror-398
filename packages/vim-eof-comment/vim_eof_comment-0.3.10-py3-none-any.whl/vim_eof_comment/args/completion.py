# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
Argument parsing completion utilities for ``vim-eof-comment``.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
__all__ = ["complete_parser"]

from argparse import ArgumentParser
from typing import NoReturn

from argcomplete import autocomplete
from argcomplete.finders import default_validator


def complete_parser(parser: ArgumentParser, **kwargs) -> NoReturn:
    """
    Complete the script argument parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The ``ArgumentParser`` object.
    **kwargs
        Extra parameters.
    """
    autocomplete(parser, validator=default_validator, **kwargs)

# vim: set ts=4 sts=4 sw=4 et ai si sta:
