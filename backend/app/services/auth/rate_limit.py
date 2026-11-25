"""
In-memory sliding-window rate limiter for login, sign-up and demo creation.

State is per process and resets on restart; it is a first line of defence against
password guessing, not a replacement for a shared rate limiter in front of the app.
"""

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Hashable

from fastapi import Request


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: float):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: Dict[Hashable, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: Hashable, now: float) -> Deque[float]:
        events = self._events[key]
        while events and events[0] <= now - self.window_seconds:
            events.popleft()
        if not events:
            self._events.pop(key, None)
        return events

    def retry_after(self, key: Hashable) -> int:
        """Seconds until another event is allowed for this key (0 if allowed now)."""
        now = time.monotonic()
        with self._lock:
            events = self._prune(key, now)
            if len(events) < self.max_events:
                return 0
            return max(1, int(events[0] + self.window_seconds - now) + 1)

    def record(self, key: Hashable) -> None:
        with self._lock:
            self._events[key].append(time.monotonic())

    def reset(self, key: Hashable) -> None:
        with self._lock:
            self._events.pop(key, None)


# Failed logins per (client, username); successful login clears the counter
login_failures = SlidingWindowLimiter(max_events=10, window_seconds=15 * 60)
# Accounts created per client
registrations = SlidingWindowLimiter(max_events=10, window_seconds=60 * 60)
# Demo instances created per client
demo_logins = SlidingWindowLimiter(max_events=30, window_seconds=60 * 60)


def client_ip(request: Request) -> str:
    """
    The backend only listens on 127.0.0.1 behind the Next.js proxy, which appends the
    real client address to X-Forwarded-For; the last entry is the one the proxy added.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"
