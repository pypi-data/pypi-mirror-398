"""Growl/GNTP notification plugin."""

import logging
from typing import Any, Dict, Optional

try:
    from gntplib import Publisher, Resource  # type: ignore
    GNTP_AVAILABLE = True
except ImportError:
    GNTP_AVAILABLE = False

from .base import NotificationPlugin, ConfigurationError, SendError
from ..logger import setup_logger

logger = setup_logger('xnotify.plugins.growl')


class GrowlPlugin(NotificationPlugin):
    """Growl/GNTP notification plugin (legacy support)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.hosts = self.config.get('hosts', ['127.0.0.1:23053'])
        self.app_name = self.config.get('app_name', 'xnotify')
        self.notifications = self.config.get('notifications', ['Notification'])
        self.timeout = self.config.get('timeout', 10)
        self.icon = self.config.get('icon')
        
        if not GNTP_AVAILABLE:
            logger.warning("GNTP library not installed. Install with: pip install gntplib")
            self.enabled = False
    
    def validate_config(self) -> bool:
        """Validate Growl configuration."""
        if not self.hosts:
            raise ConfigurationError("At least one Growl host is required")
        return True
    
    def _parse_host(self, host_string: str) -> tuple:
        """Parse host string to (host, port) tuple."""
        if ':' in host_string:
            host, port = host_string.split(':', 1)
            return host.strip(), int(port.strip())
        return host_string.strip(), 23053
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Growl/GNTP.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (priority, sticky, icon)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Growl plugin is disabled")
            return False
        
        try:
            self.validate_config()
            
            notification_type = kwargs.get('notification_type', self.notifications[0])
            priority = kwargs.get('priority', 0)
            sticky = kwargs.get('sticky', False)
            icon = kwargs.get('icon', self.icon)
            
            # Load icon if provided
            icon_resource = None
            if icon:
                try:
                    if icon.startswith('http'):
                        icon_resource = Resource(url=icon)  # type: ignore
                    else:
                        icon_resource = Resource().from_file(icon)  # type: ignore
                except Exception as e:
                    logger.warning(f"Failed to load icon: {e}")
            
            success = False
            for host_string in self.hosts:
                host, port = self._parse_host(host_string)
                
                try:
                    publisher = Publisher(  # type: ignore
                        kwargs.get("app_name", self.app_name),
                        self.notifications,
                        host=host,
                        port=port,
                        timeout=self.timeout
                    )
                    
                    # Register application
                    publisher.register()
                    
                    # Send notification
                    publisher.publish(
                        notification_type,
                        title,
                        message,
                        icon=icon_resource,
                        sticky=sticky,
                        priority=priority
                    )
                    
                    logger.info(f"Growl notification sent to {host}:{port}: {title}")
                    success = True
                    
                except Exception as e:
                    logger.warning(f"Failed to send to {host}:{port}: {e}")
                    continue
            
            if not success:
                raise SendError("Failed to send to any Growl host")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Growl notification: {e}")
            raise SendError(f"Growl send failed: {e}")