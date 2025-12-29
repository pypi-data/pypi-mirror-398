import json
import logging
import os
from pathlib import Path

def _resolve_config_path():
    # 1. Environment variable override
    env_path = os.getenv("SAP_LOG_FORWARDER_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    # 2. Existing local config.json (backward compatibility)
    local = Path("config.json")
    if local.exists():
        return local

    # 3. Default in user home
    home_path = Path.home() / ".sapecslogforwarder"
    try:
        home_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return home_path / "config.json"


CONFIG_FILE = _resolve_config_path()

def validate_input(inp):
    provider = inp.get("provider")
    required = {
        "gcp": ["subscription"],
        "aws": ["queue","region","bucket"],
        "azure": ["queue","storageAccount"]
    }.get(provider, [])
    missing = [r for r in required if not inp.get(r)]
    if missing:
        raise ValueError(f"Input '{inp.get('name')}' missing required fields: {missing}")
    if not isinstance(inp.get("outputs", []), list):
        raise ValueError(f"Input '{inp.get('name')}' outputs must be a list.")
    auth = inp.get("authentication")
    if not auth:
        return  # auth optional

    if not isinstance(auth, dict):
        raise ValueError(f"Input '{inp.get('name')}' authentication must be an object.")

    if provider == "aws":
        static_ok = ("accessKeyId" in auth and "secretAccessKey" in auth)
        dynamic_ok = (all(k in auth for k in ("clientId","clientSecret","loginUrl")) and ("awsCredsUrl" in auth or "credsUrl" in auth))
        if not (static_ok or dynamic_ok):
            raise ValueError(
                f"Input '{inp.get('name')}' AWS auth must include either static keys "
                "(accessKeyId, secretAccessKey) or dynamic fields "
                "(clientId, clientSecret, loginUrl, awsCredsUrl)."
            )
    elif provider == "azure":
        static_ok = ("sasToken" in auth)
        dynamic_ok = (all(k in auth for k in ("clientId","clientSecret","loginUrl","credsUrl")))
        if not (static_ok or dynamic_ok):
            raise ValueError(
                f"Input '{inp.get('name')}' Azure auth must include either 'sasToken' "
                "or dynamic fields (clientId, clientSecret, loginUrl, credsUrl)."
            )
    elif provider == "gcp":
        if "serviceAccountJson" not in auth:
            raise ValueError(f"Input '{inp.get('name')}' GCP auth missing 'serviceAccountJson'.")


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file missing: {CONFIG_FILE.resolve()}")
    with CONFIG_FILE.open() as f:
        data = json.load(f)
    if "inputs" not in data or not isinstance(data["inputs"], list):
        raise ValueError("Config must contain 'inputs' list.")
    for inp in data["inputs"]:
        validate_input(inp)
    return data

def save_config(cfg):
    # Ensure parent exists
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    with CONFIG_FILE.open("w") as f:
        json.dump(cfg, f, indent=2)


def get_log_level(cfg):
    level = cfg.get("logLevel", "INFO").upper()
    return getattr(logging, level, logging.INFO)

def get_log_file(cfg):
    """Return log file path if configured, else None."""
    path = cfg.get("logFile")
    if not path:
        return None
    return str(Path(path).expanduser())