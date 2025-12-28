# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
Per-filetype modeline comment class.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
__all__ = ["Comments", "export_json", "import_json", "list_filetypes"]

import json
import os
from io import TextIOWrapper
from os.path import exists, isdir, realpath
from typing import Dict, Iterator, List, NoReturn, Tuple

from ..util import die
from .types import GeneratedEOFComments, IndentMapDict

_JSON_FILE: str = realpath("./vim_eof_comment/comments/filetypes.json")


def import_json() -> Tuple[GeneratedEOFComments, IndentMapDict]:
    """
    Import default vars from JSON file.

    Returns
    -------
    comments : GeneratedEOFComments
        The default ``GeneratedEOFComments``.
    map_dict : IndentMapDict
        The default ``IndentMapDict``.
    """
    splitter: str = "/" if os.name != "nt" else "\\"
    split = __file__.split(splitter)
    length = len(split) - 1
    parent: str = splitter.join(split[:length])
    file: TextIOWrapper = open(parent + f"{splitter}filetypes.json", "r")

    data: str = "".join(file.read().split("\n"))
    file.close()

    result: Tuple[GeneratedEOFComments, IndentMapDict] = json.loads(data)

    return result[0], result[1]


_formats, _DEFAULT = import_json()


class Comments():
    """
    Vim EOF comments class.

    Parameters
    ----------
    mappings : IndentMapDict, optional, default=None
        The ``str`` to ``IndentMap`` dictionary.

    Attributes
    ----------
    __DEFAULT : IndentMapDict
        The default/fallback alternative to ``langs``.
    __formats : GeneratedEOFComments
        The default/fallback alternative to ``comments``.
    langs : IndentMapDict
        A dictionary of ``IndentMap`` type objects.
    comments : GeneratedEOFComments
        A dictionary of file-extension-to-EOF-comment mappings.

    Methods
    -------
    __is_available(lang)
    __fill_langs(langs)
    get_defaults()
    """

    __DEFAULT: IndentMapDict = _DEFAULT.copy()
    __formats: GeneratedEOFComments = _formats.copy()
    comments: GeneratedEOFComments
    langs: IndentMapDict

    def __init__(self, mappings: IndentMapDict | None = None):
        """
        Creates a new Vim EOF comment object.

        Parameters
        ----------
        mappings : IndentMapDict, optional, default=None
            The ``str`` to ``IndentMap`` dictionary.
        """
        if mappings is None or len(mappings) == 0:
            self.langs = self.__DEFAULT.copy()
            return

        langs = dict()
        for lang, mapping in mappings.items():
            if not (self.__is_available(lang)) or len(mapping) == 0:
                continue

            indent, expandtab = mapping["level"], True
            if len(mapping) > 1:
                expandtab = mapping["expandtab"]

            langs[lang] = {"level": indent, "expandtab": expandtab}

        self.__fill_langs(langs)

    def __iter__(self) -> Iterator[str]:
        """Iterate through comment langs."""
        for k, v in self.langs.items():
            yield (k, v)

    def __is_available(self, lang: str) -> bool:
        """
        Check if a given lang is available within the class.

        Parameters
        ----------
        lang : str
            The file extension.

        Returns
        -------
        bool
            Represents whether the file extension has been included in the defaults.
        """
        return lang in self.__DEFAULT.keys()

    def __fill_langs(self, langs: IndentMapDict) -> NoReturn:
        """
        Fill languages dict.

        Parameters
        ----------
        langs : IndentMapDict
            A dictionary of ``IndentMap`` type objects.
        """
        if len(langs) == 0:
            self.langs = self.__DEFAULT.copy()
            return

        for lang, mapping in self.__DEFAULT.items():
            langs[lang] = langs.get(lang, mapping)

        self.langs = IndentMapDict(**langs)

    def get_defaults(self) -> IndentMapDict:
        """
        Retrieve the default comment dictionary.

        Returns
        -------
        IndentMapDict
            A dictionary of ``IndentMap`` type objects.
        """
        return self.__DEFAULT

    def generate(self) -> GeneratedEOFComments:
        """
        Generate the comments list.

        Returns
        -------
        GeneratedEOFComments
            The customly generated comments dictionary.
        """
        comments: Dict[str, str] = dict()
        for lang, fmt in self.__formats.items():
            lvl, expandtab = self.langs[lang]["level"], self.langs[lang]["expandtab"]
            et, sw = "noet", 0

            if expandtab:
                et, sw = "et", lvl

            comments[lang] = fmt.format(ts=lvl, sts=lvl, sw=sw, et=et)

        self.comments: GeneratedEOFComments = GeneratedEOFComments(**comments)
        return self.comments

    def get_ft(self, ext: str) -> str | None:
        """
        Get the comment string by filetype (or None if it doesn't exist).

        Parameters
        ----------
        ext : str
            The file extension to be fetched.

        Returns
        -------
        str or None
            Either the file extension string, or if not available then ``None``.
        """
        comments: GeneratedEOFComments = self.generate()
        return comments.get(ext, None)


def list_filetypes() -> NoReturn:
    """List all available filetypes."""
    txt: List[str] = [""]

    c: Comments = Comments()
    defaults: IndentMapDict = c.get_defaults()
    for ext, indents in defaults.items():
        txt.append(f"- {ext}: {indents}")

    die(*txt, code=0, sep="\n")


def export_json() -> NoReturn:
    """Export default vars to JSON."""
    if not (exists("./vim_eof_comment/comments") and isdir("./vim_eof_comment/comments")):
        return

    try:
        data: str = json.dumps((_formats, _DEFAULT), ensure_ascii=False)
    except KeyboardInterrupt:
        die(code=1)
    except Exception:
        raise RuntimeError("Data encoding failed!")

    try:
        file: TextIOWrapper = open(_JSON_FILE, "w")
    except Exception:
        die("Failed to write encoded data!", code=5)

    if file.write(data + "\n") != len(data) + 1:
        file.close()
        raise IOError("Failed to write data properly!")

    file.close()

# vim: set ts=4 sts=4 sw=4 et ai si sta:
