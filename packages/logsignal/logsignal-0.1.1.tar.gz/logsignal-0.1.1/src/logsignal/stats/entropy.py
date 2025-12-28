import math
from collections import Counter, deque


class EntropySpike:
    name = "entropy_spike"
    level = "MEDIUM"

    def __init__(
        self,
        window=50,
        threshold=2.5,
        tokenizer="char",
        min_std=0.3,
        cooldown=10,
    ):
        self.window = window
        self.threshold = threshold
        self.tokenizer = tokenizer
        self.min_std = min_std
        self.cooldown = cooldown

        self.entropy_history = deque(maxlen=window)
        self.cooldown_left = 0

    def _tokenize(self, message: str):
        if self.tokenizer == "word":
            return message.split()
        return list(message)

    def _entropy(self, tokens):
        counts = Counter(tokens)
        total = sum(counts.values())

        entropy = 0.0
        for c in counts.values():
            p = c / total
            entropy -= p * math.log2(p)

        return entropy

    def feed(self, record):
        message = record.get("message", "")
        tokens = self._tokenize(message)

        if not tokens:
            return []

        entropy = self._entropy(tokens)

        # warm-up
        if len(self.entropy_history) < self.window:
            self.entropy_history.append(entropy)
            return []

        mean = sum(self.entropy_history) / len(self.entropy_history)
        variance = sum((e - mean) ** 2 for e in self.entropy_history) / len(self.entropy_history)
        std = max(math.sqrt(variance), self.min_std)

        z = (entropy - mean) / std

        signals = []

        if self.cooldown_left > 0:
            self.cooldown_left -= 1
        elif z > self.threshold:
            signals.append({
                "name": self.name,
                "level": self.level,
                "message": "Log entropy spike detected",
                "details": {
                    "entropy": round(entropy, 3),
                    "mean": round(mean, 3),
                    "std": round(std, 3),
                    "z": round(z, 2),
                    "window": self.window,
                },
            })
            self.cooldown_left = self.cooldown

        # baseline 보호: 정상일 때만 학습
        if not signals:
            self.entropy_history.append(entropy)

        return signals
