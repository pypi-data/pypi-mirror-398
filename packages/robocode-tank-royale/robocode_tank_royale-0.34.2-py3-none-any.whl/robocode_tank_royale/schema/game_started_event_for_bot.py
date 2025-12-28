"""
Generated Python class from game-started-event-for-bot.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .game_setup import GameSetup

class GameStartedEventForBot(Message):
    """Event occurring when a new game has started. Gives game info for a bot."""

    def __init__(self, my_id: int | None, game_setup: GameSetup | None, type: 'Message.Type | None', start_x: float | None = None, start_y: float | None = None, start_direction: float | None = None, teammate_ids: list[int | None] | None = None):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if my_id is None:
            raise ValueError("The 'my_id' parameter must be provided.")
        if game_setup is None:
            raise ValueError("The 'game_setup' parameter must be provided.")
        super().__init__(type)
        self.my_id = my_id
        self.start_x = start_x
        self.start_y = start_y
        self.start_direction = start_direction
        self.teammate_ids = teammate_ids
        self.game_setup = game_setup
