import threading
from collections import Counter
import time

class _Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = Counter()
        self._start = time.time()

    def inc(self, name, value=1):
        with self._lock:
            self._counters[name] += value

    def snapshot(self):
        with self._lock:
            return dict(self._counters), self._start
        
    def reset(self):
        with self._lock:
            self._counters = Counter()
            self._start = time.time()

metrics = _Metrics()

def inc(name, value=1):
    metrics.inc(name, value)

def format_metrics():
    counters, start = metrics.snapshot()
    lines = [f"# start_time_seconds {start:.0f}"]
    for k,v in counters.items():
        lines.append(f"{k} {v}")
    return "\n".join(lines)

def reset_metrics():
    metrics.reset()