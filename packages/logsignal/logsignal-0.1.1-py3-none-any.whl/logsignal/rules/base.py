from abc import ABC, abstractmethod
from typing import Dict, List
from logsignal.signal import Signal


class Rule(ABC):
    """
    Base class for all rule-based detectors.
    """

    @abstractmethod
    def feed(self, log: Dict) -> List[Signal]:
        """
        Consume a parsed log entry.
        Return a list of generated signals (can be empty).
        """
        raise NotImplementedError
