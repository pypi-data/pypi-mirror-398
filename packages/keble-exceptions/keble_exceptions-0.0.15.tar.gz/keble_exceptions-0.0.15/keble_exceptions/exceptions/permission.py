from typing import Optional

from .base import KebleException


class NoObjectPermission(KebleException):
    """No Permission on certain Object"""

    def __init__(
        self,
        *,
        object_id: str,
        object_type: Optional[str] = None,
    ):
        super(NoObjectPermission, self).__init__(
            how_to_resolve={
                "ENGLISH": f"You have no permission to perform this action. (<{object_type}> id: {object_id})",
                "SIMPLIFIED_CHINESE": f"你没有权限去执行这个操作。（<{object_type} id: {object_id}>）",
            },
            fingerprint=[f"object_type={object_type}"],
        )


class NoRolePermission(KebleException):
    """No Permission due to Role"""

    def __init__(self, *, current_role: str, require_role: str):
        super(NoRolePermission, self).__init__(
            how_to_resolve={
                "ENGLISH": f"It requires a higher-level role permission to perform this action. (current role: {current_role}, require role: {require_role})",
                "SIMPLIFIED_CHINESE": "这需要更高级的帐号权限才能执行此操作",
            },
            fingerprint=[
                f"current_role={current_role}",
                f"require_role={require_role}",
            ],
        )
