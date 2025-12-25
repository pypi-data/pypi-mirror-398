from typing import Literal

Severity = Literal["error", "warning", "info"]

class ApiBeanError(Exception):
    """
    Base class for all apibean-client errors.
    """

    # --- Required fields ---
    code: str = "unknown_error"
    message: str = "An error occurred"
    severity: Severity = "error"

    # --- Optional fields ---
    title: str | None = None
    detail: str | None = None
    hint: str | None = None

    message_template: str | None = None

    def __init__(self, *,
        message=None,
        message_template=None,
        message_data=None,
        cause: Exception | None = None,
        detail: str | None = None,
        hint: str | None = None
    ):
        self.message_data = message_data or {}

        message_template = message_template or self.message_template

        if message:
            self.message = message
        elif message_template:
            self.message = message_template.format(**self.message_data)
        else:
            self.message = self.__class__.__name__

        self.cause = cause

        if detail:
            self.detail = detail
        if hint:
            self.hint = hint

        super().__init__(self.message)
