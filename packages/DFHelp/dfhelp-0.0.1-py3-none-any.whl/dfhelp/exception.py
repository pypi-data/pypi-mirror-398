"""Exceptions raised by the package."""


class DFHelpError(Exception):
    """Base class for all exceptions raised by this package."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        return
