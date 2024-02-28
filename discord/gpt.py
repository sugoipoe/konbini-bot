import os
from openai import OpenAI

GPT_KEY = os.getenv('OPENAI_KEY')
openai_client = OpenAI(
    api_key=GPT_KEY
)

async def ask_gpt(message: str):
    # Define your prompt here
    prompt = """You are a Japanese コンビニ clerk.
    Please only respond in Japanese.
    Speak formally like a clerk would.
    Assume that I am purchasing one of the following: microwaveable curry, a coffee, or a large bottle of water.
    Consider the following questions, depending on what you decide I am purchasing.
    - Do you need a bag?
    - Would you like me to heat it up?
    - Do you have a point card?
    At the start, comment on what I am purchasing (so that I know what it is too).
    """

    # Concatenate the prompt with the user's message to form the full input
    full_message = prompt + message

    response = openai_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": full_message
            }
        ],
        model="gpt-3.5-turbo",
    )

    answer = response.choices[0].message.content
    return answer
