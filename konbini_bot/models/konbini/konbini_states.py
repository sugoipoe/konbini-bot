from models.game_state import GameState

class StartState(GameState):
    def __init__(self):
        super().__init__(
            name="start",
            prompt="You're at the entrance of the konbini. What do you want to do?\n"
                   "1. Go to the fridge\n"
                   "2. Go to the heated drinks section\n"
                   "3. Walk through the aisles\n"
                   "4. Go to the checkout counter\n",
            options={"1": "fridge", "2": "heated_section", "3": "aisles", "4": "checkout"}
        )

class FridgeState(GameState):
    def __init__(self):
        super().__init__(
            name="fridge",
            prompt="You're at the fridge. What do you want to do?\n"
                   "1. Pick up onigiri A\n"
                   "2. Pick up onigiri B\n"
                   "3. Pick up onigiri C\n"
                   "4. Go back\n"
                   "5. Checkout\n",
            options={"1": "inspect_tsuna_mayo_onigiri", "2": "inspect_shake_onigiri", "3": "inspect_ebi_onigiri", "4": "start", "5": "checkout"}
        )

class HeatedSectionState(GameState):
    def __init__(self):
        super().__init__(
            name="heated_section",
            prompt="You're at the heated drinks section. What do you want to do?\n"
                   "1. Pick up drink A\n"
                   "2. Pick up drink B\n"
                   "3. Pick up drink C\n"
                   "4. Go back"
                   "5. Checkout",
            options={"1": "inspect_drink_a", "2": "inspect_drink_b", "3": "inspect_drink_c", "4": "start"}
        )

class AislesState(GameState):
    def __init__(self):
        super().__init__(
            name="aisles",
            prompt="You're walking through the aisles. What do you want to do?\n"
                   "1. Pick up item A\n"
                   "2. Pick up item B\n"
                   "3. Pick up item C\n"
                   "4. Go back"
                   "5. Checkout",
            options={"1": "inspect_item_a", "2": "inspect_item_b", "3": "inspect_item_c", "4": "start"}
        )

class InspectState(GameState):
    image_map = {
        #"ebi_onigiri": "images/ebi_onigiri.jpeg",
        "shake_onigiri": "images/shake_onigiri.jpg",
        "tsuna_mayo_onigiri": "images/tsuna_mayo_onigiri.jpg",
        "coffee": "images/coffee.webp",
    }  # Fill with items -> image 

    last_state = ""

    def __init__(self, item_name, last_state):
        super().__init__(
            name=f"inspect_{item_name}",
            prompt=f"You're inspecting the {item_name}. What do you want to do?\n"
                   "1. Keep it\n"
                   "2. Return it\n",
            options={"1": "keep", "2": "return"}
        )
        self.held_item_image = self.image_map.get(item_name)
        self.last_state = last_state

class CheckoutState(GameState):
    # This is always the final state -- after this, the scenario ends.
    def __init__(self):
        super().__init__(
            name="checkout",
            prompt="You're at the checkout counter. konbini clerk is waiting for you in #konbini-test!\n",
            options={}
        )
# Add more states as needed...