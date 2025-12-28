from . import args as args
from . import comments as comments
from . import eof as eof
from . import file as file
from . import regex as regex
from . import types as types
from . import util as util
from .eof import main as main
from .version import version_info as version_info

__all__ = ['args', 'comments', 'eof', 'file', 'main', 'regex', 'types', 'util', 'version', 'version_info']

version: str

# vim: set ts=4 sts=4 sw=4 et ai si sta:
