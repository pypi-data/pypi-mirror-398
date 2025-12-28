from typing import List, Dict, Iterable
from logsignal.rules.base import Rule
from logsignal.notifiers.console import ConsoleNotifier
import time


class LogWatcher:
    def __init__(self):
        self.rules: List[Rule] = []
        self.stats = []
        self.notifiers = []

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def add_stat(self, stat):
        self.stats.append(stat)

    def add_notifier(self, notifier):
        self.notifiers.append(notifier)

    def process(self, log: Dict):
        for rule in self.rules:
            signals = rule.feed(log)
            for signal in signals:
                for notifier in self.notifiers:
                    notifier.notify(signal)

        for stat in self.stats:
            for signal in stat.feed(log):
                for notifier in self.notifiers:
                    notifier.notify(signal)

    def watch_stream(self, stream, tick_interval: float = 1.0):
        last_tick = time.time()

        for line in stream:
            now = time.time()

            if now - last_tick >= tick_interval:
                self.tick()
                last_tick = now

            log = {
                "message": line.strip(),
                "level": "ERROR" if "ERROR" in line else "INFO",
            }

            self.process(log)

    def tick(self):
        for rule in self.rules:
            if hasattr(rule, "tick"):
                for signal in rule.tick():
                    for notifier in self.notifiers:
                        notifier.notify(signal)
