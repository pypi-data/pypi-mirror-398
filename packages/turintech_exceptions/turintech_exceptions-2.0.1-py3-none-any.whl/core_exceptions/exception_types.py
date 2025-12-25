# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from enum import Enum

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                               Business Exception Types                                               #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class ExceptionType(str, Enum):
    NOT_FOUND = "not_found"
    INVALID_PARAMS = "invalid_params"
    CONFLICT = "conflict"
    INTERNAL = "internal"
    UNPROCESSABLE = "unprocessable"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    UNAUTHORIZED = "unauthorized"
