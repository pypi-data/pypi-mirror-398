"""Slack webhook notification plugin."""

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
logger = setup_logger('xnotify.plugins.slack')


class SlackPlugin(NotificationPlugin):
    """Slack Webhook notification plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.webhook_url = self.config.get('webhook_url')
        self.channel = self.config.get('channel')
        self.username = self.config.get('username', 'xnotify')
        self.timeout = self.config.get('timeout', 10)
        
        if not PROGRESS_SESSION_AVAILABLE:
            logger.warning("'progress_session' library not installed. Install with: pip install progress_session")
            self.enabled = False
    
    def validate_config(self) -> bool:
        """Validate Slack configuration."""
        if not self.webhook_url:
            raise ConfigurationError("Slack webhook URL is required")
        return True
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Slack webhook.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (channel, username, icon_emoji, icon_url)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Slack plugin is disabled")
            return False
        
        try:
            self.validate_config()
            
            payload = {
                'text': f"*{title}*\n{message}",
                'username': kwargs.get('username', self.username),
            }
            
            if 'channel' in kwargs:
                payload['channel'] = kwargs['channel']
            elif self.channel:
                payload['channel'] = self.channel
            
            if 'icon_emoji' in kwargs:
                payload['icon_emoji'] = kwargs['icon_emoji']
            elif 'icon_url' in kwargs:
                payload['icon_url'] = kwargs['icon_url']
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Slack notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            raise SendError(f"Slack send failed: {e}")