"""
Generated Python class from bot-state-with-id.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .bot_state import BotState
from .color import Color

class BotStateWithId(BotState):
    """Current state of a bot, which included an id"""

    def __init__(self, id: int | None, session_id: str | None, energy: float | None, x: float | None, y: float | None, direction: float | None, gun_direction: float | None, radar_direction: float | None, radar_sweep: float | None, speed: float | None, turn_rate: float | None, gun_turn_rate: float | None, radar_turn_rate: float | None, gun_heat: float | None, enemy_count: int | None, std_out: str | None = None, std_err: str | None = None, debug_graphics: str | None = None, is_droid: bool | None = None, body_color: Color | None = None, turret_color: Color | None = None, radar_color: Color | None = None, bullet_color: Color | None = None, scan_color: Color | None = None, tracks_color: Color | None = None, gun_color: Color | None = None, is_debugging_enabled: bool | None = None):
        if x is None:
            raise ValueError("The 'x' parameter must be provided.")
        if radar_turn_rate is None:
            raise ValueError("The 'radar_turn_rate' parameter must be provided.")
        if session_id is None:
            raise ValueError("The 'session_id' parameter must be provided.")
        if radar_direction is None:
            raise ValueError("The 'radar_direction' parameter must be provided.")
        if direction is None:
            raise ValueError("The 'direction' parameter must be provided.")
        if enemy_count is None:
            raise ValueError("The 'enemy_count' parameter must be provided.")
        if turn_rate is None:
            raise ValueError("The 'turn_rate' parameter must be provided.")
        if y is None:
            raise ValueError("The 'y' parameter must be provided.")
        if id is None:
            raise ValueError("The 'id' parameter must be provided.")
        if gun_direction is None:
            raise ValueError("The 'gun_direction' parameter must be provided.")
        if speed is None:
            raise ValueError("The 'speed' parameter must be provided.")
        if energy is None:
            raise ValueError("The 'energy' parameter must be provided.")
        if radar_sweep is None:
            raise ValueError("The 'radar_sweep' parameter must be provided.")
        if gun_heat is None:
            raise ValueError("The 'gun_heat' parameter must be provided.")
        if gun_turn_rate is None:
            raise ValueError("The 'gun_turn_rate' parameter must be provided.")
        super().__init__(energy, x, y, direction, gun_direction, radar_direction, radar_sweep, speed, turn_rate, gun_turn_rate, radar_turn_rate, gun_heat, enemy_count, is_droid, body_color, turret_color, radar_color, bullet_color, scan_color, tracks_color, gun_color, is_debugging_enabled)
        self.id = id
        self.session_id = session_id
        self.std_out = std_out
        self.std_err = std_err
        self.debug_graphics = debug_graphics
