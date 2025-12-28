from logsignal import LogWatcher
from logsignal.stats.entropy import EntropySpike

watcher = LogWatcher()
watcher.add_stat(
    EntropySpike(
        window=10,
        threshold=0.1,      # 낮춰서 명확히
    )
)

# 🔹 매우 낮은 entropy baseline
for _ in range(15):
    watcher.process({"message": "AAAAAAAAAAAAAA"})

# 🔥 매우 높은 entropy 로그
attack_logs = [
    "a8F!kP$Qz19@Lm#2xY",
    "GET /login.php?id=1' OR '1'='1'",
    "POST /wp-admin.php HTTP/1.1",
]

for msg in attack_logs:
    watcher.process({"message": msg})
