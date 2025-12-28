"""
Generated Python class from scanned-bot-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .event import Event

class ScannedBotEvent(Event):
    """Event occurring when a bot has scanned another bot"""

    def __init__(self, scanned_by_bot_id: int | None, scanned_bot_id: int | None, energy: float | None, x: float | None, y: float | None, direction: float | None, speed: float | None, turn_number: int | None, type: 'Message.Type | None'):
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        if energy is None:
            raise ValueError("The 'energy' parameter must be provided.")
        if direction is None:
            raise ValueError("The 'direction' parameter must be provided.")
        if scanned_by_bot_id is None:
            raise ValueError("The 'scanned_by_bot_id' parameter must be provided.")
        if y is None:
            raise ValueError("The 'y' parameter must be provided.")
        if scanned_bot_id is None:
            raise ValueError("The 'scanned_bot_id' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if speed is None:
            raise ValueError("The 'speed' parameter must be provided.")
        if x is None:
            raise ValueError("The 'x' parameter must be provided.")
        super().__init__(turn_number, type)
        self.scanned_by_bot_id = scanned_by_bot_id
        self.scanned_bot_id = scanned_bot_id
        self.energy = energy
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
