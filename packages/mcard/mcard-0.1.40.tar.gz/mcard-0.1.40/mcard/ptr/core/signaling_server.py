#!/usr/bin/env python3
"""
Simple Signaling Server for WebRTC P2P coordination.

This is the Python equivalent of the TypeScript signaling server in mcard-js.
It provides SSE (Server-Sent Events) based signaling for WebRTC peer discovery
and SDP/ICE candidate exchange.

Usage:
    uv run python mcard/ptr/core/signaling_server.py
    # or with port:
    PORT=3001 uv run python mcard/ptr/core/signaling_server.py
"""

import asyncio
import json
import logging
import os
import sys
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[Signal] %(message)s'
)
logger = logging.getLogger(__name__)


class SignalingServer:
    """
    In-memory signaling server for WebRTC coordination.
    
    Features:
    - SSE (Server-Sent Events) for real-time message delivery
    - Message buffering for offline peers
    - Peer registration and discovery
    """
    
    def __init__(self):
        # peer_id -> response writer (for SSE)
        self.clients: Dict[str, Any] = {}
        # peer_id -> list of buffered messages
        self.message_buffer: Dict[str, List[Dict]] = defaultdict(list)
        # Lock for thread-safe operations
        self._lock = asyncio.Lock() if sys.version_info >= (3, 10) else None
    
    def register_client(self, peer_id: str, response: Any) -> None:
        """Register a client for SSE messages."""
        logger.info(f"Client connected: {peer_id}")
        self.clients[peer_id] = response
        
        # Flush buffered messages
        if peer_id in self.message_buffer:
            for msg in self.message_buffer[peer_id]:
                self._send_sse(response, msg)
            del self.message_buffer[peer_id]
    
    def unregister_client(self, peer_id: str) -> None:
        """Unregister a client."""
        logger.info(f"Client disconnected: {peer_id}")
        if peer_id in self.clients:
            del self.clients[peer_id]
    
    def relay_message(self, target: str, message: Dict) -> bool:
        """Relay a message to a target peer."""
        msg_type = message.get('type', 'unknown')
        logger.info(f"Relaying {msg_type} to {target}")
        
        if target in self.clients:
            self._send_sse(self.clients[target], message)
            return True
        else:
            logger.info(f"Target {target} offline, buffering...")
            self.message_buffer[target].append(message)
            return False
    
    def _send_sse(self, response: Any, data: Dict) -> None:
        """Send an SSE message to a client."""
        try:
            message = f"data: {json.dumps(data)}\n\n"
            response.wfile.write(message.encode('utf-8'))
            response.wfile.flush()
        except Exception as e:
            logger.error(f"Failed to send SSE: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        return {
            "connected_peers": list(self.clients.keys()),
            "buffered_messages": {
                peer: len(msgs) for peer, msgs in self.message_buffer.items()
            }
        }


# Global signaling server instance
signaling = SignalingServer()


class SignalingHandler(BaseHTTPRequestHandler):
    """HTTP handler for signaling requests."""
    
    protocol_version = 'HTTP/1.1'
    
    def log_message(self, format: str, *args: Any) -> None:
        """Override to use our logger."""
        logger.debug(f"{self.address_string()} - {args[0]}")
    
    def _set_cors_headers(self) -> None:
        """Set CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self) -> None:
        """Handle CORS preflight."""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # Health check / Status
        if path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(signaling.get_status()).encode('utf-8'))
            return
        
        # SSE Registration: GET /signal?peer_id=...
        if path == '/signal':
            peer_id = query.get('peer_id', [None])[0]
            
            if not peer_id:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(b'Missing peer_id')
                return
            
            # Setup SSE
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self._set_cors_headers()
            self.end_headers()
            
            # Register client
            signaling.register_client(peer_id, self)
            
            # Keep connection alive
            try:
                while True:
                    # Send keepalive every 15 seconds
                    import time
                    time.sleep(15)
                    self.wfile.write(b': keep-alive\n\n')
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                signaling.unregister_client(peer_id)
            return
        
        # 404 for other paths
        self.send_response(404)
        self._set_cors_headers()
        self.end_headers()
    
    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # Signal relay: POST /signal
        if path == '/signal':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                msg = json.loads(body)
                
                target = msg.get('target')
                if not target:
                    self.send_response(400)
                    self._set_cors_headers()
                    self.end_headers()
                    self.wfile.write(b'Missing target')
                    return
                
                # Relay the message
                signaling.relay_message(target, msg)
                
                self.send_response(200)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(b'Sent')
                
            except json.JSONDecodeError as e:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(f'Invalid JSON: {e}'.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error handling POST: {e}")
                self.send_response(500)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
            return
        
        # 404 for other paths
        self.send_response(404)
        self._set_cors_headers()
        self.end_headers()


def kill_process_on_port(port: int) -> bool:
    """
    Kill any existing process on the specified port (macOS/Linux only).
    Safeguarded against killing the current process.
    
    Returns True if a process was killed, False otherwise.
    """
    import subprocess
    import os
    
    try:
        # Find PID using lsof
        result = subprocess.run(
            f"lsof -ti:{port}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            logger.info(f"No existing process on port {port}")
            return False
            
        try:
            target_pid = int(result.stdout.strip().split('\n')[0]) # Take first line
        except ValueError:
             return False

        if target_pid == os.getpid():
            logger.warning(f"Port {port} is held by CURRENT process ({target_pid}). NOT killing it.")
            return False
            
        # Kill the process
        kill_res = subprocess.run(
            f"kill -9 {target_pid}",
            shell=True,
            capture_output=True
        )
        
        if kill_res.returncode == 0:
            logger.info(f"Killed existing process {target_pid} on port {port}")
            time.sleep(0.5)  # Wait for port to be released
            return True
        else:
            logger.error(f"Failed to kill process {target_pid}: {kill_res.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.debug(f"Error killing process on port: {e}")
        return False


def find_available_port(start_port: int = 3000, max_tries: int = 10) -> int:
    """
    Find an available port starting from start_port.
    
    Args:
        start_port: Port to start searching from
        max_tries: Maximum number of ports to try
        
    Returns:
        An available port number
        
    Raises:
        OSError: If no available port found
    """
    import socket
    
    for attempt in range(max_tries):
        port = start_port + attempt
        try:
            # Try to bind to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('', port))
                return port
        except OSError:
            if attempt == 0:
                # Try killing existing process on first attempt
                logger.info(f"Port {port} in use, attempting to kill existing process...")
                if kill_process_on_port(port):
                    # Try again after killing
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            sock.bind(('', port))
                            return port
                    except OSError:
                        pass
            logger.info(f"Port {port} still in use, trying next...")
    
    raise OSError(f"Could not find available port after {max_tries} attempts starting from {start_port}")


def run_server(port: int = 3000, background: bool = False, auto_find_port: bool = True) -> HTTPServer:
    """
    Run the signaling server.
    
    Args:
        port: Port to listen on (default: 3000)
        background: If True, run in a background thread
        auto_find_port: If True, automatically find an available port if default is in use
        
    Returns:
        The HTTPServer instance
    """
    actual_port = port
    
    if auto_find_port:
        try:
            actual_port = find_available_port(port)
            if actual_port != port:
                logger.info(f"Requested port {port} unavailable, using port {actual_port}")
        except OSError as e:
            logger.error(str(e))
            raise
    
    try:
        server = HTTPServer(('', actual_port), SignalingHandler)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {actual_port} is already in use")
            if auto_find_port:
                # Try one more time with port killing
                kill_process_on_port(actual_port)
                server = HTTPServer(('', actual_port), SignalingHandler)
            else:
                raise
        else:
            raise
    
    # Store actual port for reference
    server.actual_port = actual_port
    
    if background:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Server running on port {actual_port} (background)")
    else:
        logger.info(f"Server running on port {actual_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
            server.shutdown()
    
    return server


if __name__ == '__main__':
    import time
    port = int(os.environ.get('PORT', 3000))
    run_server(port)

