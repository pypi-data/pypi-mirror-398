import logging
import threading
import time

from sap_ecs_log_forwarder.json_logging import setup_structured_logging
from sap_ecs_log_forwarder.metrics import format_metrics, reset_metrics
from .config import CONFIG_FILE, get_log_file, load_config, get_log_level
from .aws import AWSRunner
from .gcp import GCPRunner
from .azure import AzureRunner

PROVIDERS = {
    "gcp": GCPRunner,
    "aws": AWSRunner,
    "azure": AzureRunner,
}

def _metrics_logger():
    while True:
        time.sleep(30)
        logging.info("metrics snapshot\n" + format_metrics())
        ## Verify if is the beginning of the day (00:00 UTC)
        now = time.gmtime()
        if now.tm_hour == 0 and (now.tm_min == 0 or now.tm_min == 1):
            logging.info("Daily metrics snapshot\n" + format_metrics())
            reset_metrics()

def run_all():
    cfg = load_config()
    logging.info(f"Using config file: {CONFIG_FILE.resolve()}")
    setup_structured_logging(get_log_level(cfg), get_log_file(cfg))
    inputs = cfg.get("inputs", [])
    if not inputs:
        logging.warning("No inputs configured.")
        return
    m_thread = threading.Thread(target=_metrics_logger, daemon=True)
    m_thread.start()
    threads = []
    for inp in inputs:
        p = inp.get("provider")
        cls = PROVIDERS.get(p)
        if not cls:
            logging.error(f"Unknown provider: {p}")
            continue
        runner = cls(inp)
        t = threading.Thread(target=runner.start, name=f"{p}-{inp.get('name','input')}", daemon=True)
        t.start()
        threads.append(t)
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logging.info("Shutdown requested.")

if __name__ == "__main__":
    run_all()