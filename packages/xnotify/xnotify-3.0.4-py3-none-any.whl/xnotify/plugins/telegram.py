"""Telegram notification plugin."""

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
logger = setup_logger('xnotify.plugins.telegram')


class TelegramPlugin(NotificationPlugin):
    """Telegram Bot notification plugin."""
    
    API_URL = "https://api.telegram.org/bot{token}/sendMessage"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.bot_token = self.config.get('bot_token')
        self.chat_id = self.config.get('chat_id')
        self.timeout = self.config.get('timeout', 10)
        
        if not PROGRESS_SESSION_AVAILABLE:
            logger.warning("'progress_session' library not installed. Install with: pip install progress_session")
            self.enabled = False
    
    def validate_config(self) -> bool:
        """Validate Telegram configuration."""
        if not self.bot_token:
            raise ConfigurationError("Telegram bot token is required")
        if not self.chat_id:
            raise ConfigurationError("Telegram chat ID is required")
        return True
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Telegram.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (parse_mode, disable_notification)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Telegram plugin is disabled")
            return False
        
        try:
            self.validate_config()
            
            text = f"<b>{title}</b>\n\n{message}"
            
            payload = {
                'chat_id': kwargs.get('chat_id', self.chat_id),
                'text': text,
                'parse_mode': kwargs.get('parse_mode', 'HTML'),
                'disable_notification': kwargs.get('disable_notification', False),
            }
            
            url = self.API_URL.format(token=self.bot_token)
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            logger.info(f"Telegram notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            raise SendError(f"Telegram send failed: {e}")