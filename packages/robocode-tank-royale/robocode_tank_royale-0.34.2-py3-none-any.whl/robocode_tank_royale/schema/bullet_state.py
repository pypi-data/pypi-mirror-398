"""
Generated Python class from bullet-state.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .color import Color

class BulletState:
    """Bullet state"""

    def __init__(self, bullet_id: int | None, owner_id: int | None, power: float | None, x: float | None, y: float | None, direction: float | None, color: Color | None = None):
        if direction is None:
            raise ValueError("The 'direction' parameter must be provided.")
        if x is None:
            raise ValueError("The 'x' parameter must be provided.")
        if y is None:
            raise ValueError("The 'y' parameter must be provided.")
        if bullet_id is None:
            raise ValueError("The 'bullet_id' parameter must be provided.")
        if owner_id is None:
            raise ValueError("The 'owner_id' parameter must be provided.")
        if power is None:
            raise ValueError("The 'power' parameter must be provided.")
        self.bullet_id = bullet_id
        self.owner_id = owner_id
        self.power = power
        self.x = x
        self.y = y
        self.direction = direction
        self.color = color
