"""Pushover notification plugin."""

import logging
from typing import Any, Dict, Optional

try:
    from progress_session import ProgressSession  # type: ignore
    requests = ProgressSession()
    PROGRESS_SESSION_AVAILABLE = True
except ImportError:
    PROGRESS_SESSION_AVAILABLE = False

from .base import NotificationPlugin, ConfigurationError, SendError
from ..logger import setup_logger
# logger = logging.getLogger(__name__)
logger = setup_logger('xnotify.plugins.pushover')


class PushoverPlugin(NotificationPlugin):
    """Pushover notification plugin (30-day free trial)."""
    
    API_URL = "https://api.pushover.net/1/messages.json"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.user_key = self.config.get('user_key')
        self.api_token = self.config.get('api_token')
        self.timeout = self.config.get('timeout', 10)
        
        if not PROGRESS_SESSION_AVAILABLE:
            logger.warning("'progress_session' library not installed. Install with: pip install progress_session")
            self.enabled = False
    
    def validate_config(self) -> bool:
        """Validate Pushover configuration."""
        if not self.user_key:
            raise ConfigurationError("Pushover user key is required")
        if not self.api_token:
            raise ConfigurationError("Pushover API token is required")
        return True
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Pushover.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (device, priority, sound, url, url_title)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Pushover plugin is disabled")
            return False
        
        try:
            self.validate_config()
            
            payload = {
                'token': self.api_token,
                'user': self.user_key,
                'title': title,
                'message': message,
            }
            
            # Optional parameters
            if 'device' in kwargs:
                payload['device'] = kwargs['device']
            if 'priority' in kwargs:
                payload['priority'] = kwargs['priority']
            if 'sound' in kwargs:
                payload['sound'] = kwargs['sound']
            if 'url' in kwargs:
                payload['url'] = kwargs['url']
            if 'url_title' in kwargs:
                payload['url_title'] = kwargs['url_title']
            
            response = requests.post(
                self.API_URL,
                data=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Pushover notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Pushover notification: {e}")
            raise SendError(f"Pushover send failed: {e}")