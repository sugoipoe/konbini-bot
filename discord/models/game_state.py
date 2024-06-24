class GameState:
    def __init__(self, name, prompt, options):
        self.name = name
        self.prompt = prompt
        self.options = options

class StartState(GameState):
    def __init__(self):
        super().__init__(
            name="start",
            prompt="You're at the entrance of the konbini. What do you want to do?\n"
                   "1. Go to the fridge\n"
                   "2. Go to the heated section\n"
                   "3. Walk the aisles\n"
                   "4. Go to the checkout counter\n"
                   "5. Leave",
            options={"1": "go_to_counter", "2": "go_to_fridge", "3": "go_to_heated_section", "4": "default"}
        )

class FridgeState(GameState):
    def __init__(self):
        super().__init__(
            name="fridge",
            prompt="You're at the fridge. What do you want to do?\n"
                   "1. Pick up onigiri A\n"
                   "2. Pick up onigiri B\n"
                   "3. Pick up onigiri C\n"
                   "4. Go back",
            options={"1": "pick_onigiri_a", "2": "pick_onigiri_b", "3": "pick_onigiri_c", "4": "default"}
        )

class HeatedSectionState(GameState):
    def __init__(self):
        super().__init__(
            name="heated_section",
            prompt="You're at the heated drinks section. What do you want to do?\n"
                   "1. Pick up drink A\n"
                   "2. Pick up drink B\n"
                   "3. Pick up drink C\n"
                   "4. Go back",
            options={"1": "pick_drink_a", "2": "pick_drink_b", "3": "pick_drink_c", "4": "default"}
        )

# Add more states as needed...
