import hashlib
from typing import Any


def hash_string(s: Any) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()


def hash_admin_note(s: Any) -> str:
    if s is None:
        return "<no admin note>"
    return hash_string(s)


def wrap_alert_admin_fingerprint(alert_admin: bool) -> str:
    return f"Alert admin={alert_admin}"
