from typing import Iterator, NoReturn

from .types import GeneratedEOFComments, IndentMapDict

__all__ = ['Comments', 'export_json', 'import_json', 'list_filetypes']

def import_json() -> tuple[GeneratedEOFComments, IndentMapDict]:
    """
    Import default vars from JSON file.

    Returns
    -------
    comments : GeneratedEOFComments
        The default ``GeneratedEOFComments``.
    map_dict : IndentMapDict
        The default ``IndentMapDict``.
    """

class Comments:
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
    __DEFAULT: IndentMapDict
    __formats: GeneratedEOFComments
    comments: GeneratedEOFComments
    langs: IndentMapDict
    def __init__(self, mappings: IndentMapDict | None = None) -> None:
        """
        Creates a new Vim EOF comment object.

        Parameters
        ----------
        mappings : IndentMapDict, optional, default=None
            The ``str`` to ``IndentMap`` dictionary.
        """
    def __iter__(self) -> Iterator[str]:
        """Iterate through comment langs."""
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
    def __fill_langs(self, langs: IndentMapDict) -> NoReturn:
        """
        Fill languages dict.

        Parameters
        ----------
        langs : IndentMapDict
            A dictionary of ``IndentMap`` type objects.
        """
    def get_defaults(self) -> IndentMapDict:
        """
        Retrieve the default comment dictionary.

        Returns
        -------
        IndentMapDict
            A dictionary of ``IndentMap`` type objects.
        """
    def generate(self) -> GeneratedEOFComments:
        """
        Generate the comments list.

        Returns
        -------
        GeneratedEOFComments
            The customly generated comments dictionary.
        """
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

def list_filetypes() -> NoReturn:
    """List all available filetypes."""
def export_json() -> NoReturn:
    """Export default vars to JSON."""

# vim: set ts=4 sts=4 sw=4 et ai si sta:
