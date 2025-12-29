import os
from cryptography.fernet import Fernet

_ENV_KEY = "FORWARDER_ENCRYPTION_KEY"

def decrypt_auth_dict(auth):
    if not isinstance(auth, dict):
        return {}
    dec = {}
    for k, v in auth.items():
        if k == "encrypted":
            continue
        # URLs are not encrypted; keep as-is
        if k in ("loginUrl","credsUrl","awsCredsUrl"):
            dec[k] = v
            continue
        dec[k] = decrypt_value_if_needed(v)
    return dec

def get_active_key():
    key = os.getenv(_ENV_KEY)
    return key

def generate_key():
    return Fernet.generate_key().decode()

def encrypt_value(value, key):
    if not value:
        return value
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.encrypt(value.encode()).decode()

def decrypt_value_if_needed(value):
    if not value or not value.startswith("enc:"):
        return value
    key = get_active_key()
    if not key:
        return value  # Cannot decrypt without key
    raw = value[4:]
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.decrypt(raw.encode()).decode()