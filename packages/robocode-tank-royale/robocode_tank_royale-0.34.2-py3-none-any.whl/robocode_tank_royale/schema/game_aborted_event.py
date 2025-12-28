"""
Generated Python class from game-aborted-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class GameAbortedEvent(Message):
    """Event occurring when game has been aborted. No score is available."""

    def __init__(self, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
