from typing import Any

from keble_exceptions.exceptions.utils import wrap_alert_admin_fingerprint

from .base import KebleException


class RequestFailure(KebleException):
    def __init__(self, *, admin_note: Any, function_identifier: str, alert_admin: bool):
        super(RequestFailure, self).__init__(
            admin_note=admin_note,
            function_identifier=function_identifier,
            how_to_resolve={
                "ENGLISH": "Internal resource error. You can retry and if the problem persist, you may need to wait for dev update the code to resolve this issue.",
                "SIMPLIFIED_CHINESE": "系统资源出现了问题，这个是程序员所导致的，并非你（用户）。你先再次尝试。如果多次尝试都是如此的话，很有可能需要等待开发修复了这个问题才能继续。",
            },
            alert_admin=alert_admin,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"function_identifier={function_identifier}",
            ],
        )
