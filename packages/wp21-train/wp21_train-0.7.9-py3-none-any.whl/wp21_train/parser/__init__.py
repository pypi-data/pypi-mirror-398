# __init__.py

from wp21_train.utils.version import __version__
from .hls_parser              import hls_parser
from .aie_parser              import aie_parser
from .athena_parser           import athena_parser

__all__ = ["hls_parser", "aie_parser",  "athena_parser", "__version__"]
