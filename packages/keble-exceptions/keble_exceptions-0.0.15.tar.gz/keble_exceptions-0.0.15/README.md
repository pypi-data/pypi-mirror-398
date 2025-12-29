# keble-exceptions

This package provides a set of predefined exceptions for various error scenarios within the Keble codebase. These exceptions inherit from the base `KebleException` class.

## Base `KebleException` Signature

```python
def __init__(
    self,
    *,
    alert_admin: bool = False,
    function_identifier: Optional[str] = None,
    admin_note: Optional[str] = None,
    status_code: int = 400,
    how_to_resolve: Optional[HowToResolve] = None,
    fingerprint: Optional[List[str]] = None,
):
    ...
```

## Predefined Exceptions Signatures

### Authentication and Authorization Exceptions

* **TokenExpired**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **TokenPurposeUnmatched**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **InactiveUser**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **UserNotFound**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **UserIdentityVerificationIsRequired**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **UserOrOrgIdentityNoSufficientToken**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **NoObjectPermission**
    ```python
    def __init__(self, *, object_id: str, object_type: Optional[str] = None, *args, **kwargs):
        ...
    ```
* **NoRolePermission**
    ```python
    def __init__(self, *, current_role: str, require_role: str, *args, **kwargs):
        ...
    ```

### Email and Registration Exceptions

* **EmailNotRegistered**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **EmailRegistered**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **InvalidEmailConfirmationCode**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```
* **InvalidEmailOrPassword**
    ```python
    def __init__(self, *args, **kwargs):
        ...
    ```

### Parameter Validation Exceptions

* **ServerSideMissingParams**
    ```python
    def __init__(self, *, missing_params: str, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```
* **ClientSideMissingParams**
    ```python
    def __init__(self, *, missing_params: str, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```
* **ServerSideInvalidParams**
    ```python
    def __init__(self, *, invalid_params: str | int, expected: str | int | Type, but_got: str | int | Type, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```
* **ClientSideInvalidParams**
    ```python
    def __init__(self, *, invalid_params: str | int, expected: str | int | Type, but_got: str | int | Type, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```

### Data and Object Exceptions

* **ObjectNotFound**
    ```python
    def __init__(self, *, object_name: str, id: Any, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```
* **DataIntegrityCompromised**
    ```python
    def __init__(self, *, object_name: Optional[str] = None, id: Any = None, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```

### Processing and Iteration Exceptions

* **MaxIterationReached**
    ```python
    def __init__(self, *, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```
* **UnhandledScenarioOrCase**
    ```python
    def __init__(self, *, unhandled_case: str, alert_admin: bool, admin_note: Optional[Any] = None, *args, **kwargs):
        ...
    ```

### Request and Response Exceptions

* **RequestFailure**
    ```python
    def __init__(self, *, admin_note: Any, function_identifier: str, alert_admin: bool, *args, **kwargs):
        ...
    ```
* **LlmInvalidResponse**
    ```python
    def __init__(self, *, alert_admin: bool, admin_note: Optional[Any] = None, function_identifier: Optional[str] = None, *args, **kwargs):
        ...
    ```

### Rate Limiting Exceptions

* **EmailSendingLimitReached**
    ```python
    def __init__(self, *, wait_minutes: str | float | int, alert_admin: bool, function_identifier: Optional[str] = None, *args, **kwargs):
        ...
    ```
* **SmsSendingLimitReached**
    ```python
    def __init__(self, *, wait_minutes: str | float | int, alert_admin: bool, function_identifier: Optional[str] = None, *args, **kwargs):
        ...
    ```
* **FrequencyLimitReached**
    ```python
    def __init__(self, *, wait_minutes: str | float | int, alert_admin: bool, function_identifier: Optional[str] = None, *args, **kwargs):
        ...
    ```
* **WechatBindingLimitExceeded**
    ```python
    def __init__(self, *, limit: int = 3, alert_admin: bool, admin_note: Any | None = None, *args, **kwargs):
        ...
    ```

## `raise_if_not` Function

```python
def raise_if_not(condition: bool | List[bool], exception: KebleException):
    # raise when condition is not TRUE or not all TRUE
    ...
```
