"""Plugin system for xnotify."""

import logging
from typing import Dict, List, Type

from .growl import GrowlPlugin
from .base import NotificationPlugin
from .pushbullet import PushbulletPlugin
from .ntfy import NtfyPlugin
from .pushover import PushoverPlugin
from .telegram import TelegramPlugin
from .discord import DiscordPlugin
from .slack import SlackPlugin

logger = logging.getLogger(__name__)

# Registry of available plugins
AVAILABLE_PLUGINS: Dict[str, Type[NotificationPlugin]] = {
    'pushbullet': PushbulletPlugin,
    'ntfy': NtfyPlugin,
    'pushover': PushoverPlugin,
    'telegram': TelegramPlugin,
    'discord': DiscordPlugin,
    'slack': SlackPlugin,
    'growl': GrowlPlugin,
}


def get_plugin(name: str) -> Type[NotificationPlugin]:
    """
    Get plugin class by name.
    
    Args:
        name: Plugin name
        
    Returns:
        Plugin class
        
    Raises:
        KeyError: If plugin not found
    """
    return AVAILABLE_PLUGINS[name.lower()]


def list_plugins() -> List[str]:
    """Get list of available plugin names."""
    return list(AVAILABLE_PLUGINS.keys())


__all__ = [
    'NotificationPlugin',
    'PushbulletPlugin',
    'NtfyPlugin',
    'PushoverPlugin',
    'TelegramPlugin',
    'DiscordPlugin',
    'SlackPlugin',
    'AVAILABLE_PLUGINS',
    'get_plugin',
    'list_plugins',
]