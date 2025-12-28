"""
Generated Python class from next-turn.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class NextTurn(Message):
    """Command to make the next turn when the game is paused used for single stepping when debugging."""

    def __init__(self, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
