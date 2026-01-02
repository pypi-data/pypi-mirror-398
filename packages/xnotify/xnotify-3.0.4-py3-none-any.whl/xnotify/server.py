"""Server for receiving and routing notifications."""

import socket
import json
import logging
import signal
import sys
from typing import Optional, Callable
from datetime import datetime
from .logger import setup_logger, tracebacklog

# logger = logging.getLogger(__name__)
logger = setup_logger('xnotify.server')


class XNotifyServer:
    """Server for receiving notifications via UDP."""
    
    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 33000,
        buffer_size: int = 8192,
        on_notification: Optional[Callable] = None
    ):
        """
        Initialize server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            buffer_size: UDP buffer size
            on_notification: Callback function for notifications
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.on_notification = on_notification
        self.running = False
        self.socket: Optional[socket.socket] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.running = True
            
            logger.info(f"Server listening on {self.host}:{self.port}")
            print(f"🚀 XNotify Server started on {self.host}:{self.port}")
            print(f"📦 PID: {os.getpid()}")
            print("Press Ctrl+C to stop\n")
            
            self._listen()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            tracebacklog(logger)
            raise
    
    def _listen(self):
        """Listen for incoming notifications."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(self.buffer_size)
                self._handle_notification(data, addr)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error receiving data: {e}")
    
    def _handle_notification(self, data: bytes, addr: tuple):
        """
        Handle incoming notification.
        
        Args:
            data: Received data
            addr: Client address
        """
        try:
            # Parse JSON
            payload = json.loads(data.decode('utf-8'))
            
            # Extract fields
            title = payload.get('title', 'No Title')
            message = payload.get('message', 'No Message')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Log notification
            logger.info(f"Notification from {addr[0]}:{addr[1]} - {title}")
            print(f"[{timestamp}] 📨 From {addr[0]}:{addr[1]}")
            print(f"   📌 Title: {title}")
            print(f"   💬 Message: {message}\n")
            
            # Call callback if provided
            if self.on_notification:
                self.on_notification(title, message, payload)
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {addr[0]}:{addr[1]}")
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    def stop(self):
        """Stop the server."""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("Server stopped")
        print("\n👋 Server stopped gracefully")


def run_server(
    host: str = '0.0.0.0',
    port: int = 33000,
    on_notification: Optional[Callable] = None
):
    """
    Run notification server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        on_notification: Callback for notifications
    """
    server = XNotifyServer(host, port, on_notification=on_notification)
    server.start()


# Router mode - forward notifications
class XNotifyRouter(XNotifyServer):
    """Server that routes notifications through XNotify."""
    
    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 33000,
        xnotify_instance=None
    ):
        """
        Initialize router.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            xnotify_instance: XNotify instance for forwarding
        """
        self.xnotify = xnotify_instance
        super().__init__(host, port, on_notification=self._forward_notification)
    
    def _forward_notification(self, title: str, message: str, payload: dict):
        """Forward notification through XNotify."""
        if self.xnotify:
            try:
                plugins = payload.get('plugins')
                self.xnotify.send(title, message, plugins=plugins, **payload)
                logger.info(f"Forwarded: {title}")
            except Exception as e:
                logger.error(f"Failed to forward notification: {e}")


import os  # Add missing import