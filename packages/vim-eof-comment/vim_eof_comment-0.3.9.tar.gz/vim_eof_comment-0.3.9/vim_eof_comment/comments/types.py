# -*- coding: utf-8 -*-
# Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
Per-filetype modeline comment class.

Copyright (c) 2025 Guennadi Maximov C. All Rights Reserved.
"""
__all__ = ["GeneratedEOFComments", "IndentMapDict"]

from typing import TypedDict

from ..types import IndentMap


class GeneratedEOFComments(TypedDict):
    """A ``TypedDict`` object containing all the file-extension to comment elements."""

    C: str
    H: str
    Makefile: str
    bash: str
    c: str
    cc: str
    cpp: str
    css: str
    fish: str
    h: str
    hh: str
    hpp: str
    htm: str
    html: str
    latex: str
    lua: str
    markdown: str
    md: str
    mk: str
    py: str
    pyi: str
    rb: str
    sh: str
    tex: str
    xml: str
    zsh: str


class IndentMapDict(TypedDict):
    """A ``TypedDict`` object with ``IndentMap`` values."""

    C: IndentMap
    H: IndentMap
    Makefile: IndentMap
    bash: IndentMap
    c: IndentMap
    cc: IndentMap
    cpp: IndentMap
    css: IndentMap
    fish: IndentMap
    h: IndentMap
    hh: IndentMap
    hpp: IndentMap
    htm: IndentMap
    html: IndentMap
    latex: IndentMap
    lua: IndentMap
    markdown: IndentMap
    md: IndentMap
    mk: IndentMap
    py: IndentMap
    pyi: IndentMap
    rb: IndentMap
    sh: IndentMap
    tex: IndentMap
    xml: IndentMap
    zsh: IndentMap

# vim: set ts=4 sts=4 sw=4 et ai si sta:
