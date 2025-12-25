"""confee - Configuration Enhanced & Easy ☕️

A Hydra-like configuration parser helper package with Pydantic support.
"""

__version__ = "0.1.0"
__author__ = "JunSeok Kim <infend@gmail.com>"
__license__ = "MIT"

from .config import ConfigBase
from .loaders import ConfigLoader, load_config, load_from_file
from .overrides import HelpFormatter, OverrideHandler, is_help_command
from .parser import ConfigParser

__all__ = [
    "ConfigBase",
    "ConfigLoader",
    "load_config",
    "load_from_file",
    "ConfigParser",
    "OverrideHandler",
    "HelpFormatter",
    "is_help_command",
]
