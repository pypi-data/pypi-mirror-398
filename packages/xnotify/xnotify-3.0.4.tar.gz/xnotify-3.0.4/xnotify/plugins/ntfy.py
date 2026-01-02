"""Ntfy notification plugin."""

import logging
import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
try:
    from progress_session import ProgressSession  # type: ignore
    requests = ProgressSession()
    PROGRESS_SESSION_AVAILABLE = True
except ImportError:
    PROGRESS_SESSION_AVAILABLE = False

from .base import NotificationPlugin, ConfigurationError, SendError
from ..logger import setup_logger, tracebacklog

logger = setup_logger('xnotify.plugins.ntfy')


class NtfyPlugin(NotificationPlugin):
    """Ntfy notification plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.servers = self.config.get('servers', ['https://ntfy.sh'])
        if isinstance(self.servers, str):
            self.servers = [s.strip() for s in self.servers.split(',')]
        
        self.topic = self.config.get('topic', 'xnotify')
        self.timeout = self.config.get('timeout', 10)
        
        if not PROGRESS_SESSION_AVAILABLE:
            logger.warning("'progress_session' library not installed. Install with: pip install progress_session")
            self.enabled = False
    
    def validate_config(self) -> bool:
        """Validate Ntfy configuration."""
        if not self.servers:
            raise ConfigurationError("At least one ntfy server is required")
        
        if not self.topic:
            raise ConfigurationError("Ntfy topic is required")
        
        return True
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Ntfy.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (priority, tags, icon, click, attach, actions, email)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Ntfy plugin is disabled")
            return False
        
        try:
            self.validate_config()
            
            # Build notification payload
            payload = {
                'topic': kwargs.get('topic', self.topic),
                'title': title,
                'message': message,
                'priority': kwargs.get('priority', 3),
            }
            
            # Optional fields
            if 'tags' in kwargs:
                tags = kwargs['tags']
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',')]
                payload['tags'] = tags
            
            if 'icon' in kwargs:
                if kwargs['icon'].startswith('http'):
                    payload['icon'] = kwargs['icon'] 
                # else:

                    # icon_path = Path(kwargs['icon'])
                    # if icon_path.is_file():
                    #     with open(icon_path, 'rb') as f:
                    #         import base64
                    #         encoded_icon = base64.b64encode(f.read()).decode('utf-8')
                    #         payload['icon'] = f'data:image/{icon_path.suffix[1:]};base64,{encoded_icon}'
            
            if 'click' in kwargs:
                payload['click'] = kwargs['click']
            
            if 'attach' in kwargs:
                payload['attach'] = kwargs['attach']
            
            if 'filename' in kwargs:
                payload['filename'] = kwargs['filename']
            
            if 'actions' in kwargs:
                payload['actions'] = kwargs['actions']
            
            if 'email' in kwargs:
                payload['email'] = kwargs['email']
            
            # Send to all configured servers
            success = False
            logger.warning(f"payload: {payload}")
            logger.warning(f"server: {self.servers}")
            for server in self.servers:
                if not server.startswith('http'):
                    server = f'https://{server}'
                
                try:
                    response = requests.post(  # type: ignore
                        server,
                        data=json.dumps(payload),
                        headers={'Content-Type': 'application/json'},
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    success = True
                    logger.info(f"Ntfy notification sent to {server}: {title}")
                    
                except requests.exceptions.RequestException as e:  # type: ignore
                    logger.error(f"Failed to send to {server}: {e}")
                    tracebacklog(logger)
                    continue
            
            if not success:
                raise SendError("Failed to send to any ntfy server")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Ntfy notification: {e}")
            tracebacklog(logger)
            raise SendError(f"Ntfy send failed: {e}")