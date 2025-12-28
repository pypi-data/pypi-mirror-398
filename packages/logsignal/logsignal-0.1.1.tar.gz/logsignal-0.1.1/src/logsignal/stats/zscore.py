import time
from collections import deque
from statistics import mean, stdev
from typing import Dict, List

from logsignal.signal import Signal


class ZScoreVolume:
    """
    Detect anomaly based on log volume using Z-score.
    """

    def __init__(
        self,
        window: int = 300,
        threshold: float = 3.0,
        min_samples: int = 5,
    ):
        self.window = window
        self.threshold = threshold
        self.min_samples = min_samples

        self.timestamps = deque()
        self.history = deque(maxlen=100)

        self.in_anomaly = False

    def feed(self, log: Dict) -> List[Signal]:
        now = time.time()

        # 로그가 들어올 때마다 timestamp 기록
        self.timestamps.append(now)

        # window 밖 제거
        cutoff = now - self.window
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

        current_count = len(self.timestamps)

        # 히스토리 쌓기
        self.history.append(current_count)

        if len(self.history) < self.min_samples:
            return []

        mu = mean(self.history)
        sigma = stdev(self.history)

        if sigma == 0:
            return []

        z = (current_count - mu) / sigma

        if abs(z) >= self.threshold:
            if not self.in_anomaly:
                self.in_anomaly = True
                return [
                    Signal(
                        name="volume_zscore_anomaly",
                        severity="medium",
                        message="Log volume anomaly detected (z-score)",
                        meta={
                            "current": current_count,
                            "mean": round(mu, 2),
                            "std": round(sigma, 2),
                            "z": round(z, 2),
                            "window": self.window,
                        },
                    )
                ]
        else:
            # 정상으로 회복
            if self.in_anomaly:
                self.in_anomaly = False

        return []
