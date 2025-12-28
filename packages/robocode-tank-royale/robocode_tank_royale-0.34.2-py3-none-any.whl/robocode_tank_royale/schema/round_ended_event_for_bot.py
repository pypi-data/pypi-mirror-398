"""
Generated Python class from round-ended-event-for-bot.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .results_for_bot import ResultsForBot

class RoundEndedEventForBot(Message):
    """Event occurring when a round has ended. Gives all game results visible for a bot."""

    def __init__(self, round_number: int | None, turn_number: int | None, results: ResultsForBot | None, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if turn_number is None:
            raise ValueError("The 'turn_number' parameter must be provided.")
        if results is None:
            raise ValueError("The 'results' parameter must be provided.")
        if round_number is None:
            raise ValueError("The 'round_number' parameter must be provided.")
        super().__init__(type)
        self.round_number = round_number
        self.turn_number = turn_number
        self.results = results
