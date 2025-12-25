"""
Lubit API Exceptions
"""


class LubitAPIError(Exception):
    """Exception raised for Lubit API errors."""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(f"Lubit API Error: {message}")
