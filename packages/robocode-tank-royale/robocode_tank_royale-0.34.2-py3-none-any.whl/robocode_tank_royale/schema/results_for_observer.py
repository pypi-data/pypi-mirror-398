"""
Generated Python class from results-for-observer.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from .results_for_bot import ResultsForBot

class ResultsForObserver(ResultsForBot):
    """Individual participant results visible for an observer, where id, name, and version is available as well."""

    def __init__(self, id: int | None, name: str | None, version: str | None, rank: int | None, survival: int | None, last_survivor_bonus: int | None, bullet_damage: int | None, bullet_kill_bonus: int | None, ram_damage: int | None, ram_kill_bonus: int | None, total_score: int | None, first_places: int | None, second_places: int | None, third_places: int | None):
        if rank is None:
            raise ValueError("The 'rank' parameter must be provided.")
        if third_places is None:
            raise ValueError("The 'third_places' parameter must be provided.")
        if bullet_damage is None:
            raise ValueError("The 'bullet_damage' parameter must be provided.")
        if last_survivor_bonus is None:
            raise ValueError("The 'last_survivor_bonus' parameter must be provided.")
        if bullet_kill_bonus is None:
            raise ValueError("The 'bullet_kill_bonus' parameter must be provided.")
        if ram_kill_bonus is None:
            raise ValueError("The 'ram_kill_bonus' parameter must be provided.")
        if name is None:
            raise ValueError("The 'name' parameter must be provided.")
        if second_places is None:
            raise ValueError("The 'second_places' parameter must be provided.")
        if ram_damage is None:
            raise ValueError("The 'ram_damage' parameter must be provided.")
        if version is None:
            raise ValueError("The 'version' parameter must be provided.")
        if first_places is None:
            raise ValueError("The 'first_places' parameter must be provided.")
        if id is None:
            raise ValueError("The 'id' parameter must be provided.")
        if survival is None:
            raise ValueError("The 'survival' parameter must be provided.")
        if total_score is None:
            raise ValueError("The 'total_score' parameter must be provided.")
        super().__init__(rank, survival, last_survivor_bonus, bullet_damage, bullet_kill_bonus, ram_damage, ram_kill_bonus, total_score, first_places, second_places, third_places)
        self.id = id
        self.name = name
        self.version = version
