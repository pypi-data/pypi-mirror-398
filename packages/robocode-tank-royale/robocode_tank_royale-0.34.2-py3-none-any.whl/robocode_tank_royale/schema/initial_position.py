"""
Generated Python class from initial-position.schema.yaml
This file is auto-generated. Do not edit manually.
"""


class InitialPosition:
    """description: |
  Initial start position of the bot used for debugging as a comma-separated format taking the x and y coordinates
  and shared starting direction of the body, gun, and radar.
"""

    def __init__(self, x: float | None = None, y: float | None = None, direction: float | None = None):
        self.x = x
        self.y = y
        self.direction = direction
