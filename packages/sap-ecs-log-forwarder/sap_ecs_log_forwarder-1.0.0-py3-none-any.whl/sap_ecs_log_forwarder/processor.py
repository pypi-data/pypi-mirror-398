import os
import logging
import requests
import gzip

from sap_ecs_log_forwarder import metrics
from sap_ecs_log_forwarder.crypto import decrypt_value_if_needed
from sap_ecs_log_forwarder.utils import compile_filters, is_relevant

def write_file(lines, source_name, cfg):
    dest_dir = cfg.get("destination")
    if not dest_dir:
        logging.error("File output missing 'destination'.")
        return
    source_name = source_name.lstrip("/")
    path = os.path.join(dest_dir, source_name)
    compress = cfg.get("compress", False)
    if compress:
        out_path = path if path.endswith(".gz") else path + ".gz"
        opener = lambda p, m: gzip.open(p, m)
        mode = "at"
    else:
        out_path = path[:-3] if path.endswith(".gz") else path
        opener = lambda p, m: open(p, m)
        mode = "a"
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with opener(out_path, mode) as f:
            for line in lines:
                f.write(line + "\n")
            metrics.inc("files_forward_success")
        logging.debug(f"Wrote logs to {out_path}")
    except Exception as e:
        logging.error(f"Write file error {out_path}: {e}")
        metrics.inc("files_forward_error")

def send_http(lines, cfg):
    dest = cfg.get("destination")
    if not dest:
        logging.error("HTTP output missing 'destination'.", extra={"outputType":"http"})
        return
    tls = cfg.get("tls", {})
    auth_cfg = cfg.get("authorization", {})
    # Decrypt secrets if encrypted
    if auth_cfg.get("encrypted"):
        token = auth_cfg.get("token")
        api_key = auth_cfg.get("apiKey")
        password = auth_cfg.get("password")
        auth_cfg["token"] = decrypt_value_if_needed(token)
        auth_cfg["apiKey"] = decrypt_value_if_needed(api_key)
        auth_cfg["password"] = decrypt_value_if_needed(password)
        auth_cfg["encrypted"] = False
    cert = None
    if tls.get("pathToClientCert") and tls.get("pathToClientKey"):
        cert = (tls["pathToClientCert"], tls["pathToClientKey"])
    verify = not tls.get("insecureSkipVerify", False)
    if verify and tls.get("pathToCACert"):
        verify = tls["pathToCACert"]
    headers = {"Content-Type": "application/json"}
    auth = None
    t = (auth_cfg.get("type") or "").lower()
    if t == "bearer":
        headers["Authorization"] = f"Bearer {auth_cfg.get('token','')}"
    elif t == "api-key":
        headers["X-API-Key"] = auth_cfg.get("apiKey","")
    elif t == "basic":
        auth = (auth_cfg.get("user",""), auth_cfg.get("password",""))
    for line in lines:
        try:
            resp = requests.post(dest, data=line, headers=headers, cert=cert, auth=auth, verify=verify, timeout=10)
            resp.raise_for_status()
            metrics.inc("http_forward_success")
        except Exception as e:
            metrics.inc("http_forward_error")
            logging.error(f"HTTP send failed ({dest}): {e}", extra={"outputType":"http","destination":dest})


def send_console(lines, _cfg):
    for l in lines:
        print(l)

OUTPUT_HANDLERS = {
    "files": write_file,
    "http": send_http,
    "console": send_console,
}

def emit(lines, source_name, outputs):
    for out in outputs:
        handler = OUTPUT_HANDLERS.get(out.get("type"))
        if not handler:
            logging.warning(f"Unknown output type {out.get('type')}", extra={"source":source_name})
            continue
        # Apply output-level filters if provided
        inc_patterns = out.get("includeFilter", [])
        exc_patterns = out.get("excludeFilter", [])
        if inc_patterns or exc_patterns:
            inc, exc = compile_filters(inc_patterns, exc_patterns)
            if not is_relevant(source_name, inc, exc):
                logging.debug(f"Skipping output '{out.get('type')}' for {source_name} due to output-level filters", extra={"source":source_name})
                continue

        if out.get("type") == "files":
            handler(lines, source_name, out)
        else:
            handler(lines, out)
        metrics.inc("output_invocations")