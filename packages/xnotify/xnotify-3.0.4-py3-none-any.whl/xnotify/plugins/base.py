"""Base plugin interface for xnotify."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..logger import setup_logger, tracebacklog

logger = setup_logger('xnotify.plugins.base')

class NotificationPlugin(ABC):
    """Base class for all notification plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the plugin.
        
        Args:
            config: Plugin-specific configuration dictionary
        """
        self.config = config or {}
        logger.debug(f"self.config: {self.config}")
        self.enabled = self.config.get('enabled', True)
        self.name = self.__class__.__name__.replace('Plugin', '').lower()
        
    @abstractmethod
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional plugin-specific parameters
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate plugin configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self.enabled
    
    def get_name(self) -> str:
        """Get plugin name."""
        return self.name


class PluginError(Exception):
    """Base exception for plugin errors."""
    pass


class ConfigurationError(PluginError):
    """Raised when plugin configuration is invalid."""
    pass


class SendError(PluginError):
    """Raised when sending notification fails."""
    pass