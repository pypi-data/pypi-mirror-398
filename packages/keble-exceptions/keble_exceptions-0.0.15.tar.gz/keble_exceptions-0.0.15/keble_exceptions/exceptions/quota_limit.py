from typing import Any, Optional

from .base import KebleException


class EmailSendingLimitReached(KebleException):
    def __init__(
        self,
        *,
        wait_minutes: str | float | int,
        alert_admin: bool,
        function_identifier: Optional[str] = None,
    ):
        super(EmailSendingLimitReached, self).__init__(
            how_to_resolve={
                "ENGLISH": f"You have reached the sending limit, you may retry after {wait_minutes} minutes.",
                "SIMPLIFIED_CHINESE": f"你达到了发送邮件的次数限制，你最好等{wait_minutes}分钟后再尝试",
            },
            alert_admin=alert_admin,
            function_identifier=function_identifier,
        )


class SmsSendingLimitReached(KebleException):
    def __init__(
        self,
        *,
        wait_minutes: str | float | int,
        alert_admin: bool,
        function_identifier: Optional[str] = None,
    ):
        super(SmsSendingLimitReached, self).__init__(
            how_to_resolve={
                "ENGLISH": f"You have reached the sms limit, you may retry after {wait_minutes} minutes.",
                "SIMPLIFIED_CHINESE": f"你达到了发送短信的次数限制，你最好等{wait_minutes}分钟后再尝试",
            },
            alert_admin=alert_admin,
            function_identifier=function_identifier,
        )


class FrequencyLimitReached(KebleException):
    def __init__(
        self,
        *,
        wait_minutes: str | float | int,
        alert_admin: bool,
        function_identifier: Optional[str] = None,
    ):
        super(FrequencyLimitReached, self).__init__(
            how_to_resolve={
                "ENGLISH": f"You are performing this action too often, you may retry after {wait_minutes} minutes.",
                "SIMPLIFIED_CHINESE": f"你尝试了太多次，请等候{wait_minutes}分钟后再尝试",
            },
            alert_admin=alert_admin,
            function_identifier=function_identifier,
        )


class WechatBindingLimitExceeded(KebleException):
    def __init__(
        self,
        *,
        limit: int = 3,
        alert_admin: bool,
        admin_note: Any | None = None,
    ):
        super().__init__(
            how_to_resolve={
                "ENGLISH": (
                    f"This WeChat account is already bound to {limit} users, which is the maximum allowed. To continue, please use a different WeChat account or contact customer support."
                ),
                "SIMPLIFIED_CHINESE": (
                    f"该微信账号已有 {limit} 个用户的绑定历史记录，已达到尝试绑定的上限。如需继续操作，请更换微信账号，或联系客服协助处理。"
                ),
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
        )
