from typing import Any, Optional

from keble_exceptions.exceptions.utils import wrap_alert_admin_fingerprint

from .base import KebleException


class LlmInvalidResponse(KebleException):
    def __init__(
        self,
        *,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
        function_identifier: Optional[str] = None
    ):
        super(LlmInvalidResponse, self).__init__(
            how_to_resolve={
                "ENGLISH": "Our model just provide an invalid response. This issue is likely caused by the prompt rather than you (the end user). However, you should retry and the our model may resolve this issue automatically. If this problem persist, you will need to wait for the developers to resolve this problem.",
                "SIMPLIFIED_CHINESE": "我们的模型出了点问题。这很大概率是程序员导致的错误，并非你（终端用户）。你可以重新尝试一下，如果还是继续错误下去，你可能需要等程序员修复这个问题。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            function_identifier=function_identifier,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                function_identifier
            ] if function_identifier is not None else None
        )
