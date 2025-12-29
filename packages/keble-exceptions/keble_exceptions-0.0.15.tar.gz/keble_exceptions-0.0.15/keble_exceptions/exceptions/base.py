from typing import List, Optional, TypedDict

HowToResolve = TypedDict("HowToResolve", {"ENGLISH": str, "SIMPLIFIED_CHINESE": str})


class KebleException(Exception):
    def __init__(
        self,
        *,
        # internal, server side
        alert_admin: bool = False,
        function_identifier: Optional[str] = None,
        admin_note: Optional[str] = None,
        # client side, for end user
        status_code: int = 400,
        how_to_resolve: Optional[HowToResolve] = None,
        # fingerprint: Optional[str] = None
        fingerprint: Optional[List[str]] = None,
    ):
        self.status_code = status_code
        self.alert_admin = alert_admin
        self.how_to_resolve = how_to_resolve
        self.function_identifier = function_identifier
        self.admin_note = admin_note
        self.fingerprint = fingerprint

    def __str__(self):
        base_message = f"[{self.__class__.__name__}] {self.how_to_resolve['ENGLISH'] if self.how_to_resolve is not None else ''}"
        metadata = []

        if self.function_identifier:
            metadata.append(f"Function: {self.function_identifier}")
        if self.admin_note:
            metadata.append(f"Admin Note: {self.admin_note}")
        if self.alert_admin:
            metadata.append("Alert Admin: True")

        return base_message + (f" | {' | '.join(metadata)}" if metadata else "")

    @property
    def exception_name(self):
        return self.__class__.__name__

    @property
    def default_sentry_fingerprint(self) -> List[str]:
        base = [
            self.exception_name,
            self.alert_admin,
        ]
        if self.function_identifier is not None:
            base += [self.function_identifier]
        return base

    # @classmethod
    # def get_sentry_before_send(cls):
    #     def _before_send(event, hint):
    #         # pull the actual exception object (if any)
    #         exc = hint.get("exc_info", (None, None, None))[1]
    #         if isinstance(exc, KebleException):
    #             # tag it so you can filter “is:tagged keble_exception”
    #             tags = event.setdefault("tags", {})
    #             tags["keble_exception"] = exc.exception_name
    #             tags["alert_admin"] = str(exc.alert_admin)

    #             extra = event.setdefault("extra", {})
    #             extra["function_identifier"] = exc.function_identifier
    #             extra["admin_note"] = exc.admin_note
    #             extra["status_code"] = exc.status_code
    #             extra["how_to_resolve"] = exc.how_to_resolve
    #         return event

    #     return _before_send

    @classmethod
    def get_sentry_before_send(cls):
        def _before_send(event, hint):
            # pull the actual exception object (if any)
            exc = hint.get("exc_info", (None, None, None))[1]
            if isinstance(exc, KebleException):
                # === tags (for search/filter) ===
                tags = event.setdefault("tags", {})
                tags["keble_exception"] = exc.exception_name
                tags["alert_admin"] = str(exc.alert_admin)

                # === extras (for detail display) ===
                extra = event.setdefault("extra", {})
                extra["function_identifier"] = exc.function_identifier
                extra["admin_note"] = exc.admin_note
                extra["status_code"] = exc.status_code
                extra["how_to_resolve"] = exc.how_to_resolve

                # === custom fingerprint (for grouping) ===
                # You can customize this to group by whatever combo you want
                event["fingerprint"] = exc.fingerprint or exc.default_sentry_fingerprint

            return event

        return _before_send
