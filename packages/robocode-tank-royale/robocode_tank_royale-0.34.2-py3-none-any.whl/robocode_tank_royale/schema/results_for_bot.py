"""
Generated Python class from results-for-bot.schema.yaml
This file is auto-generated. Do not edit manually.
"""


class ResultsForBot:
    """Individual participants results visible for a bot, where name and version is hidden."""

    def __init__(self, rank: int | None, survival: int | None, last_survivor_bonus: int | None, bullet_damage: int | None, bullet_kill_bonus: int | None, ram_damage: int | None, ram_kill_bonus: int | None, total_score: int | None, first_places: int | None, second_places: int | None, third_places: int | None):
        if rank is None:
            raise ValueError("The 'rank' parameter must be provided.")
        if third_places is None:
            raise ValueError("The 'third_places' parameter must be provided.")
        if total_score is None:
            raise ValueError("The 'total_score' parameter must be provided.")
        if bullet_damage is None:
            raise ValueError("The 'bullet_damage' parameter must be provided.")
        if bullet_kill_bonus is None:
            raise ValueError("The 'bullet_kill_bonus' parameter must be provided.")
        if ram_kill_bonus is None:
            raise ValueError("The 'ram_kill_bonus' parameter must be provided.")
        if second_places is None:
            raise ValueError("The 'second_places' parameter must be provided.")
        if ram_damage is None:
            raise ValueError("The 'ram_damage' parameter must be provided.")
        if first_places is None:
            raise ValueError("The 'first_places' parameter must be provided.")
        if survival is None:
            raise ValueError("The 'survival' parameter must be provided.")
        if last_survivor_bonus is None:
            raise ValueError("The 'last_survivor_bonus' parameter must be provided.")
        self.rank = rank
        self.survival = survival
        self.last_survivor_bonus = last_survivor_bonus
        self.bullet_damage = bullet_damage
        self.bullet_kill_bonus = bullet_kill_bonus
        self.ram_damage = ram_damage
        self.ram_kill_bonus = ram_kill_bonus
        self.total_score = total_score
        self.first_places = first_places
        self.second_places = second_places
        self.third_places = third_places
