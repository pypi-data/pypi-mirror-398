"""
Generated Python class from bullet-hit-bot-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .event import Event
from .bullet_state import BulletState

class BulletHitBotEvent(Event):
    """Event occurring when a bot has been hit by a bullet from another bot"""

    def __init__(self, victim_id: int | None, bullet: BulletState | None, damage: float | None, energy: float | None, turn_number: int | None, type: 'Message.Type | None'):
        if victim_id is None:
            raise ValueError("The 'victim_id' parameter must be provided.")
        if bullet is None:
            raise ValueError("The 'bullet' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if damage is None:
            raise ValueError("The 'damage' parameter must be provided.")
        if energy is None:
            raise ValueError("The 'energy' parameter must be provided.")
        super().__init__(turn_number, type)
        self.victim_id = victim_id
        self.bullet = bullet
        self.damage = damage
        self.energy = energy
