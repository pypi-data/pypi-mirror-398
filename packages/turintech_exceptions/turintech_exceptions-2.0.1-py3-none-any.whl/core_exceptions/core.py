# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Optional

# Core Source imports
from core_exceptions.exception_types import ExceptionType

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "BaseGenericException",
    "ElementNotFoundException",
    "InvalidParameterException",
    "ElementAlreadyExistsException",
    "ExceptionType",
]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                 Business Exceptions                                                  #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class BaseGenericException(Exception):
    """
    Categorised error, by default it is considered undefined-internal error.
    """

    type: ExceptionType = ExceptionType.INTERNAL
    message = "Internal Exception - no message"

    def __init__(self, message: Optional[str] = None, details: Optional[str] = None):
        """
        Args:
            message (str): Error message. This will replace the defined class message.
            details (str): Details about the error.
        """
        self.message = self._compose_message(message=message, details=details)
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def _compose_message(self, message: Optional[str] = None, details: Optional[str] = None) -> str:
        """Composition of the error message.

        Args:
            message (str): Error message. This will replace the defined class message.
            details (str): Details about the error.

        Returns:
            message (str): A message  error with the following format:
                self.message: message - details

        """
        return " - ".join([msg for msg in [message or self.message, details] if msg])


class ElementNotFoundException(BaseGenericException):
    type = ExceptionType.NOT_FOUND


class InvalidParameterException(BaseGenericException):
    type = ExceptionType.INVALID_PARAMS


class ElementAlreadyExistsException(BaseGenericException):
    type = ExceptionType.CONFLICT

    def __init__(self, message: Optional[str] = None, resource: Optional[str] = None, details: Optional[str] = None):
        _message = message or (f"The {resource} already exists" if resource else self.message)
        super().__init__(_message, details=details)
