import os
from typing import List, Dict, Any
from openai import OpenAI

from models.konbini_session import SessionData

GPT_KEY = os.getenv('OPENAI_KEY')
openai_client = OpenAI(
    api_key=GPT_KEY
)

async def ask_gpt(message: str, 
                  messages: List[Dict[str, Any]] = None, 
                  model_name: str = "gpt-3.5-turbo",
                  # Low temperature to make use of our fine-tuned models
                  temperature: float = 0.1):
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

async def ask_gpt_session(message: str, session_data: SessionData):
    # Format the message list from sessionData format
    messages = [{
        "role": "system",
        "content": session_data.system_message
    }]
    unformatted_messages = session_data.get_chat_history()
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

    model = session_data.model_name
    try:
        answer = await ask_gpt(message, messages, model)
        session_data.add_chat_history((message, answer))
        return answer
    except Exception as e:
        print(e)
        print("Request to ChatGPT failed. Not including conversation history.")
        return ""

async def ask_gpt_result(session_data: SessionData):
    messages = [{
        "role": "system",
        "content": "Below is a transcript of a conversation between a konbini clerk and a customer. Your job is to read through the transcript and determine whether or not the customer was able to complete a set of objectives. Return a list of True or False values, where the order corresponds to the order of the listed objectives. Don’t return any explanation, just a list in the form: '1,0,0', for example. 1 is True, and don't include the quotes. The objectives are copied below, and the conversation transcript below that."
    }]

    chat_history_str = session_data.get_chat_history_as_string()
    objectives_str = session_data.mission.stringify_objectives_for_result()
    message = f"Objectives:\n{objectives_str}\n\nConversation:\n{chat_history_str}"

    try:
        answer = await ask_gpt(message, messages)
        return answer
    except Exception as e:
        print(e)
        print("Request to ChatGPT failed. Not including conversation history.")
        return ""