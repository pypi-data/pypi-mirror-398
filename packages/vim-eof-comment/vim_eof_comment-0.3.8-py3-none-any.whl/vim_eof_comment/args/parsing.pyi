from argparse import ArgumentParser, Namespace

from ..types import IndentHandler, ParserSpec

__all__ = ['gen_parser_specs', 'bootstrap_args', 'arg_parser_init', 'indent_handler']

def gen_parser_specs(*specs) -> tuple[ParserSpec]:
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
def bootstrap_args(parser: ArgumentParser, specs: tuple[ParserSpec]) -> Namespace:
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
def arg_parser_init(prog: str = 'vim-eof-comment') -> tuple[ArgumentParser, Namespace]:
    '''
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
    '''
def indent_handler(indent: str) -> list[IndentHandler]:
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

# vim: set ts=4 sts=4 sw=4 et ai si sta:
