# LogSignal

> Lightweight rule-based and statistical log anomaly detection for Python backends

**LogSignal** is a lightweight library for detecting security signals and anomalies
in **any Python backend that produces logs** — including FastAPI, Flask, Django,
batch jobs, CLI tools, and long-running daemons.

It is designed to be **simple, fast, and dependency-free**, making it suitable
for both personal projects and production systems.

---

## Why LogSignal?

Most existing logging or security solutions fall into one of these categories:

* Too heavy (SIEMs, Elastic stacks, LLM-based systems)
* Too complex (regex-heavy configuration, steep learning curves)
* Overkill for small teams or personal projects

**LogSignal has a clear goal:**

> *“If you have logs, you should be able to detect anomalies in under 5 minutes.”*

---

## Key Characteristics

* ❌ No SIEM required
* ❌ No complex configuration
* ❌ No LLMs or external APIs
* ✅ Rule-based detection
* ✅ Statistical detection
* ✅ Native Python `logging` integration

---

## Key Features

### 1️⃣ Rule-Based Detection (Default)

Deterministic and immediate detection based on explicit rules.

* Keyword matching
* Log level matching
* Frequency / spike detection within a time window

```python
from logsignal import Rule

Rule.contains("ERROR")
Rule.level("CRITICAL")
Rule.spike(threshold=5, window=10)
```

Rule-based detectors work **immediately** and are ideal for hard signals
such as errors, crashes, or known failure patterns.

---

### 2️⃣ Statistical Detection (Optional)

Adaptive detectors based on lightweight statistical methods.

* Moving averages
* Z-score based spike detection
* Automatic baseline learning

```python
from logsignal import StatRule

StatRule.error_rate_zscore(z=3.0)
```

> ❗ This is **math/statistics-based**, not ML
> → fast, explainable, and operationally safe

Statistical detectors are designed to **complement**, not replace, rule-based detection.

---

### 3️⃣ Zero Vendor Lock-in

* Built on Python’s standard `logging` module
* No external services, APIs, or agents
* Works anywhere Python runs

---

## Installation

Using `pip`:

```bash
pip install logsignal
```

Using `uv`:

```bash
uv add logsignal
```

---

## Quick Start

### 1️⃣ Create a LogWatcher

```python
from logsignal import LogWatcher

watcher = LogWatcher(
    rules=[
        "ERROR",
        "CRITICAL",
    ]
)
```

---

### 2️⃣ Process Logs

```python
watcher.process("ERROR database connection failed")
```

Example output:

```text
[LogSignal] RuleTriggered: keyword='ERROR'
```

---

### 3️⃣ Spike Detection Example

```python
from logsignal import LogWatcher, Rule
import time

watcher = LogWatcher(
    rules=[
        Rule.spike(threshold=3, window=5)
    ]
)

for _ in range(5):
    watcher.process("ERROR something bad happened")
    time.sleep(0.5)
```

---

## Integration with `logging`

LogSignal integrates directly with Python’s standard logging system.

```python
import logging
from logsignal import LogSignalHandler

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

handler = LogSignalHandler()
logger.addHandler(handler)

logger.error("DB connection timeout")
```

---

## Entropy-Based Detection (Experimental)

LogSignal provides an **experimental entropy-based detector** that identifies
**sudden increases in log randomness**, which may indicate suspicious or automated activity.

Typical signals include:

* Injection-like payloads
* Obfuscated requests
* Unexpected input patterns

Entropy-based detection does **not rely on signatures or predefined rules**.

---

### Example

```python
import random
from logsignal import LogWatcher
from logsignal.stats.entropy import EntropySpike

watcher = LogWatcher()
watcher.add_stat(EntropySpike(window=10, threshold=2.5))

normal_logs = [
    "INFO ok",
    "INFO request processed",
    "INFO heartbeat",
    "INFO user active",
]

for _ in range(30):
    watcher.process({"message": random.choice(normal_logs)})

attack = "GET /login.php?id=1' OR '1'='1' UNION SELECT password FROM users"

for _ in range(5):
    watcher.process({"message": attack})
```

Example output:

```text
[LogSignal] entropy_spike detected (z=2.93)
```

---

### Notes

* Entropy detectors require a **warm-up period** to learn a baseline
* Detection is **relative to historical behavior**, not absolute thresholds
* Best used alongside rule-based detectors

---

### Status

* Experimental API
* Enabled via `add_stat()`
* No external dependencies

---

### Design Philosophy

* No regex
* No signatures
* No ML models
* Fully explainable
* Lightweight enough for personal projects

> Entropy detection in LogSignal is intentionally simple, transparent,
> and designed to complement rule-based alerts—not replace them.

---

## Status

* Experimental (API may change)
* Enabled via `add_stat()`
* No external dependencies

---

## Design Philosophy

* **Rule-first**
* **Statistics second**
* **ML optional**
* **Explainable over fancy**
* **Personal-project friendly**

LogSignal favors clarity, predictability, and operational safety over black-box intelligence.

---

## Statistical Detectors Are Relative

Statistical detectors operate on **deviation from a learned baseline**.

They assume:

* Historical data represents normal behavior
* Anomalies are statistically significant deviations from that behavior

They are **not** intended for absolute thresholding.

For immediate and deterministic alerts, use **rule-based detectors** alongside
statistical ones.

---

## Roadmap

### v0.1.x

* [x] Keyword rules
* [x] Spike rules
* [x] Standard logging handler
* [ ] Callback / hook system

### v0.2.x

* [ ] Statistical baseline learning improvements
* [ ] Z-score / EWMA detectors
* [ ] JSON / structured log support

### v0.3.x

* [ ] ML-based anomaly plugins
* [ ] FastAPI middleware
* [ ] Prometheus exporter

---

## Use Cases

* Security monitoring for personal projects
* FastAPI / Flask backend monitoring
* Batch job failure detection
* CI log anomaly detection
* Lightweight security signal triggering

---

## License

MIT License

---

## Contributing & Support

* GitHub Issues
* Pull requests are welcome

---

