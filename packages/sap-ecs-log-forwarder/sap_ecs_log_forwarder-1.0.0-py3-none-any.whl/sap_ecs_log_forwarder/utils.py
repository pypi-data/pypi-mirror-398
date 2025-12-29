import gzip
import logging
import re

def compile_filters(include, exclude):
    return [re.compile(p) for p in include], [re.compile(p) for p in exclude]

def is_relevant(name: str, include_regex, exclude_regex):
    lower = name.lower()
    if "logserv" not in lower:
        return False
    if any(r.search(lower) for r in exclude_regex):
        return False
    if include_regex and not any(r.search(lower) for r in include_regex):
        return False
    return True

def decode_bytes(raw: bytes):
    try:
        return gzip.decompress(raw).decode("utf-8")
    except Exception:
        try:
            return raw.decode("utf-8", errors="replace")
        except Exception as e:
            logging.error(f"Failed to decode bytes: {e}")
            return ""
def split_lines(text: str):
    return [l for l in text.splitlines() if l.strip()]