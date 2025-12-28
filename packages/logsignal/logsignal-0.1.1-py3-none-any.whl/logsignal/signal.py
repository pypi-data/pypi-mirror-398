from dataclasses import dataclass, field
from typing import Dict, Any
import time


@dataclass
class Signal:
    name: str
    severity: str  # low | medium | high
    message: str
    timestamp: float = field(default_factory=lambda: time.time())
    meta: Dict[str, Any] = field(default_factory=dict)
