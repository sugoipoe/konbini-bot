import os
from typing import List, Dict, Any
from openai import OpenAI

from models.konbini_session import SessionData

GPT_KEY = os.getenv('OPENAI_KEY')
openai_client = OpenAI(
    api_key=GPT_KEY
)

async def ask_gpt(message: str, messages: List[Dict[str, Any]] = None, model_name: str = "gpt-3.5-turbo"):
    if not messages:
        messages = [{
            "role": "system",
            "content": "You are a Japanese speaking chat bot. Respond to the user's prompts in Japanese!"
        }]
    # Add the user prompt as the final message
    messages.append({
        "role": "user",
        "content": message
    })

    # Concatenate the prompt with the user's message to form the full input
    response = openai_client.chat.completions.create(
        messages=messages,
        model=model_name
    )

    answer = response.choices[0].message.content
    return answer

async def ask_gpt_session(message: str, sessionData: SessionData):
    # Format the message list from sessionData format
    messages = [{
        "role": "system",
        "content": sessionData.system_message
    }]
    unformatted_messages = sessionData.get_chat_history()
    for prompt_response_tuple in unformatted_messages:
        prompt, response = prompt_response_tuple
        messages.extend([
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "assistant",
                "content": response
            }
        ])

    model = sessionData.model_name
    try:
        answer = ask_gpt(message, messages, model)
        sessionData.add_chat_history((message, answer))
        return answer
    except Exception as e:
        print(e)
        print("Request to ChatGPT failed. Not including conversation history.")
