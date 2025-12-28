"""
Generated Python class from bullet-hit-bullet-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .event import Event
from .bullet_state import BulletState

class BulletHitBulletEvent(Event):
    """Event occurring when a bullet has hit another bullet"""

    def __init__(self, bullet: BulletState | None, hit_bullet: BulletState | None, turn_number: int | None, type: 'Message.Type | None'):
        if hit_bullet is None:
            raise ValueError("The 'hit_bullet' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        if bullet is None:
            raise ValueError("The 'bullet' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(turn_number, type)
        self.bullet = bullet
        self.hit_bullet = hit_bullet
