# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
# PYTHON_ARGCOMPLETE_OK
"""
Ensure EOF Vim comment in specific filetypes.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
__all__ = ["append_eof_comment", "eof_comment_search", "main"]

from io import TextIOWrapper
from typing import Dict, List, NoReturn

from colorama import Fore, Style
from colorama import init as color_init

from .args.parsing import arg_parser_init, indent_handler
from .comments.generator import Comments, list_filetypes
from .file import bootstrap_paths, get_last_line, modify_file, open_batch_paths
from .regex import matches
from .types import (BatchPathDict, EOFCommentSearch, IndentHandler,
                    IOWrapperBool)
from .util import die, gen_indent_maps, verbose_print, version_print
from .version import list_versions, version_info

_RED: int = Fore.LIGHTRED_EX
_GREEN: int = Fore.LIGHTGREEN_EX
_BRIGHT: int = Style.BRIGHT
_RESET: int = Style.RESET_ALL


def eof_comment_search(
    files: Dict[str, BatchPathDict],
    comments: Comments,
    **kwargs
) -> Dict[str, EOFCommentSearch]:
    """
    Search through opened files.

    Parameters
    ----------
    files : Dict[str, BatchPathDict]
        A dictionary of ``str`` to ``BatchPathDict`` objects.
    comments : Comments
        The ``Comments`` object containing the hardcoded comments per file extension.
    **kwargs
        COntains the ``verbose`` and ``newline`` boolean options.

    Returns
    -------
    Dict[str, EOFCommentSearch]
        A dictionary of ``str`` to ``EOFCommentSearch`` objects.

    See Also
    --------
    vim_eof_comment.types.BatchPathDict
        The ``files`` type objects in its dictionary values.
    vim_eof_comment.types.EOFCommentSearch
        The object type for the returning dictionary values.
    """
    verbose: bool = kwargs.get("verbose", False)
    newline: bool = kwargs.get("newline", False)

    result: Dict[str, EOFCommentSearch] = dict()
    comment_map = comments.generate()

    color_init()

    verbose_print(f"{_RESET}Analyzing files...\n", verbose=verbose)
    for path, file in files.items():
        file_obj: TextIOWrapper = file["file"]
        ext: str = file["ext"]

        wrapper = get_last_line(file_obj)
        last_line, has_nwl = wrapper["line"], wrapper["has_nwl"]

        verbose_print(f"{_RESET} - {path} ==> ", verbose=verbose, end="", sep="")
        if last_line != comment_map[ext] or (newline and not has_nwl):
            verbose_print(f"{_BRIGHT}{_RED}CHANGED", verbose=verbose)
            result[path] = EOFCommentSearch(
                state=IOWrapperBool(file=open(path, "r"), has_nwl=has_nwl),
                lang=ext,
                match=matches(last_line, verbose)
            )
        else:
            verbose_print(f"{_BRIGHT}{_GREEN}OK", verbose=verbose)

    return result


def append_eof_comment(
    files: Dict[str, EOFCommentSearch],
    comments: Comments,
    newline: bool
) -> NoReturn:
    """
    Append a Vim EOF comment to files missing it.

    Parameters
    ----------
    files : Dict[str, EOFCommentSearch]
        A dictionary of ``str`` to ``EOFCommentSearch`` objects.
    comments : Comments
        The ``Comments`` object containing the hardcoded comments per file extension.
    newline : bool
        Indicates whether a newline should be added before the comment.
    """
    comment_map = comments.generate()
    for path, file in files.items():
        file_obj = file["state"]["file"]
        has_nwl = file["state"]["has_nwl"]
        matching = file["match"]
        ext = file["lang"]

        txt = modify_file(
            file_obj,
            comment_map,
            ext=ext,
            newline=newline,
            has_nwl=has_nwl,
            matching=matching
        )
        file_obj = open(path, "w")

        file_obj.write(txt)
        file_obj.close()


def main() -> int:
    """
    Execute the main workflow.

    This must be passed as an argument for ``sys.exit()``.

    Returns
    -------
    int
        The exit code for the program.
    """
    parser, ns = arg_parser_init()

    if ns.version:
        version_print(str(version_info))

    if ns.list_fts:
        list_filetypes()

    if ns.list_versions:
        list_versions()

    if not (ns.directories and ns.exts) or len(ns.directories) == 0 or ns.exts == "":
        die(code=1, func=parser.print_usage)

    dirs: List[str] = ns.directories
    exts: List[str] = ns.exts.split(",")
    newline: bool = ns.newline
    indent: List[IndentHandler] = indent_handler(ns.indent)
    verbose: bool = ns.verbose

    dry_run: bool = ns.dry_run

    if dry_run:
        verbose = True

    indent = gen_indent_maps(indent.copy())

    comments = Comments(indent)

    files = open_batch_paths(bootstrap_paths(dirs, exts))
    if len(files) == 0:
        die("No matching files found!", code=1)

    results = eof_comment_search(files, comments, verbose=verbose, newline=newline)
    if len(results) > 0 and not dry_run:
        append_eof_comment(results, comments, newline)

    return 0

# vim: set ts=4 sts=4 sw=4 et ai si sta:
