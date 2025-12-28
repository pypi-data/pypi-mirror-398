# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
Argument parsing utilities for ``vim-eof-comment``.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
__all__ = ["gen_parser_specs", "bootstrap_args", "arg_parser_init", "indent_handler"]

from argparse import (ArgumentDefaultsHelpFormatter, ArgumentError,
                      ArgumentParser, Namespace)
from typing import List, Tuple

from argcomplete.completers import DirectoriesCompleter

from ..types import IndentHandler, ParserSpec
from ..util import die
from .completion import complete_parser


def gen_parser_specs(*specs) -> Tuple[ParserSpec]:
    """
    Generate a ``ParserSpec`` object.

    Parameters
    ----------
    *specs
        All the list-like dictionaries.

    Returns
    -------
    Tuple[ParserSpec]
        The converted dictionaries inside a tuple.
    """
    return tuple([ParserSpec(**d) for d in [*specs]])


def bootstrap_args(parser: ArgumentParser, specs: Tuple[ParserSpec]) -> Namespace:
    """
    Bootstrap the program arguments.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The ``argparse.ArgumentParser`` object.
    specs : List[vim_eof_comment.types.ParserSpec]
        A list containing ``ParserSpec`` objects.

    Returns
    -------
    argparse.Namespace
        The generated ``argparse.Namespace`` object.
    """
    for spec in specs:
        opts, kwargs = spec["opts"], spec["kwargs"]
        if spec["completer"] is not None:
            parser.add_argument(*opts, **kwargs).completer = spec["completer"]
        else:
            parser.add_argument(*opts, **kwargs)

    complete_parser(parser)

    try:
        namespace: Namespace = parser.parse_args()
    except ArgumentError:
        die(code=1, func=parser.print_usage)

    return namespace


def arg_parser_init(prog: str = "vim-eof-comment") -> Tuple[ArgumentParser, Namespace]:
    """
    Generate the argparse namespace.

    Parameters
    ----------
    prog : str, optional, default="vim-eof-comment"
        The program name.

    Returns
    -------
    parser : argparse.ArgumentParser
        The generated ``argparse.ArgumentParser`` object.
    namespace : argparse.Namespace
        The generated ``argparse.Namespace`` object.
    """
    parser = ArgumentParser(
        prog=prog,
        description="Checks for Vim EOF comments in all matching files in specific directories",
        epilog="Both the directory path(s) and the `-e` option are required!",
        exit_on_error=False,
        formatter_class=ArgumentDefaultsHelpFormatter,
        add_help=True,
        allow_abbrev=True
    )
    spec: Tuple[ParserSpec] = gen_parser_specs(
        {
            "opts": ["directories"],
            "kwargs": {
                "nargs": "*",
                "help": "The target directories to be checked",
                "metavar": "/path/to/directory",
            },
            "completer": DirectoriesCompleter(),
        },
        {
            "opts": ["-v", "--verbose"],
            "kwargs": {
                "required": False,
                "action": "store_true",
                "help": "Enable verbose mode",
                "dest": "verbose",
            },
            "completer": None,
        },
        {
            "opts": ["-V", "--version"],
            "kwargs": {
                "required": False,
                "action": "store_true",
                "help": "Show version",
                "dest": "version",
            },
            "completer": None,
        },
        {
            "opts": ["-L", "--list-versions"],
            "kwargs": {
                "required": False,
                "action": "store_true",
                "help": "List all versions of this script.",
                "dest": "list_versions",
            },
            "completer": None,
        },
        {
            "opts": ["-D", "--dry-run"],
            "kwargs": {
                "required": False,
                "action": "store_true",
                "help": "Don't modify the files, but do execute the rest",
                "dest": "dry_run",
            },
            "completer": None,
        },
        {
            "opts": ["-l", "--list-filetypes"],
            "kwargs": {
                "required": False,
                "action": "store_true",
                "help": "List available filetypes",
                "dest": "list_fts",
            },
            "completer": None,
        },
        {
            "opts": ["-n", "--newline"],
            "completer": None,
            "kwargs": {
                "required": False,
                "action": "store_true",
                "help": "Add newline before inserted comment",
                "dest": "newline",
            },
        },
        {
            "opts": ["-e", "--extensions"],
            "completer": None,
            "kwargs": {
                "required": False,
                "metavar": "EXT1[,EXT2[,EXT3[,...]]]",
                "help": "A comma-separated list of file extensions (e.g. \"lua,c,cpp,cc,c++\")",
                "dest": "exts",
            },
        },
        {
            "opts": ["-i", "--indents"],
            "completer": None,
            "kwargs": {
                "required": False,
                "metavar": "EXT1:INDENT1[:<Y|N>][,...]",
                "help": """
                A comma-separated list of per-extension mappings
                (indent level and, optionally, a Y/N value to indicate if tabs are expanded).
                For example: "lua:4,py:4:Y,md:2:N"
                """,
                "default": "",
                "dest": "indent",
            },
        },
    )

    return parser, bootstrap_args(parser, spec)


def indent_handler(indent: str) -> List[IndentHandler]:
    """
    Parse indent levels defined by the user.

    Parameters
    ----------
    indent : str
        The ``-i`` option argument string.

    Returns
    -------
    List[vim_eof_comment.types.IndentHandler]
        A list of ``IndentHandler`` objects.
    """
    if indent == "":
        return list()

    indents: List[str] = indent.split(",")
    maps: List[IndentHandler] = list()
    for ind in indents:
        inds: List[str] = ind.split(":")
        if len(inds) <= 1:
            continue

        ext, ind_level, et = inds[0], int(inds[1]), True
        if len(inds) >= 3 and inds[2].upper() in ("Y", "N"):
            et = not inds[2].upper() == "N"

        maps.append(IndentHandler(ext=ext, level=ind_level, expandtab=et))

    return maps

# vim: set ts=4 sts=4 sw=4 et ai si sta:
