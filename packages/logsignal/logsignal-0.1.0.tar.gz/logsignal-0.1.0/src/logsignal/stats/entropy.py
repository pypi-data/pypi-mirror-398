import math
from collections import Counter, deque

class EntropySpike:
    name = "entropy_spike"
    level = "MEDIUM"

    def __init__(self, window=50, threshold=1.5, tokenizer="char"):
        self.window = window
        self.threshold = threshold
        self.tokenizer = tokenizer

        self.entropy_history = deque(maxlen=window)

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
            print(f"[DEBUG] entropy warm-up ({len(self.entropy_history)}/{self.window})")
            return []

        mean = sum(self.entropy_history) / len(self.entropy_history)
        variance = sum((e - mean) ** 2 for e in self.entropy_history) / len(self.entropy_history)
        std = math.sqrt(variance)

        # 안전장치
        if std < 1e-6:
            self.entropy_history.append(entropy)
            return []

        z = (entropy - mean) / std
        # print(
        #     "[DEBUG]",
        #     "entropy=", round(entropy, 3),
        #     "mean=", round(mean, 3),
        #     "std=", round(std, 3),
        #     "z=", round(z, 3),
        # )

        signal = []
        if z > self.threshold:
            signal.append({
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

        # 이제 baseline 업데이트
        self.entropy_history.append(entropy)

        return signal
