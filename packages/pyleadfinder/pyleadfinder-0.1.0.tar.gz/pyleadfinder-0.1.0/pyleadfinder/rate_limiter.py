"""Rate limiting utilities for API calls."""

import time
import threading
from collections import deque


class RateLimiter:
    """Thread-safe rate limiter for API requests."""

    def __init__(self, max_requests_per_minute: int):
        self.max_requests = max_requests_per_minute
        self.request_times = deque()
        self.lock = threading.Lock()

    def wait_if_needed(self):
        """Block until a request can be made within rate limits."""
        with self.lock:
            now = time.time()

            # Remove requests older than 60 seconds
            while self.request_times and now - self.request_times[0] >= 60:
                self.request_times.popleft()

            # Wait if we're at the limit
            if len(self.request_times) >= self.max_requests:
                sleep_time = 60 - (now - self.request_times[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    self.request_times.popleft()

            # Record this request
            self.request_times.append(time.time())
