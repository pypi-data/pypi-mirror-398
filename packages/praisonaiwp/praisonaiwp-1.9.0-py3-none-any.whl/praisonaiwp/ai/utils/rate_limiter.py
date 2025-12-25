"""Rate limiting for API calls"""
import logging
import time
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(
        self,
        max_requests: int = 10,
        time_window: int = 60
    ):
        """Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    def wait_if_needed(self) -> Optional[float]:
        """Wait if rate limit would be exceeded

        Returns:
            float: Seconds waited (None if no wait needed)
        """
        now = time.time()

        # Remove old requests outside the time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # Check if we need to wait
        if len(self.requests) >= self.max_requests:
            # Calculate how long to wait
            oldest_request = self.requests[0]
            wait_until = oldest_request + self.time_window
            sleep_time = wait_until - now

            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached ({self.max_requests} requests/"
                    f"{self.time_window}s). Waiting {sleep_time:.1f}s..."
                )
                time.sleep(sleep_time)

                # Clean up again after waiting
                now = time.time()
                while self.requests and self.requests[0] < now - self.time_window:
                    self.requests.popleft()

                return sleep_time

        # Record this request
        self.requests.append(now)
        return None

    def reset(self):
        """Reset the rate limiter"""
        self.requests.clear()

    def get_remaining(self) -> int:
        """Get remaining requests in current window

        Returns:
            int: Number of requests remaining
        """
        now = time.time()

        # Remove old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        return max(0, self.max_requests - len(self.requests))
