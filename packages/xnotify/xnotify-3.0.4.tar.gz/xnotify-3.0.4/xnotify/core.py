"""Core notification manager for xnotify."""

import logging
from typing import Any, Dict, List, Optional

from .config import Config
from .plugins import AVAILABLE_PLUGINS, get_plugin
from .plugins.base import NotificationPlugin
from .logger import setup_logger, tracebacklog

logger = setup_logger('xnotify.core')
# logger = logging.getLogger(__name__)


class XNotify:
    """Main notification manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize XNotify.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config = Config(config_file)
        self.plugins: Dict[str, NotificationPlugin] = {}
        self._load_plugins()
    
    def _load_plugins(self):
        """Load and initialize plugins from configuration."""
        plugins_config = self.config.get('plugins', {})
        
        for plugin_name, plugin_config in plugins_config.items():
            if plugin_name not in AVAILABLE_PLUGINS:
                logger.warning(f"Unknown plugin: {plugin_name}")
                continue
            
            try:
                plugin_class = get_plugin(plugin_name)
                plugin = plugin_class(plugin_config)
                self.plugins[plugin_name] = plugin
                logger.info(f"Loaded plugin: {plugin_name}")
                
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                tracebacklog(logger)
    
    def send(
        self,
        title: str,
        message: str,
        plugins: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, bool]:
        """
        Send notification through specified plugins.
        
        Args:
            title: Notification title
            message: Notification message
            plugins: List of plugin names to use (None = use all enabled)
            **kwargs: Additional plugin-specific parameters
            
        Returns:
            Dictionary mapping plugin names to success status
        """
        if plugins is None:
            plugins = list(self.plugins.keys())
        
        results = {}
        logger.debug(f"self.plugins: {self.plugins}")
        logger.debug(f"plugins: {plugins}")
        
        for plugin_name in plugins:
            if plugin_name not in self.plugins:
                logger.warning(f"Plugin not loaded: {plugin_name}")
                results[plugin_name] = False
                continue
            
            plugin = self.plugins[plugin_name]
            logger.debug(f"plugin.is_enabled(): {plugin.is_enabled()}")
            
            if not plugin.is_enabled():
                logger.debug(f"Plugin disabled: {plugin_name}")
                results[plugin_name] = False
                continue
            
            try:
                success = plugin.send(title, message, **kwargs)
                results[plugin_name] = success
                
            except Exception as e:
                logger.error(f"Plugin {plugin_name} failed: {e}")
                tracebacklog(logger)
                results[plugin_name] = False
        
        return results
    
    def enable_plugin(self, plugin_name: str):
        """Enable a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            logger.info(f"Enabled plugin: {plugin_name}")
    
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            logger.info(f"Disabled plugin: {plugin_name}")
    
    def get_plugin_status(self) -> Dict[str, bool]:
        """Get status of all plugins."""
        return {
            name: plugin.is_enabled()
            for name, plugin in self.plugins.items()
        }