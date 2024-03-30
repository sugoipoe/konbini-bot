from dataclasses import dataclass, field
from typing import List

@dataclass
# TODO move to a new file when we have more session types
class SessionData:
    """A class to represent general session data."""
    system_message: str = ""
    model_name: str = ""

    chat_history: List[(str, str)] = field(default_factory=list)
    conversation_difficulty: int = 50  # This is essentially the speed of chat passed to VoiceVox
    user: str = ""

    def get_chat_history(self):
        return self.chat_history
    
    def add_chat_history(self, prompt_response_tuple):
        self.chat_history.append(prompt_response_tuple)
        return

@dataclass
class KonbiniSession(SessionData):
    """A class to represent a Konbini-specific session, inheriting from SessionData."""
    # Add Konbini-specific parameters here as needed
    # For now, it inherits all attributes from SessionData without adding new ones

    system_message = "You are a clerk at a Japanese convienence store. You will check out the items brought by the customer, and provide change, a bag, etc. appropriately as needed."
    model_name = "ft:gpt-3.5-turbo-1106:personal:konbini-chatcomp:97phX4ud"
