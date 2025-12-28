"""
Generated Python class from game-ended-event-for-observer.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .results_for_observer import ResultsForObserver

class GameEndedEventForObserver(Message):
    """Event occurring when game has ended. Gives all game results visible for an observer."""

    def __init__(self, number_of_rounds: int | None, results: list[ResultsForObserver | None] | None, type: 'Message.Type | None'):
        if number_of_rounds is None:
            raise ValueError("The 'number_of_rounds' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if results is None:
            raise ValueError("The 'results' parameter must be provided.")
        super().__init__(type)
        self.number_of_rounds = number_of_rounds
        self.results = results
