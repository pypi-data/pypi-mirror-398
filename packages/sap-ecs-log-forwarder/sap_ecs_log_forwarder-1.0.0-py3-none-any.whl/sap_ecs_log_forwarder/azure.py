import asyncio
import base64
from http.cookies import Morsel
import json
import logging
import re
from time import time
from urllib.parse import urlparse
import aiohttp
from azure.storage.queue.aio import QueueServiceClient
from azure.storage.blob import BlobClient, BlobServiceClient
from sap_ecs_log_forwarder import metrics
from sap_ecs_log_forwarder.crypto import decrypt_auth_dict
from sap_ecs_log_forwarder.processor import emit
from sap_ecs_log_forwarder.utils import compile_filters, decode_bytes, is_relevant, split_lines

refresh_token_minutes = 30
refresh_token_fallback_seconds = 60

class AzureRunner:
    def __init__(self, cfg):
        self.cfg = cfg
        self.inc, self.exc = compile_filters(cfg.get("includeFilter", []), cfg.get("excludeFilter", []))
        self.max_retries = cfg.get("maxRetries", 5)
        self.retry_delay = cfg.get("retryDelay", 10)
        self._stop = False
        self._blob_auth = None  # cached auth dict
        self._sas_token = None  # rotating SAS token
        self._sas_expiry_ts = 0  # initialize expiry
        lvl = getattr(logging, str(self.cfg.get("logLevel","INFO")).upper(), logging.INFO)
        self.log = logging.getLogger(f"input.{self.cfg.get('name','aws')}")
        self.log.setLevel(lvl)
        self._sas_generation = 0
        self._active_generation = 0
        self.qsc = None
        self._queue_client = None
    
    async def _refresh_sas_loop(self):
        """
        If Azure authentication is configured for dynamic SAS, renew every 15 minutes (or before expiration).
        """
        while not self._stop:
            sleep_for = refresh_token_minutes * 60
            try:
                self.log.debug(f"[{self.cfg['name']}] Refreshing SAS token...")
                await self._ensure_sas_token()
                self._sas_generation += 1
                now = time()
                if self._sas_expiry_ts > now:
                    sleep_for = max(60, min(refresh_token_minutes*60, int(self._sas_expiry_ts - now - 60)))
                self.log.debug(f"[{self.cfg['name']}] SAS refreshed; next in ~{sleep_for}s (gen {self._sas_generation}).")
            except Exception as e:
                self.log.error(f"[{self.cfg['name']}] SAS refresh error: {e}")
                sleep_for = refresh_token_fallback_seconds
            self.log.debug(f"[{self.cfg['name']}] Next SAS refresh in {sleep_for} seconds.")
            await asyncio.sleep(sleep_for)

    async def _ensure_sas_token(self):
        """
        Populate or refresh a temporary SAS token via backend if dynamic auth configured.
        Supports:
          - Static: sasToken in cfg.authentication
          - Dynamic: clientId/clientSecret + URLs (loginUrl, credsUrl) returning SAS and Expiration
        """
        auth = decrypt_auth_dict(self.cfg.get("authentication", {}))
        # Dynamic mode detection
        client_id = auth.get("clientId")
        client_secret = auth.get("clientSecret")
        login_url = auth.get("loginUrl")
        creds_url = auth.get("credsUrl")
        storage_account_name = self.cfg.get("storageAccount")
        if client_id and client_secret and login_url and creds_url and storage_account_name:
            async with aiohttp.ClientSession() as session:
                # Login to get session cookie
                data = {"client_id": client_id, "client_secret": client_secret}
                async with session.post(login_url, data=data, headers={"content-type":"application/x-www-form-urlencoded"}) as r:
                    if r.status != 200:
                        raise RuntimeError(f"Login failed: HTTP {r.status}")
                    # Extract cookie session-id-raven
                    cookies = session.cookie_jar.filter_cookies(login_url)
                    sid = cookies.get("session-id-raven")
                    if not sid:
                        if login_url.startswith("http://localhost"):
                            cookieHeaders = r.headers.getall("Set-Cookie", [])
                            for ch in cookieHeaders:
                                m = re.search(r"session-id-raven=([^;]+);", ch)
                                if m:
                                    sid = Morsel[str]()
                                    sid.set("session-id-raven", m.group(1), m.group(1))
                                    break
                        if not sid:
                            raise RuntimeError("Login OK but session-id-raven cookie missing")
                # Request temporary credentials
                params = {"storage-account-name": storage_account_name}
                headers = {"Content-Type":"application/json","Cookie":f"session-id-raven={sid.value}"}
                async with session.get(creds_url, params=params, headers=headers) as r2:
                    if r2.status != 200:
                        raise RuntimeError(f"Creds fetch failed: HTTP {r2.status}")
                    payload = await r2.json()
                data = payload.get("data", {})
                sas_token = data.get("SASToken")
                expiry = data.get("Expiration")
                if not sas_token:
                    raise RuntimeError("SASToken missing in credentials response")
                # Parse expiry RFC3339 to epoch
                try:
                    from datetime import datetime, timezone
                    self._sas_expiry_ts = datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() if expiry else time.time() + refresh_token_minutes*60
                except Exception:
                    self._sas_expiry_ts = time.time() + 15*60
                self._sas_token = sas_token
                self._blob_auth = {"sasToken": sas_token}
                self.log.debug(f"[{self.cfg['name']}] SAS token refreshed; expires at {expiry}")
            return

        # Static mode fallback
        sas_token = auth.get("sasToken")
        if sas_token:
            self._sas_token = sas_token
            self._blob_auth = auth
            
    def start(self):
        asyncio.run(self._run())

    async def _run(self):
        account = self.cfg.get("storageAccount")
        queue_name = self.cfg["queue"]
        auth = decrypt_auth_dict(self.cfg.get("authentication", {}))
        await self._ensure_sas_token()
        dynamic = all(auth.get(k) for k in ("clientId","clientSecret","loginUrl","credsUrl"))
        refresh_task = asyncio.create_task(self._refresh_sas_loop()) if dynamic else None
        
        async def build_clients():
            # close previous context if exists
            if self.qsc:
                try:
                    await self.qsc.close()
                except Exception:
                    pass
            if "AccountKey=" in (account or "") or "SharedAccessSignature=" in (account or ""):
                self.qsc = QueueServiceClient.from_connection_string(account)
            else:
                self.qsc = QueueServiceClient(account_url=f"https://{account}.queue.core.windows.net", credential=self._sas_token)
            self._queue_client = self.qsc.get_queue_client(queue_name)
            self._active_generation = self._sas_generation
            self.log.debug(f"[{self.cfg['name']}] Queue client (gen {self._active_generation}) ready.")

        await build_clients()
        self.log.info(f"[{self.cfg['name']}] Listening Azure queue {queue_name}")
        while not self._stop:
            try:
                # Rebuild if SAS rotated or expiring soon
                if self._active_generation != self._sas_generation or (self._sas_expiry_ts - time()) <= 90:
                    self.log.debug(f"[{self.cfg['name']}] Rebuilding clients due to SAS rotation/expiry.")
                    await build_clients()
                async with self.qsc:  # lightweight context for this cycle
                    async for msg in self._queue_client.receive_messages(messages_per_page=10, visibility_timeout=60):
                        await self._process(self._queue_client, msg)
                await asyncio.sleep(self.retry_delay)
            except Exception as e:
                self.log.error(f"Azure loop error: {e}")
                if getattr(e, "status_code",0) == 403:
                    self.log.debug(f"[{self.cfg['name']}] Rebuilding clients due to 403 error.")
                    self._active_generation = -1  # force rebuild
                await asyncio.sleep(15)
        if refresh_task:
            refresh_task.cancel()

    async def _process(self, qc, msg):
        try:
            decoded = base64.b64decode(msg.content).decode("utf-8")
            payload = json.loads(decoded)
        except Exception:
            await qc.delete_message(msg)
            return
        event_type = payload.get("eventType","")
        subject = payload.get("subject","")
        if event_type != "Microsoft.Storage.BlobCreated" or not is_relevant(subject, self.inc, self.exc):
            self.log.debug(f"[{self.cfg['name']}] Ignoring Azure blob event: {subject} ({event_type})")
            await qc.delete_message(msg)
            return
        blob_url = payload.get("data",{}).get("url","")
        retry = int(payload.get("retry_count",0))
        if retry >= self.max_retries or not blob_url:
            self.log.error(f"[{self.cfg['name']}] Max retries reached or invalid blob URL for {subject}, deleting message.")
            await qc.delete_message(msg)
            return

        try:
            self.log.debug(f"[{self.cfg['name']}] Processing Azure blob: {blob_url}")
            content_bytes = self._download_blob(blob_url)
            text = decode_bytes(content_bytes)
            lines = split_lines(text)
            emit(lines, subject, self.cfg.get("outputs", []))
            await qc.delete_message(msg)
            self.log.debug(f"[{self.cfg['name']}] Processed Azure blob: {blob_url}")
            metrics.inc("azure_messages_processed")
        except Exception as e:
            retry += 1
            self.log.error(f"Azure processing failed (retry {retry}): {e}")
            metrics.inc("azure_retry")
            payload["retry_count"] = retry
            updated = base64.b64encode(json.dumps(payload).encode()).decode()
            try:
                await qc.update_message(msg, content=updated, visibility_timeout=60)
            except Exception:
                await qc.delete_message(msg)
            
    def _download_blob(self, blob_url):
        """
        Download blob content using SAS token or connection string credentials.
        Falls back to anonymous only if no credentials present (will fail for private accounts).
        """
        auth = self._blob_auth or {}
        sas_token = auth.get("sasToken")
        try:
            if sas_token:
                # blob_url may lack SAS; append if not present
                if "?" not in blob_url:
                    blob_client = BlobClient.from_blob_url(blob_url + "?" + sas_token)
                else:
                    blob_client = BlobClient.from_blob_url(blob_url, credential=sas_token)
            elif "AccountKey=" in (self.cfg.get("storageAccount") or "") or "SharedAccessSignature=" in (self.cfg.get("storageAccount") or ""):
                # Connection string case; create service client and get blob client
                service = BlobServiceClient.from_connection_string(self.cfg["storageAccount"])
                parsed = urlparse(blob_url)
                # path format /container/blobpath
                parts = parsed.path.lstrip("/").split("/", 1)
                container = parts[0]
                blob_name = parts[1] if len(parts) > 1 else ""
                blob_client = service.get_blob_client(container=container, blob=blob_name)
            else:
                # Anonymous attempt (likely to fail on private account)
                blob_client = BlobClient.from_blob_url(blob_url)
            return blob_client.download_blob().readall()
        except Exception as e:
            raise RuntimeError(f"Blob download failed: {e}")

    def stop(self):
        self._stop = True