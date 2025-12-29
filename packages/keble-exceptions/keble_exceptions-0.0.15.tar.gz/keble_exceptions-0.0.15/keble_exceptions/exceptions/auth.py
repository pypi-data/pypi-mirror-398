from .base import KebleException


class TokenExpired(KebleException):
    def __init__(self):
        super(TokenExpired, self).__init__(
            status_code=401,
        )


class TokenPurposeUnmatched(KebleException):
    def __init__(self):
        super(TokenPurposeUnmatched, self).__init__(
            status_code=401,
            how_to_resolve={
                "ENGLISH": "You may want to switch your role to user/organization and then switch back to refresh the page.",
                "SIMPLIFIED_CHINESE": "你可以尝试切换角色，从用户切换成组织，然后再切换回来，来重置。这个可能能够解决这个问题。",
            },
        )


class InactiveUser(KebleException):
    def __init__(self):
        super(InactiveUser, self).__init__(
            status_code=401,
            how_to_resolve={
                "ENGLISH": "User is deleted. You no longer have access to this account.",
                "SIMPLIFIED_CHINESE": "用户已删除。此账户已无法再使用。",
            },
        )


class UserNotFound(KebleException):
    def __init__(self):
        super(UserNotFound, self).__init__(
            status_code=401,
            how_to_resolve={
                "ENGLISH": "User not found. Please check your email and password.",
                "SIMPLIFIED_CHINESE": "用户未找到。请检查你的邮箱和密码。",
            },
        )


class UserIdentityVerificationIsRequired(KebleException):
    def __init__(self):
        super(UserIdentityVerificationIsRequired, self).__init__(
            status_code=428,
            how_to_resolve={
                "ENGLISH": "User identity verification is required.",
                "SIMPLIFIED_CHINESE": "需要进行身份验证",
            },
        )


class UserOrOrgIdentityNoSufficientToken(KebleException):
    def __init__(self):
        super(UserOrOrgIdentityNoSufficientToken, self).__init__(status_code=402)


class UserOrOrgIdentityTokenCooldown(KebleException):
    def __init__(self):
        super(UserOrOrgIdentityTokenCooldown, self).__init__(status_code=423)


class NoObjectPermission(KebleException):
    """No Permission on certain Object"""

    def __init__(self):
        super(NoObjectPermission, self).__init__(
            how_to_resolve={
                "ENGLISH": "You do not have permission to access this data.",
                "SIMPLIFIED_CHINESE": "你无权读取/使用/或修改这个数据。",
            },
        )


class NoRolePermission(KebleException):
    """No Permission due to Role"""

    def __init__(self):
        super(NoRolePermission, self).__init__(
            how_to_resolve={
                "ENGLISH": "You do not have the role permission to access this data.",
                "SIMPLIFIED_CHINESE": "你缺少访问这个数据的角色权限。",
            },
        )


class EmailNotRegistered(KebleException):
    def __init__(self):
        super(EmailNotRegistered, self).__init__(
            how_to_resolve={
                "ENGLISH": "The email is not registered. Please signup first.",
                "SIMPLIFIED_CHINESE": "邮箱未注册，请先注册帐号。",
            },
        )


class EmailRegistered(KebleException):
    def __init__(self):
        super(EmailRegistered, self).__init__(
            how_to_resolve={
                "ENGLISH": "The email is already registered. Please login.",
                "SIMPLIFIED_CHINESE": "邮箱已注册，请直接登录。",
            },
        )


class InvalidEmailConfirmationCode(KebleException):
    def __init__(self):
        super(InvalidEmailConfirmationCode, self).__init__(
            how_to_resolve={
                "ENGLISH": "The email confirmation code is invalid. Please try again.",
                "SIMPLIFIED_CHINESE": "邮箱验证码无效，请重新尝试。",
            },
        )


class InvalidEmailOrPassword(KebleException):
    def __init__(self):
        super(InvalidEmailOrPassword, self).__init__(
            how_to_resolve={
                "ENGLISH": "The email or password is invalid. Please try again.",
                "SIMPLIFIED_CHINESE": "邮箱或密码无效，请重新尝试。",
            },
        )
