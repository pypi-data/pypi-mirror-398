"""
Generated Python class from tick-event-for-observer.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .event import Event
from .bot_state_with_id import BotStateWithId
from .bullet_state import BulletState

class TickEventForObserver(Event):
    """Event occurring for before each new turn in the battle. Gives details for observers."""

    def __init__(self, round_number: int | None, bot_states: list[BotStateWithId | None] | None, bullet_states: list[BulletState | None] | None, events: list[Event | None] | None, turn_number: int | None, type: 'Message.Type | None'):
        if bullet_states is None:
            raise ValueError("The 'bullet_states' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        if bot_states is None:
            raise ValueError("The 'bot_states' parameter must be provided.")
        if round_number is None:
            raise ValueError("The 'round_number' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if events is None:
            raise ValueError("The 'events' parameter must be provided.")
        super().__init__(turn_number, type)
        self.round_number = round_number
        self.bot_states = bot_states
        self.bullet_states = bullet_states
        self.events = events
