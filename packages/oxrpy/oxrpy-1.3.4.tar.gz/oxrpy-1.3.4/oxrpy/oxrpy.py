import requests
import logging
import time
import threading
from typing import Optional, Union

class OxfordAPIError(Exception):
    """Base exception for Oxford API errors."""
    pass

class RateLimitError(OxfordAPIError):
    """Exception raised when rate limit is exceeded."""
    pass

class ServerOfflineError(OxfordAPIError):
    """Exception raised when server is offline or unavailable (HTTP 503)."""
    pass

class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_tokens(self, tokens: int = 1, timeout: float = None) -> bool:
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if tokens were acquired, False if timeout exceeded
        """
        start_time = time.time()
        while True:
            if self.consume(tokens):
                return True
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.01)  # Small sleep to avoid busy waiting

class OxfordAPI:
    def __init__(self, server_key: Optional[str] = None, global_key: Optional[str] = None, server_id: Optional[str] = None, timeout: int = 10, rate_limit: Union[str, float, None] = "auto", max_retries: int = 3):
        """
        Initialize the Oxford API client.
        
        Args:
            server_key (Optional[str]): API key for server authentication (server-specific key).
            global_key (Optional[str]): Global API key for authentication (has its own rate limits).
            server_id (Optional[str]): Unique private server identifier (UUID format). Deprecated - no longer required.
            timeout (int): Request timeout in seconds. Default is 10.
            rate_limit (Union[str, float, None]): Rate limiting configuration.
                - "auto": Default rate limiting (~29 requests/second, optimized for GET endpoints with 30/sec limits)
                - "none": Disable rate limiting entirely
                - float: Custom minimum time between requests in seconds
                - None: Same as "none" (for backward compatibility)
                Note: execute_command() has a stricter 1/sec API limit. Global keys have their own rate limits.
            max_retries (int): Maximum number of retries for rate-limited requests. Default is 3.
        """
        if not server_key and not global_key:
            raise ValueError("Either server_key or global_key is required")
        
        if server_key and global_key:
            raise ValueError("Cannot specify both server_key and global_key")
        
        self.is_global_key = global_key is not None
        
        # Parse rate_limit parameter
        if self.is_global_key:
            # Global keys have their own rate limits, so disable client-side rate limiting
            self.rate_limiter = None
            self.command_limiter = None
        elif rate_limit == "auto":
            # Token bucket: 29 tokens/second capacity, burst up to 30
            self.rate_limiter = TokenBucket(rate=29.0, capacity=30)
            # Separate limiter for commands (1/sec)
            self.command_limiter = TokenBucket(rate=1.0, capacity=1)
        elif rate_limit == "none" or rate_limit is None:
            self.rate_limiter = None
            self.command_limiter = None
        elif isinstance(rate_limit, (int, float)):
            if rate_limit < 0:
                raise ValueError("rate_limit must be non-negative")
            # For custom rates, use a token bucket with the specified rate
            self.rate_limiter = TokenBucket(rate=1.0/rate_limit, capacity=max(1, int(1.0/rate_limit)))
            # Commands still use 1/sec regardless of custom rate
            self.command_limiter = TokenBucket(rate=1.0, capacity=1)
        else:
            raise ValueError("rate_limit must be 'auto', 'none', None, or a non-negative number")
        
        self.base_url = "https://api.oxfd.re/v1"
        
        # Set up headers based on authentication type
        if self.is_global_key:
            self.headers = {
                "Authorization": global_key
            }
        else:
            self.headers = {
                "server-key": server_key
            }
            # Add server-id header only if provided (for backward compatibility)
            if server_id:
                self.headers["server-id"] = server_id
                
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """Internal method to make API requests with error handling, rate limiting, and retries."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            # Rate limiting (if enabled)
            if self.rate_limiter is not None:
                # Wait for a token to be available (with timeout)
                if not self.rate_limiter.wait_for_tokens(timeout=30.0):
                    raise RateLimitError(f"Rate limit timeout waiting for token on {endpoint}")
            
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers, timeout=self.timeout)
                elif method == "POST":
                    response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                self.logger.info(f"Successfully called {method} {endpoint}")
                return response.json()
                
            except requests.HTTPError as e:
                if response.status_code == 429:  # Too Many Requests
                    if attempt < self.max_retries:
                        # Exponential backoff: wait 2^attempt seconds
                        wait_time = 2 ** attempt
                        self.logger.warning(f"Rate limited on {endpoint}, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise RateLimitError(f"Rate limit exceeded for {endpoint} after {self.max_retries + 1} attempts")
                elif response.status_code == 503:  # Service Unavailable - Server offline
                    # /server endpoint is always available even when server is offline
                    if endpoint == "/server":
                        # For /server endpoint, 503 might still contain valid data
                        try:
                            return response.json()
                        except:
                            # If we can't parse JSON, treat as offline
                            raise ServerOfflineError(f"Server is offline or unavailable")
                    else:
                        raise ServerOfflineError(f"Server is offline or unavailable")
                else:
                    self.logger.error(f"HTTP error for {endpoint}: {e}")
                    raise OxfordAPIError(f"HTTP error: {e}")
                    
            except requests.Timeout:
                self.logger.error(f"Request to {endpoint} timed out")
                raise OxfordAPIError(f"Request to {endpoint} timed out")
            except requests.RequestException as e:
                self.logger.error(f"Request error for {endpoint}: {e}")
                raise OxfordAPIError(f"Request error: {e}")
        
        # This should never be reached, but just in case
        raise OxfordAPIError(f"Request failed after {self.max_retries + 1} attempts")

    @property
    def servers(self):
        """Access server-related endpoints."""
        return Servers(self)

    @property
    def logs(self):
        """Access log-related endpoints."""
        return Logs(self)

    @property
    def commands(self):
        """Access command execution endpoints."""
        return Commands(self)

    def get_server(self):
        """Returns general information about the private server."""
        return self._make_request("GET", "/server")

    def get_players(self):
        """Returns a list of players currently in the server."""
        return self._make_request("GET", "/server/players")

    def get_queue(self):
        """Returns the current reserved server queue."""
        return self._make_request("GET", "/server/queue")

    def get_bans(self):
        """Returns active bans for the server."""
        return self._make_request("GET", "/server/bans")

    def get_killlogs(self):
        """Returns recent kill logs (maximum 100 entries)."""
        return self._make_request("GET", "/server/killlogs")

    def get_commandlogs(self):
        """Returns recent command execution logs."""
        return self._make_request("GET", "/server/commandlogs")

    def get_joinlogs(self):
        """Returns recent player join/leave logs."""
        return self._make_request("GET", "/server/joinlogs")

    def get_modcalls(self):
        """Returns recent moderator call requests."""
        return self._make_request("GET", "/server/modcalls")

    def get_vehicles(self):
        """Returns vehicles currently spawned in the server."""
        return self._make_request("GET", "/server/vehicles")

    def get_robberies(self):
        """
        Returns the current status of all robbery locations.
        Each entry contains:
            - Name (str): The name of the robbery location.
            - Alarm (bool): Whether the alarm is active.
            - Available (bool): Whether the location is available for robbery.
        """
        return self._make_request("GET", "/server/robberies")

    def get_radiocalls(self):
        """
        Returns recent radio calls.
        Each entry contains:
            - Timestamp (int): Unix timestamp of the call.
            - AuthorUserId (int): The user ID of the caller.
            - AuthorUsername (str): The username of the caller.
            - Location (str): The location of the call.
            - Description (str): The description of the call.
            - Channel (str): The radio channel.
        """
        return self._make_request("GET", "/server/radiocalls")

    def execute_command(self, command: str):
        """Executes a permitted command on the server."""
        if not command:
            raise ValueError("Command cannot be empty")
        
        # Commands have stricter rate limiting (1/sec), so use the command limiter
        if self.command_limiter is not None:
            if not self.command_limiter.wait_for_tokens(timeout=30.0):
                raise RateLimitError("Command rate limit timeout")
        
        data = {"command": command}
        return self._make_request("POST", "/server/command", data)

class Servers:
    """Manager for server-related endpoints."""
    
    def __init__(self, api: 'OxfordAPI'):
        self.api = api

    def get_server(self):
        """Returns general information about the private server."""
        return self.api.get_server()

    def get_players(self):
        """Returns a list of players currently in the server."""
        return self.api.get_players()

    def get_queue(self):
        """Returns the current reserved server queue."""
        return self.api.get_queue()

    def get_bans(self):
        """Returns active bans for the server."""
        return self.api.get_bans()

    def get_vehicles(self):
        """Returns vehicles currently spawned in the server."""
        return self.api.get_vehicles()

class Logs:
    """Manager for log-related endpoints."""
    
    def __init__(self, api: 'OxfordAPI'):
        self.api = api

    def get_killlogs(self):
        """Returns recent kill logs (maximum 100 entries)."""
        return self.api.get_killlogs()

    def get_commandlogs(self):
        """Returns recent command execution logs."""
        return self.api.get_commandlogs()

    def get_joinlogs(self):
        """Returns recent player join/leave logs."""
        return self.api.get_joinlogs()

    def get_modcalls(self):
        """Returns recent moderator call requests."""
        return self.api.get_modcalls()

    def get_robberies(self):
        """
        Returns the current status of all robbery locations.
        Each entry contains:
            - Name (str): The name of the robbery location.
            - Alarm (bool): Whether the alarm is active.
            - Available (bool): Whether the location is available for robbery.
        """
        return self.api.get_robberies()

    def get_radiocalls(self):
        """
        Returns recent radio calls.
        Each entry contains:
            - Timestamp (int): Unix timestamp of the call.
            - AuthorUserId (int): The user ID of the caller.
            - AuthorUsername (str): The username of the caller.
            - Location (str): The location of the call.
            - Description (str): The description of the call.
            - Channel (str): The radio channel.
        """
        return self.api.get_radiocalls()

class Commands:
    """Manager for command execution endpoints."""
    
    def __init__(self, api: 'OxfordAPI'):
        self.api = api

    def execute_command(self, command: str):
        """Executes a permitted command on the server."""
        return self.api.execute_command(command)