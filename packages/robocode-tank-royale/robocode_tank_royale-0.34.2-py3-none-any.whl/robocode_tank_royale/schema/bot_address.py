"""
Generated Python class from bot-address.schema.yaml
This file is auto-generated. Do not edit manually.
"""


class BotAddress:
    """Bot address"""

    def __init__(self, host: str | None, port: int | None):
        if port is None:
            raise ValueError("The 'port' parameter must be provided.")
        if host is None:
            raise ValueError("The 'host' parameter must be provided.")
        self.host = host
        self.port = port
