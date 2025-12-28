"""
Generated Python class from bot-intent.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .message import Message
from .team_message import TeamMessage
from .color import Color

class BotIntent(Message):
    """The intent (request) sent from a bot each turn for controlling the bot and provide the server with data.
A field only needs to be set, if the value must be changed. Otherwise the server will use the field value from the
last time the field was set.
"""

    def __init__(self, type: 'Message.Type | None', turn_rate: float | None = None, gun_turn_rate: float | None = None, radar_turn_rate: float | None = None, target_speed: float | None = None, firepower: float | None = None, adjust_gun_for_body_turn: bool | None = None, adjust_radar_for_body_turn: bool | None = None, adjust_radar_for_gun_turn: bool | None = None, rescan: bool | None = None, fire_assist: bool | None = None, body_color: Color | None = None, turret_color: Color | None = None, radar_color: Color | None = None, bullet_color: Color | None = None, scan_color: Color | None = None, tracks_color: Color | None = None, gun_color: Color | None = None, std_out: str | None = None, std_err: str | None = None, team_messages: list[TeamMessage | None] | None = None, debug_graphics: str | None = None):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        super().__init__(type)
        self.turn_rate = turn_rate
        self.gun_turn_rate = gun_turn_rate
        self.radar_turn_rate = radar_turn_rate
        self.target_speed = target_speed
        self.firepower = firepower
        self.adjust_gun_for_body_turn = adjust_gun_for_body_turn
        self.adjust_radar_for_body_turn = adjust_radar_for_body_turn
        self.adjust_radar_for_gun_turn = adjust_radar_for_gun_turn
        self.rescan = rescan
        self.fire_assist = fire_assist
        self.body_color = body_color
        self.turret_color = turret_color
        self.radar_color = radar_color
        self.bullet_color = bullet_color
        self.scan_color = scan_color
        self.tracks_color = tracks_color
        self.gun_color = gun_color
        self.std_out = std_out
        self.std_err = std_err
        self.team_messages = team_messages
        self.debug_graphics = debug_graphics
