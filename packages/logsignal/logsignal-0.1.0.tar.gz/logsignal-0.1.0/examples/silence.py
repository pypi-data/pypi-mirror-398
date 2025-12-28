import time
from logsignal import LogWatcher
from logsignal.rules import SilenceRule
from logsignal.notifiers.console import ConsoleNotifier

watcher = LogWatcher()
watcher.add_rule(SilenceRule(timeout=3))
watcher.add_notifier(ConsoleNotifier())

# 로그 몇 개 들어옴
for _ in range(5):
    watcher.process({"message": "INFO working"})
    time.sleep(1)

print("---- stop logs ----")

# 로그 멈춤
for _ in range(5):
    watcher.tick()
    time.sleep(1)
