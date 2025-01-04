from dataclasses import dataclass, field
from typing import List

@dataclass
class KonbiniObjective:
    description: str
    is_complete: bool = False
    required_items: List[str] = field(default_factory=list)

    def check_completion(self, inventory: List[str]):
        pass
    
    def is_completed(self, inventory: List[str]):
        if not self.is_complete:
            self.check_completion(inventory)
        return self.is_complete
    

##### Clerk Objectives #####
@dataclass
class GetBagObjective(KonbiniObjective):
    def __init__(self):
        super().__init__(description="Get a bag", required_items=["bag"])

    def check_completion(self, inventory: List[str]):
        if "bag" in inventory:
            self.is_complete = True

@dataclass
class GetReceiptObjective(KonbiniObjective):
    def __init__(self):
        super().__init__(description="Get a receipt", required_items=["receipt"])

    def check_completion(self, inventory: List[str]):
        if "receipt" in inventory:
            self.is_complete = True

##### Buy Objectives #####
@dataclass
class BuyOnigiriObjective(KonbiniObjective):
    def __init__(self):
        super().__init__(description="Buy onigiri", required_items=["onigiri"])

    def check_completion(self, inventory: List[str]):
        if "onigiri" in inventory:
            self.is_complete = True

@dataclass
class BuyCoffeeObjective(KonbiniObjective):
    def __init__(self):
        super().__init__(description="Buy coffee", required_items=["coffee"])

    def check_completion(self, inventory: List[str]):
        if "coffee" in inventory:
            self.is_complete = True

##### Action Objectives #####
@dataclass
class HeatCurryObjective(KonbiniObjective):
    def __init__(self):
        super().__init__(description="Heat up the curry", required_items=["curry_hot"])

    def check_completion(self, inventory: List[str]):
        if "curry_hot" in inventory:
            self.is_complete = True
