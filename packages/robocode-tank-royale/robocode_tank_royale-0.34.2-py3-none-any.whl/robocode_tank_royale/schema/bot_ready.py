"""
Generated Python class from bot-ready.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class BotReady(Message):
    """Message from a bot that is ready to play a game"""

    def __init__(self, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
