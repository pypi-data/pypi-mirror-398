from typing import Any, Optional, Type

from .base import KebleException
from .utils import wrap_alert_admin_fingerprint


class ServerSideMissingParams(KebleException):
    def __init__(
        self,
        *,
        missing_params: str,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(ServerSideMissingParams, self).__init__(
            how_to_resolve={
                "ENGLISH": f"Missing <{missing_params}>. This may cause by the programmer rather than you (the end user). You may need to wait for devs to resolve this problem.",
                "SIMPLIFIED_CHINESE": f"缺少了数据 <{missing_params}>。这很大概率是程序员导致的错误，并非你（终端用户）。你有可能需要等程序员下个版本更新迭代才能解决这个问题。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"missing_params={missing_params}",
            ],
        )


class ClientSideMissingParams(KebleException):
    def __init__(
        self,
        *,
        missing_params: str,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(ClientSideMissingParams, self).__init__(
            how_to_resolve={
                "ENGLISH": f"Missing <{missing_params}>. This may cause by the the client side or user(the end user). You may need to recheck your form, or you may need to wait for devs to resolve this problem.",
                "SIMPLIFIED_CHINESE": f"缺少了数据 <{missing_params}>。这很大概率是客户端，或者是你的表格填写的有问题。你可以先尝试检查表格是否有填写错误的信息。如果没有，那么很有可能你需要等程序员更新版本后才能解决这个问题了。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"missing_params={missing_params}",
            ],
        )


class ServerSideInvalidParams(KebleException):
    def __init__(
        self,
        *,
        invalid_params: str | int,
        expected: str | int | Type,
        but_got: str | int | Type,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(ServerSideInvalidParams, self).__init__(
            how_to_resolve={
                "ENGLISH": f"Invalid value in <{invalid_params}>. Expected {expected}, but got {but_got}. This issue is likely caused by the programmer rather than you (the end user). You may need to wait for the developers to resolve this problem.",
                "SIMPLIFIED_CHINESE": f"<{invalid_params}> 的值无效。本应 {expected}，但却 {but_got}。这很大概率是程序员导致的错误，并非你（终端用户）。你可能需要等程序员修复这个问题。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"invalid_params={invalid_params}",
            ],
        )


class ClientSideInvalidParams(KebleException):
    def __init__(
        self,
        *,
        invalid_params: str | int,
        expected: str | int | Type,
        but_got: str | int | Type,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(ClientSideInvalidParams, self).__init__(
            how_to_resolve={
                "ENGLISH": f"Invalid value in <{invalid_params}>. Expected {expected}, but got {but_got}. This issue is likely caused by incorrect input from the client side or the user (you). Please double-check your form or input before submitting again.",
                "SIMPLIFIED_CHINESE": f"<{invalid_params}> 的值无效。本应 {expected}，但却 {but_got}。这很大概率是客户端或你的输入问题。请检查你的表单或输入数据后再提交。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"invalid_params={invalid_params}",
            ],
        )


class ObjectNotFound(KebleException):
    def __init__(
        self,
        *,
        object_name: str,
        id: Any,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(ObjectNotFound, self).__init__(
            how_to_resolve={
                "ENGLISH": f"Object <{object_name}> not found <{id}>. This issue is likely caused by incorrect input from the client side or the user (you). You can retry or refresh. If this problem persist, you may need to inform admin/devs manually.",
                "SIMPLIFIED_CHINESE": f"<{object_name}>的数据<{id}>未找到。此问题可能是由于客户端或用户（您）输入错误导致的。您可以重试或刷新。如果问题仍然存在，您可能需要手动通知管理员或开发人员。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"object_name={object_name}",
            ],
        )


class DataIntegrityCompromised(KebleException):
    def __init__(
        self,
        *,
        object_name: Optional[str] = None,
        id: Any = None,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(DataIntegrityCompromised, self).__init__(
            how_to_resolve={
                "ENGLISH": f"Data integrity compromised <object_name={object_name}, id={id}>. This issue is likely caused by server side bad coding, not by user (you). You can retry or refresh. If this problem persist, you may need to inform admin/devs manually.",
                "SIMPLIFIED_CHINESE": f"数据完整性受损 <object_name={object_name}, id={id}>。此问题很可能由服务器端代码错误引起，与用户（您）无关。您可以重试或刷新。如果问题持续存在，您可能需要手动通知管理员/开发人员。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"object_name={object_name}",
            ]
            if object_name is not None
            else None,
        )


class MaxIterationReached(KebleException):
    def __init__(
        self,
        *,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(MaxIterationReached, self).__init__(
            how_to_resolve={
                "ENGLISH": "Server side failed to handle data, and reached maximum retried. This issue is likely caused by bad code. You can retry right now, but if the problem persist, you may need to wait for devs to resolve it. Devs have already been informed.",
                "SIMPLIFIED_CHINESE": "服务器端未能处理数据，并已达到最大重试次数。此问题可能是由于代码问题引起的。您可以立即重试，但如果问题仍然存在，可能需要等待开发人员解决。开发人员已收到通知。",
            },
            alert_admin=alert_admin,
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
            ],
        )


class UnhandledScenarioOrCase(KebleException):
    def __init__(
        self,
        *,
        unhandled_case: str,
        alert_admin: bool,
        admin_note: Optional[Any] = None,
    ):
        super(UnhandledScenarioOrCase, self).__init__(
            how_to_resolve={
                "ENGLISH": f"{unhandled_case} is/are unsupported in current version of codebase. However, this could happen in future update.",
                "SIMPLIFIED_CHINESE": f"目前系统还不能处理：{unhandled_case}。目前要等开发更新迭代之后在后续考虑支持。",
            },
            alert_admin=alert_admin,  # Since it's a client-side issue, no need to alert the admin
            admin_note=admin_note,
            fingerprint=[
                wrap_alert_admin_fingerprint(alert_admin),
                f"unhandled_case={unhandled_case}",
            ],
        )
