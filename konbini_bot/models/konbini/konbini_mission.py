from dataclasses import dataclass, field
from typing import List
from models.konbini.konbini_objective import (KonbiniObjective,
    BuyOnigiriObjective,
    BuyCoffeeObjective,
    GetBagObjective,
    GetReceiptObjective
)

@dataclass
class KonbiniMission:
    objectives: List[KonbiniObjective] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)
    player_location: str = "entrance"

    def initialize_objectives(self, difficulty: str = "easy"):
        if difficulty == "easy":
            self.objectives = [
                BuyOnigiriObjective(),
                BuyCoffeeObjective(),
                GetBagObjective(),
                GetReceiptObjective()
            ]

    def get_unfinished_objectives(self):
        for obj in self.objectives:
            if not obj.is_completed(self.inventory):
                yield obj

    def stringify_objectives_for_result(self):
        return "\n".join([obj.description for obj in self.objectives])
