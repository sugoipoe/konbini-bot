from dataclasses import dataclass, field
from typing import List, Tuple
from discord import File
from models.konbini.konbini_mission import KonbiniMission
from models.konbini.konbini_states import (
    GameState,
    StartState,
    FridgeState,
    HeatedSectionState,
    InspectState,
    CheckoutState
)

@dataclass
# TODO move to a new file when we have more session types
class SessionData:
    """A class to represent general session data."""
    system_message: str
    model_name: str

    chat_history: List[Tuple[str, str]] = field(default_factory=list)
    conversation_difficulty: str = "easy"
    user: str = ""

    def get_chat_history(self):
        return self.chat_history

    def get_chat_history_as_string(self):
        chat_history_str = ""
        for prompt, response in self.chat_history:
            chat_history_str += f"User: {prompt}\nAssistant: {response}\n"
        return chat_history_str

    def add_chat_history(self, prompt_response_tuple):
        self.chat_history.append(prompt_response_tuple)
        return

@dataclass
# TODO: Move to models/konbini directory
class KonbiniSession(SessionData):
    """A class to represent a Konbini-specific session, inheriting from SessionData."""
    # Add Konbini-specific parameters here as needed

    system_message: str = (
        "You are a clerk at a Japanese convienence store. "
        "You will check out the items brought by the customer, "
        "and provide change, a bag, etc. appropriately as needed."
        #"When the user has paid and you are ready to end the conversation, "
        #"say 'ありがとうございます'."
    )
    # GPT params
    model_name: str = "ft:gpt-3.5-turbo-1106:personal:konbini-epochup:9Cwj1gOa:ckpt-step-130"
    temperature: float = 0.1

    def __init__(self, user, difficulty):
        super().__init__(system_message=self.system_message, model_name=self.model_name)
        self.user = user
        self.difficulty = difficulty
        self.current_state = StartState()
        self.states = {
            "start": self.current_state,
            "fridge": FridgeState(),
            "heated_section": HeatedSectionState(),
            "checkout": CheckoutState(),
            # Add other states...
        }

    def initialize_mission(self):
        # Initializes KonbiniMission
        self.mission = KonbiniMission()
        self.mission.initialize_objectives(self.conversation_difficulty)
        pass

    async def prompt_user(self, channel):
        print(f"current state is: {self.current_state.name}")
        if self.current_state.name.startswith("inspect_"):
            await channel.send("You picked this up", files=[File(self.current_state.held_item_image)])

        await channel.send(self.current_state.prompt)

    def continue_text_session(self):
        # If the current state is the checkout state, we return False to indicate to the caller
        # that we want to terminate the loop.
        if self.current_state.name == "checkout":
            return False
        else:
            return True

    async def handle_inspect_state(self, user_choice, channel):
        # If the user chooses to keep the item, add it to the inventory
        if self.current_state.options[user_choice] == "keep":
            item_name = self.current_state.name.split("inspect_")[1]
            self.mission.inventory.append(item_name)
        
        # Move back to the previous state after inspecting
        next_state_name = self.current_state.last_state
        self.current_state = self.states[next_state_name]
        await channel.send(f"You have returned to {next_state_name} state.")

    async def handle_checkout_state(self, channel):
        await channel.send("You're at the checkout counter. konbini clerk is waiting for you in #konbini-test!")

    async def handle_response(self, response, channel):
        user_choice = response.content

        # Temporary check to show inventory
        if response.content == "show inventory":
            await channel.send(self.mission.inventory)
            return

        # Early return if the user's choice is invalid
        if user_choice not in self.current_state.options:
            await channel.send("Invalid option, please try again.")
            return

        # Handle inspect state transitions separately
        if self.current_state.name.startswith("inspect_"):
            await self.handle_inspect_state(user_choice, channel)
            return

        # Transition to the next state based on the user's choice
        next_state_name = self.current_state.options[user_choice]
        if next_state_name.startswith("inspect_"):
            # Transition to an inspect state
            item_name = next_state_name.split("inspect_")[1]
            next_state = InspectState(item_name, self.current_state.name)
            self.current_state = next_state
        else:
            # Transition to a regular state
            self.current_state = self.states[next_state_name]
