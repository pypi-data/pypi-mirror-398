"""
Generated Python class from game-paused-event-for-observer.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class GamePausedEventForObserver(Message):
    """Event occurring when a game has been paused"""

    def __init__(self, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
