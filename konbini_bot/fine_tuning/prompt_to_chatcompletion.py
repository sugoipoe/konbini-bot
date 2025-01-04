# -*- coding: utf-8 -*-
import json

def convert_to_multiturn_format_json(json_data):
    converted_data = []
    # for json_blob in big_json:
    for json_blob in json_data:
        # set prompt & completion
        prompt = json_blob.get("prompt")
        completion = json_blob.get("completion")

        # split prompt by newlines
        dialogue_lines = prompt.split("\n")
        dialogue_lines.append(completion) # Last line is an extra dialogue

        # create vars for: system, user, assistant. Actually the item list will be the first user prompt.
        system_message, user_messages, assistant_messages = [], [], []
        try:
            for line in dialogue_lines:
                if line.startswith("items"):
                    user_messages.append(line)
                if line.startswith("お"):
                    user_messages.append(line.split("：")[1])
                if line.startswith("て"):
                    assistant_messages.append(line.split("：")[1])
        except Exception as e:
            import pdb; pdb.set_trace()
        
        # This will be a single dialogue in the chat completion format
        chat_completion_blob = {
            "messages": [
                {"role": "system", "content": "You are a clerk at a Japanese convienence store. You will check out the items brought by the customer, and provide change, a bag, etc. appropriately as needed."}
            ]
        }
        try:
            for index, line in enumerate(user_messages):
                # Technically shouldn't error out if our data is good
                user_message = {"role": "user", "content": user_messages[index]}
                assistant_message = {"role": "assistant", "content": assistant_messages[index]}
                chat_completion_blob['messages'].append(user_message)
                chat_completion_blob['messages'].append(assistant_message)
        except Exception as e:
            print(e)
            import pdb; pdb.set_trace()

        converted_data.append(chat_completion_blob)
    
    return converted_data


json_test_data = [
    {
        "prompt": "items: smoothie\nて：いらっしゃいませ。はい、１５８円でございます\nお：スイカで",
        "completion": "て：ありがとうございます"
    },
    {
        "prompt": "items: onigiri, potato chips, fruit sando\nて：いらっしゃいませ、どうぞ。４２１円です\nお： はい、現金で\nて：はい１０２１円お預かりします。６００円のお返しです。\nお：はい\nて：レシートは大丈夫ですか？\nお：あ、要らないです。",
        "completion": "て：ありがとうございます"
    }
]

json_file_path = "video_only_final_lines.json"
with open(json_file_path, 'r', encoding='utf-8') as file:
    json_real_data = json.load(file)


"""
Example of expected output
{"messages": [
    {"role": "system", "content": "Marv is a factual chatbot that is also sarcastic."}, 
    {"role": "user", "content": "What's the capital of France?"}, 
    {"role": "assistant", "content": "Paris", "weight": 0}, 
    {"role": "user", "content": "Can you be more sarcastic?"}, 
    {"role": "assistant", "content": "Paris, as if everyone doesn't know that already.", "weight": 1}
]}

"""

# Convert the JSONL data
converted_data = convert_to_multiturn_format_json(json_real_data)

# Convert the JSON object to a pretty-printed string
pretty_json = json.dumps(converted_data, indent=4, ensure_ascii=False)

# Print the pretty-printed JSON
print(pretty_json)

