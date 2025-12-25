"""Rate limiting utilities for API calls."""
import time
import asyncio
from collections import deque
from datetime import datetime, timedelta


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Plane API limits: 3600 requests/hour
    We use 50 requests/minute for better burst protection and safety.
    """
    
    def __init__(self, requests_per_minute: int = 50):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute (default: 50)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_minute * 60  # For display
        self.requests_per_second = requests_per_minute / 60.0
        self.min_interval = 1.0 / self.requests_per_second  # Seconds between requests
        
        # Track request timestamps (use per-minute buffer)
        self.request_times = deque(maxlen=requests_per_minute * 2)  # 2-minute buffer
        self.last_request_time = 0.0
        
        # Statistics
        self.total_requests = 0
        self.total_wait_time = 0.0
    
    async def acquire(self):
        """
        Acquire permission to make a request.
        Blocks if rate limit would be exceeded.
        """
        current_time = time.time()
        
        # Check if we need to wait based on minimum interval
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
            self.total_wait_time += wait_time
            current_time = time.time()
        
        # Check per-minute window
        one_minute_ago = current_time - 60
        
        # Remove requests older than 1 minute
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()
        
        # If we're at the per-minute limit, wait until oldest request expires
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = self.request_times[0]
            wait_time = (oldest_request + 60) - current_time + 0.1  # Add 100ms buffer
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.total_wait_time += wait_time
                current_time = time.time()
                
                # Clean up expired requests again
                one_minute_ago = current_time - 60
                while self.request_times and self.request_times[0] < one_minute_ago:
                    self.request_times.popleft()
        
        # Record this request
        self.request_times.append(current_time)
        self.last_request_time = current_time
        self.total_requests += 1
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        current_time = time.time()
        one_minute_ago = current_time - 60
        one_hour_ago = current_time - 3600
        
        # Count recent requests
        requests_last_minute = sum(1 for t in self.request_times if t > one_minute_ago)
        requests_last_hour = sum(1 for t in self.request_times if t > one_hour_ago)
        
        return {
            'total_requests': self.total_requests,
            'requests_last_minute': requests_last_minute,
            'requests_last_hour': requests_last_hour,
            'limit_per_minute': self.requests_per_minute,
            'limit_per_hour': self.requests_per_hour,
            'utilization_minute': f"{(requests_last_minute / self.requests_per_minute) * 100:.1f}%",
            'utilization_hour': f"{(requests_last_hour / self.requests_per_hour) * 100:.1f}%",
            'total_wait_time': f"{self.total_wait_time:.2f}s",
            'avg_wait_per_request': f"{(self.total_wait_time / self.total_requests * 1000):.1f}ms" if self.total_requests > 0 else "0ms",
        }
    
    def reset(self):
        """Reset rate limiter state."""
        self.request_times.clear()
        self.last_request_time = 0.0
        self.total_requests = 0
        self.total_wait_time = 0.0


class RateLimitError(Exception):
    """Raised when rate limit is exceeded and cannot be retried."""
    
    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f". Retry after {retry_after} seconds"
        super().__init__(msg)

