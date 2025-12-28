"""
Generated Python class from event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class Event(Message):
    """Abstract event occurring during a battle"""

    def __init__(self, turn_number: int | None, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        super().__init__(type)
        self.turn_number = turn_number
