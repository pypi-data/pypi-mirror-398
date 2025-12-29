import asyncio
from http.cookies import Morsel
import json
import logging
import re
import time
import threading
import aiohttp
import boto3

from sap_ecs_log_forwarder import metrics
from sap_ecs_log_forwarder.crypto import decrypt_auth_dict
from sap_ecs_log_forwarder.processor import emit
from sap_ecs_log_forwarder.utils import compile_filters, decode_bytes, is_relevant, split_lines

class AWSRunner:
    def __init__(self, cfg):
        self.cfg = cfg
        self._stop = threading.Event()
        self.inc, self.exc = compile_filters(cfg.get("includeFilter", []), cfg.get("excludeFilter", []))
        self.max_retries = cfg.get("maxRetries", 5)
        lvl = getattr(logging, str(self.cfg.get("logLevel","INFO")).upper(), logging.INFO)
        self.log = logging.getLogger(f"input.{self.cfg.get('name','aws')}")
        self.log.setLevel(lvl)
        # rotating session credentials
        self._aws_kwargs = {}
        self._aws_expiry_ts = 0
        self._gen = 0              # increments when creds refreshed
        self._active_gen = -1      # last gen applied to clients
        self.sqs = None
        self.s3 = None
    
    def _creds_valid(self):
        return self._aws_kwargs and (self._aws_expiry_ts - time.time() > 60)
    
    async def _refresh_temp_creds(self):
        while not self._stop.is_set():
            try:
                self.log.info(f"[{self.cfg['name']}] Refreshing AWS Creds...")
                await self._ensure_credentials()
                self._gen += 1
                now = time.time()
                if self._aws_expiry_ts > now:
                    sleep_for = max(60, min(30*60, int(self._aws_expiry_ts - now - 60)))
                else:
                    sleep_for = 30 * 60
            except Exception as e:
                self.log.error(f"[{self.cfg['name']}] AWS Creds refresh error: {e}")
                sleep_for = 60
            self.log.info(f"[{self.cfg['name']}] Next AWS Creds refresh in {sleep_for} seconds.")
            await asyncio.sleep(sleep_for)

    async def _ensure_credentials(self):
        auth = decrypt_auth_dict(self.cfg.get("authentication", {}))
        client_id = auth.get("clientId")
        client_secret = auth.get("clientSecret")
        login_url = auth.get("loginUrl")
        aws_creds_url = auth.get("awsCredsUrl") or auth.get("credsUrl")  # allow shared key name
        bucket = self.cfg.get("bucket")
        # Dynamic mode
        if client_id and client_secret and login_url and aws_creds_url and bucket:
            async with aiohttp.ClientSession() as session:
                # Login to get cookie
                data = {"client_id": client_id, "client_secret": client_secret}
                async with session.post(login_url, data=data, headers={"content-type":"application/x-www-form-urlencoded"}) as r:
                    if r.status != 200:
                        raise RuntimeError(f"Login failed: HTTP {r.status}")
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
                # Fetch temporary AWS creds
                headers = {"Cookie": f"session-id-raven={sid.value}"}
                params = {"bucket": bucket}
                async with session.get(aws_creds_url, params=params, headers=headers) as r2:
                    if r2.status != 200:
                        raise RuntimeError(f"Creds fetch failed: HTTP {r2.status}")
                    payload = await r2.json()
            data = payload.get("data", {})
            akid = data.get("AccessKeyId")
            secret = data.get("SecretAccessKey")
            token = data.get("SessionToken")
            region = data.get("Region") or self.cfg.get("region")
            expiry = data.get("Expiration")
            if not (akid and secret and token):
                raise RuntimeError("Temporary AWS credentials missing required fields")
            # parse expiry
            try:
                from datetime import datetime, timezone
                self._aws_expiry_ts = datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() if expiry else time.time() + 30*60
            except Exception:
                self._aws_expiry_ts = time.time() + 30*60
            self._aws_kwargs = {
                "aws_access_key_id": akid,
                "aws_secret_access_key": secret,
                "aws_session_token": token,
            }
            self._dynamic_region = region
            self.log.info(f"[{self.cfg['name']}] AWS temporary creds refreshed; expires at {expiry}")
            return
        # Static mode
        static = decrypt_auth_dict(self.cfg.get("authentication", {}))
        if static.get("accessKeyId") and static.get("secretAccessKey"):
            self._aws_kwargs = {
                "aws_access_key_id": static["accessKeyId"],
                "aws_secret_access_key": static["secretAccessKey"],
            }
            self._dynamic_region = None

    def start(self):
        asyncio.run(self._run())

    async def _run(self):
        await self._ensure_credentials()
        auth = decrypt_auth_dict(self.cfg.get("authentication", {}))
        dynamic = all(auth.get(k) for k in ("clientId","clientSecret","loginUrl")) and (auth.get("awsCredsUrl") or auth.get("credsUrl"))
        refresh_task = asyncio.create_task(self._refresh_temp_creds()) if dynamic else None    

        queue_url = self.cfg["queue"]
        
        def build_clients():
            region = self._dynamic_region if self._dynamic_region else self.cfg["region"]
            aws_kwargs = self._aws_kwargs or {}
            self.sqs = boto3.client("sqs", region_name=region, **aws_kwargs)
            self.s3 = boto3.client("s3", region_name=region, **aws_kwargs)
            self._active_gen = self._gen
            self.log.info(f"[{self.cfg['name']}] AWS clients built (gen {self._active_gen}).")
        
        build_clients()
        self.log.info(f"[{self.cfg['name']}] Polling SQS {queue_url}")
        while not self._stop.is_set():
            try:
                # Rebuild clients when creds rotated or expiring soon
                if self._active_gen != self._gen or (self._aws_expiry_ts - time.time()) <= 60:
                    self.log.info(f"[{self.cfg['name']}] Rebuilding AWS clients due to creds rotation/expiry.")
                    self.log.info(f"[{self.cfg['name']}] Refreshing AWS Creds...")
                    await self._ensure_credentials()
                    self._gen += 1
                    build_clients()

                resp = self.sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=15,
                    VisibilityTimeout=45,
                    AttributeNames=["ApproximateReceiveCount"],
                )
                for m in resp.get("Messages", []):
                    self._process(self.sqs, self.s3, m)
            except Exception as e:
                self.log.error(f"AWS polling error: {e}")
                await asyncio.sleep(10)
        if refresh_task:
            refresh_task.cancel()

    def _process(self, sqs, s3, message):
        handle = message.get("ReceiptHandle")
        body = message.get("Body","")
        try:
            payload = json.loads(body)
        except Exception:
            self.log.error("AWS message is not valid JSON, deleting.")
            sqs.delete_message(QueueUrl=self.cfg["queue"], ReceiptHandle=handle)
            return
        for record in payload.get("Records", []):
            event = record.get("eventName","")
            bname = record.get("s3",{}).get("bucket",{}).get("name","")
            key = record.get("s3",{}).get("object",{}).get("key","")
            if event != "ObjectCreated:Put" or bname != self.cfg.get("bucket") or not is_relevant(key, self.inc, self.exc):
                self.log.debug(f"[{self.cfg['name']}] Ignoring S3 object s3://{bname}/{key} (event: {event})")
                continue
            retry = int(record.get("retry_count",0))
            if retry >= self.max_retries:
                self.log.error(f"[{self.cfg['name']}] Max retries reached for s3://{bname}/{key}, deleting message.")
                continue
            try:
                self.log.debug(f"[{self.cfg['name']}] Processing S3 object s3://{bname}/{key}")
                obj = s3.get_object(Bucket=bname, Key=key)
                raw = obj["Body"].read()
                text = decode_bytes(raw)
                lines = split_lines(text)
                emit(lines, key, self.cfg.get("outputs", []))
                self.log.debug(f"[{self.cfg['name']}] Processed S3 object s3://{bname}/{key}")
                sqs.delete_message(QueueUrl=self.cfg["queue"], ReceiptHandle=handle)
                metrics.inc("aws_messages_processed")
                return
            except Exception as e:
                self.log.error(f"AWS processing failed; requeued: {e}")
                metrics.inc("aws_retry")
                retry += 1
                record["retry_count"] = retry
                payload["Records"] = [record]
                sqs.send_message(QueueUrl=self.cfg["queue"], MessageBody=json.dumps(payload))
                sqs.delete_message(QueueUrl=self.cfg["queue"], ReceiptHandle=handle)
                return
        sqs.delete_message(QueueUrl=self.cfg["queue"], ReceiptHandle=handle)

    def stop(self):
        self._stop.set()