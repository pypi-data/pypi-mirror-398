"""
Generated Python class from resume-game.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class ResumeGame(Message):
    """Command to resume a game"""

    def __init__(self, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
