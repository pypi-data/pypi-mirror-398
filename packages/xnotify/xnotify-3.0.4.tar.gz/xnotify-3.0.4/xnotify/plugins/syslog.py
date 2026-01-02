"""Syslog notification plugin."""

import logging
import socket
from typing import Any, Dict, Optional
from datetime import datetime

from .base import NotificationPlugin, ConfigurationError, SendError

logger = logging.getLogger(__name__)


class SyslogPlugin(NotificationPlugin):
    """Syslog notification plugin."""
    
    # Syslog severity levels
    SEVERITY = {
        'emergency': 0,
        'alert': 1,
        'critical': 2,
        'error': 3,
        'warning': 4,
        'notice': 5,
        'info': 6,
        'debug': 7,
    }
    
    # Syslog facilities
    FACILITY = {
        'kern': 0,
        'user': 1,
        'mail': 2,
        'daemon': 3,
        'auth': 4,
        'syslog': 5,
        'lpr': 6,
        'news': 7,
        'uucp': 8,
        'cron': 9,
        'authpriv': 10,
        'ftp': 11,
        'local0': 16,
        'local1': 17,
        'local2': 18,
        'local3': 19,
        'local4': 20,
        'local5': 21,
        'local6': 22,
        'local7': 23,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.servers = self.config.get('servers', ['127.0.0.1:514'])
        self.facility = self.config.get('facility', 'daemon')
        self.severity = self.config.get('severity', 'info')
        self.hostname = socket.gethostname()
        self.app_name = self.config.get('app_name', 'xnotify')
        self.timeout = self.config.get('timeout', 5)
    
    def validate_config(self) -> bool:
        """Validate Syslog configuration."""
        if not self.servers:
            raise ConfigurationError("At least one syslog server is required")
        
        if self.facility not in self.FACILITY:
            raise ConfigurationError(f"Invalid facility: {self.facility}")
        
        if self.severity not in self.SEVERITY:
            raise ConfigurationError(f"Invalid severity: {self.severity}")
        
        return True
    
    def _parse_server(self, server_string: str) -> tuple:
        """Parse server string to (host, port) tuple."""
        if ':' in server_string:
            host, port = server_string.split(':', 1)
            return host.strip(), int(port.strip())
        return server_string.strip(), 514
    
    def _create_syslog_message(
        self,
        message: str,
        facility: Optional[str] = None,
        severity: Optional[str] = None
    ) -> bytes:
        """
        Create RFC 3164 syslog message.
        
        Args:
            message: Message text
            facility: Syslog facility
            severity: Syslog severity
            
        Returns:
            Formatted syslog message
        """
        facility = facility or self.facility
        severity = severity or self.severity
        
        # Calculate priority
        pri = (self.FACILITY[facility] * 8) + self.SEVERITY[severity]
        
        # Format timestamp
        timestamp = datetime.now().strftime('%b %d %H:%M:%S')
        
        # Build message
        syslog_msg = f"<{pri}>{timestamp} {self.hostname} {self.app_name}: {message}"
        
        return syslog_msg.encode('utf-8')
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """
        Send notification via Syslog.
        
        Args:
            title: Notification title
            message: Notification message
            **kwargs: Additional parameters (facility, severity)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.debug("Syslog plugin is disabled")
            return False
        
        try:
            self.validate_config()
            
            # Combine title and message
            full_message = f"{title}: {message}"
            
            # Get custom facility/severity if provided
            facility = kwargs.get('facility', self.facility)
            severity = kwargs.get('severity', self.severity)
            
            # Create syslog message
            syslog_data = self._create_syslog_message(full_message, facility, severity)
            
            success = False
            for server_string in self.servers:
                host, port = self._parse_server(server_string)
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(self.timeout)
                    sock.sendto(syslog_data, (host, port))
                    sock.close()
                    
                    logger.info(f"Syslog message sent to {host}:{port}")
                    success = True
                    
                except Exception as e:
                    logger.warning(f"Failed to send to {host}:{port}: {e}")
                    continue
            
            if not success:
                raise SendError("Failed to send to any syslog server")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Syslog notification: {e}")
            raise SendError(f"Syslog send failed: {e}")