"""Project-specific exceptions."""


class ListingAutopilotError(Exception):
    def __init__(self, message: str, code: str = "LISTING_AUTOPILOT_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ProviderExecutionError(ListingAutopilotError):
    pass


class ExportError(ListingAutopilotError):
    pass
