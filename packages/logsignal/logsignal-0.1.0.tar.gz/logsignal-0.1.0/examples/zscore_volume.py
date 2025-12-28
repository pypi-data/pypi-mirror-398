import time
from logsignal import LogWatcher
from logsignal.stats import ZScoreVolume
from logsignal.notifiers.console import ConsoleNotifier

watcher = LogWatcher()
watcher.add_stat(ZScoreVolume(window=5, threshold=2.0))
watcher.add_notifier(ConsoleNotifier())

# baseline: 아주 천천히
for _ in range(20):
    watcher.process({"message": "INFO normal"})
    time.sleep(1.0)

# spike: 아주 빠르게
for _ in range(30):
    watcher.process({"message": "INFO spike"})
