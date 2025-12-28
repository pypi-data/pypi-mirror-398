import time
from collections import deque
from typing import Dict, List

from logsignal.rules.base import Rule
from logsignal.signal import Signal


class ErrorSpikeRule(Rule):
    def __init__(
        self,
        level: str = "ERROR",
        threshold: int = 10,
        window: int = 60,
    ):
        self.level = level
        self.threshold = threshold
        self.window = window
        self.timestamps = deque()

    def feed(self, log: Dict) -> List[Signal]:
        now = time.time()

        # level 필터
        if log.get("level") != self.level:
            return []

        # 현재 timestamp 추가
        self.timestamps.append(now)

        # window 밖의 timestamp 제거
        cutoff = now - self.window
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

        if len(self.timestamps) >= self.threshold:
            return [
                Signal(
                    name="error_spike",
                    severity="high",
                    message=f"{self.level} logs spiked in last {self.window}s",
                    meta={
                        "count": len(self.timestamps),
                        "window": self.window,
                    },
                )
            ]

        return []
