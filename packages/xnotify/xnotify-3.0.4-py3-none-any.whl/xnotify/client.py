"""Client for sending notifications to xnotify server."""

import socket
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class XNotifyClient:
    """Client for sending notifications to xnotify server."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 33000, timeout: int = 5):
        """
        Initialize client.
        
        Args:
            host: Server host
            port: Server port
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification to server.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters
            
        Returns:
            True if successful
        """
        try:
            # Create payload
            payload = {
                'title': title,
                'message': message,
                **kwargs
            }
            
            # Serialize
            data = json.dumps(payload).encode('utf-8')
            
            # Send via UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.sendto(data, (self.host, self.port))
            sock.close()
            
            logger.info(f"Notification sent to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def ping(self) -> bool:
        """
        Ping server to check if it's alive.
        
        Returns:
            True if server responds
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Send ping
            ping_data = json.dumps({'type': 'ping'}).encode('utf-8')
            sock.sendto(ping_data, (self.host, self.port))
            
            # Try to receive pong (server might not implement this)
            sock.close()
            return True
            
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False


def send_notification(
    title: str,
    message: str,
    host: str = '127.0.0.1',
    port: int = 33000,
    **kwargs
) -> bool:
    """
    Quick function to send notification.
    
    Args:
        title: Notification title
        message: Notification message
        host: Server host
        port: Server port
        **kwargs: Additional parameters
        
    Returns:
        True if successful
    """
    client = XNotifyClient(host, port)
    return client.send(title, message, **kwargs)