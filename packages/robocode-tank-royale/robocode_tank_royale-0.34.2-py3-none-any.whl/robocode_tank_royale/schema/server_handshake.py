"""
Generated Python class from server-handshake.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .game_setup import GameSetup

class ServerHandshake(Message):
    """Server handshake"""

    def __init__(self, session_id: str | None, variant: str | None, version: str | None, game_types: list[str | None] | None, type: 'Message.Type | None', name: str | None = None, game_setup: GameSetup | None = None):
        if version is None:
            raise ValueError("The 'version' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if variant is None:
            raise ValueError("The 'variant' parameter must be provided.")
        if game_types is None:
            raise ValueError("The 'game_types' parameter must be provided.")
        if session_id is None:
            raise ValueError("The 'session_id' parameter must be provided.")
        super().__init__(type)
        self.session_id = session_id
        self.name = name
        self.variant = variant
        self.version = version
        self.game_types = game_types
        self.game_setup = game_setup
