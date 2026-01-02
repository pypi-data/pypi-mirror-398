import logging

from .__version__ import (
    __version__,
    __author__,
    __email__,
    __license__,
    __url__,
    __description__,
)

from .core import XNotify
from .config import Config
from .plugins import (
    NotificationPlugin,
    list_plugins,
    get_plugin,
)

notify = XNotify

# Setup default logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

__all__ = [
    '__version__',
    '__author__',
    '__email__',
    '__license__',
    '__url__',
    '__description__',
    'XNotify',
    'Config',
    'NotificationPlugin',
    'list_plugins',
    'get_plugin',
]