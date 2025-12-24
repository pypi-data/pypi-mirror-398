# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Utility functions and decorators."""

import functools
import time
from collections import deque
from typing import Callable, Dict


class RateLimiter:
    """Rate limiting decorator using token bucket algorithm."""

    def __init__(self, max_calls: int = 100, period: int = 3600):
        """Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in period
            period: Time period in seconds (default: 1 hour)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: Dict[str, deque] = {}  # Track per-instance

    def __call__(self, func: Callable) -> Callable:
        """Decorate function with rate limiting."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as key (could be enhanced with user ID)
            key = func.__name__

            if key not in self.calls:
                self.calls[key] = deque()

            now = time.time()
            call_times = self.calls[key]

            # Remove calls outside the time window
            while call_times and call_times[0] < now - self.period:
                call_times.popleft()

            # Check if limit exceeded
            if len(call_times) >= self.max_calls:
                oldest_call = call_times[0]
                wait_time = self.period - (now - oldest_call)
                raise RuntimeError(
                    f"Rate limit exceeded for {func.__name__}. "
                    f"Maximum {self.max_calls} calls per {self.period}s. "
                    f"Try again in {wait_time:.0f} seconds."
                )

            # Record this call
            call_times.append(now)

            # Execute function
            return func(*args, **kwargs)

        return wrapper


# Global rate limiter instances
# NOTE: Increased for benchmarking - TODO: restore to production limits after benchmark
rate_limit_analysis = RateLimiter(max_calls=10000, period=3600)  # 10000 per hour for benchmark
rate_limit_repair = RateLimiter(max_calls=10000, period=3600)  # 10000 per hour for benchmark
rate_limit_counterfactual = RateLimiter(
    max_calls=10000, period=3600
)  # 10000 per hour for benchmark
