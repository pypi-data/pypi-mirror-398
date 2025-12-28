"""
Generated Python class from round-started-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class RoundStartedEvent(Message):
    """Event occurring when a new round has started."""

    def __init__(self, round_number: int | None, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if round_number is None:
            raise ValueError("The 'round_number' parameter must be provided.")
        super().__init__(type)
        self.round_number = round_number
