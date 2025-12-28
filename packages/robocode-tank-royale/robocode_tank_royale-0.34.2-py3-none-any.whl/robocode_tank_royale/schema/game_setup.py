"""
Generated Python class from game-setup.schema.yaml
This file is auto-generated. Do not edit manually.
"""


class GameSetup:
    """Game setup"""

    def __init__(self, game_type: str | None, arena_width: int | None, is_arena_width_locked: bool | None, arena_height: int | None, is_arena_height_locked: bool | None, min_number_of_participants: int | None, is_min_number_of_participants_locked: bool | None, is_max_number_of_participants_locked: bool | None, number_of_rounds: int | None, is_number_of_rounds_locked: bool | None, gun_cooling_rate: float | None, is_gun_cooling_rate_locked: bool | None, max_inactivity_turns: int | None, is_max_inactivity_turns_locked: bool | None, turn_timeout: int | None, is_turn_timeout_locked: bool | None, ready_timeout: int | None, is_ready_timeout_locked: bool | None, default_turns_per_second: int | None, max_number_of_participants: int | None = None):
        if arena_width is None:
            raise ValueError("The 'arena_width' parameter must be provided.")
        if ready_timeout is None:
            raise ValueError("The 'ready_timeout' parameter must be provided.")
        if game_type is None:
            raise ValueError("The 'game_type' parameter must be provided.")
        if is_min_number_of_participants_locked is None:
            raise ValueError("The 'is_min_number_of_participants_locked' parameter must be provided.")
        if is_number_of_rounds_locked is None:
            raise ValueError("The 'is_number_of_rounds_locked' parameter must be provided.")
        if max_inactivity_turns is None:
            raise ValueError("The 'max_inactivity_turns' parameter must be provided.")
        if default_turns_per_second is None:
            raise ValueError("The 'default_turns_per_second' parameter must be provided.")
        if min_number_of_participants is None:
            raise ValueError("The 'min_number_of_participants' parameter must be provided.")
        if is_max_inactivity_turns_locked is None:
            raise ValueError("The 'is_max_inactivity_turns_locked' parameter must be provided.")
        if is_turn_timeout_locked is None:
            raise ValueError("The 'is_turn_timeout_locked' parameter must be provided.")
        if is_gun_cooling_rate_locked is None:
            raise ValueError("The 'is_gun_cooling_rate_locked' parameter must be provided.")
        if gun_cooling_rate is None:
            raise ValueError("The 'gun_cooling_rate' parameter must be provided.")
        if is_max_number_of_participants_locked is None:
            raise ValueError("The 'is_max_number_of_participants_locked' parameter must be provided.")
        if arena_height is None:
            raise ValueError("The 'arena_height' parameter must be provided.")
        if is_arena_width_locked is None:
            raise ValueError("The 'is_arena_width_locked' parameter must be provided.")
        if is_ready_timeout_locked is None:
            raise ValueError("The 'is_ready_timeout_locked' parameter must be provided.")
        if number_of_rounds is None:
            raise ValueError("The 'number_of_rounds' parameter must be provided.")
        if turn_timeout is None:
            raise ValueError("The 'turn_timeout' parameter must be provided.")
        if is_arena_height_locked is None:
            raise ValueError("The 'is_arena_height_locked' parameter must be provided.")
        self.game_type = game_type
        self.arena_width = arena_width
        self.is_arena_width_locked = is_arena_width_locked
        self.arena_height = arena_height
        self.is_arena_height_locked = is_arena_height_locked
        self.min_number_of_participants = min_number_of_participants
        self.is_min_number_of_participants_locked = is_min_number_of_participants_locked
        self.max_number_of_participants = max_number_of_participants
        self.is_max_number_of_participants_locked = is_max_number_of_participants_locked
        self.number_of_rounds = number_of_rounds
        self.is_number_of_rounds_locked = is_number_of_rounds_locked
        self.gun_cooling_rate = gun_cooling_rate
        self.is_gun_cooling_rate_locked = is_gun_cooling_rate_locked
        self.max_inactivity_turns = max_inactivity_turns
        self.is_max_inactivity_turns_locked = is_max_inactivity_turns_locked
        self.turn_timeout = turn_timeout
        self.is_turn_timeout_locked = is_turn_timeout_locked
        self.ready_timeout = ready_timeout
        self.is_ready_timeout_locked = is_ready_timeout_locked
        self.default_turns_per_second = default_turns_per_second
