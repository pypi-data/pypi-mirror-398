"""
Generated Python class from team-message.schema.yaml
This file is auto-generated. Do not edit manually.
"""


class TeamMessage:
    """Message sent between teammates"""

    def __init__(self, message: str | None, message_type: str | None, receiver_id: int | None = None):
        if message_type is None:
            raise ValueError("The 'message_type' parameter must be provided.")
        if message is None:
            raise ValueError("The 'message' parameter must be provided.")
        self.message = message
        self.message_type = message_type
        self.receiver_id = receiver_id
