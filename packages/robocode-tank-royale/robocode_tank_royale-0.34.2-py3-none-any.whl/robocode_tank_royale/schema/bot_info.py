"""
Generated Python class from bot-info.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .bot_handshake import BotHandshake
from .initial_position import InitialPosition

class BotInfo(BotHandshake):
    """Bot info"""

    def __init__(self, host: str | None, port: int | None, session_id: str | None, name: str | None, version: str | None, authors: list[str | None] | None, type: 'Message.Type | None', description: str | None = None, homepage: str | None = None, country_codes: list[str | None] | None = None, game_types: list[str | None] | None = None, platform: str | None = None, programming_lang: str | None = None, initial_position: InitialPosition | None = None, team_id: int | None = None, team_name: str | None = None, team_version: str | None = None, is_droid: bool | None = None, secret: str | None = None):
        if port is None:
            raise ValueError("The 'port' parameter must be provided.")
        if host is None:
            raise ValueError("The 'host' parameter must be provided.")
        if version is None:
            raise ValueError("The 'version' parameter must be provided.")
        if authors is None:
            raise ValueError("The 'authors' parameter must be provided.")
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        if name is None:
            raise ValueError("The 'name' parameter must be provided.")
        if session_id is None:
            raise ValueError("The 'session_id' parameter must be provided.")
        super().__init__(session_id, name, version, authors, type, description, homepage, country_codes, game_types, platform, programming_lang, initial_position, team_id, team_name, team_version, is_droid, secret)
        self.host = host
        self.port = port
