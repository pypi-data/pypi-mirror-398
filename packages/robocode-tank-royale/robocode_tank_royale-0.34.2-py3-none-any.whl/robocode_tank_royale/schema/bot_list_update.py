"""
Generated Python class from bot-list-update.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .bot_info import BotInfo

class BotListUpdate(Message):
    """Snapshot of all bots currently connected to the server. Extends message.schema.yaml and therefore includes the required `type` field with value `BotListUpdate`. Emitted to observers/controllers whenever a bot joins or leaves, and when a client connects and requests the current list. The list may be empty when no bots are connected. Order is not guaranteed and should not be relied upon."""

    def __init__(self, bots: list[BotInfo | None] | None, type: 'Message.Type | None'):
        if bots is None:
            raise ValueError("The 'bots' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
        self.bots = bots
