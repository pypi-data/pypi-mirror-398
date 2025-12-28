"""
Generated Python class from game-started-event-for-observer.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .participant import Participant
from .game_setup import GameSetup

class GameStartedEventForObserver(Message):
    """Event occurring when a new game has started. Gives game info for an observer."""

    def __init__(self, game_setup: GameSetup | None, participants: list[Participant | None] | None, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if participants is None:
            raise ValueError("The 'participants' parameter must be provided.")
        if game_setup is None:
            raise ValueError("The 'game_setup' parameter must be provided.")
        super().__init__(type)
        self.game_setup = game_setup
        self.participants = participants
