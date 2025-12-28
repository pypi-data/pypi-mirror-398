"""
Generated Python class from skipped-turn-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .event import Event

class SkippedTurnEvent(Event):
    """Event occurring when a bot has skipped a turn, meaning that no intent has reached the server for a specific turn"""

    def __init__(self, turn_number: int | None, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        super().__init__(turn_number, type)
