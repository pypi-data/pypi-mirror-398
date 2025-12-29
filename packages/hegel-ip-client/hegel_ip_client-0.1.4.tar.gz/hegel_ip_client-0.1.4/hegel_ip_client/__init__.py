"""Python client library for Hegel amplifiers."""

from .client import (
    apply_state_changes,
    HegelClient,
    HegelStateUpdate,
    parse_reply_message,
)
from .const import COMMANDS
from .exceptions import HegelConnectionError, HegelError

__all__ = [
    "HegelClient",
    "HegelStateUpdate",
    "parse_reply_message",
    "apply_state_changes",
    "COMMANDS",
    "HegelError",
    "HegelConnectionError",
]
