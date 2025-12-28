"""
Generated Python class from start-game.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .game_setup import GameSetup
from .bot_address import BotAddress

class StartGame(Message):
    """Command to start a new game"""

    def __init__(self, bot_addresses: list[BotAddress | None] | None, type: 'Message.Type | None', game_setup: GameSetup | None = None):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if bot_addresses is None:
            raise ValueError("The 'bot_addresses' parameter must be provided.")
        super().__init__(type)
        self.game_setup = game_setup
        self.bot_addresses = bot_addresses
