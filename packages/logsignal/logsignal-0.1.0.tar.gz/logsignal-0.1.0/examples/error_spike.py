import time
from logsignal import LogWatcher
from logsignal.rules import ErrorSpikeRule
from logsignal.notifiers.console import ConsoleNotifier

watcher = LogWatcher()
watcher.add_rule(ErrorSpikeRule(threshold=3, window=5))
watcher.add_notifier(ConsoleNotifier())

logs = [
    "INFO app started",
    "ERROR database failed",
    "ERROR connection timeout",
    "ERROR retry failed",
]

for line in logs:
    watcher.process({
        "message": line,
        "level": "ERROR" if "ERROR" in line else "INFO"
    })
    time.sleep(1)
