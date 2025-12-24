"""TrampolineClient - Thread-based client for connecting to Trampoline proxy."""

from httpx._config import Timeout
import asyncio
import base64
import json
import logging
import ssl
import threading
from typing import Optional
from urllib.parse import urljoin

import httpx
import websockets

logger = logging.getLogger("trampoline_client")


class TrampolineClient(threading.Thread):
    """
    A thread-based client for connecting to a Trampoline reverse proxy server.
    
    Connects to the Trampoline server via WebSocket and forwards incoming requests
    to a local target server.
    
    Args:
        host: The Trampoline server URL (e.g., "ws://localhost:8080" or "wss://t.example.com")
        name: The tunnel name to register (e.g., "my-service")
        secret: Optional authentication secret (matches TUNNEL_SECRET on server)
        target: The local server to forward requests to (default: "http://localhost:80")
        existing_ok: If True, allows joining an existing tunnel pool for load balancing (default: False)
        max_retries: Maximum reconnection attempts (default: 5, 0 = infinite retries)
        retry_delay: Initial delay between reconnection attempts in seconds (default: 5)
        daemon: Whether to run as a daemon thread (default: True)
    
    Example:
        # Single worker
        client = TrampolineClient(
            host="wss://t.example.com",
            name="myapp",
            secret="secret",
            target="http://localhost:3000"
        )
        
        # Multiple workers with load balancing
        client = TrampolineClient(
            host="wss://t.example.com",
            name="myapp",
            secret="secret",
            target="http://localhost:3000",
            existing_ok=True  # Join existing pool
        )
        client.start()
        
        # Check if connected
        if client.connected:
            print("Tunnel is active!")
        
        # Get public URL (e.g., https://myapp.t.example.com)
        print(f"Service available at: {client.remote_address}")
        
        # Stop the client
        client.stop()
    """
    
    def __init__(
        self,
        host: str,
        name: str,
        secret: Optional[str] = None,
        target: str = "http://localhost:80",
        existing_ok: bool = False,
        verify_ssl: bool = True,
        max_retries: int = 5,
        retry_delay: float = 5.0,
        daemon: bool = True,
    ):
        """
        Initialize the TrampolineClient.
        
        Args:
            host: The Trampoline server WebSocket URL
            name: The tunnel name to register
            secret: Optional authentication secret
            target: The local server to forward requests to
            existing_ok: If True, allows joining an existing tunnel pool
            verify_ssl: If False, disables SSL certificate verification (for development)
            max_retries: Maximum reconnection attempts (0 = infinite retries)
            retry_delay: Initial delay between reconnection attempts in seconds
            daemon: Whether to run as a daemon thread (default: True)
        """
        super().__init__(daemon=daemon)
        self.host = host.rstrip("/")
        self.name = name
        self.secret = secret
        self.target = target.rstrip("/")
        self.existing_ok = existing_ok
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._max_retry_delay = 60.0  # Cap exponential backoff at 60 seconds
        self._stop_event = threading.Event()
        self._connected = False
        self._remote_address: Optional[str] = None
        self._remote_address_roundrobin: Optional[str] = None
        self._worker_index: int = -1
        self._pool_size: int = 0
        self._reconnect_count: int = 0
        self._lock = threading.Lock()
    
    @property
    def connected(self) -> bool:
        """Check if the WebSocket connection is currently active."""
        with self._lock:
            return self._connected
    
    @property
    def remote_address(self) -> Optional[str]:
        """
        Get the public URL for this specific worker.
        
        Returns the index-specific address (e.g., "https://myapp-0.t.example.com")
        if the connection is established, None otherwise.
        
        Note: Requires the server to have BASE_DOMAIN configured.
        """
        with self._lock:
            return self._remote_address
    
    @property
    def remote_address_roundrobin(self) -> Optional[str]:
        """
        Get the public URL for round-robin access to the worker pool.
        
        Returns the generic address (e.g., "https://myapp.t.example.com")
        if the connection is established, None otherwise.
        """
        with self._lock:
            return self._remote_address_roundrobin
    
    @property
    def worker_index(self) -> int:
        """Get the assigned worker index (-1 if not connected)."""
        with self._lock:
            return self._worker_index
    
    @property
    def pool_size(self) -> int:
        """Get the number of workers in this tunnel's pool."""
        with self._lock:
            return self._pool_size
    
    @property
    def reconnect_count(self) -> int:
        """Get the number of reconnection attempts made."""
        with self._lock:
            return self._reconnect_count
    
    def _set_connected(
        self, 
        value: bool, 
        remote_address: Optional[str] = None, 
        remote_address_roundrobin: Optional[str] = None,
        worker_index: int = -1,
        pool_size: int = 0
    ) -> None:
        """Set the connection status thread-safely."""
        with self._lock:
            self._connected = value
            self._remote_address = remote_address if value else None
            self._remote_address_roundrobin = remote_address_roundrobin if value else None
            self._worker_index = worker_index if value else -1
            self._pool_size = pool_size if value else 0
    
    def run(self) -> None:
        """Main thread execution method - runs the async event loop."""
        asyncio.run(self._run_async())
    
    async def _run_async(self) -> None:
        """Async main loop for WebSocket connection with auto-reconnect."""
        tunnel_url = f"{self.host}/tunnel"
        
        headers = {
            "X-Tunnel-Name": self.name,
            "X-Existing-Ok": "true" if self.existing_ok else "false",
        }
        if self.secret:
            headers["Authorization"] = f"Bearer {self.secret}"
        
        # Setup SSL context once
        ssl_context = None
        if tunnel_url.startswith("wss://"):
            if self.verify_ssl:
                ssl_context = ssl.create_default_context()
            else:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
        
        current_delay = self.retry_delay
        
        while not self._stop_event.is_set():
            try:
                logger.info(f"Connecting to {tunnel_url} as '{self.name}'...")
                
                async with websockets.connect(tunnel_url, additional_headers=headers, ssl=ssl_context) as ws:
                    # Reset reconnect delay on successful connection
                    current_delay = self.retry_delay
                    
                    # Wait for welcome message from server
                    welcome_msg = await ws.recv()
                    welcome = json.loads(welcome_msg)
                    
                    if welcome.get("type") == "welcome":
                        public_address = welcome.get("public_address", "")
                        public_address_generic = welcome.get("public_address_generic", "")
                        worker_index = welcome.get("worker_index", 0)
                        pool_size = welcome.get("pool_size", 1)
                        self._set_connected(
                            True, 
                            public_address, 
                            public_address_generic,
                            worker_index,
                            pool_size
                        )
                        
                        if public_address:
                            logger.info(f"Connected! Worker '{self.name}' index {worker_index} at: {public_address}")
                            logger.info(f"Round-robin address: {public_address_generic}")
                        else:
                            logger.info(f"Connected! Tunnel '{self.name}' worker {worker_index} is active (no public URL configured).")
                    else:
                        self._set_connected(True)
                        logger.info(f"Connected! Tunnel '{self.name}' is now active.")
                    
                    # Reset reconnect count on successful connection
                    with self._lock:
                        self._reconnect_count = 0
                    
                    try:
                        await self._handle_messages(ws)
                    finally:
                        self._set_connected(False)
                        
            except websockets.exceptions.ConnectionClosed as e:
                self._set_connected(False)
                logger.warning(f"Connection closed: {e}")
            except Exception as e:
                self._set_connected(False)
                logger.error(f"Connection error: {e}")
            
            # Check if we should stop
            if self._stop_event.is_set():
                break
            
            # Handle reconnection
            with self._lock:
                self._reconnect_count += 1
                attempt = self._reconnect_count
            
            # Check retry limit (0 = infinite)
            if self.max_retries > 0 and attempt > self.max_retries:
                logger.error(f"Max reconnection attempts ({self.max_retries}) reached. Giving up.")
                break
            
            logger.info(f"Reconnecting in {current_delay:.1f}s (attempt {attempt}{f'/{self.max_retries}' if self.max_retries > 0 else ''})...")
            
            # Wait before reconnecting (check stop event every 0.5s)
            wait_time = 0
            while wait_time < current_delay and not self._stop_event.is_set():
                await asyncio.sleep(0.5)
                wait_time += 0.5
            
            # Exponential backoff with cap
            current_delay = min(current_delay * 2, self._max_retry_delay)
        
        logger.info("Disconnected from server.")
    
    async def _handle_messages(self, ws) -> None:
        """Handle incoming messages from the WebSocket."""
        async with httpx.AsyncClient(timeout=Timeout(timeout=15.0)) as http_client:
            while not self._stop_event.is_set():
                try:
                    # Wait for message with timeout to check stop event
                    message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    request = json.loads(message)
                    
                    logger.debug(f"Received request: {request['method']} {request['path']}")
                    
                    # Forward request to target server
                    response = await self._forward_request(http_client, request)
                    
                    # Send response back
                    await ws.send(json.dumps(response))
                    logger.debug(f"Sent response: {response['status']}")
                    
                except asyncio.TimeoutError:
                    # Check stop event and continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
    
    async def _forward_request(self, client: httpx.AsyncClient, request: dict) -> dict:
        """Forward a request to the target server and return the response."""
        request_id = request["id"]
        method = request["method"]
        path = request["path"]
        headers = request.get("headers", {})
        body_b64 = request.get("body", "")
        
        # Decode body
        body = base64.b64decode(body_b64) if body_b64 else None
        
        # Build target URL
        url = urljoin(self.target, path)
        
        # Remove hop-by-hop headers
        hop_by_hop = {"connection", "keep-alive", "transfer-encoding", "upgrade"}
        filtered_headers = {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}
        
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=filtered_headers,
                content=body,
                follow_redirects=True,
            )
            
            # Build response
            response_headers = {k: v for k, v in response.headers.items()}
            response_body = base64.b64encode(response.content).decode("utf-8")
            
            return {
                "id": request_id,
                "status": response.status_code,
                "headers": response_headers,
                "body": response_body,
            }
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            error_body = json.dumps({"error": str(e)})
            return {
                "id": request_id,
                "status": 502,
                "headers": {"Content-Type": "application/json"},
                "body": base64.b64encode(error_body.encode()).decode("utf-8"),
            }
    
    def stop(self) -> None:
        """Signal the client to stop and disconnect."""
        self._stop_event.set()
