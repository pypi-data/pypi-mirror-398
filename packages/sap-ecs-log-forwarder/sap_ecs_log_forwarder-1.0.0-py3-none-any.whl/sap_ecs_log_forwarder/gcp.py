import json
import time
import logging
from functools import partial
from google.cloud import pubsub_v1
from google.api_core.exceptions import PermissionDenied, NotFound
from google.oauth2 import service_account

from sap_ecs_log_forwarder import metrics
from sap_ecs_log_forwarder.crypto import decrypt_auth_dict
from sap_ecs_log_forwarder.processor import emit
from sap_ecs_log_forwarder.utils import compile_filters, decode_bytes, is_relevant, split_lines

class GCPRunner:
    def __init__(self, cfg):
        self.cfg = cfg
        self._stop = False
        inc, exc = compile_filters(cfg.get("includeFilter", []), cfg.get("excludeFilter", []))
        self.include = inc
        self.exclude = exc
        self.max_retries = cfg.get("maxRetries", 5)
        self.retry_delay = cfg.get("retryDelay", 10)
        lvl = getattr(logging, str(self.cfg.get("logLevel","INFO")).upper(), logging.INFO)
        self.log = logging.getLogger(f"input.{self.cfg.get('name','aws')}")
        self.log.setLevel(lvl)

    def _valid_sub(self, path):
        try:
            c = pubsub_v1.SubscriberClient(credentials=self._storage_credentials) if self._storage_credentials else pubsub_v1.SubscriberClient()
            c.get_subscription(request={"subscription": path})
            return True
        except PermissionDenied:
            return True
        except NotFound:
            self.log.error(f"Subscription not found: {path}")
            return False
        except Exception as e:
            self.log.error(f"Subscription check failed: {e}")
            return False

    def start(self):
        credentials = None
        auth = decrypt_auth_dict(self.cfg.get("authentication", {}))
        sa_json = auth.get("serviceAccountJson")
        if sa_json:
            try:
                info = json.loads(sa_json)
                credentials = service_account.Credentials.from_service_account_info(info)
            except Exception as e:
                self.log.error(f"Failed to parse GCP service account JSON: {e}")
        client = pubsub_v1.SubscriberClient(credentials=credentials) if credentials else pubsub_v1.SubscriberClient()
        self._storage_credentials = credentials
        path = self.cfg.get("subscription")
        if not path or not self._valid_sub(path):
            return
        cb = partial(self._callback, credentials=credentials)
        future = client.subscribe(path, callback=cb)
        self.log.info(f"[{self.cfg['name']}] Listening on {path}")
        try:
            future.result()
        except Exception as e:
            self.log.error(f"GCP runner stopped: {e}")
            future.cancel()

    def _callback(self, message, credentials=None):
        if self._stop:
            message.nack()
            return
        try:
            payload = json.loads(message.data.decode("utf-8"))
        except Exception as e:
            self.log.error(f"JSON decode failure: {e}")
            message.ack()
            return
        bucket = payload.get("bucket")
        name = payload.get("name","")
        event_type = message.attributes.get("eventType")
        if event_type != "OBJECT_FINALIZE" or not is_relevant(name, self.include, self.exclude):
            self.log.debug(f"[{self.cfg['name']}] Ignoring GCP object event: {name} ({event_type})")
            message.ack()
            return
        retries = 0
        while retries < self.max_retries:
            try:
                self.log.debug(f"[{self.cfg['name']}] Processing GCP object gs://{bucket}/{name}")
                from google.cloud import storage
                sc = storage.Client(credentials=credentials) if credentials else storage.Client()
                blob = sc.bucket(bucket).blob(name)
                raw = blob.download_as_bytes()
                text = decode_bytes(raw)
                lines = split_lines(text)
                emit(lines, name, self.cfg.get("outputs", []))
                self.log.debug(f"[{self.cfg['name']}] Processed GCP object gs://{bucket}/{name}")
                message.ack()
                metrics.inc("gcp_messages_processed")
                return
            except Exception as e:
                retries += 1
                metrics.inc("gcp_retry")
                self.log.error(f"GCP process error attempt {retries}: {e}")
                time.sleep(min(self.retry_delay * (2 ** (retries-1)), 120))
        message.ack()

    def stop(self):
        self._stop = True