from typing import Any, TextIO, TypedDict

from argcomplete.completers import DirectoriesCompleter

__all__ = ['BatchPairDict', 'BatchPathDict', 'CommentMap', 'EOFCommentSearch', 'IOWrapperBool', 'IndentHandler', 'IndentMap', 'LineBool', 'ParserSpec']

class ParserSpec(TypedDict):
    """
    Stores the spec for ``argparse`` operations in a constant value.

    This is a ``TypedDict``-like object.

    Attributes
    ----------
    opts : List[str]
        A list containing all the relevant iterations of the same option.
    kwargs : Dict[str, str]
        Extra arguments for ``argparse.ArgumentParser``.
    completer : argcomplete.DirectoriesCompleter, optional, default=None
        An optional ``argcomplete`` completer object.
    """
    opts: list[str]
    kwargs: dict[str, Any]
    completer: DirectoriesCompleter | None

class CommentMap(TypedDict):
    """
    Stores a dict with a ``level`` key.

    This is a ``TypedDict``-like object.

    Attributes
    ----------
    level : int
        The indentation level.
    """
    level: int

class IndentMap(TypedDict):
    """A ``TypedDict`` container."""
    level: int
    expandtab: bool

class IndentHandler(TypedDict):
    """
    A dict containing ``ext``, ``level`` and ``expandtab`` as keys.

    Attributes
    ----------
    ext : str
        The file extension.
    level : str
        The string representation of the indent level.
    expandtab : bool
        Whether to expand tabs or not.
    """
    ext: str
    level: str
    expandtab: bool

class IOWrapperBool(TypedDict):
    """A ``TypedDict`` container."""
    file: TextIO
    has_nwl: bool

class LineBool(TypedDict):
    """A ``TypedDict`` container."""
    line: str
    has_nwl: bool

class BatchPathDict(TypedDict):
    """A ``TypedDict`` container."""
    file: TextIO
    ext: str

class BatchPairDict(TypedDict):
    """A ``TypedDict`` container."""
    fpath: str
    ext: str

class EOFCommentSearch(TypedDict):
    """A ``TypedDict`` container."""
    state: IOWrapperBool
    lang: str
    match: bool

# vim: set ts=4 sts=4 sw=4 et ai si sta:
