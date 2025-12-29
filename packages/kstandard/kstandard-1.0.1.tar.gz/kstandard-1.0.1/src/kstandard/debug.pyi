
# debug.pyi

#- Imports -----------------------------------------------------------------------------------------

from enum import Enum
from typing import Any


#- Alert Level -------------------------------------------------------------------------------------

class AlertLevel(Enum):
    """
    Level of alerts:
        ALERT: General alert message
        WARNING: Warning message
        ERROR: Error message
    """
    ALERT = ...
    WARNING = ...
    ERROR = ...
    ...


#- Alert Function ----------------------------------------------------------------------------------

# Print where this procedure was called, with optional message.
def alert(prompt: Any = "", backtrack: int = 1, level: AlertLevel = AlertLevel.ALERT) -> None:
    """
    Prints the alert message to stderr along with the caller's file and line number.

    Parameters:
        prompt: Message to display alongside the alert level.
        backtrack: Number of stack frames to backtrack to find the caller info (default is 1).
        level: The level of the alert (default is AlertLevel.ALERT).
    """
    ...

