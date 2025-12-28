"""
Generated Python class from bot-state.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .color import Color

class BotState:
    """Current state of a bot, but without an id that must be kept secret from opponent bots"""

    def __init__(self, energy: float | None, x: float | None, y: float | None, direction: float | None, gun_direction: float | None, radar_direction: float | None, radar_sweep: float | None, speed: float | None, turn_rate: float | None, gun_turn_rate: float | None, radar_turn_rate: float | None, gun_heat: float | None, enemy_count: int | None, is_droid: bool | None = None, body_color: Color | None = None, turret_color: Color | None = None, radar_color: Color | None = None, bullet_color: Color | None = None, scan_color: Color | None = None, tracks_color: Color | None = None, gun_color: Color | None = None, is_debugging_enabled: bool | None = None):
        if radar_turn_rate is None:
            raise ValueError("The 'radar_turn_rate' parameter must be provided.")
        if gun_turn_rate is None:
            raise ValueError("The 'gun_turn_rate' parameter must be provided.")
        if energy is None:
            raise ValueError("The 'energy' parameter must be provided.")
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
        if gun_direction is None:
            raise ValueError("The 'gun_direction' parameter must be provided.")
        if speed is None:
            raise ValueError("The 'speed' parameter must be provided.")
        if x is None:
            raise ValueError("The 'x' parameter must be provided.")
        if gun_heat is None:
            raise ValueError("The 'gun_heat' parameter must be provided.")
        if radar_sweep is None:
            raise ValueError("The 'radar_sweep' parameter must be provided.")
        self.is_droid = is_droid
        self.energy = energy
        self.x = x
        self.y = y
        self.direction = direction
        self.gun_direction = gun_direction
        self.radar_direction = radar_direction
        self.radar_sweep = radar_sweep
        self.speed = speed
        self.turn_rate = turn_rate
        self.gun_turn_rate = gun_turn_rate
        self.radar_turn_rate = radar_turn_rate
        self.gun_heat = gun_heat
        self.enemy_count = enemy_count
        self.body_color = body_color
        self.turret_color = turret_color
        self.radar_color = radar_color
        self.bullet_color = bullet_color
        self.scan_color = scan_color
        self.tracks_color = tracks_color
        self.gun_color = gun_color
        self.is_debugging_enabled = is_debugging_enabled
