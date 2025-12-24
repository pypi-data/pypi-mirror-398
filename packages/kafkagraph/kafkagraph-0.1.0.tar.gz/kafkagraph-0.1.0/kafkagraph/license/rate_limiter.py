import time
from collections import deque

class RateLimiter:
    def __init__(self, per_sec=None, per_min=None):
        self.ps = per_sec
        self.pm = per_min
        self.s = deque()
        self.m = deque()

    def allow(self, n=1):
        now = time.time()
        while self.s and now - self.s[0] > 1:
            self.s.popleft()
        while self.m and now - self.m[0] > 60:
            self.m.popleft()

        if self.ps and len(self.s) + n > self.ps:
            return False
        if self.pm and len(self.m) + n > self.pm:
            return False

        for _ in range(n):
            self.s.append(now)
            self.m.append(now)
        return True
