"""
Generated Python class from bot-hit-bot-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .event import Event

class BotHitBotEvent(Event):
    """Event occurring when a bot has collided with another bot"""

    def __init__(self, victim_id: int | None, bot_id: int | None, energy: float | None, x: float | None, y: float | None, rammed: bool | None, turn_number: int | None, type: 'Message.Type | None'):
        if victim_id is None:
            raise ValueError("The 'victim_id' parameter must be provided.")
        if bot_id is None:
            raise ValueError("The 'bot_id' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        if rammed is None:
            raise ValueError("The 'rammed' parameter must be provided.")
        if y is None:
            raise ValueError("The 'y' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if x is None:
            raise ValueError("The 'x' parameter must be provided.")
        if energy is None:
            raise ValueError("The 'energy' parameter must be provided.")
        super().__init__(turn_number, type)
        self.victim_id = victim_id
        self.bot_id = bot_id
        self.energy = energy
        self.x = x
        self.y = y
        self.rammed = rammed
