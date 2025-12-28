"""
Generated Python class from tps-changed-event.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class TpsChangedEvent(Message):
    """Event occurring when a controller has changed the TPS (Turns Per Second), which is the number of turns displayed for an observer. TPS is similar to FPS, where a frame is equal to a turn."""

    def __init__(self, type: 'Message.Type | None', tps: int | None = None):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
        self.tps = tps
