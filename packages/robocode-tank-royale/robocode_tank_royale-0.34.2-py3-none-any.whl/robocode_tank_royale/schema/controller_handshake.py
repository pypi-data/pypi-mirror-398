"""
Generated Python class from controller-handshake.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message

class ControllerHandshake(Message):
    """Controller handshake"""

    def __init__(self, session_id: str | None, name: str | None, version: str | None, type: 'Message.Type | None', author: str | None = None, secret: str | None = None):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if name is None:
            raise ValueError("The 'name' parameter must be provided.")
        if version is None:
            raise ValueError("The 'version' parameter must be provided.")
        if session_id is None:
            raise ValueError("The 'session_id' parameter must be provided.")
        super().__init__(type)
        self.session_id = session_id
        self.name = name
        self.version = version
        self.author = author
        self.secret = secret
