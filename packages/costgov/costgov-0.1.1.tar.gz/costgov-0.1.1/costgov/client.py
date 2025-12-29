"""Main CostGov client implementation."""

import os
import time
import atexit
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import requests

from .exceptions import APIError, ConfigError


class CostGov:
    """
    CostGov client for tracking billable events.
    
    Example:
        >>> from costgov import CostGov
        >>> 
        >>> client = CostGov(
        ...     api_key="cg_prod_xxxxx",
        ...     project_id="proj_xxxxx"
        ... )
        >>> 
        >>> # Track an event
        >>> client.track("ai.openai.gpt4", 1500)
        >>> 
        >>> # Shutdown when done
        >>> client.shutdown()
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        api_url: Optional[str] = None,
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ):
        """
        Initialize CostGov client.
        
        Args:
            api_key: Your CostGov API key (or set COSTGOV_API_KEY env var)
            project_id: Your project ID (or set COSTGOV_PROJECT_ID env var)
            api_url: API endpoint URL (or set COSTGOV_API_URL env var)
            batch_size: Maximum events to batch before sending
            flush_interval: Seconds between automatic flushes
        
        Raises:
            ConfigError: If required configuration is missing
        """
        self.api_key = api_key or os.getenv("COSTGOV_API_KEY")
        self.project_id = project_id or os.getenv("COSTGOV_PROJECT_ID")
        self.api_url = api_url or os.getenv("COSTGOV_API_URL", "http://localhost:3001")
        
        if not self.api_key:
            raise ConfigError("API key is required. Provide api_key or set COSTGOV_API_KEY")
        if not self.project_id:
            raise ConfigError("Project ID is required. Provide project_id or set COSTGOV_PROJECT_ID")
        
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self._queue = []
        self._last_flush = time.time()
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "costgov-python/0.1.0",
        })
        
        # Register cleanup on exit
        atexit.register(self.shutdown)
    
    def track(self, metric: str, units: float, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track a billable event.
        
        Args:
            metric: Event metric name (e.g., "ai.openai.gpt4")
            units: Number of units consumed
            metadata: Optional metadata dictionary
        
        Returns:
            True if event was queued successfully
        
        Example:
            >>> client.track("ai.openai.gpt4", 1500)
            >>> client.track("email.send", 1, metadata={"provider": "sendgrid"})
        """
        event = {
            "metric": metric,
            "units": units,
            "timestamp": int(time.time() * 1000),  # milliseconds
        }
        
        if metadata:
            event["metadata"] = metadata
        
        self._queue.append(event)
        
        # Auto-flush if batch size reached or interval elapsed
        if len(self._queue) >= self.batch_size or \
           (time.time() - self._last_flush) >= self.flush_interval:
            self.flush()
        
        return True
    
    def flush(self) -> bool:
        """
        Flush queued events to the API immediately.
        
        Returns:
            True if flush was successful
        
        Raises:
            APIError: If the API request fails
        """
        if not self._queue:
            return True
        
        events_to_send = self._queue.copy()
        self._queue.clear()
        self._last_flush = time.time()
        
        try:
            endpoint = urljoin(self.api_url, "/v1/events")
            
            # Send each event individually for now
            # TODO: Implement batch endpoint
            for event in events_to_send:
                response = self._session.post(
                    endpoint,
                    json=event,
                    timeout=10,
                )
                
                if response.status_code >= 400:
                    raise APIError(
                        f"API request failed: {response.text}",
                        status_code=response.status_code
                    )
            
            return True
            
        except requests.RequestException as e:
            # Re-queue events on failure
            self._queue.extend(events_to_send)
            raise APIError(f"Network error: {str(e)}")
    
    def shutdown(self):
        """
        Flush remaining events and clean up resources.
        
        Call this when your application exits.
        """
        try:
            self.flush()
        except Exception as e:
            print(f"[CostGov] Error during shutdown: {e}")
        finally:
            self._session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False
