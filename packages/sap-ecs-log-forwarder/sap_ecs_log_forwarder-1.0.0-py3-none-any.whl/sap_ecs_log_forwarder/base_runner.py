import threading
import logging
import time
import signal

class BaseRunner:
    def __init__(self, cfg):
        self.cfg = cfg
        self._stop = threading.Event()

    def start(self):
        raise NotImplementedError

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.is_set()

def install_signal_handler(runners):
    def handler(sig, frame):
        logging.info(f"Shutdown signal ({sig}) received.")
        for r in runners:
            r.stop()
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)