"""Discord webhook notification plugin."""

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
logger = setup_logger('xnotify.plugins.discord')


class DiscordPlugin(NotificationPlugin):
    """Discord Webhook notification plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.webhook_url = self.config.get('webhook_url')
        self.username = self.config.get('username', 'xnotify')
        self.timeout = self.config.get('timeout', 10)
        
        if not PROGRESS_SESSION_AVAILABLE:
            logger.warning("'progress_session' library not installed. Install with: pip install progress_session")
            self.enabled = False
    
    def validate_config(self) -> bool:
        """Validate Discord configuration."""
        if not self.webhook_url:
            raise ConfigurationError("Discord webhook URL is required")
        return True
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Discord webhook.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (username, avatar_url, color)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Discord plugin is disabled")
            return False
        
        try:
            self.validate_config()
            
            embed = {
                'title': title,
                'description': message,
                'color': kwargs.get('color', 3447003),  # Blue color
            }
            
            payload = {
                'username': kwargs.get('username', self.username),
                'embeds': [embed],
            }
            
            if 'avatar_url' in kwargs:
                payload['avatar_url'] = kwargs['avatar_url']
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Discord notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            raise SendError(f"Discord send failed: {e}")