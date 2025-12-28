from typing import Callable, NoReturn, TextIO

from .types import IndentHandler, IndentMap

__all__ = ['die', 'error', 'gen_indent_maps', 'verbose_print', 'version_print']

def error(*msg, **kwargs) -> NoReturn:
    """
    Print to stderr.

    Parameters
    ----------
    *msg
        The data to be printed to stderr.
    **kwargs
        Extra arguments for the ``print()`` function.

    See Also
    --------
    print : This function is essentially being wrapped around here.
    """
def die(*msg, code: int = 0, func: Callable[[TextIO], None] | None = None, **kwargs) -> NoReturn:
    '''
    Kill the program execution.

    Summons ``sys.exit()`` with a provided code and optionally prints code to stderr or stdout
    depending on the provuded exit code.

    Parameters
    ----------
    *msg : optional
        Data to be printed.
    code : int, default=0
        The exit code.
    func : Callable[[TextIO], None], optional
        A function to be called with a TextIO object if provided.
    **kwargs
        Extra arguments for the ``print()`` function.

    See Also
    --------
    vim_eof_comment.util.error : Function to be used if exit code is not 0.

    Examples
    --------
    To kill the program with code 0 without any message.

    >>> from vim_eof_comment.util import die
    >>> die(code=0)

    To kill the program with non-zero exit code with message (will print to stderr).

    >>> from vim_eof_comment.util import die
    >>> die("foo", "bar", code=1)
    foo bar

    To kill the program with exit code 0 with message (will print to stdout).

    >>> from vim_eof_comment.util import die
    >>> die("foo", "bar")
    foo bar
    '''
def verbose_print(*msg, verbose: bool | None = None, **kwargs) -> NoReturn:
    """
    Only prints the given data if verbose mode is activated.

    Parameters
    ----------
    *msg
        Data to be printed.
    verbose : bool or None, default=None
        Flag to signal whether to execute this function or not.
    **kwargs
        Extra arguments for the ``print()`` function.

    See Also
    --------
    print : This function is essentially being wrapped around here.
    """
def version_print(version: str) -> NoReturn:
    """
    Print project version, then exit.

    Parameters
    ----------
    version : str
        The version string.

    See Also
    --------
    vim_eof_comment.util.die : The function used for this function.
    """
def gen_indent_maps(maps: list[IndentHandler]) -> dict[str, IndentMap] | None:
    """
    Generate a dictionary from the custom indent maps.

    Parameters
    ----------
    maps : List[IndentHandler]
        A list of IndentHandler objects.

    Returns
    -------
    Dict[str, IndentMap]
        The generated indent map dictionary.

    Raises
    ------
    ValueError : This will happen if any element of the only parameter
                  is less or equal to one.
    """

# vim: set ts=4 sts=4 sw=4 et ai si sta:
