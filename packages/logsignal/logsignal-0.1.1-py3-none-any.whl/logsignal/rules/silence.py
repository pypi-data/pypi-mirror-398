import time
from typing import Dict, List

from logsignal.rules.base import Rule
from logsignal.signal import Signal


class SilenceRule(Rule):
    """
    Detect when no logs are received for a given timeout.
    """

    def __init__(
        self,
        timeout: int = 60,
        severity: str = "high",
    ):
        self.timeout = timeout
        self.severity = severity

        self.last_seen = time.time()
        self.in_silence = False

    def feed(self, log: Dict) -> List[Signal]:
        now = time.time()
        self.last_seen = now

        # 로그가 들어오면 silence 상태 해제
        if self.in_silence:
            self.in_silence = False

        return []

    def tick(self) -> List[Signal]:
        """
        Should be called periodically to check silence.
        """
        now = time.time()
        elapsed = now - self.last_seen

        if elapsed >= self.timeout and not self.in_silence:
            self.in_silence = True
            return [
                Signal(
                    name="log_silence",
                    severity=self.severity,
                    message=f"No logs received for {int(elapsed)} seconds",
                    meta={
                        "timeout": self.timeout,
                        "elapsed": int(elapsed),
                    },
                )
            ]

        return []
