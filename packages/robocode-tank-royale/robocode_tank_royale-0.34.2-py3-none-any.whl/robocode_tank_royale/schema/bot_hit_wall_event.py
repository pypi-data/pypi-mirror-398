"""
Generated Python class from bot-hit-wall-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .event import Event

class BotHitWallEvent(Event):
    """Event occurring when a bot has hit a wall"""

    def __init__(self, victim_id: int | None, turn_number: int | None, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if victim_id is None:
            raise ValueError("The 'victim_id' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        super().__init__(turn_number, type)
        self.victim_id = victim_id
