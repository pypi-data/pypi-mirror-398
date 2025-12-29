import json
import logging
import time
from logging import StreamHandler, FileHandler

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "thread": record.threadName,
            "pid": record.process,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "stack": self.formatException(record.exc_info) if record.exc_info else None,
        }
        if hasattr(record, "source"):
            data["source"] = record.source
        if record.__dict__.get("destination"):
            data["destination"] = record.__dict__["destination"]
        return json.dumps(data)

def setup_structured_logging(level, log_file: str):
    formatter = JsonFormatter()
    root = logging.getLogger()
    root.handlers.clear()

    # Always keep console output
    sh = StreamHandler()
    sh.setFormatter(formatter)
    root.addHandler(sh)

    # Optional file output
    if log_file:
        fh = FileHandler(log_file)
        fh.setFormatter(formatter)
        root.addHandler(fh)

    root.setLevel(level)