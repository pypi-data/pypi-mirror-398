"""
Generated Python class from bot-policy-update.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class BotPolicyUpdate(Message):
    """One or more bot policies have been updated"""

    def __init__(self, bot_id: int | None, debugging_enabled: bool | None, type: 'Message.Type | None'):
        if debugging_enabled is None:
            raise ValueError("The 'debugging_enabled' parameter must be provided.")
        if bot_id is None:
            raise ValueError("The 'bot_id' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
        self.bot_id = bot_id
        self.debugging_enabled = debugging_enabled
