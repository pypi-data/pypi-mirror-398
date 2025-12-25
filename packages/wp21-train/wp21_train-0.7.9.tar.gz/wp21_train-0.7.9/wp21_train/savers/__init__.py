# __init__.py

from wp21_train.utils.version  import __version__
from .adapter                  import adapter
from .json_adapter             import json_adapter
from .root_adapter             import root_adapter
from .pickle_adapter           import pickle_adapter
from .yml_adapter              import yml_adapter

__all__ = ["adapter", "json_adapter", "root_adapter", "pickle_adapter", "yml_adapter", "__version__"]
