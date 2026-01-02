"""Pushbullet notification plugin."""

import logging
from typing import Any, Dict, Optional

try:
    import pushbullet as pb
    PUSHBULLET_AVAILABLE = True
except ImportError:
    PUSHBULLET_AVAILABLE = False

from .base import NotificationPlugin, ConfigurationError, SendError

logger = logging.getLogger(__name__)


class PushbulletPlugin(NotificationPlugin):
    """Pushbullet notification plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self._client = None
        
        if not PUSHBULLET_AVAILABLE:
            logger.warning("Pushbullet library not installed. Install with: pip install pushbullet.py")
            self.enabled = False
    
    def validate_config(self) -> bool:
        """Validate Pushbullet configuration."""
        if not self.api_key:
            raise ConfigurationError("Pushbullet API key is required")
        return True
    
    def _get_client(self):
        """Get or create Pushbullet client."""
        if self._client is None and PUSHBULLET_AVAILABLE:
            try:
                self._client = pb.Pushbullet(self.api_key)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize Pushbullet: {e}")
        return self._client
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Pushbullet.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (device, email, channel)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Pushbullet plugin is disabled")
            return False
        
        try:
            self.validate_config()
            client = self._get_client()
            
            device = kwargs.get('device')
            email = kwargs.get('email')
            channel = kwargs.get('channel')
            
            if device:
                client.push_note(title, message, device=device)
            elif email:
                client.push_note(title, message, email=email)
            elif channel:
                client.push_note(title, message, channel=channel)
            else:
                client.push_note(title, message)
            
            logger.info(f"Pushbullet notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Pushbullet notification: {e}")
            raise SendError(f"Pushbullet send failed: {e}")