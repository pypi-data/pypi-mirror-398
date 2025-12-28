from argparse import ArgumentParser
from typing import NoReturn

__all__ = ['complete_parser']

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

# vim: set ts=4 sts=4 sw=4 et ai si sta:
