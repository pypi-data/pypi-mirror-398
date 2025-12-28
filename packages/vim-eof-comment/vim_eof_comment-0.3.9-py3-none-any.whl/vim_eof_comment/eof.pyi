from typing import NoReturn

from .comments.generator import Comments
from .types import BatchPathDict, EOFCommentSearch

__all__ = ['append_eof_comment', 'eof_comment_search', 'main']

def eof_comment_search(files: dict[str, BatchPathDict], comments: Comments, **kwargs) -> dict[str, EOFCommentSearch]:
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
def append_eof_comment(files: dict[str, EOFCommentSearch], comments: Comments, newline: bool) -> NoReturn:
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
def main() -> int:
    """
    Execute the main workflow.

    This must be passed as an argument for ``sys.exit()``.

    Returns
    -------
    int
        The exit code for the program.
    """

# vim: set ts=4 sts=4 sw=4 et ai si sta:
